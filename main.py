import logging
import os
import yaml
import sys
import time
from logging.handlers import RotatingFileHandler

from core.camera import CameraController
from core.osc_controller import OSCController
from core.voice_engine import VoiceEngine
from core.gesture_engine import GestureEngine
from core.command_dispatcher import CommandDispatcher
from core.system_controller import SystemController
from core.ollama_bridge import OllamaBridge
from core.obsidian_logger import ObsidianLogger
from core.file_tools import FileTools
from core.intent_router import IntentRouter
from core.config_validator import validate_config
from ui.tray_app import run_ui

# ─── Configuración de logging ───────────────────────────────────────────────
# Además de la consola, se escribe a logs/nova.log con rotación. Si NOVA se
# lanza sin consola visible (ej. desde el arranque automático de Windows,
# general.start_with_windows), la consola no existe y sin este archivo
# cualquier error o traceback se perdería sin dejar rastro.
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

_log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "nova.log"), maxBytes=2 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
_file_handler.setFormatter(logging.Formatter(_log_format))

logging.basicConfig(
    level=logging.INFO,
    format=_log_format,
    handlers=[logging.StreamHandler(), _file_handler],
)
logger = logging.getLogger("NOVA")

class NovaAssistant:
    def __init__(self):
        logger.info("Iniciando NOVA...")
        self.load_config()

        config_errors = validate_config(self.config)
        if config_errors:
            logger.error("config.yaml tiene errores, NOVA no puede arrancar:")
            for err in config_errors:
                logger.error(f"  - {err}")
            sys.exit(1)

        # 1. Hardware y Control
        self.camera = CameraController(
            camera_index=self.config['camera']['camera_index'],
            width=int(self.config['camera']['resolution'].split('x')[0]),
            height=int(self.config['camera']['resolution'].split('x')[1]),
            device_name=self.config['camera'].get('device_name'),
        )
        # Antes, si se desconectaba la cámara físicamente a mitad de sesión,
        # el video se congelaba para siempre sin ningún aviso. Ahora se avisa
        # por UI y queda en el log de sesión (estos callbacks corren en el
        # hilo de captura de la cámara, no en el de Qt — show_toast ya es
        # seguro para eso, ver ui/panel_widget.py).
        self.camera.on_camera_disconnected = self.on_camera_disconnected
        self.camera.on_camera_reconnected = self.on_camera_reconnected
        self.osc = OSCController(
            ip=self.config['camera']['osc_host'],
            port=self.config['camera']['osc_port']
        )
        
        # 2. Control de Sistema, Ollama y Logs
        self.system = SystemController()
        self.ollama = OllamaBridge()
        self.logger_db = ObsidianLogger(self.config['obsidian']['vault_path'], self.config['obsidian']['nova_folder'])

        # 2b. Herramientas del asistente (acotadas a carpetas autorizadas) + enrutador de intención
        assistant_cfg = self.config.get('assistant', {})
        self.file_tools = FileTools(
            allowed_folders=assistant_cfg.get('allowed_folders', []),
            vault_path=self.config['obsidian']['vault_path'],
            notes_folder=assistant_cfg.get('notes_folder', 'NOVA/Notas'),
        )
        self.intent_router = IntentRouter(self.ollama, self.file_tools)

        # 3. Despachador de comandos (el "Cerebro" de acciones)
        self.dispatcher = CommandDispatcher(self.osc, self.system, self.ollama, self.intent_router, camera_controller=self.camera)

        # El router necesita al dispatcher para ejecutar comandos parafraseados
        # de cámara/sistema (run_command) y abrir apps (open_app) reusando sus
        # diccionarios ya existentes, en vez de duplicarlos.
        self.intent_router.dispatcher = self.dispatcher

        # 4. Motores de Percepción (Voz y Gestos)
        self.voice = VoiceEngine(self.config['voice'])
        self.dispatcher.voice = self.voice
        self.gestures = GestureEngine(self.config['gestures'])
        self.gesture_commands = self._load_yaml("presets/gestures.yaml").get('gestures', {})

        # Conectar callbacks
        self.voice.on_wake_word_detected = self.on_wake_word
        self.voice.on_command_recognized = self.on_voice_command
        self.voice.on_voice_engine_failed = self.on_voice_engine_failed
        self.gestures.on_gesture_detected = self.on_gesture
        self.osc.on_status_updated = self.on_osc_status_updated

    def on_osc_status_updated(self, tracking_state: str, zoom_level: float):
        """Notifica a la UI los cambios de estado detectados por OSC en tiempo real."""
        import ui.panel_widget as pw
        pw.update_status_safe(tracking_state, zoom_level)

    def load_config(self):
        try:
            with open("config.yaml", "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
            logger.info("Configuración cargada correctamente")
        except Exception as e:
            logger.error(f"Error cargando config.yaml: {e}")
            sys.exit(1)

    def _load_yaml(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error cargando {path}: {e}")
            return {}

    def on_wake_word(self):
        """Se ejecuta cuando NOVA escucha su nombre."""
        # Mostrar el UI de escucha activamente
        from ui.panel_widget import show_listening
        show_listening()
        self.logger_db.log_action("Voz", "Wake word detectado")

    def on_voice_engine_failed(self, error_msg: str):
        """Se ejecuta si el hilo de voz no pudo arrancar (ej. micrófono inválido).

        Antes esto fallaba en silencio: NOVA seguía corriendo pero sin voz,
        sin ningún indicio visible de por qué. Ahora se avisa por UI y queda
        en el log de Obsidian igual que cualquier otro evento de sesión.
        """
        from ui.panel_widget import show_toast
        logger.error(f"Motor de voz caído: {error_msg}")
        show_toast("Voz desactivada", "No se pudo abrir el micrófono configurado", success=False)
        self.logger_db.log_action("Sistema", f"Motor de voz caído: {error_msg}")

    def on_camera_disconnected(self):
        """Se ejecuta si la cámara deja de responder (ej. desconexión física)."""
        from ui.panel_widget import show_toast
        logger.warning("Cámara desconectada, reintentando...")
        show_toast("Cámara desconectada", "Reintentando reconectar...", success=False)
        self.logger_db.log_action("Sistema", "Cámara desconectada, reintentando")

    def on_camera_reconnected(self):
        """Se ejecuta cuando la cámara vuelve a responder tras una desconexión."""
        from ui.panel_widget import show_toast
        logger.info("Cámara reconectada.")
        show_toast("Cámara reconectada", "El video volvió a la normalidad", success=True)
        self.logger_db.log_action("Sistema", "Cámara reconectada")

    def on_voice_command(self, text: str):
        """Se ejecuta cuando Whisper transcribe el comando."""
        from ui.panel_widget import hide_listening, show_toast
        hide_listening()
        
        # Enviar comando al despachador
        respuesta = self.dispatcher.process_command(text)
        
        if hasattr(respuesta, '__iter__') and not isinstance(respuesta, (str, bytes)):
            # Es un generador de oraciones en streaming (Ollama)
            # Lo consumimos en un hilo secundario para no bloquear el bucle de escucha de voz
            def _consume_stream():
                texto_completo = []
                for oracion in respuesta:
                    if oracion and oracion.strip():
                        self.voice.speak(oracion)
                        texto_completo.append(oracion)
                
                respuesta_completa = " ".join(texto_completo)
                show_toast("Comando de Voz", respuesta_completa, success=True)
                if self.config['obsidian']['log_voice_commands']:
                    self.logger_db.log_action("Voz", text, respuesta_completa)
            
            threading.Thread(target=_consume_stream, daemon=True, name="NOVA-StreamConsumer").start()
        else:
            # Respuesta estática clásica
            show_toast("Comando de Voz", respuesta, success=True)
            if self.config['obsidian']['log_voice_commands']:
                self.logger_db.log_action("Voz", text, respuesta)
            self.voice.speak(respuesta)

    def on_gesture(self, gesture: str):
        """Se ejecuta cuando MediaPipe detecta un gesto sostenido.

        El gesto se traduce a un comando de texto vía presets/gestures.yaml
        y se procesa exactamente igual que un comando de voz — así el mapeo
        gesto→acción se edita en el YAML, sin tocar código.
        """
        command_text = self.gesture_commands.get(gesture)
        if not command_text:
            logger.warning(f"Gesto '{gesture}' sin comando asignado en presets/gestures.yaml")
            return

        logger.info(f"Procesando acción para gesto: {gesture} -> '{command_text}'")
        action_taken = self.dispatcher.process_command(command_text)

        if self.config['obsidian']['log_gestures']:
            self.logger_db.log_action("Gesto", gesture, action_taken)

    def _vision_loop(self):
        """Bucle en segundo plano para procesar la visión (MediaPipe) del frame de la cámara.

        Todo el cuerpo va envuelto en try/except: un error en un solo frame
        (cámara, MediaPipe o UI) no puede tumbar el hilo para el resto de la
        sesión — antes un error no capturado aquí dejaba los gestos y el video
        congelados en silencio hasta reiniciar NOVA.
        """
        while self.is_running:
            try:
                frame = self.camera.get_frame()
                if frame is not None:
                    # Procesar frame para gestos (devuelve el frame pintado opcionalmente)
                    processed_frame = self.gestures.process_frame(frame)

                    # Enviar frame a la UI si el panel está abierto. Se usa
                    # update_video_frame_safe (no acceso directo a
                    # _panel_instance) porque este hilo NO es el hilo de Qt —
                    # llamar métodos de un QWidget fuera del hilo de Qt es
                    # comportamiento indefinido, no solo un riesgo de
                    # RuntimeError por objeto destruido.
                    import ui.panel_widget as pw
                    pw.update_video_frame_safe(processed_frame)
            except Exception:
                logger.exception("Error inesperado procesando un frame; se continúa con el siguiente.")

            time.sleep(0.03) # ~30 fps

    def start(self):
        self.is_running = True

        # Lanzar el driver de OBSBOT en segundo plano (sin ventana) antes de abrir la cámara
        general_cfg = self.config.get('general', {})
        if general_cfg.get('start_obsbot_center') and general_cfg.get('obsbot_path'):
            self.system.launch_obsbot_center(general_cfg['obsbot_path'])

        # Despertar la cámara por si quedó en standby (las OBSBOT Tiny se
        # suspenden solas tras inactividad) antes de intentar abrir el video.
        time.sleep(1.0)
        self.osc.wake_camera()
        time.sleep(1.0)

        # Iniciar modelos de voz (asíncrono/hilos)
        self.voice.initialize_models()
        self.voice.start_listening()

        # Iniciar cámara
        self.camera.start()
        
        # Bucle de visión
        import threading
        self.vision_thread = threading.Thread(target=self._vision_loop, daemon=True)
        self.vision_thread.start()
        
        # Log de inicio
        self.logger_db.log_action("Sistema", "NOVA iniciada exitosamente")
        
        # Iniciar UI. on_exit se llama desde el menú "Salir" de la bandeja,
        # ANTES de que Qt cierre la aplicación — es la única vía real de
        # cierre hoy (setQuitOnLastWindowClosed(False) impide que cerrar el
        # panel por sí solo termine el proceso), pero self.stop() es
        # idempotente por si en el futuro hay más de un camino de salida.
        logger.info("Iniciando Interfaz de Usuario...")
        run_ui(self.dispatcher, on_exit=self.stop)

        # Red de seguridad: si run_ui() retornara por una vía que no pasó
        # por on_exit, igual se libera todo (stop() no hace nada la segunda vez).
        self.stop()

    def stop(self):
        if getattr(self, "_stopped", False):
            return
        self._stopped = True

        logger.info("Deteniendo servicios de NOVA...")
        self.is_running = False
        self.voice.stop()

        # Pedirle a la cámara que se suspenda de verdad al cerrar NOVA.
        # Antes esto faltaba por completo: start() la despertaba (wake_camera)
        # pero nada la volvía a dormir al salir, así que quedaba con el
        # gimbal/chip de IA activo indefinidamente aunque NOVA ya no la usara
        # — esto es fire-and-forget por UDP, no falla si OBSBOT no está
        # escuchando (ver HANDOVER.md §5, el switch OSC de OBSBOT Center).
        self.osc.sleep_camera()
        self.camera.stop()

        if hasattr(self, "vision_thread") and self.vision_thread.is_alive():
            self.vision_thread.join(timeout=2.0)

        self.logger_db.log_action("Sistema", "NOVA apagada")
        logger.info("NOVA se ha apagado correctamente.")

if __name__ == "__main__":
    nova = NovaAssistant()
    nova.start()
