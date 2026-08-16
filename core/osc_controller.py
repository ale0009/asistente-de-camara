import logging
import threading
import time
from collections import deque
from typing import Any, Dict, Optional, Union

from pythonosc import dispatcher as osc_dispatcher
from pythonosc import osc_server, udp_client

logger = logging.getLogger(__name__)


class OSCController:
    """Control OSC para OBSBOT Center con diagnóstico de confirmación.

    UDP no confirma que la cámara física ejecutó una orden. Por eso este
    controlador separa explícitamente el envío local de la confirmación por
    feedback OSC que publica OBSBOT Center.
    """

    def __init__(
        self,
        ip: str = "127.0.0.1",
        port: int = 16284,
        feedback_port: int = 16285,
        feedback_host: str = "127.0.0.1",
        confirmation_timeout_sec: float = 5.0,
    ):
        self.ip = ip
        self.port = port
        self.feedback_host = feedback_host
        self.feedback_port = feedback_port
        self.confirmation_timeout_sec = confirmation_timeout_sec
        self.client = udp_client.SimpleUDPClient(self.ip, self.port)

        # Callbacks opcionales de UI. Se mantiene la firma histórica de
        # on_status_updated para no romper los llamadores existentes.
        self.on_status_updated = None
        self.on_diagnostic_updated = None
        self.current_tracking_state = "Sin confirmar"
        self.current_zoom_level = 1.0
        self.requested_zoom_level: Optional[float] = None
        self.camera_power_state = "Sin confirmar"

        self.last_command: Optional[Dict[str, Any]] = None
        self.command_history = deque(maxlen=30)
        self.last_feedback: Optional[Dict[str, Any]] = None
        self.last_feedback_at: Optional[float] = None
        self.feedback_count = 0
        self.last_send_error: Optional[str] = None
        self.feedback_listener_active = False

        self._server = None
        self._server_thread = None
        self._start_feedback_listener()
        logger.info(
            "OSCController inicializado: envío=%s:%s, feedback=%s:%s",
            self.ip,
            self.port,
            self.feedback_host,
            self.feedback_port,
        )

    # ------------------------------------------------------------------
    # Feedback y estado
    # ------------------------------------------------------------------
    def _start_feedback_listener(self) -> None:
        try:
            disp = osc_dispatcher.Dispatcher()
            disp.map("/OBSBOT/WebCam/Tiny/AiTrackingInfo", self._handle_tracking_feedback)
            disp.map("/OBSBOT/WebCam/General/ZoomInfo", self._handle_zoom_feedback)
            disp.set_default_handler(self._handle_generic_feedback)

            # OBSBOT Center se ejecuta en el mismo equipo. Escuchar solo el
            # loopback evita aceptar paquetes OSC de otros equipos de la LAN.
            self._server = osc_server.ThreadingOSCUDPServer(
                (self.feedback_host, self.feedback_port), disp
            )
            self._server_thread = threading.Thread(
                target=self._server.serve_forever,
                daemon=True,
                name="NOVA-OSC-Feedback",
            )
            self._server_thread.start()
            self.feedback_listener_active = True
            logger.info(
                "Servidor de feedback OSC escuchando en %s:%s",
                self.feedback_host,
                self.feedback_port,
            )
        except Exception as exc:
            self.last_send_error = f"No se pudo abrir feedback OSC: {exc}"
            logger.warning("No se pudo iniciar listener OSC: %s", exc)

    def _record_feedback(self, address: str, args) -> None:
        now = time.time()
        self.last_feedback_at = now
        self.feedback_count += 1
        self.last_feedback = {
            "address": address,
            "args": list(args),
            "received_at": now,
        }
        logger.info("Feedback OSC recibido: %s %s", address, list(args))

    def _handle_generic_feedback(self, address, *args) -> None:
        """Registra feedback oficial no interpretado aún (conexión, preset, etc.)."""
        self._record_feedback(address, args)
        if address == "/OBSBOT/WebCam/General/ConnectedResp":
            self.camera_power_state = "Conexión confirmada"
        self._emit_diagnostic()

    def _handle_tracking_feedback(self, address, *args) -> None:
        if not args:
            return
        value = args[0]
        self._record_feedback(address, args)
        self.current_tracking_state = "Humano" if value in (1, "1", True) else "Apagado"
        self._confirm_last_command("tracking", self.current_tracking_state)
        logger.info("Feedback OSC tracking: %s", self.current_tracking_state)
        self._emit_status()
        self._emit_diagnostic()

    def _handle_zoom_feedback(self, address, *args) -> None:
        if not args:
            return
        try:
            raw_value = float(args[0])
        except (TypeError, ValueError):
            logger.warning("Feedback OSC zoom inválido: %r", args)
            return

        self._record_feedback(address, args)
        self.current_zoom_level = round(1.0 + (raw_value / 100.0) * 3.0, 1)
        self._confirm_last_command("zoom", raw_value)
        logger.info("Feedback OSC zoom: %sx", self.current_zoom_level)
        self._emit_status()
        self._emit_diagnostic()

    def _confirm_last_command(self, feedback_type: str, value: Any) -> None:
        """Marca confirmada una orden solo si el feedback coincide con ella."""
        command = self.last_command
        if not command or command.get("status") != "pending":
            return

        expected = command.get("expected_feedback") or {}
        if expected.get("type") != feedback_type:
            return

        expected_value = expected.get("value")
        matches = value == expected_value
        if feedback_type == "zoom":
            try:
                matches = abs(float(value) - float(expected_value)) <= 1.0
            except (TypeError, ValueError):
                matches = False

        if matches:
            command["status"] = "confirmed"
            command["confirmed_at"] = time.time()
            logger.info("Orden OSC confirmada por feedback: %s", command["action"])
        else:
            command["status"] = "feedback_mismatch"
            command["feedback_value"] = value
            logger.warning(
                "Feedback OSC no coincide con %s: esperado=%r, recibido=%r",
                command["action"],
                expected_value,
                value,
            )

    def _emit_status(self) -> None:
        if self.on_status_updated:
            self.on_status_updated(self.current_tracking_state, self.current_zoom_level)

    def _emit_diagnostic(self) -> None:
        if self.on_diagnostic_updated:
            self.on_diagnostic_updated(self.get_diagnostics())

    # ------------------------------------------------------------------
    # Envío y diagnóstico
    # ------------------------------------------------------------------
    def stop(self) -> None:
        """Detiene el servidor de feedback si está activo."""
        if self._server:
            try:
                self._server.shutdown()
                self._server.server_close()
            except Exception:
                pass
        self.feedback_listener_active = False

    def send_message(self, address: str, value: Union[int, float, str, Any] = None) -> bool:
        """Envía UDP y devuelve si el socket aceptó el paquete localmente.

        Un resultado verdadero no implica que OBSBOT haya ejecutado la acción.
        La confirmación real se obtiene de los mensajes de feedback.
        """
        try:
            if value is not None:
                self.client.send_message(address, value)
                logger.debug("Enviado OSC: %s %s", address, value)
            else:
                self.client.send_message(address, [])
                logger.debug("Enviado OSC: %s", address)
            self.last_send_error = None
            return True
        except Exception as exc:
            self.last_send_error = str(exc)
            logger.error("Error enviando OSC %s: %s", address, exc)
            return False

    def _send_control_command(
        self,
        action: str,
        address: str,
        value: Union[int, float, str, Any],
        expected_feedback: Optional[Dict[str, Any]] = None,
    ) -> bool:
        sent = self.send_message(address, value)
        self.last_command = {
            "action": action,
            "address": address,
            "value": value,
            "sent_at": time.time(),
            "status": "pending" if sent else "send_error",
            "expected_feedback": expected_feedback,
        }
        self.command_history.append(dict(self.last_command))
        self._emit_diagnostic()
        return sent

    def get_diagnostics(self) -> Dict[str, Any]:
        """Estado serializable para UI, voz y futuras APIs locales."""
        last_command = dict(self.last_command) if self.last_command else None
        if last_command:
            age_sec = round(max(0.0, time.time() - last_command["sent_at"]), 1)
            last_command["age_sec"] = age_sec
            if last_command["status"] == "pending" and age_sec > self.confirmation_timeout_sec:
                last_command["status"] = "timeout_without_feedback"

        return {
            "send_endpoint": f"{self.ip}:{self.port}",
            "feedback_endpoint": f"{self.feedback_host}:{self.feedback_port}",
            "feedback_listener_active": self.feedback_listener_active,
            "feedback_count": self.feedback_count,
            "last_feedback": dict(self.last_feedback) if self.last_feedback else None,
            "tracking_state": self.current_tracking_state,
            "zoom_level": self.current_zoom_level,
            "requested_zoom_level": self.requested_zoom_level,
            "camera_power_state": self.camera_power_state,
            "last_command": last_command,
            "last_send_error": self.last_send_error,
        }

    def diagnostic_summary(self) -> str:
        """Resumen breve para TTS sin prometer acciones no confirmadas."""
        diagnostics = self.get_diagnostics()
        listener = "activo" if diagnostics["feedback_listener_active"] else "no disponible"
        command = diagnostics["last_command"]

        if not command:
            command_summary = "aún no se ha enviado ninguna orden en esta sesión"
        else:
            status_map = {
                "confirmed": "confirmada por feedback OSC",
                "pending": "enviada y esperando feedback OSC",
                "timeout_without_feedback": "enviada, pero sin feedback OSC dentro del tiempo esperado",
                "feedback_mismatch": "respondida con un estado distinto al solicitado",
                "send_error": "no pudo enviarse por UDP",
            }
            command_summary = (
                f"última orden: {command['action']}; "
                f"{status_map.get(command['status'], command['status'])}"
            )

        feedback_text = "sí" if diagnostics["last_feedback"] else "no"
        return (
            f"Diagnóstico OBSBOT. Receptor de feedback {listener}. "
            f"Feedback recibido: {feedback_text}. "
            f"Tracking: {diagnostics['tracking_state']}. {command_summary}."
        )

    # ------------------------------------------------------------------
    # Comandos OBSBOT oficiales
    # ------------------------------------------------------------------
    def start_tracking(self) -> str:
        sent = self._send_control_command(
            "activar seguimiento",
            "/OBSBOT/WebCam/Tiny/ToggleAILock",
            1,
            {"type": "tracking", "value": "Humano"},
        )
        self.current_tracking_state = "Pendiente" if sent else "Error de envío"
        self._emit_status()
        return (
            "Orden de seguimiento enviada; esperando confirmación de OBSBOT."
            if sent else "No pude enviar la orden de seguimiento a OBSBOT."
        )

    def stop_tracking(self) -> str:
        sent = self._send_control_command(
            "detener seguimiento",
            "/OBSBOT/WebCam/Tiny/ToggleAILock",
            0,
            {"type": "tracking", "value": "Apagado"},
        )
        self.current_tracking_state = "Pendiente" if sent else "Error de envío"
        self._emit_status()
        return (
            "Orden para detener seguimiento enviada; esperando confirmación de OBSBOT."
            if sent else "No pude enviar la orden para detener el seguimiento."
        )

    def track_human(self) -> str:
        return self.start_tracking()

    def trigger_preset(self, index: int) -> str:
        """Activa un preset interno oficial 0-2 (visible como posición 1-3)."""
        index = int(index)
        if index not in (0, 1, 2):
            return "El preset debe estar entre 1 y 3."
        sent = self._send_control_command(
            f"ir al preset {index + 1}",
            "/OBSBOT/WebCam/Tiny/TriggerPreset",
            index,
        )
        return (
            f"Orden enviada al preset {index + 1}; espera la confirmación visual de la cámara."
            if sent else f"No pude enviar la orden al preset {index + 1}."
        )

    def wake_camera(self) -> str:
        sent = self._send_control_command(
            "despertar cámara", "/OBSBOT/WebCam/General/WakeSleep", 1
        )
        self.camera_power_state = "Despertar pendiente" if sent else "Error de envío"
        return (
            "Orden para despertar la cámara enviada. Verifica el vídeo o consulta el diagnóstico."
            if sent else "No pude enviar la orden para despertar la cámara."
        )

    def sleep_camera(self) -> str:
        sent = self._send_control_command(
            "suspender cámara", "/OBSBOT/WebCam/General/WakeSleep", 0
        )
        self.camera_power_state = "Suspensión pendiente" if sent else "Error de envío"
        return (
            "Orden para suspender la cámara enviada. Verifica el vídeo o consulta el diagnóstico."
            if sent else "No pude enviar la orden para suspender la cámara."
        )

    def set_zoom(self, zoom_value: float) -> str:
        zoom_value = max(0, min(100, int(zoom_value)))
        sent = self._send_control_command(
            f"ajustar zoom a {zoom_value}%",
            "/OBSBOT/WebCam/General/SetZoom",
            zoom_value,
            {"type": "zoom", "value": zoom_value},
        )
        self.requested_zoom_level = zoom_value
        return (
            f"Orden de zoom al {zoom_value} por ciento enviada; esperando confirmación de OBSBOT."
            if sent else "No pude enviar la orden de zoom a OBSBOT."
        )

    def zoom_max(self) -> bool:
        return self._send_control_command("zoom máximo", "/OBSBOT/WebCam/General/SetZoomMax", 1)

    def zoom_min(self) -> bool:
        return self._send_control_command("zoom mínimo", "/OBSBOT/WebCam/General/SetZoomMin", 1)

    def set_view(self, mode: int) -> bool:
        return self._send_control_command(
            "cambiar campo de visión", "/OBSBOT/WebCam/General/SetView", int(mode)
        )

    def gimbal_reset(self) -> bool:
        return self._send_control_command("resetear gimbal", "/OBSBOT/WebCam/General/ResetGimbal", 1)

    def gimbal_up(self, amount: int = 60) -> bool:
        return self._send_control_command("mover gimbal arriba", "/OBSBOT/WebCam/General/SetGimbalUp", int(amount))

    def gimbal_down(self, amount: int = 60) -> bool:
        return self._send_control_command("mover gimbal abajo", "/OBSBOT/WebCam/General/SetGimbalDown", int(amount))

    def gimbal_left(self, amount: int = 60) -> bool:
        return self._send_control_command("mover gimbal izquierda", "/OBSBOT/WebCam/General/SetGimbalLeft", int(amount))

    def gimbal_right(self, amount: int = 60) -> bool:
        return self._send_control_command("mover gimbal derecha", "/OBSBOT/WebCam/General/SetGimbalRight", int(amount))

    def look_left(self) -> bool:
        return self.gimbal_left()

    def look_right(self) -> bool:
        return self.gimbal_right()

    def look_up(self) -> bool:
        return self.gimbal_up()

    def look_down(self) -> bool:
        return self.gimbal_down()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    osc = OSCController()
    print(osc.track_human())
    time.sleep(1)
    print(osc.diagnostic_summary())
    osc.stop()
