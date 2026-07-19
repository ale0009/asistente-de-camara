import threading
from pythonosc import udp_client, osc_server, dispatcher as osc_dispatcher
import logging
from typing import Union, Any

logger = logging.getLogger(__name__)

class OSCController:
    """
    Controlador OSC para OBSBOT Center.

    Direcciones verificadas contra las plantillas oficiales de TouchOSC que
    OBSBOT Center trae en su propia instalación.
    """
    def __init__(self, ip: str = "127.0.0.1", port: int = 16284, feedback_port: int = 16285):
        self.ip = ip
        self.port = port
        self.client = udp_client.SimpleUDPClient(self.ip, self.port)
        
        # Callback para notificar cambios de estado a la UI (tracking: str, zoom: float)
        self.on_status_updated = None
        self.current_tracking_state = "Apagado"
        self.current_zoom_level = 1.0
        
        # Iniciar listener de feedback en segundo plano
        self._server = None
        self._server_thread = None
        self._start_feedback_listener(feedback_port)
        logger.info(f"OSCController inicializado en {self.ip}:{self.port}")

    def _start_feedback_listener(self, port: int):
        try:
            disp = osc_dispatcher.Dispatcher()
            disp.map("/OBSBOT/WebCam/Tiny/AiTrackingInfo", self._handle_tracking_feedback)
            disp.map("/OBSBOT/WebCam/General/ZoomInfo", self._handle_zoom_feedback)
            
            self._server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", port), disp)
            self._server_thread = threading.Thread(
                target=self._server.serve_forever, daemon=True, name="NOVA-OSC-Feedback"
            )
            self._server_thread.start()
            logger.info(f"Servidor de feedback OSC escuchando en el puerto {port}")
        except Exception as e:
            logger.warning(f"No se pudo iniciar el listener de feedback OSC en puerto {port}: {e}")

    def _handle_tracking_feedback(self, address, *args):
        if args:
            val = args[0]
            self.current_tracking_state = "Humano" if val in (1, "1", True) else "Apagado"
            logger.debug(f"Feedback OSC Tracking: {self.current_tracking_state}")
            if self.on_status_updated:
                self.on_status_updated(self.current_tracking_state, self.current_zoom_level)

    def _handle_zoom_feedback(self, address, *args):
        if args:
            try:
                raw_val = float(args[0])
                self.current_zoom_level = round(1.0 + (raw_val / 100.0) * 3.0, 1)
                logger.debug(f"Feedback OSC Zoom: {self.current_zoom_level}x")
                if self.on_status_updated:
                    self.on_status_updated(self.current_tracking_state, self.current_zoom_level)
            except (ValueError, TypeError):
                pass

    def stop(self):
        """Detiene el servidor de feedback si está activo."""
        if self._server:
            try:
                self._server.shutdown()
            except Exception:
                pass

    def send_message(self, address: str, value: Union[int, float, str, Any] = None):
        """Envía un mensaje OSC."""
        try:
            if value is not None:
                self.client.send_message(address, value)
                logger.debug(f"Enviado OSC: {address} {value}")
            else:
                self.client.send_message(address, [])
                logger.debug(f"Enviado OSC: {address}")
        except Exception as e:
            logger.error(f"Error enviando comando OSC {address}: {e}")

    # =========================================================================
    # Tracking / AI Lock
    # =========================================================================
    # El toggle real de seguimiento es "ToggleAILock" — la plantilla oficial no
    # tiene ningún "SetTrackingMode" (esa dirección era una reconstrucción de
    # terceros para el Tiny 2 Lite y no existe en el protocolo real de este
    # modelo, probablemente la causa de que el tracking nunca respondiera).

    def start_tracking(self):
        """Activa el AI Lock (seguimiento)."""
        self.send_message("/OBSBOT/WebCam/Tiny/ToggleAILock", 1)
        self.current_tracking_state = "Humano"
        if self.on_status_updated:
            self.on_status_updated(self.current_tracking_state, self.current_zoom_level)

    def stop_tracking(self):
        """Desactiva el AI Lock (seguimiento)."""
        self.send_message("/OBSBOT/WebCam/Tiny/ToggleAILock", 0)
        self.current_tracking_state = "Apagado"
        if self.on_status_updated:
            self.on_status_updated(self.current_tracking_state, self.current_zoom_level)

    def track_human(self):
        """Alias usado por el dispatcher: activa el tracking por defecto."""
        self.start_tracking()

    def trigger_preset(self, index: int):
        """Va a una posición de cámara preestablecida (0, 1 o 2), guardada antes en OBSBOT Center."""
        self.send_message("/OBSBOT/WebCam/Tiny/TriggerPreset", int(index))

    # =========================================================================
    # Wake / Sleep
    # =========================================================================

    def wake_camera(self):
        """Despierta la cámara si quedó en standby."""
        self.send_message("/OBSBOT/WebCam/General/WakeSleep", 1)

    def sleep_camera(self):
        """Suspende la cámara (mismo comando que wake_camera, valor opuesto)."""
        self.send_message("/OBSBOT/WebCam/General/WakeSleep", 0)

    # =========================================================================
    # Zoom
    # =========================================================================

    def set_zoom(self, zoom_value: float):
        """Ajusta el zoom. Rango oficial: 0-100."""
        self.send_message("/OBSBOT/WebCam/General/SetZoom", int(zoom_value))
        self.current_zoom_level = round(1.0 + (float(zoom_value) / 100.0) * 3.0, 1)
        if self.on_status_updated:
            self.on_status_updated(self.current_tracking_state, self.current_zoom_level)

    def zoom_max(self):
        self.send_message("/OBSBOT/WebCam/General/SetZoomMax", 1)

    def zoom_min(self):
        self.send_message("/OBSBOT/WebCam/General/SetZoomMin", 1)

    # =========================================================================
    # Campo de visión
    # =========================================================================

    def set_view(self, mode: int):
        """Cambia el campo de visión: 0 = 86°, 1 = 78°, 2 = 65°."""
        self.send_message("/OBSBOT/WebCam/General/SetView", int(mode))

    # =========================================================================
    # Gimbal — un comando por dirección (no un solo mensaje con pan/tilt como
    # se asumía antes). El valor 0-100 es la intensidad/velocidad del giro.
    # =========================================================================

    def gimbal_reset(self):
        """Resetea el gimbal a su posición inicial."""
        self.send_message("/OBSBOT/WebCam/General/ResetGimbal", 1)

    def gimbal_up(self, amount: int = 60):
        self.send_message("/OBSBOT/WebCam/General/SetGimbalUp", int(amount))

    def gimbal_down(self, amount: int = 60):
        self.send_message("/OBSBOT/WebCam/General/SetGimbalDown", int(amount))

    def gimbal_left(self, amount: int = 60):
        self.send_message("/OBSBOT/WebCam/General/SetGimbalLeft", int(amount))

    def gimbal_right(self, amount: int = 60):
        self.send_message("/OBSBOT/WebCam/General/SetGimbalRight", int(amount))

    # Alias usados por el dispatcher para "mira a la izquierda/derecha/arriba/abajo"
    def look_left(self):
        self.gimbal_left()

    def look_right(self):
        self.gimbal_right()

    def look_up(self):
        self.gimbal_up()

    def look_down(self):
        self.gimbal_down()

if __name__ == "__main__":
    # Prueba rápida
    import time
    logging.basicConfig(level=logging.DEBUG)
    osc = OSCController()
    osc.track_human()
    time.sleep(1)
    osc.stop_tracking()
