import logging
import yaml
import sys
import time

from core.camera import CameraController
from core.osc_controller import OSCController
from core.voice_engine import VoiceEngine
from core.gesture_engine import GestureEngine
from core.command_dispatcher import CommandDispatcher
from core.system_controller import SystemController
from core.ollama_bridge import OllamaBridge
from core.obsidian_logger import ObsidianLogger
from ui.tray_app import run_ui

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("NOVA")

class NovaAssistant:
    def __init__(self):
        logger.info("Iniciando NOVA...")
        self.load_config()
        
        # 1. Hardware y Control
        self.camera = CameraController(
            camera_index=self.config['camera']['camera_index'],
            width=int(self.config['camera']['resolution'].split('x')[0]),
            height=int(self.config['camera']['resolution'].split('x')[1])
        )
        self.osc = OSCController(
            ip=self.config['camera']['osc_host'],
            port=self.config['camera']['osc_port']
        )
        
        # 2. Control de Sistema, Ollama y Logs
        self.system = SystemController()
        self.ollama = OllamaBridge()
        self.logger_db = ObsidianLogger(self.config['obsidian']['vault_path'], self.config['obsidian']['nova_folder'])
        
        # 3. Despachador de comandos (el "Cerebro" de acciones)
        self.dispatcher = CommandDispatcher(self.osc, self.system, self.ollama)
        
        # 4. Motores de Percepción (Voz y Gestos)
        self.voice = VoiceEngine(self.config['voice'])
        self.gestures = GestureEngine(self.config['gestures'])
        
        # Conectar callbacks
        self.voice.on_wake_word_detected = self.on_wake_word
        self.voice.on_command_recognized = self.on_voice_command
        self.gestures.on_gesture_detected = self.on_gesture
        
    def load_config(self):
        try:
            with open("config.yaml", "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)
            logger.info("Configuración cargada correctamente")
        except Exception as e:
            logger.error(f"Error cargando config.yaml: {e}")
            sys.exit(1)

    def on_wake_word(self):
        """Se ejecuta cuando NOVA escucha su nombre."""
        # Mostrar el UI de escucha activamente
        from ui.panel_widget import show_listening
        show_listening()
        self.logger_db.log_action("Voz", "Wake word detectado")

    def on_voice_command(self, text: str):
        """Se ejecuta cuando Whisper transcribe el comando."""
        from ui.panel_widget import hide_listening, show_toast
        hide_listening()
        
        # Enviar comando al despachador
        respuesta = self.dispatcher.process_command(text)
        
        # Mostrar la respuesta breve en la UI
        show_toast("Comando de Voz", respuesta, success=True)
        
        # Registrar en Obsidian
        if self.config['obsidian']['log_voice_commands']:
            self.logger_db.log_action("Voz", text, respuesta)
            
        # Responder con voz
        self.voice.speak(respuesta)

    def on_gesture(self, gesture: str):
        """Se ejecuta cuando MediaPipe detecta un gesto sostenido."""
        logger.info(f"Procesando acción para gesto: {gesture}")
        action_taken = ""
        
        if gesture == "palma_abierta":
            self.osc.track_human()
            action_taken = "Activado tracking humano"
        elif gesture == "puno":
            self.osc.stop_tracking()
            action_taken = "Tracking detenido"
        elif gesture == "pellizco":
            # Zoom In temporal (ejemplo)
            self.osc.set_zoom(60.0)
            action_taken = "Zoom in"
        elif gesture == "victoria":
            # Comando especial
            self.system.take_screenshot()
            action_taken = "Captura de pantalla"
            
        if self.config['obsidian']['log_gestures'] and action_taken:
            self.logger_db.log_action("Gesto", gesture, action_taken)

    def _vision_loop(self):
        """Bucle en segundo plano para procesar la visión (MediaPipe) del frame de la cámara."""
        while self.is_running:
            frame = self.camera.get_frame()
            if frame is not None:
                # Procesar frame para gestos (devuelve el frame pintado opcionalmente)
                processed_frame = self.gestures.process_frame(frame)
                
                # Enviar frame a la UI si el panel está abierto
                import ui.panel_widget as pw
                try:
                    if pw._panel_instance and not pw._panel_instance.isHidden():
                        pw._panel_instance.update_video_frame(processed_frame)
                except RuntimeError:
                    # El panel se cerró (objeto Qt destruido) justo entre la lectura
                    # de la referencia y su uso; se ignora este frame y se sigue.
                    pass
                    
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
        
        # Iniciar UI
        logger.info("Iniciando Interfaz de Usuario...")
        run_ui(self.dispatcher)
        
        # Al cerrar la UI
        self.stop()

    def stop(self):
        logger.info("Deteniendo servicios de NOVA...")
        self.is_running = False
        self.voice.stop()
        self.camera.stop()
        self.logger_db.log_action("Sistema", "NOVA apagada")
        logger.info("NOVA se ha apagado correctamente.")

if __name__ == "__main__":
    nova = NovaAssistant()
    nova.start()
