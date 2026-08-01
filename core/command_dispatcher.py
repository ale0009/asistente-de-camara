# -*- coding: utf-8 -*-
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
            "modo presentación": self._activate_presentation_mode,
            "modo presentacion": self._activate_presentation_mode,
            "modo stream": self._activate_presentation_mode,
            "modo reunión": self._activate_presentation_mode,
            "modo reunion": self._activate_presentation_mode,
            "modo trabajo": self._activate_work_mode,
            "modo escritorio": self._activate_work_mode,
            "modo descanso": self._activate_rest_mode,
            "modo privacidad": self._activate_rest_mode,
            "modo silencio": self._activate_rest_mode,
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
            "abre blender": lambda: self._open_app("blender"),
            "modo blender": lambda: self._open_app("blender"),
            "abre reporte de addons": lambda: self.process_command("qué dice mi reporte de addons"),
            "abre obs": lambda: self._open_app("obs"),
            "modo obs": lambda: self._open_app("obs"),
            "modo transmisión": lambda: self._activate_presentation_mode(),
            "modo transmision": lambda: self._activate_presentation_mode(),
            "inicia grabación": lambda: "Iniciando grabación en OBS Studio",
            "detén grabación": lambda: "Deteniendo grabación en OBS Studio",
        }

    def _activate_presentation_mode(self) -> str:
        """Modo Presentación / Stream / Reunión: despierta la cámara, enciende tracking y acomoda el zoom."""
        self.osc.wake_camera()
        self.osc.track_human()
        self.osc.set_zoom(0.0)
        try:
            from ui.panel_widget import show_toast
            show_toast("Modo Escena", "Modo Presentación Activado 🎥", success=True)
        except Exception:
            pass
        return "Modo Presentación activado: cámara despierta y tracking encendido."

    def _activate_work_mode(self) -> str:
        """Modo Trabajo / Escritorio: apaga tracking y centra el gimbal."""
        self.osc.stop_tracking()
        self.osc.gimbal_reset()
        try:
            from ui.panel_widget import show_toast
            show_toast("Modo Escena", "Modo Trabajo Activado 💻", success=True)
        except Exception:
            pass
        return "Modo Trabajo activado: tracking pausado y gimbal centrado."

    def _activate_rest_mode(self) -> str:
        """Modo Descanso / Privacidad: apaga tracking y pone la cámara a dormir."""
        self.osc.stop_tracking()
        self.osc.sleep_camera()
        if self.system:
            try:
                self.system.mute_volume()
            except Exception:
                pass
        try:
            from ui.panel_widget import show_toast
            show_toast("Modo Escena", "Modo Privacidad / Descanso Activado 🌙", success=True)
        except Exception:
            pass
        return "Modo Descanso activado: cámara suspendida."

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

        # ─── Comandos Dinámicos Numéricos (Zoom y Volumen) ─────────────────────
        if "zoom" in text:
            import re
            match = re.search(r'(?:al\s+|en\s+|a\s+)?(\d+)(?:\s*%)?', text)
            if match:
                try:
                    val = float(match.group(1))
                    if 0 <= val <= 100:
                        logger.info(f"Ajustando zoom dinámico por voz a: {val}%")
                        self.osc.set_zoom(val)
                        return f"Zoom ajustado al {int(val)} por ciento"
                except Exception as e:
                    logger.error(f"Error procesando zoom dinámico por voz: {e}")

        if "volumen" in text and not ("sube" in text or "baja" in text):
            import re
            match = re.search(r'(?:al\s+|en\s+|a\s+)?(\d+)(?:\s*%)?', text)
            if match:
                try:
                    val = float(match.group(1))
                    if 0 <= val <= 100:
                        logger.info(f"Ajustando volumen dinámico por voz a: {val}%")
                        if self.system:
                            return self.system.set_volume(val)
                except Exception as e:
                    logger.error(f"Error procesando volumen dinámico por voz: {e}")

        # Detección de micrófono independiente de acentos y codificación
        if ("micr" in text and "fon" in text) and ("cambia" in text or "selecciona" in text or "pon" in text):
            import re
            patterns = [
                r'cambia\s+el\s+micr[oó]fono\s+(?:al\s+|a\s+)\s*(.+)',
                r'cambia\s+de\s+micr[oó]fono\s+(?:al\s+|a\s+)\s*(.+)',
                r'cambia\s+micr[oó]fono\s+(?:al\s+|a\s+)\s*(.+)',
                r'selecciona\s+el\s+micr[oó]fono\s+(?:de\s+|a\s+)?\s*(.+)',
                r'pon\s+el\s+micr[oó]fono\s+(?:en\s+|a\s+)?\s*(.+)',
                r'micr[oó]fono\s+(?:al\s+|a\s+|en\s+)\s*(.+)'
            ]
            query = None
            for pattern in patterns:
                m = re.search(pattern, text)
                if m:
                    query = m.group(1).strip()
                    break
            if query:
                logger.info(f"Comando de cambio de micrófono detectado. Query: '{query}'")
                return self.select_microphone_by_name(query)

        # 1. Comandos de Cámara
        for cmd, action in self.camera_commands.items():
            if cmd in text:
                logger.info(f"Ejecutando comando de cámara: {cmd}")
                res = action()
                if res and isinstance(res, str):
                    return res
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

    def _normalize_text(self, text: str) -> str:
        import unicodedata
        # Quitar acentos
        text = "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
        text = text.lower().strip()
        # Quitar caracteres especiales residuales de codificación (reemplazar por espacio)
        text = "".join(c if (c.isalnum() or c.isspace()) else " " for c in text)
        
        # Mapeo de sinónimos comunes de hardware (Español -> Inglés)
        synonyms = {
            "camara": "camera",
            "audifonos": "headphone",
            "audifono": "headphone",
            "auriculares": "headphone",
            "auricular": "headphone",
            "microfono": "mic",
            "parlante": "speaker",
            "parlantes": "speaker",
            "altavoz": "speaker",
            "altavoces": "speaker",
            "inalambrico": "wireless",
            "inalambricos": "wireless",
        }
        for sp, en in synonyms.items():
            text = text.replace(sp, en)
        return text

    def select_microphone_by_name(self, name_query: str) -> str:
        """Busca un micrófono por nombre (coincidencia de palabras clave y sinónimos) y lo activa."""
        if not self.voice:
            return "El motor de voz no está disponible"
            
        try:
            devices = self.voice.get_input_devices()
        except Exception as e:
            logger.error(f"Error obteniendo dispositivos de entrada: {e}")
            return "No pude listar los micrófonos disponibles"

        # Normalizar y extraer palabras clave significativas
        query_norm = self._normalize_text(name_query)
        stop_words = {"de", "la", "el", "al", "en", "con", "del", "para"}
        keywords = [w for w in query_norm.split() if w not in stop_words and len(w) > 1]
        
        if not keywords:
            return "No especificaste palabras clave válidas para el micrófono"

        best_index = None
        best_name = None
        
        for idx, dev_name in devices.items():
            dev_norm = self._normalize_text(dev_name)
            # Validar que TODAS las palabras clave buscadas estén en el nombre del dispositivo
            if all(kw in dev_norm for kw in keywords):
                best_index = idx
                best_name = dev_name
                break
                
        if best_index is not None:
            try:
                self.voice.set_microphone(best_index)
                return f"Micrófono cambiado a {best_name}"
            except Exception as e:
                logger.error(f"Error al cambiar de micrófono a index {best_index}: {e}")
                return f"No pude cambiar al micrófono {best_name}"
        else:
            return f"No encontré ningún micrófono que coincida con {name_query}"
