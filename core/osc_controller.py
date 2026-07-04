from pythonosc import udp_client
import logging
from typing import Union, Any

logger = logging.getLogger(__name__)

class OSCController:
    """
    Controlador OSC para OBSBOT Center.
    Envia comandos OSC locales para controlar el PTZ y Tracking de la OBSBOT Tiny 3.
    """
    def __init__(self, ip: str = "127.0.0.1", port: int = 16284):
        self.ip = ip
        self.port = port
        self.client = udp_client.SimpleUDPClient(self.ip, self.port)
        logger.info(f"OSCController inicializado en {self.ip}:{self.port}")

    def send_message(self, address: str, value: Union[int, float, str, Any] = None):
        """Envía un mensaje OSC."""
        try:
            if value is not None:
                self.client.send_message(address, value)
                logger.debug(f"Enviado OSC: {address} {value}")
            else:
                # Algunos comandos no requieren argumentos, pero python-osc permite enviar []
                self.client.send_message(address, [])
                logger.debug(f"Enviado OSC: {address}")
        except Exception as e:
            logger.error(f"Error enviando comando OSC {address}: {e}")

    # =========================================================================
    # Tracking Commands
    # =========================================================================
    # Direcciones y tipos verificados contra la documentación oficial de OBSBOT
    # y proyectos de terceros (probados en Tiny 2 Lite; Tiny 3 Lite debería ser
    # compatible pero los códigos exactos de cada submodo AI no están confirmados
    # todavía para este modelo específico — probar con la cámara delante).

    def wake_camera(self):
        """
        Despierta la cámara si quedó en standby (las OBSBOT Tiny se suspenden
        solas tras inactividad). Comando documentado como "WakeSleep"; el valor
        exacto que corresponde a "despertar" (0 o 1) no está confirmado todavía
        para el Tiny 3 Lite — si no reacciona, probar con 0 en vez de 1.
        """
        self.send_message("/OBSBOT/WebCam/General/WakeSleep", 1)

    def start_tracking(self):
        """Activa el tracking AI (comando dedicado, independiente del submodo)."""
        self.send_message("/OBSBOT/WebCam/Tiny/SetTrackingMode", 1)

    def stop_tracking(self):
        """Detiene el tracking AI."""
        self.send_message("/OBSBOT/WebCam/Tiny/SetTrackingMode", 0)

    def track_human(self):
        """Alias usado por el dispatcher: activa el tracking por defecto."""
        self.start_tracking()

    def set_ai_mode(self, mode: int):
        """
        Cambia el submodo de encuadre AI. Documentado (Tiny 2 Lite): 0=Headroom,
        1=Standard, 2=Motion. PENDIENTE de verificar los códigos que use tu
        Tiny 3 Lite (probablemente tenga más submodos: grupo, pizarra, escritorio...).
        """
        self.send_message("/OBSBOT/WebCam/Tiny/SetAiMode", int(mode))

    # =========================================================================
    # PTZ Commands
    # =========================================================================

    def set_zoom(self, zoom_value: float):
        """Ajusta el zoom. Rango documentado: 0-100 (no 1.0-4.0 como antes)."""
        self.send_message("/OBSBOT/WebCam/General/SetZoom", int(zoom_value))

    def gimbal_reset(self):
        """Resetea el gimbal a su posición inicial."""
        self.send_message("/OBSBOT/WebCam/General/ResetGimbal", 0)

    def gimbal_rotate(self, pan: float, tilt: float, speed: int = 45):
        """Gira el gimbal. speed: 0-90, pan: -129..129, pitch: -59..59."""
        self.send_message("/OBSBOT/WebCam/General/SetGimMotorDegree", [speed, pan, tilt])

if __name__ == "__main__":
    # Prueba rápida
    import time
    logging.basicConfig(level=logging.DEBUG)
    osc = OSCController()
    osc.track_human()
    time.sleep(1)
    osc.stop_tracking()
