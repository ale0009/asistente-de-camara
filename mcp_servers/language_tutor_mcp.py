"""Servidor MCP para Tutoría y Práctica de Idiomas (Inglés, Francés, Chino, Japonés).

Permite a NOVA actuar como tutor de conversación en tiempo real con conmutación dinámica
de voces nativas TTS de alta fidelidad, corrección pedagógica y temas interactivos.
"""

import logging
from typing import Dict, Any, List, Optional
from core.ollama_bridge import OllamaBridge

logger = logging.getLogger("NOVA.LanguageTutorMCPServer")

LANGUAGE_PROFILES = {
    "en": {
        "name": "Inglés",
        "voice": "en-US-JennyNeural",
        "system_prompt": (
            "You are NOVA, a bilingual technical mentor and English tutor. "
            "Help the user master their engineering projects (Blender, Python, AI vision, hardware) while speaking in English. "
            "Ask engaging questions about their project architecture, next steps, and algorithms. "
            "Keep your responses concise (2-3 sentences). "
            "If the user makes a grammar, vocabulary, or technical phrasing mistake, provide a gentle correction tip in parentheses at the end."
        )
    },
    "fr": {
        "name": "Francés",
        "voice": "fr-FR-DeniseNeural",
        "system_prompt": (
            "Tu es NOVA, un tuteur technique et mentor d'ingénierie en français. "
            "Aide l'utilisateur à maîtriser et discuter de ses projets (addons Blender, vision par caméra, code Python, architecture) en français. "
            "Enseigne-lui le vocabulaire technique adéquat (ex: 'maillage 3D', 'traitement d'image', 'extraction d'assets', 'algorithme'). "
            "Maintiens une conversation naturelle et stimulante (2-3 phrases par réponse). "
            "Si l'utilisateur fait une faute de grammaire ou de vocabulaire, ajoute un bref conseil amical entre parenthèses à la fin."
        )
    },
    "zh": {
        "name": "Chino Mandarín",
        "voice": "zh-CN-XiaoxiaoNeural",
        "system_prompt": (
            "你是NOVA，一位专业且热情的中文工程导师。帮助用户在用中文交流的同时，深入探讨和掌握他们的技术项目（如Blender插件开发、AI视觉相机、Python架构等）。"
            "教授他们地道的中文技术词汇（例如：三维网格、实时图像处理、资源提取、跟踪算法）。"
            "每次回复保持简洁自然（2-3句话）。如有语法或词汇错误，请在末尾括号中提供简短友好的纠正建议。"
        )
    },
    "ja": {
        "name": "Japonés",
        "voice": "ja-JP-NanamiNeural",
        "system_prompt": (
            "あなたはNOVA、親切で高度な技術力を持つ日本語のメンター兼チューターです。"
            "ユーザーが自分のプロジェクト（Blenderプラグイン、AIビジョン、Python開発など）について日本語で流暢に議論できるようサポートしてください。"
            "回答は自然で簡潔に（2〜3文）。間違いがあれば、文末の括弧内に短いアドバイスを添えてください。"
        )
    }
}

DEFAULT_SPANISH_VOICE = "es-CO-SalomeNeural"

class LanguageTutorMCPServer:
    def __init__(self, ollama_bridge: Optional[OllamaBridge] = None, voice_engine: Optional[Any] = None):
        self.ollama = ollama_bridge or OllamaBridge()
        self.voice_engine = voice_engine
        self.active_session: Optional[Dict[str, Any]] = None

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "language_start_session",
                "description": "Inicia una sesión de práctica de idiomas (francés, chino, inglés o japonés) orientada a dominar y discutir proyectos técnicos del usuario.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "language": {
                            "type": "string",
                            "enum": ["en", "fr", "zh", "ja"],
                            "description": "Código del idioma: 'fr' (Francés), 'zh' (Chino), 'en' (Inglés), 'ja' (Japonés)."
                        },
                        "topic": {
                            "type": "string",
                            "description": "Tema de conversación o proyecto a discutir (ej. 'Blender addons', 'cámara inteligente', 'arquitectura')."
                        },
                        "project_context": {
                            "type": "string",
                            "description": "Contexto técnico o resumen del proyecto extraído de Obsidian para enriquecer la conversación."
                        },
                        "level": {
                            "type": "string",
                            "enum": ["beginner", "intermediate", "advanced"],
                            "description": "Nivel del estudiante."
                        }
                    },
                    "required": ["language"]
                }
            },
            {
                "name": "language_get_status",
                "description": "Devuelve el estado de la sesión activa de idiomas (idioma actual, voz activa, tema).",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "language_end_session",
                "description": "Finaliza la práctica de idiomas y restaura el modo asistente habitual en español.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "language_converse",
                "description": "Procesa un turno de conversación pedagógica en el idioma activo de la sesión.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_message": {
                            "type": "string",
                            "description": "Mensaje del usuario en el idioma de práctica."
                        }
                    },
                    "required": ["user_message"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "language_start_session":
            lang = arguments.get("language", "fr").lower()
            topic = arguments.get("topic", "proyectos técnicos")
            project_context = arguments.get("project_context", "")
            level = arguments.get("level", "intermediate")
            return self._start_session(lang, topic, level, project_context)
        elif tool_name == "language_get_status":
            return self._get_status()
        elif tool_name == "language_end_session":
            return self._end_session()
        elif tool_name == "language_converse":
            return self._converse(arguments.get("user_message", ""))
        else:
            return {"success": False, "error": f"Herramienta desconocida: {tool_name}"}

    def _start_session(self, lang: str, topic: str, level: str, project_context: str = "") -> Dict[str, Any]:
        if lang not in LANGUAGE_PROFILES:
            return {"success": False, "error": f"Idioma no soportado '{lang}'. Opciones: 'fr', 'zh', 'en', 'ja'."}

        profile = LANGUAGE_PROFILES[lang]
        base_prompt = profile["system_prompt"]
        
        if project_context:
            system_prompt = (
                f"{base_prompt}\n\n"
                f"--- CONTEXT OF THE USER'S ACTIVE PROJECT ---\n"
                f"{project_context}\n"
                f"Discuss this specific project with the user in {profile['name']}, using accurate technical vocabulary."
            )
        else:
            system_prompt = base_prompt

        self.active_session = {
            "language": lang,
            "name": profile["name"],
            "voice": profile["voice"],
            "topic": topic,
            "level": level,
            "project_context": project_context,
            "system_prompt": system_prompt
        }

        # Conmutar voz en el motor si está enlazado
        if self.voice_engine and hasattr(self.voice_engine, "tts_voice"):
            self.voice_engine.tts_voice = profile["voice"]
            logger.info(f"Voz TTS de VoiceEngine conmutada a '{profile['voice']}' ({profile['name']})")

        welcome_prompt = (
            f"{system_prompt}\n"
            f"Greet the student warmly in {profile['name']}, introduce yourself as NOVA their technical mentor, "
            f"and ask the first open question about their project: '{topic}' (level: {level})."
        )
        first_greeting = self.ollama.query(welcome_prompt)

        return {
            "success": True,
            "session": self.active_session,
            "first_message": first_greeting,
            "message": f"Modo Mentor de {profile['name']} activado. Voz conmutada a {profile['voice']}."
        }

    def _get_status(self) -> Dict[str, Any]:
        if not self.active_session:
            return {
                "success": True,
                "active": False,
                "language": "es",
                "name": "Español",
                "voice": DEFAULT_SPANISH_VOICE
            }
        return {
            "success": True,
            "active": True,
            "session": self.active_session
        }

    def _end_session(self) -> Dict[str, Any]:
        prev_lang = self.active_session.get("name", "") if self.active_session else "idiomas"
        self.active_session = None

        if self.voice_engine and hasattr(self.voice_engine, "tts_voice"):
            self.voice_engine.tts_voice = DEFAULT_SPANISH_VOICE
            logger.info("Voz TTS restaurada a español por defecto.")

        return {
            "success": True,
            "active": False,
            "message": f"Sesión de {prev_lang} finalizada. Hemos regresado al modo asistente en español."
        }

    def _converse(self, user_message: str) -> Dict[str, Any]:
        if not self.active_session:
            return {"success": False, "error": "No hay ninguna sesión de idiomas activa. Usa language_start_session primero."}

        system_prompt = self.active_session["system_prompt"]
        response = self.ollama.query(
            prompt=user_message,
            system=system_prompt
        )

        return {
            "success": True,
            "language": self.active_session["language"],
            "response": response
        }
