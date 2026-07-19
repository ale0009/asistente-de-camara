import cv2
import logging
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)


def find_camera_index_by_name(name_substring: str) -> Optional[int]:
    """Busca el índice DirectShow de una cámara por nombre de dispositivo.

    El índice numérico que usa cv2.VideoCapture(i, cv2.CAP_DSHOW) depende del
    orden de enumeración de Windows, que puede cambiar solo entre sesiones
    (ya pasó: el OBSBOT saltó de índice 1 a 0 sin razón aparente). pygrabber
    enumera los mismos dispositivos DirectShow por nombre, así que resolver
    el índice por nombre en cada arranque evita depender de ese orden.
    Devuelve None si pygrabber no está disponible o no encuentra coincidencia
    (el llamador debe usar camera_index de config.yaml como fallback).
    """
    if not name_substring:
        return None
    try:
        from pygrabber.dshow_graph import FilterGraph
        import pythoncom
    except ImportError:
        logger.warning("pygrabber no está instalado; no se puede detectar la cámara por nombre.")
        return None

    # pygrabber usa COM (vía comtypes) y COM requiere que CADA hilo que lo usa
    # llame CoInitialize primero — el hilo principal lo tiene inicializado
    # implícitamente (comtypes lo hace al importarse por primera vez), pero
    # el hilo de captura de la cámara (usado al reconectar tras una
    # desconexión) no, y sin esto fallaba con
    # "[WinError -2147221008] No se ha llamado a CoInitialize". Llamar
    # CoInitialize/CoUninitialize en pareja es seguro incluso si el hilo ya
    # lo tenía inicializado (devuelve S_FALSE, no es un error).
    pythoncom.CoInitialize()
    try:
        devices = FilterGraph().get_input_devices()
    except Exception as e:
        logger.warning(f"No se pudo enumerar cámaras DirectShow: {e}")
        return None
    finally:
        pythoncom.CoUninitialize()

    name_lower = name_substring.lower()
    for index, device_name in enumerate(devices):
        if name_lower in device_name.lower():
            logger.info(f"Cámara '{device_name}' encontrada por nombre en índice {index}.")
            return index

    logger.warning(f"Ninguna cámara con nombre que contenga '{name_substring}' encontrada.")
    return None


def get_available_cameras() -> dict:
    """Devuelve un diccionario {índice: nombre_cámara} con las cámaras DirectShow conectadas al sistema."""
    cameras = {}
    try:
        from pygrabber.dshow_graph import FilterGraph
        import pythoncom
        pythoncom.CoInitialize()
        try:
            devices = FilterGraph().get_input_devices()
            for index, device_name in enumerate(devices):
                cameras[index] = device_name
        finally:
            pythoncom.CoUninitialize()
    except Exception as e:
        logger.warning(f"No se pudieron enumerar cámaras con pygrabber ({e}). Probando escaneo DirectShow...")

    # Si pygrabber no devolvió nada, hacer escaneo secundario con cv2
    if not cameras:
        for i in range(4):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                cameras[i] = f"Cámara Video #{i}"
                cap.release()
    return cameras


# Lecturas fallidas consecutivas antes de considerar la cámara desconectada
# e intentar reabrirla (a ~100ms por intento fallido, ~5s de margen para no
# reaccionar a un simple hipo momentáneo del stream USB).
RECONNECT_AFTER_FAILURES = 50
# Pausa entre intentos de reconexión mientras la cámara sigue sin responder,
# para no ocupar el CPU reabriendo el dispositivo en bucle cerrado.
RECONNECT_RETRY_DELAY_SEC = 2.0


class CameraController:
    """
    Controlador para la captura de video UVC de la cámara.
    Maneja el stream en un hilo separado para no bloquear la aplicación principal.
    """
    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 360, device_name: str = None):
        self.camera_index = camera_index
        self.device_name = device_name
        self.width = width
        self.height = height

        self.cap: Optional[cv2.VideoCapture] = None
        self.current_frame = None
        # Protege current_frame: se escribe desde _capture_loop y se lee
        # desde el hilo de visión de main.py (get_frame) sin ninguna
        # sincronización antes — funcionaba por el GIL de CPython, pero no
        # es una garantía documentada.
        self._frame_lock = threading.Lock()

        self.is_running = False
        self._thread: Optional[threading.Thread] = None

        # Callbacks opcionales (main.py los conecta a avisos visibles en la
        # UI) — antes, si se desconectaba la cámara a mitad de sesión, el
        # video se congelaba para siempre sin ningún aviso ni intento de
        # reconexión.
        self.on_camera_disconnected = None
        self.on_camera_reconnected = None

    def get_available_cameras(self) -> dict:
        """Devuelve las cámaras disponibles conectadas."""
        return get_available_cameras()

    def set_camera(self, index: int, device_name: str = "") -> bool:
        """Cambia el dispositivo de cámara activo y guarda la preferencia en config.yaml."""
        logger.info(f"Cambiando cámara activa al índice {index} ({device_name})...")
        self.camera_index = index
        if device_name:
            self.device_name = device_name

        # Persistir en config.yaml
        try:
            import os
            import yaml
            if os.path.exists("config.yaml"):
                with open("config.yaml", "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                if "camera" not in cfg:
                    cfg["camera"] = {}
                cfg["camera"]["camera_index"] = index
                if device_name:
                    cfg["camera"]["camera_name"] = device_name
                with open("config.yaml", "w", encoding="utf-8") as f:
                    yaml.safe_dump(cfg, f, default_flow_style=False, allow_unicode=True)
                logger.info("config.yaml actualizado con la nueva cámara.")
        except Exception as e:
            logger.error(f"Error al guardar preferencia de cámara en config.yaml: {e}")

        # Forzar reapertura del dispositivo si la cámara está activa
        if self.is_running and self.cap:
            try:
                self.cap.release()
                self.cap = None
                logger.info("Dispositivo de cámara liberado; se reabrirá con el nuevo índice.")
                return True
            except Exception as e:
                logger.error(f"Error al reabrir stream de cámara: {e}")
                return False
        return True

    def _open_capture(self) -> bool:
        """Resuelve el índice (por nombre si es posible) y abre cv2.VideoCapture.

        Se usa tanto en start() como al reintentar reconectar desde
        _capture_loop tras una desconexión — el índice se vuelve a resolver
        por nombre cada vez porque Windows puede reordenar los dispositivos
        entre una desconexión física y su reconexión.
        """
        resolved_index = find_camera_index_by_name(self.device_name)
        if resolved_index is not None:
            self.camera_index = resolved_index
        else:
            logger.info(f"Usando camera_index de config.yaml como fallback: {self.camera_index}")

        logger.info(f"Intentando abrir cámara en índice {self.camera_index}...")
        # cv2.CAP_DSHOW es mejor en Windows
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)

        if not cap.isOpened():
            logger.error(f"No se pudo abrir la cámara en el índice {self.camera_index}")
            cap.release()
            return False

        ret, _ = cap.read()
        if not ret:
            logger.error("La cámara se abrió pero no puede leer frames.")
            cap.release()
            return False

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap = cap
        logger.info(f"¡Cámara abierta exitosamente en índice {self.camera_index}!")
        return True

    def start(self):
        """Inicia la captura de la cámara en un hilo en segundo plano."""
        if self.is_running:
            return

        if not self._open_capture():
            self.cap = None
            return

        self.is_running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def _capture_loop(self):
        """Bucle continuo para leer frames.

        Si la cámara deja de responder (ej. desconexión física del USB),
        tras RECONNECT_AFTER_FAILURES lecturas fallidas seguidas se avisa
        (on_camera_disconnected) y se intenta reabrir el dispositivo cada
        RECONNECT_RETRY_DELAY_SEC segundos hasta lograrlo o hasta que se
        detenga NOVA. Antes esto se quedaba congelado para siempre solo
        logueando advertencias, sin ningún aviso visible ni reintento.

        La condición del while solo depende de is_running (no de self.cap)
        para que el hilo siga vivo e intentando reconectar incluso mientras
        self.cap es None entre un fallo y el siguiente intento de apertura.
        """
        consecutive_failures = 0
        disconnected_notified = False

        while self.is_running:
            if not self.cap or not self.cap.isOpened():
                if self._open_capture():
                    consecutive_failures = 0
                    continue
                time.sleep(RECONNECT_RETRY_DELAY_SEC)
                continue

            ret, frame = self.cap.read()
            if ret:
                with self._frame_lock:
                    self.current_frame = frame
                consecutive_failures = 0
                if disconnected_notified:
                    logger.info("Cámara reconectada.")
                    if self.on_camera_reconnected:
                        self.on_camera_reconnected()
                    disconnected_notified = False
                continue

            consecutive_failures += 1
            logger.warning("Fallo al leer frame de la cámara")

            if consecutive_failures < RECONNECT_AFTER_FAILURES:
                # Pequeña pausa para no saturar el CPU ante un hipo momentáneo
                cv2.waitKey(100)
                continue

            if not disconnected_notified:
                logger.error("Cámara sin responder tras varios intentos — probable desconexión física. Reintentando...")
                if self.on_camera_disconnected:
                    self.on_camera_disconnected()
                disconnected_notified = True

            self.cap.release()
            self.cap = None
            # El próximo ciclo entra por la rama "not self.cap" de arriba,
            # que reintenta abrir y aplica el retry delay si vuelve a fallar.

    def get_frame(self):
        """Devuelve el último frame capturado."""
        with self._frame_lock:
            return self.current_frame

    def stop(self):
        """Detiene la captura y libera recursos."""
        logger.info("Deteniendo cámara...")
        self.is_running = False
        if self._thread:
            # El timeout cubre el peor caso de una reconexión en curso:
            # cv2.VideoCapture con DSHOW puede tardar varios segundos en
            # abrir. Con un timeout corto, el hilo podía terminar de abrir el
            # dispositivo DESPUÉS de que stop() ya había revisado self.cap,
            # dejando un handle de cámara abierto y sin liberar — la cámara
            # seguía transmitiendo/encendida pese a que NOVA ya reportaba
            # "Cámara detenida".
            self._thread.join(timeout=6.0)
            if self._thread.is_alive():
                logger.warning(
                    "El hilo de captura no terminó a tiempo (posiblemente reabriendo "
                    "el dispositivo); la cámara podría quedar sin liberar correctamente."
                )

        if self.cap:
            self.cap.release()
            self.cap = None

        with self._frame_lock:
            self.current_frame = None
        logger.info("Cámara detenida.")

if __name__ == "__main__":
    # Prueba rápida
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
