import cv2
import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)

class CameraController:
    """
    Controlador para la captura de video UVC de la cámara.
    Maneja el stream en un hilo separado para no bloquear la aplicación principal.
    """
    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 360):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        
        self.cap: Optional[cv2.VideoCapture] = None
        self.current_frame = None
        
        self.is_running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Inicia la captura de la cámara en un hilo en segundo plano."""
        if self.is_running:
            return

        logger.info(f"Intentando abrir cámara en índice {self.camera_index}...")
        # cv2.CAP_DSHOW es mejor en Windows
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                logger.info(f"¡Cámara abierta exitosamente en índice {self.camera_index}!")
            else:
                logger.error("La cámara se abrió pero no puede leer frames.")
        else:
            logger.error(f"No se pudo abrir la cámara en el índice {self.camera_index}")
            self.cap = None
            return

        # Configurar resolución
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        self.is_running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def _capture_loop(self):
        """Bucle continuo para leer frames."""
        while self.is_running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = frame
            else:
                logger.warning("Fallo al leer frame de la cámara")
                # Pequeña pausa para no saturar el CPU si la cámara se desconecta temporalmente
                cv2.waitKey(100)

    def get_frame(self):
        """Devuelve el último frame capturado."""
        return self.current_frame

    def stop(self):
        """Detiene la captura y libera recursos."""
        logger.info("Deteniendo cámara...")
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.current_frame = None
        logger.info("Cámara detenida.")

if __name__ == "__main__":
    # Prueba rápida
    import time
    logging.basicConfig(level=logging.DEBUG)
    cam = CameraController()
    cam.start()
    
    start_time = time.time()
    while time.time() - start_time < 5:
        frame = cam.get_frame()
        if frame is not None:
            cv2.imshow("Prueba Camara", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    cam.stop()
    cv2.destroyAllWindows()
