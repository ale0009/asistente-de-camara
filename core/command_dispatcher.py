import logging
import yaml
import subprocess
import os

from core.persona import NOVA_IDENTITY

logger = logging.getLogger(__name__)

class CommandDispatcher:
    """
    Recibe el texto del comando de voz y determina qué acción tomar.
    Conecta el motor de voz con la cámara y el sistema operativo.
    """
    def __init__(self, osc_controller, system_controller=None, ollama_bridge=None,
                 intent_router=None, voice_engine=None, camera_controller=None, config_path="config.yaml", apps_path="presets/apps.yaml"):
        self.osc = osc_controller
        self.system = system_controller
        self.ollama = ollama_bridge
        self.intent_router = intent_router
        self.voice = voice_engine
        self.camera = camera_controller
        self.config = self._load_yaml(config_path)
        self.apps_config = self._load_yaml(apps_path)

        # Mapeo simple de comandos de cámara
        # Nota: los submodos de encuadre AI (cuerpo completo, grupo, pizarra, etc.)
        # se quitaron de aquí porque sus códigos numéricos no están confirmados
        # todavía para el Tiny 3 Lite — hay que probarlos con la cámara delante
        # antes de reactivarlos (ver core/osc_controller.py:set_ai_mode).
        self.camera_commands = {
            "despierta la cámara": self.osc.wake_camera,
            "despierta obsbot": self.osc.wake_camera,
            "despierta la camara": self.osc.wake_camera,
            "suspéndete": self.osc.sleep_camera,
            "suspende la cámara": self.osc.sleep_camera,
            "duérmete": self.osc.sleep_camera,
            "sígueme": self.osc.track_human,
            "trackea mi cara": self.osc.track_human,
            "acércate": lambda: self.osc.set_zoom(60.0),
            "zoom más": lambda: self.osc.set_zoom(60.0),
            "aléjate": lambda: self.osc.set_zoom(0.0),
            "zoom menos": lambda: self.osc.set_zoom(0.0),
            "para de seguirme": self.osc.stop_tracking,
            "deja de seguirme": self.osc.stop_tracking,
            "resetea la cámara": self.osc.gimbal_reset,
            "mira a la izquierda": self.osc.look_left,
            "mira izquierda": self.osc.look_left,
            "mira a la derecha": self.osc.look_right,
            "mira derecha": self.osc.look_right,
            "mira arriba": self.osc.look_up,
            "mira abajo": self.osc.look_down,
            "posición 1": lambda: self.osc.trigger_preset(1),
            "preset 1": lambda: self.osc.trigger_preset(1),
            "mira posición 1": lambda: self.osc.trigger_preset(1),
            "mira a la posición 1": lambda: self.osc.trigger_preset(1),
            "posición 2": lambda: self.osc.trigger_preset(2),
            "preset 2": lambda: self.osc.trigger_preset(2),
            "mira posición 2": lambda: self.osc.trigger_preset(2),
            "mira a la posición 2": lambda: self.osc.trigger_preset(2),
            "posición 3": lambda: self.osc.trigger_preset(3),
            "preset 3": lambda: self.osc.trigger_preset(3),
            "mira posición 3": lambda: self.osc.trigger_preset(3),
            "mira a la posición 3": lambda: self.osc.trigger_preset(3),
        }
        
        # Mapeo simple de comandos de sistema
        self.system_commands = {
            "captura de pantalla": lambda: self.system.take_screenshot() if self.system else "Sin control de sistema",
            "toma una foto": lambda: self.system.take_screenshot() if self.system else "Sin control de sistema",
            "sube el volumen": lambda: self.system.change_volume(True) if self.system else "Sin control de sistema",
            "baja el volumen": lambda: self.system.change_volume(False) if self.system else "Sin control de sistema",
            "silencia": lambda: self.system.mute_volume() if self.system else "Sin control de sistema",
            "muéstrame el escritorio": lambda: self.system.show_desktop() if self.system else "Sin control de sistema",
            "minimiza todo": lambda: self.system.show_desktop() if self.system else "Sin control de sistema",
            "siguiente ventana": lambda: self.system.next_window() if self.system else "Sin control de sistema",
        }

    def _load_yaml(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error cargando {path}: {e}")
            return {}

    def process_command(self, text: str) -> str:
        """
        Procesa el texto y ejecuta la acción correspondiente.
        Devuelve el mensaje de respuesta para el TTS.
        """
        text = text.lower().strip()
        logger.info(f"Procesando comando: '{text}'")
        
        # Limpiar prefijo "nova"
        if text.startswith("nova"):
            text = text.replace("nova", "").strip()

        # 1. Comandos de Cámara
        for cmd, action in self.camera_commands.items():
            if cmd in text:
                logger.info(f"Ejecutando comando de cámara: {cmd}")
                action()
                return f"Comando de cámara {cmd} ejecutado"

        # 2. Comandos de Sistema (Capturas, volumen)
        for cmd, action in self.system_commands.items():
            if cmd in text:
                logger.info(f"Ejecutando comando de sistema: {cmd}")
                return action()

        # 3. Comandos de Sistema (Abre/Cierra apps)
        if text.startswith("abre"):
            app_name = text.replace("abre", "").strip()
            return self._open_app(app_name)
            
        if text.startswith("cierra"):
            app_name = text.replace("cierra", "").strip()
            return self.system.close_application(app_name) if self.system else "Sin control de sistema"

        # 4. Consultas directas a Ollama (frase explícita, sin pasar por el clasificador)
        if "pregúntale a ollama" in text or "dile a ollama" in text:
            prompt = text.replace("pregúntale a ollama", "").replace("dile a ollama", "").strip()
            if self.ollama:
                prompt = f"{NOVA_IDENTITY}\nResponde de forma breve y directa (máximo 3 frases), en español: {prompt}"
                tokens = self.ollama.query_stream(prompt)
                return self._stream_sentences(tokens)
            return "No tengo configurado a Ollama."

        # 5. Cualquier otro comando libre: lo interpreta el clasificador de intención
        # (buscar archivos, tomar notas, o responder como conversación normal).
        if self.intent_router:
            return self.intent_router.route(text)

        return "No entendí ese comando."

    def _open_app(self, app_name: str) -> str:
        apps = self.apps_config.get("apps", {})
        
        # Búsqueda simple
        for key, paths in apps.items():
            if key in app_name:
                for path in paths:
                    if os.path.exists(path):
                        logger.info(f"Abriendo {key}: {path}")
                        try:
                            # Start process independent of script
                            subprocess.Popen([path], shell=True)
                            return f"Abriendo {key}"
                        except Exception as e:
                            logger.error(f"Error abriendo {path}: {e}")
                            return f"Hubo un error al abrir {key}"
                
                return f"No encontré el ejecutable de {key}"
                
        return f"No tengo registrada la aplicación {app_name}"

    def _stream_sentences(self, token_generator):
        """
        Toma un generador de tokens individuales y produce un generador de
        oraciones completas, delimitadas por signos de puntuación.
        """
        buffer = ""
        delimiters = {".", "!", "?", "\n"}
        for token in token_generator:
            buffer += token
            
            while True:
                # Encontrar el delimitador más cercano
                indices = [buffer.find(d) for d in delimiters if buffer.find(d) != -1]
                if not indices:
                    break
                first_idx = min(indices)
                
                # Extraer la oración incluyendo el delimitador
                sentence = buffer[:first_idx + 1].strip()
                buffer = buffer[first_idx + 1:]
                
                if sentence:
                    yield sentence
        
        # Ceder cualquier remanente al final
        final_sentence = buffer.strip()
        if final_sentence:
            yield final_sentence
