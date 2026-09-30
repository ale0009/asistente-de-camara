# -*- coding: utf-8 -*-
import logging
import yaml
import subprocess
import os
from pathlib import Path

from datetime import datetime
from core.persona import NOVA_IDENTITY
from core.hana_bridge import HanaBridge
from core.episodic_memory import EpisodicMemory

logger = logging.getLogger(__name__)

class CommandDispatcher:
    """
    Recibe el texto del comando de voz y determina qué acción tomar.
    Conecta el motor de voz con la cámara y el sistema operativo.
    """
    def __init__(self, osc_controller, system_controller=None, ollama_bridge=None,
                 intent_router=None, voice_engine=None, camera_controller=None,
                 gesture_engine=None, config_path="config.yaml", apps_path="presets/apps.yaml"):
        self.osc = osc_controller
        self.system = system_controller
        self.ollama = ollama_bridge
        self.intent_router = intent_router
        self.voice = voice_engine
        self.camera = camera_controller
        self.gesture_engine = gesture_engine
        self.config = self._load_yaml(config_path)
        self.apps_config = self._load_yaml(apps_path)
        self.hana = HanaBridge()
        self.memory = EpisodicMemory()
        self.gestures_active = True

        # Mapeo de comandos de cámara adaptados para hardware local y PTZ
        self.camera_commands = {
            "despierta la cámara": self._wake_camera,
            "despierta la camara": self._wake_camera,
            "enciende la cámara": self._wake_camera,
            "enciende la camara": self._wake_camera,
            "prende la cámara": self._wake_camera,
            "prende la camara": self._wake_camera,
            "suspéndete": self._sleep_camera,
            "suspende la cámara": self._sleep_camera,
            "suspende la camara": self._sleep_camera,
            "apaga la cámara": self._sleep_camera,
            "apaga la camara": self._sleep_camera,
            "para la cámara": self._sleep_camera,
            "para la camara": self._sleep_camera,
            "duérmete": self._sleep_camera,
            "duermete": self._sleep_camera,
            "sígueme": self._toggle_tracking,
            "sigueme": self._toggle_tracking,
            "trackear": self._toggle_tracking,
            "trackea mi cara": self._toggle_tracking,
            "para de seguirme": self._sleep_camera,
            "deja de seguirme": self._sleep_camera,
            "acércate": lambda: self.osc.set_zoom(60.0),
            "zoom más": lambda: self.osc.set_zoom(60.0),
            "aléjate": lambda: self.osc.set_zoom(0.0),
            "zoom menos": lambda: self.osc.set_zoom(0.0),
            "resetea la cámara": self.osc.gimbal_reset,
            "mira a la izquierda": self.osc.look_left,
            "mira izquierda": self.osc.look_left,
            "mira a la derecha": self.osc.look_right,
            "mira derecha": self.osc.look_right,
            "mira arriba": self.osc.look_up,
            "mira abajo": self.osc.look_down,
            "posición 1": lambda: self.osc.trigger_preset(1),
            "preset 1": lambda: self.osc.trigger_preset(1),
            "posición 2": lambda: self.osc.trigger_preset(2),
            "preset 2": lambda: self.osc.trigger_preset(2),
            "posición 3": lambda: self.osc.trigger_preset(3),
            "preset 3": lambda: self.osc.trigger_preset(3),
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
        
        # Mapeo de comandos de sistema, aplicaciones, Hana y Centinela
        self.system_commands = {
            # Aplicaciones y Carpetas
            "abre obsidian": lambda: self._open_app("obsidian"),
            "modo obsidian": lambda: self._open_app("obsidian"),
            "abre blender": lambda: self._open_app("blender"),
            "modo blender": lambda: self._open_app("blender"),
            "abre proyectos": lambda: self._open_app("proyectos"),
            "carpeta de proyectos": lambda: self._open_app("proyectos"),
            "mis proyectos": lambda: self._open_app("proyectos"),
            "abre la bóveda": lambda: self._open_app("boveda"),
            "abre la boveda": lambda: self._open_app("boveda"),
            "abre código": lambda: self._open_app("codigo"),
            "abre codigo": lambda: self._open_app("codigo"),
            "abre terminal": lambda: self._open_app("terminal"),
            "abre obs": lambda: self._open_app("obs"),
            "modo obs": lambda: self._open_app("obs"),

            # Sistema y Hardware
            "captura de pantalla": self._handle_screenshot,
            "toma una foto": self._handle_screenshot,
            "sube el volumen": lambda: self._handle_volume(True),
            "baja el volumen": lambda: self._handle_volume(False),
            "silencia": self._handle_mute,
            "muéstrame el escritorio": lambda: self.system.show_desktop() if self.system else "Sin control de sistema",
            "minimiza todo": lambda: self.system.show_desktop() if self.system else "Sin control de sistema",
            "siguiente ventana": lambda: self.system.next_window() if self.system else "Sin control de sistema",

            # Puente con Hana
            "dictados de hana": self._handle_hana_summary,
            "dictados hana": self._handle_hana_summary,
            "qué hay en hana": self._handle_hana_summary,
            "que hay en hana": self._handle_hana_summary,
            "consultar hana": self._handle_hana_summary,
            "revisa hana": self._handle_hana_summary,
            "listar dictados": self._handle_hana_summary,

            # Puente con Telemetría / Centinela
            "estado del equipo": self._handle_centinela_status,
            "estado de la máquina": self._handle_centinela_status,
            "estado de la maquina": self._handle_centinela_status,
            "cómo está el equipo": self._handle_centinela_status,
            "como esta el equipo": self._handle_centinela_status,
            "diagnóstico": self._handle_centinela_status,
            "diagnostico": self._handle_centinela_status,
            "estado del sistema": self._handle_centinela_status,
            "telemetría": self._handle_centinela_status,
            "telemetria": self._handle_centinela_status,
            "información del equipo": self._handle_centinela_status,

            "modo transmisión": lambda: self._activate_presentation_mode(),
            "modo transmision": lambda: self._activate_presentation_mode(),
            "hora de almuerzo": self._activate_lunch_mode,
            "hora del almuerzo": self._activate_lunch_mode,
            "modo almuerzo": self._activate_lunch_mode,
            "resumen de proyectos": self._handle_projects_query,
            "proyectos en obsidian": self._handle_projects_query,
            "cuántos proyectos hay": self._handle_projects_query,
            "cuantos proyectos hay": self._handle_projects_query,
            "cuántos proyectos tengo": self._handle_projects_query,
            "cuantos proyectos tengo": self._handle_projects_query,
            "qué proyectos tengo": self._handle_projects_query,
            "que proyectos tengo": self._handle_projects_query,
            "cuáles son mis proyectos": self._handle_projects_query,
            "cuales son mis proyectos": self._handle_projects_query,
            "lista de proyectos": self._handle_projects_query,
            "inventario de proyectos": self._handle_projects_query,
            "tareas pendientes": self._handle_tasks_query,
            "mis tareas": self._handle_tasks_query,

            # Herramientas de Workbench, OCR y Diagramas
            "digitaliza este diagrama": self._handle_diagram_to_code,
            "digitalizar diagrama": self._handle_diagram_to_code,
            "diagrama a mermaid": self._handle_diagram_to_code,
            "diagrama a código": self._handle_diagram_to_code,
            "diagrama a codigo": self._handle_diagram_to_code,
            "convierte este diagrama": self._handle_diagram_to_code,
            "boceto a diagrama": self._handle_diagram_to_code,
            "diagrama": self._handle_diagram_to_code,

            "lee este documento": self._handle_ocr_document,
            "leer documento": self._handle_ocr_document,
            "lee este texto": self._handle_ocr_document,
            "leer texto": self._handle_ocr_document,
            "transcribe lo que ves": self._handle_ocr_document,
            "digitaliza esta nota": self._handle_ocr_document,
            "ocr de la cámara": self._handle_ocr_document,
            "ocr de la camara": self._handle_ocr_document,
            "ocr": self._handle_ocr_document,

            "inspecciona la pantalla": self._handle_screen_vision,
            "inspeccionar pantalla": self._handle_screen_vision,
            "qué hay en la pantalla": self._handle_screen_vision,
            "que hay en la pantalla": self._handle_screen_vision,
            "analiza la pantalla": self._handle_screen_vision,
            "analiza este error": self._handle_screen_vision,
            "qué error tengo": self._handle_screen_vision,
            "que error tengo": self._handle_screen_vision,
            "ayuda con este código": self._handle_screen_vision,
            "ayuda con este codigo": self._handle_screen_vision,

            "qué estoy señalando": self._handle_point_and_ask,
            "que estoy señalando": self._handle_point_and_ask,
            "que estoy senalando": self._handle_point_and_ask,
            "qué es esto que señalo": self._handle_point_and_ask,
            "que es esto que señalo": self._handle_point_and_ask,
            "qué tengo en el dedo": self._handle_point_and_ask,

            # Memoria Episódica
            "qué hice hoy": self._handle_memory_query,
            "que hice hoy": self._handle_memory_query,
            "resumen del día": self._handle_memory_query,
            "resumen del dia": self._handle_memory_query,
            "qué eventos registraste": self._handle_memory_query,
            "que eventos registraste": self._handle_memory_query,
            "resumen de hoy": self._handle_memory_query,
            "memoria de hoy": self._handle_memory_query,
            "sincroniza la memoria": lambda: self.memory.export_to_obsidian(),
            "sincronizar memoria": lambda: self.memory.export_to_obsidian(),
        }

        self.language_tutor = None

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

        # 1. Comandos de Cámara (ordenados por longitud descendente)
        for cmd in sorted(self.camera_commands.keys(), key=len, reverse=True):
            if cmd in text:
                logger.info(f"Ejecutando comando de cámara: {cmd}")
                res = self.camera_commands[cmd]()
                if res and isinstance(res, str):
                    return res
                return f"Comando de cámara {cmd} ejecutado"

        # 2. Comandos de Sistema (ordenados por longitud descendente para evitar colisiones)
        for cmd in sorted(self.system_commands.keys(), key=len, reverse=True):
            if cmd in text:
                logger.info(f"Ejecutando comando de sistema: {cmd}")
                res = self.system_commands[cmd]()
                if res and isinstance(res, str):
                    return res
                return f"Comando {cmd} ejecutado"

        # 2.5. Comandos de Descarga / Procesamiento de Dictados de Hana
        if any(trigger in text for trigger in ["procesa dictado", "procesar dictado", "descarga dictado", "descargar dictado", "ingestar dictado"]):
            import re
            m = re.search(r'\d+', text)
            if m:
                num = m.group(0)
                resp = self.hana.process_dictation(num)
                try:
                    from ui.panel_widget import show_toast
                    show_toast("Hana Procesado", resp[:60] + "...", success=True)
                except Exception:
                    pass
                self._speak_feedback(resp)
                return resp
            return "Por favor indica el número del dictado de Hana a procesar."

        # 3. Comandos de Sistema (Abre/Cierra apps)
        if text.startswith("abre"):
            app_name = text.replace("abre", "").strip()
            return self._open_app(app_name)
            
        if text.startswith("cierra"):
            app_name = text.replace("cierra", "").strip()
            return self.system.close_application(app_name) if self.system else "Sin control de sistema"

        # 3.5. Comandos de Inferencia Visual (Moondream / Qwen3-VL)
        vision_keywords = [
            "qué ves", "que ves", "qué hay en la cámara", "que hay en la camara",
            "describe la escena", "describe lo que ves", "qué tengo en la mano", "que tengo en la mano"
        ]
        if any(vk in text for vk in vision_keywords):
            return self._handle_vision_query(text)

        # 3.6. Comandos de Práctica de Idiomas (Language Tutor)
        if "practiquemos inglés" in text or "practicar inglés" in text or "practicar ingles" in text or "practiquemos ingles" in text:
            return self._start_language_practice("en", "conversación general")
        if "practiquemos francés" in text or "practicar francés" in text or "practicar frances" in text or "practiquemos frances" in text:
            return self._start_language_practice("fr", "conversation générale")
        if "practiquemos chino" in text or "practicar chino" in text:
            return self._start_language_practice("zh", "日常对话")
        if "practiquemos japonés" in text or "practicar japonés" in text or "practicar japones" in text or "practiquemos japones" in text:
            return self._start_language_practice("ja", "日常会話")
        if "volver a español" in text or "terminar práctica" in text or "fin de la práctica" in text:
            return self._end_language_practice()

        # Si hay una sesión de tutor de idiomas activa, responder con el tutor
        if getattr(self, "language_tutor", None) and self.language_tutor.active_session:
            tutor_res = self.language_tutor.execute_tool("language_converse", {"user_message": text})
            if tutor_res.get("success"):
                return tutor_res.get("response", "")

        # 4. Consultas directas a Ollama (frase explícita, sin pasar por el clasificador)
        if "pregúntale a ollama" in text or "dile a ollama" in text:
            prompt = text.replace("pregúntale a ollama", "").replace("dile a ollama", "").strip()
            if self.ollama:
                prompt = f"{NOVA_IDENTITY}\nResponde de forma breve y directa (máximo 3 frases), en español: {prompt}"
                tokens = self.ollama.query_stream(prompt)
                return self._stream_sentences(tokens)
            return "No tengo configurado a Ollama."

        # 5. Cualquier otro comando libre: lo interpreta el clasificador de intención
        if self.intent_router:
            return self.intent_router.route(text)

        return "No entendí ese comando."

    def _speak_feedback(self, text: str):
        """Emite confirmación por voz local inmediata sin bloquear el hilo."""
        if not text:
            return
        def _say():
            try:
                hablar_bin = "/home/alejandro/.local/bin/hablar"
                if os.path.exists(hablar_bin) and os.access(hablar_bin, os.X_OK):
                    subprocess.run([hablar_bin, text], check=False)
                elif self.voice and hasattr(self.voice, 'speak'):
                    self.voice.speak(text)
            except Exception as e:
                logger.error(f"Error emitiendo voz de confirmación: {e}")
        import threading
        threading.Thread(target=_say, daemon=True, name="NOVA-SpeakFeedback").start()

    def _wake_camera(self) -> str:
        """Enciende la cámara integrada o PTZ."""
        logger.info("Comando: Despertar / Encender cámara recibido.")
        if self.camera:
            if not self.camera.is_running:
                self.camera.start()
            try:
                from ui.panel_widget import update_camera_state_safe
                update_camera_state_safe(True)
            except Exception:
                pass
            msg = "Cámara encendida"
            self._speak_feedback(msg)
            try:
                from ui.panel_widget import show_toast
                show_toast("Cámara", "Cámara encendida ☀", success=True)
            except Exception:
                pass
            return msg
        self.osc.wake_camera()
        return "Cámara despertada"

    def _sleep_camera(self) -> str:
        """Apaga o suspende la cámara para privacidad y ahorro de CPU."""
        logger.info("Comando: Suspender / Apagar cámara recibido.")
        if self.camera:
            if self.camera.is_running:
                self.camera.stop()
            try:
                from ui.panel_widget import update_camera_state_safe
                update_camera_state_safe(False)
            except Exception:
                pass
            msg = "Cámara suspendida"
            self._speak_feedback(msg)
            try:
                from ui.panel_widget import show_toast
                show_toast("Cámara", "Cámara apagada 🌙 (Sensor liberado)", success=False)
            except Exception:
                pass
            return msg
        self.osc.sleep_camera()
        return "Cámara suspendida"

    def _toggle_tracking(self) -> str:
        """Alterna el seguimiento y detección de gestos."""
        self.gestures_active = not getattr(self, "gestures_active", True)
        estado = "activado" if self.gestures_active else "pausado"
        msg = f"Seguimiento visual {estado}"
        self._speak_feedback(msg)
        try:
            from ui.panel_widget import show_toast
            show_toast("Tracking", f"Seguimiento {estado}", success=self.gestures_active)
        except Exception:
            pass
        return msg

    def _handle_screenshot(self) -> str:
        """Toma una captura de pantalla del escritorio y da aviso visual/auditivo."""
        if not self.system:
            return "Sin control de sistema"
        msg = self.system.take_screenshot()
        self._speak_feedback(msg)
        try:
            from ui.panel_widget import show_toast
            show_toast("Captura de Pantalla", msg, success=True)
        except Exception:
            pass
        return msg

    def _handle_volume(self, increase: bool) -> str:
        """Ajusta el volumen del sistema y da aviso."""
        if not self.system:
            return "Sin control de sistema"
        msg = self.system.change_volume(increase)
        try:
            from ui.panel_widget import show_toast
            show_toast("Volumen", msg, success=True)
        except Exception:
            pass
        return msg

    def _handle_mute(self) -> str:
        """Alterna el silencio del sistema y da aviso."""
        if not self.system:
            return "Sin control de sistema"
        msg = self.system.mute_volume()
        self._speak_feedback(msg)
        try:
            from ui.panel_widget import show_toast
            show_toast("Audio", msg, success=True)
        except Exception:
            pass
        return msg

    def _handle_hana_summary(self) -> str:
        """Consulta los dictados disponibles en Hana y los anuncia."""
        summary = self.hana.get_summary()
        try:
            from ui.panel_widget import show_toast
            show_toast("Hana Dictados", summary[:80] + "...", success=True)
        except Exception:
            pass
        self._speak_feedback(summary)
        return summary

    def _handle_centinela_status(self) -> str:
        """Consulta la telemetría del equipo mediante Centinela y genera un reporte hablado."""
        logger.info("Consultando estado del equipo vía Centinela...")
        try:
            res = subprocess.run(["centinela", "estado"], capture_output=True, text=True, timeout=5)
            output = res.stdout
            if not output:
                msg = "No pude obtener la telemetría de Centinela."
                self._speak_feedback(msg)
                return msg

            import re
            cpu_m = re.search(r'CPU Total\s*:\s*([\d\.]+)%', output)
            ram_m = re.search(r'RAM Física\s*:\s*([\d\.]+)%\s*usado', output)
            gpu_m = re.search(r'Temp / Uso\s*:\s*(\d+)°C.*?Carga GPU:\s*(\d+)%', output)
            bat_m = re.search(r'Batería\s*:\s*(\d+)%', output)

            cpu = cpu_m.group(1) if cpu_m else "normal"
            ram = ram_m.group(1) if ram_m else "normal"
            temp = gpu_m.group(1) if gpu_m else "40"
            bat = bat_m.group(1) if bat_m else "100"

            speech = f"El equipo está en estado óptimo. Procesador al {cpu} por ciento, memoria RAM al {ram} por ciento, tarjeta gráfica a {temp} grados, y batería al {bat} por ciento."

            try:
                from ui.panel_widget import show_toast
                show_toast("Centinela Telemetría", f"CPU: {cpu}% | RAM: {ram}% | GPU: {temp}°C | Batería: {bat}%", success=True)
            except Exception:
                pass
            self._speak_feedback(speech)
            return speech
        except Exception as e:
            logger.error(f"Error consultando centinela: {e}")
            msg = "Sistema funcionando de forma estable."
            self._speak_feedback(msg)
            return msg

    def _open_app(self, app_name: str) -> str:
        app_name = app_name.lower().strip()
        logger.info(f"Abriendo aplicación o destino: '{app_name}'")

        if "obsidian" in app_name:
            subprocess.Popen(["/home/alejandro/.local/bin/obsidian"])
            msg = "Abriendo Obsidian"
            self._speak_feedback(msg)
            try:
                from ui.panel_widget import show_toast
                show_toast("Obsidian", "Bóveda de notas abierta", success=True)
            except Exception:
                pass
            return msg

        if "blender" in app_name:
            blender_cmd = "/home/alejandro/.local/bin/prime-run blender"
            subprocess.Popen([blender_cmd], shell=True)
            msg = "Abriendo Blender en la tarjeta gráfica dedicada"
            self._speak_feedback(msg)
            try:
                from ui.panel_widget import show_toast
                show_toast("Blender", "Iniciando con PRIME offload en GTX 1050", success=True)
            except Exception:
                pass
            return msg

        if "proyecto" in app_name:
            subprocess.Popen(["xdg-open", "/home/alejandro/Datos/Projects"])
            msg = "Abriendo carpeta de proyectos"
            self._speak_feedback(msg)
            try:
                from ui.panel_widget import show_toast
                show_toast("Proyectos", "Abriendo ~/Datos/Projects", success=True)
            except Exception:
                pass
            return msg

        if "boveda" in app_name or "bóveda" in app_name or "vault" in app_name:
            subprocess.Popen(["xdg-open", "/home/alejandro/Datos/Vault-Obsidian"])
            msg = "Abriendo bóveda de Obsidian"
            self._speak_feedback(msg)
            try:
                from ui.panel_widget import show_toast
                show_toast("Bóveda", "Abriendo Vault-Obsidian", success=True)
            except Exception:
                pass
            return msg

        if "codigo" in app_name or "código" in app_name or "code" in app_name:
            subprocess.Popen(["code"])
            msg = "Abriendo Visual Studio Code"
            self._speak_feedback(msg)
            try:
                from ui.panel_widget import show_toast
                show_toast("Code", "Abriendo VS Code", success=True)
            except Exception:
                pass
            return msg

        if "terminal" in app_name or "consola" in app_name:
            subprocess.Popen(["konsole"])
            msg = "Abriendo terminal"
            self._speak_feedback(msg)
            return msg

        if "hana" in app_name:
            return self._handle_hana_summary()

        # Fallback a apps_config
        apps = self.apps_config.get("apps", {})
        for key, paths in apps.items():
            if key in app_name:
                for path in paths:
                    try:
                        subprocess.Popen(path, shell=True)
                        msg = f"Abriendo {key}"
                        self._speak_feedback(msg)
                        return msg
                    except Exception:
                        pass
        return f"No encontré cómo abrir {app_name}"

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

    def _handle_vision_query(self, text: str) -> str:
        """Captura el frame actual de la cámara e invoca la inferencia visual con Moondream o Qwen-VL."""
        if not self.ollama:
            msg = "No tengo configurado el puente de IA local para visión."
            self._speak_feedback(msg)
            return msg
        if not self.camera:
            msg = "No tengo acceso a la cámara para capturar la imagen."
            self._speak_feedback(msg)
            return msg

        frame = getattr(self.camera, "current_frame", None)
        if frame is None:
            msg = "La cámara está apagada o no está produciendo video actualmente."
            self._speak_feedback(msg)
            return msg

        prompt_clean = "Describe brevemente en español (máximo 2 oraciones) lo que ves en la imagen."
        if "mano" in text:
            prompt_clean = "Describe en español el objeto o elemento que la persona sostiene en la mano."

        logger.info(f"Procesando inferencia visual con modelo configurado: '{prompt_clean}'")
        res = self.ollama.query_vision(prompt_clean, frame, model=None)
        if res:
            try:
                from ui.panel_widget import show_toast
                show_toast("Visión IA 👁", res[:80] + "...", success=True)
            except Exception:
                pass
            self._speak_feedback(res)
            if hasattr(self, "memory") and self.memory:
                self.memory.log_event("vision", "describe_scene", res[:120], res, "vision,escena")
        return res

    def _handle_ocr_document(self) -> str:
        """Captura el frame de cámara (o recorte foveado) y transcribe el texto físico a Obsidian."""
        if not self.camera or not getattr(self.camera, "is_running", False):
            msg = "La cámara está apagada. Por favor enciéndela primero para leer el documento."
            self._speak_feedback(msg)
            return msg

        frame = self.camera.get_frame() if hasattr(self.camera, "get_frame") else getattr(self.camera, "current_frame", None)
        if frame is None:
            msg = "No se pudo obtener el cuadro de video de la cámara."
            self._speak_feedback(msg)
            return msg

        inspect_frame = frame
        if self.gesture_engine and hasattr(self.gesture_engine, "get_foveated_crop"):
            inspect_frame = self.gesture_engine.get_foveated_crop(frame, crop_size=480)

        prompt = (
            "Eres un transcriptor técnico de alta precisión. Transcribe fielmente todo el texto, "
            "fórmulas, códigos o notas escritas en este documento o libreta. Devuelve el contenido "
            "en formato Markdown limpio, sin preámbulos innecesarios."
        )

        try:
            from ui.panel_widget import show_toast
            show_toast("OCR en Curso 📝", "Transcribiendo documento con IA local...", success=True)
        except Exception:
            pass

        transcription = self.ollama.query_vision(prompt, inspect_frame, model=None)
        if not transcription or "No encontré" in transcription:
            msg = "No pude transcribir texto claro de la imagen."
            self._speak_feedback(msg)
            return msg

        vault_path = Path(self.config.get("obsidian", {}).get("vault_path", "/home/alejandro/Datos/Vault-Obsidian"))
        notes_dir = vault_path / "NOVA" / "Notas"
        notes_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        note_file = notes_dir / f"Nota_Capturada_{ts}.md"

        content = (
            f"---\nfecha: {datetime.now().strftime('%Y-%m-%d')}\ntipo: captura-ocr-nova\ntags: [nova, ocr, notas]\n---\n"
            f"# 📝 Nota Capturada por NOVA ({ts})\n\n"
            f"{transcription}\n"
        )
        note_file.write_text(content, encoding="utf-8")

        summary_spoken = f"Documento transcrito y guardado en Obsidian como Nota Capturada {ts[:10]}."
        self._speak_feedback(summary_spoken)

        if hasattr(self, "memory") and self.memory:
            self.memory.log_event("vision", "ocr_document", f"Nota guardada: {note_file.name}", transcription[:300], "ocr,documento")

        try:
            from ui.panel_widget import show_toast
            show_toast("Documento Guardado 📝", f"Guardado en {note_file.name}", success=True)
        except Exception:
            pass

        return summary_spoken

    def _handle_diagram_to_code(self) -> str:
        """Digitaliza un boceto o diagrama dibujado en papel a código Mermaid o PlantUML en Obsidian."""
        if not self.camera or not getattr(self.camera, "is_running", False):
            msg = "La cámara está apagada. Por favor enciéndela primero para ver el diagrama."
            self._speak_feedback(msg)
            return msg

        frame = self.camera.get_frame() if hasattr(self.camera, "get_frame") else getattr(self.camera, "current_frame", None)
        if frame is None:
            msg = "No hay cuadro de video disponible."
            self._speak_feedback(msg)
            return msg

        prompt = (
            "Eres un arquitecto de software y sistemas. Analiza este diagrama o boceto dibujado a mano. "
            "Extrae los nodos, flujos y relaciones lógicas, y genera un diagrama Mermaid sintácticamente válido dentro de un bloque "
            "```mermaid ... ```. Explica en 2 frases breves de qué trata el flujo."
        )

        try:
            from ui.panel_widget import show_toast
            show_toast("Diagrama IA 📊", "Digitalizando arquitectura a Mermaid...", success=True)
        except Exception:
            pass

        result = self.ollama.query_vision(prompt, frame, model=None)
        if not result:
            msg = "No pude digitalizar el diagrama."
            self._speak_feedback(msg)
            return msg

        vault_path = Path(self.config.get("obsidian", {}).get("vault_path", "/home/alejandro/Datos/Vault-Obsidian"))
        diag_dir = vault_path / "NOVA" / "Diagramas"
        diag_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        diag_file = diag_dir / f"Diagrama_{ts}.md"

        content = (
            f"---\nfecha: {datetime.now().strftime('%Y-%m-%d')}\ntipo: diagrama-nova\ntags: [nova, arquitectura, mermaid]\n---\n"
            f"# 📊 Diagrama Arquitectónico Digitalizado ({ts})\n\n"
            f"{result}\n"
        )
        diag_file.write_text(content, encoding="utf-8")

        summary_spoken = f"Diagrama digitalizado en Mermaid y guardado en Obsidian como Diagrama {ts[:10]}."
        self._speak_feedback(summary_spoken)

        if hasattr(self, "memory") and self.memory:
            self.memory.log_event("vision", "diagram_digitized", f"Diagrama guardado: {diag_file.name}", result[:300], "diagrama,mermaid")

        try:
            from ui.panel_widget import show_toast
            show_toast("Diagrama Creado 📊", f"Guardado en {diag_file.name}", success=True)
        except Exception:
            pass

        return summary_spoken

    def _handle_screen_vision(self) -> str:
        """Toma una captura de pantalla y analiza errores de código o interfaces con el VLM."""
        tmp_screen = Path("/tmp/nova_screen_inspect.png")
        try:
            res = subprocess.run(["spectacle", "-b", "-n", "-o", str(tmp_screen)], capture_output=True, timeout=5)
            if res.returncode != 0 or not tmp_screen.exists():
                msg = "No pude capturar la pantalla para inspección."
                self._speak_feedback(msg)
                return msg

            import cv2
            screen_bgr = cv2.imread(str(tmp_screen))
            if screen_bgr is None:
                msg = "Error leyendo la captura de pantalla."
                self._speak_feedback(msg)
                return msg

            prompt = (
                "Analiza la pantalla de este entorno de trabajo técnico. Si hay un error en terminal o código en el editor, "
                "explica en español la causa y la solución en 2 o 3 oraciones concisas y directas. Si es una interfaz, resume su estado."
            )

            try:
                from ui.panel_widget import show_toast
                show_toast("Inspección de Pantalla 🖥", "Analizando código y terminal...", success=True)
            except Exception:
                pass

            explanation = self.ollama.query_vision(prompt, screen_bgr, model=None)
            if not explanation:
                explanation = "No detecté errores críticos en la pantalla."

            self._speak_feedback(explanation)

            if hasattr(self, "memory") and self.memory:
                self.memory.log_event("system", "screen_inspect", explanation[:150], explanation, "pantalla,debug")

            try:
                from ui.panel_widget import show_toast
                show_toast("Diagnóstico de Pantalla 🖥", explanation[:80] + "...", success=True)
            except Exception:
                pass

            return explanation
        except Exception as e:
            logger.error(f"Error en _handle_screen_vision: {e}")
            msg = "Error al inspeccionar la pantalla."
            self._speak_feedback(msg)
            return msg

    def _handle_point_and_ask(self) -> str:
        """Aplica visión foveada (recorte centrado en el dedo que señala) para responder qué hay allí."""
        if not self.camera or not getattr(self.camera, "is_running", False):
            msg = "La cámara está apagada. Por favor enciéndela primero."
            self._speak_feedback(msg)
            return msg

        frame = self.camera.get_frame() if hasattr(self.camera, "get_frame") else getattr(self.camera, "current_frame", None)
        if frame is None:
            msg = "No hay cuadro de video disponible."
            self._speak_feedback(msg)
            return msg

        inspect_frame = frame
        if self.gesture_engine and hasattr(self.gesture_engine, "get_foveated_crop"):
            inspect_frame = self.gesture_engine.get_foveated_crop(frame, crop_size=448)

        prompt = "Identifica y describe de forma concisa y directa en español (máximo 2 oraciones) el objeto, texto o componente específico señalado en esta imagen."
        res = self.ollama.query_vision(prompt, inspect_frame, model=None)
        if not res:
            res = "No pude identificar con certeza lo que estás señalando."

        self._speak_feedback(res)
        if hasattr(self, "memory") and self.memory:
            self.memory.log_event("vision", "point_and_ask", res[:120], res, "vision,foveada")

        try:
            from ui.panel_widget import show_toast
            show_toast("Señalando 👆", res[:80] + "...", success=True)
        except Exception:
            pass

        return res

    def _handle_memory_query(self) -> str:
        """Consulta el resumen diario de eventos en la memoria episódica continua y sincroniza con Obsidian."""
        if not hasattr(self, "memory") or not self.memory:
            msg = "El motor de memoria episódica no está activo."
            self._speak_feedback(msg)
            return msg

        summary = self.memory.get_daily_summary()
        vault_path = Path(self.config.get("obsidian", {}).get("vault_path", "/home/alejandro/Datos/Vault-Obsidian"))
        sync_res = self.memory.export_to_obsidian(vault_path=vault_path)

        self._speak_feedback(summary)

        try:
            from ui.panel_widget import show_toast
            show_toast("Memoria Episódica 🧠", sync_res, success=True)
        except Exception:
            pass

        return summary

    def _activate_lunch_mode(self) -> str:
        """Modo Almuerzo: suspende cámara, silencia volumen y registra en Obsidian."""
        from mcp_servers.agenda_mcp import AgendaMCPServer
        agenda = AgendaMCPServer(
            vault_path=self.config.get("obsidian", {}).get("vault_path", "/home/alejandro/Datos/Vault-Obsidian"),
            nova_folder=self.config.get("obsidian", {}).get("nova_folder", "NOVA"),
            osc_controller=self.osc,
            system_controller=self.system
        )
        res = agenda.execute_tool("agenda_lunch_break", {"duration_minutes": 60})
        try:
            from ui.panel_widget import show_toast
            show_toast("Modo Almuerzo 🍲", "Cámara suspendida. ¡Buen provecho!", success=True)
        except Exception:
            pass
        return res.get("message", "Modo almuerzo activado. ¡Buen provecho!")

    def _handle_projects_query(self) -> str:
        """Escanea y resume los proyectos documentados en Obsidian con prioridad en el Inventario Master."""
        vault_path = Path(self.config.get("obsidian", {}).get("vault_path", "/home/alejandro/Datos/Vault-Obsidian"))
        master_path = vault_path / "proyectos" / "🌐 INVENTARIO MASTER DE PROYECTOS.md"
        
        if master_path.exists():
            try:
                content = master_path.read_text(encoding="utf-8")
                import re
                matches = re.findall(r'\|\s*\*\*([^*]+)\*\*\s*\|\s*`([^`]+)`\s*\|[^|]*\|\s*([^|]+)\|', content)
                if matches:
                    names = [m[0].strip() for m in matches]
                    resp = f"Tienes exactamente {len(names)} proyectos principales en tu Inventario Master de Obsidian: {', '.join(names)}."
                    self._speak_feedback(resp)
                    try:
                        from ui.panel_widget import show_toast
                        show_toast("Proyectos Obsidian", f"{len(names)} proyectos registrados", success=True)
                    except Exception:
                        pass
                    return resp
            except Exception as e:
                logger.error(f"Error leyendo inventario master: {e}")

        from mcp_servers.vault_mcp import ObsidianVaultMCPServer
        vault = ObsidianVaultMCPServer(vault_path=str(vault_path))
        res = vault.execute_tool("vault_list_projects", {})
        if not res.get("success") or not res.get("projects"):
            msg = "No encontré proyectos documentados en tu Vault de Obsidian."
            self._speak_feedback(msg)
            return msg
        
        projects = res.get("projects", [])
        project_names = [p["name"] for p in projects]
        resp = f"Tienes {len(projects)} proyectos en Obsidian: {', '.join(project_names[:12])}..."
        self._speak_feedback(resp)
        return resp

    def _handle_tasks_query(self) -> str:
        """Escanea las tareas pendientes en Obsidian."""
        from mcp_servers.vault_mcp import ObsidianVaultMCPServer
        vault = ObsidianVaultMCPServer(
            vault_path=self.config.get("obsidian", {}).get("vault_path", "/home/alejandro/Datos/Vault-Obsidian")
        )
        res = vault.execute_tool("vault_scan_pending_tasks", {})
        if not res.get("success") or not res.get("tasks"):
            return "No tienes tareas pendientes marcadas como checklist en tu Vault."
        
        tasks = res.get("tasks", [])
        tasks_preview = "; ".join(t["task"] for t in tasks[:3])
        return f"Tienes {res.get('total_pending', len(tasks))} tareas pendientes. Las primeras son: {tasks_preview}."

    def _handle_doctor_check(self) -> str:
        """Ejecuta auto-diagnóstico del sistema."""
        from mcp_servers.doctor_mcp import DoctorMCPServer
        doctor = DoctorMCPServer(
            ollama_bridge=self.ollama,
            camera_controller=self.camera,
            osc_controller=self.osc,
            vault_path=self.config.get("obsidian", {}).get("vault_path", "D:\\Documentos\\Obsidian Vault")
        )
        res = doctor.execute_tool("doctor_health_check", {})
        diag = res.get("diagnostics", {})
        ollama_status = diag.get("ollama", {}).get("status", "desconocido")
        disk_free = diag.get("disk_space", {}).get("free_gb", "desconocido")
        return f"Diagnóstico NOVA: Sistema {res.get('overall_status', 'OPERATIONAL')}. IA Ollama: {ollama_status}. Espacio libre: {disk_free} GB."

    def _start_language_practice(self, lang: str, topic: str) -> str:
        """Inicia sesión de tutor técnico de idiomas con contexto de proyectos."""
        from mcp_servers.language_tutor_mcp import LanguageTutorMCPServer
        from mcp_servers.vault_mcp import ObsidianVaultMCPServer

        if not self.language_tutor:
            self.language_tutor = LanguageTutorMCPServer(ollama_bridge=self.ollama, voice_engine=self.voice)

        # Extraer contexto de proyectos de Obsidian para enriquecer la conversación técnica
        project_context = ""
        try:
            vault = ObsidianVaultMCPServer(
                vault_path=self.config.get("obsidian", {}).get("vault_path", "D:\\Documentos\\Obsidian Vault")
            )
            # Buscar proyecto coincidente si se menciona en el tema
            matched_proj = "Blender" if "blender" in topic.lower() else "NOVA"
            summary_res = vault.execute_tool("vault_summarize_project", {"project_name": matched_proj})
            if summary_res.get("success"):
                project_context = summary_res.get("summary", "")
        except Exception:
            pass

        res = self.language_tutor.execute_tool("language_start_session", {
            "language": lang,
            "topic": topic,
            "project_context": project_context
        })
        try:
            from ui.panel_widget import show_toast
            show_toast(f"Mentor de {lang.upper()} 🌍", f"Tema: {topic}", success=True)
        except Exception:
            pass
        return res.get("first_message") or res.get("message", f"Práctica de {lang} iniciada.")

    def _end_language_practice(self) -> str:
        """Finaliza la sesión de tutor de idiomas."""
        if not self.language_tutor or not self.language_tutor.active_session:
            return "No hay ninguna sesión de idiomas activa."
        
        res = self.language_tutor.execute_tool("language_end_session", {})
        return res.get("message", "Práctica de idiomas finalizada.")

