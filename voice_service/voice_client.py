"""Servicio de Voz Desacoplado para NOVA / Segundo Cerebro (Fase 2).

Conecta la percepción auditiva (openWakeWord + Whisper STT) y la síntesis hablada (TTS)
con el servicio agéntico FastAPI (Agent Loop) a través de comunicación asíncrona WebSocket / HTTP.
"""

import os
import json
import time
import logging
import threading
from typing import Optional, Callable, Dict, Any

from core.voice_engine import VoiceEngine
from core.ollama_bridge import OllamaBridge

logger = logging.getLogger("NOVA.VoiceService")

class VoiceServiceChannel:
    def __init__(
        self,
        agent_url: str = "http://127.0.0.1:8000/v1/agent/interact",
        voice_config: Optional[Dict[str, Any]] = None
    ):
        self.agent_url = agent_url
        self.voice_config = voice_config or {
            "wake_word_models": ["hey_nova", "hey_jarvis"],
            "wake_threshold": 0.5,
            "silence_limit_sec": 1.5,
            "stt_model": "small",
            "stt_language": "es",
            "tts_voice": "es-CO-SalomeNeural",
            "tts_rate": "+0%",
            "tts_volume": "+0%"
        }
        self.engine = VoiceEngine(self.voice_config)
        self.is_running = False

        # Conectar callbacks
        self.engine.on_wake_word_detected = self._on_wake_word
        self.engine.on_command_recognized = self._on_command_recognized

    def _on_wake_word(self):
        logger.info("Voz: Palabra de activación 'Hey Nova' detectada.")

    def _on_command_recognized(self, text: str):
        logger.info(f"Voz: Comando transcrito por Whisper: '{text}'")
        # Procesamiento asíncrono hacia el Agent Loop de FastAPI
        threading.Thread(
            target=self._send_to_agent,
            args=(text,),
            daemon=True,
            name="NOVA-VoiceAgentBridge"
        ).start()

    def _send_to_agent(self, prompt: str):
        import urllib.request

        payload = json.dumps({
            "prompt": prompt,
            "channel": "voice_channel"
        }).encode("utf-8")

        headers = {"Content-Type": "application/json"}

        try:
            req = urllib.request.Request(self.agent_url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                response_text = result.get("response_text", "")
                if response_text:
                    logger.info(f"Voz: Respuesta del agente: '{response_text[:100]}...'")
                    self.engine.speak(response_text)
        except Exception as e:
            logger.error(f"Error enviando comando de voz al Agent Loop ({self.agent_url}): {e}")
            fallback_msg = f"No se pudo conectar con el orquestador agéntico: {e}"
            self.engine.speak(fallback_msg)

    def start(self):
        logger.info("Iniciando Canal de Voz Desacoplado...")
        self.is_running = True
        self.engine.initialize_models()
        self.engine.start_listening()

    def stop(self):
        logger.info("Deteniendo Canal de Voz Desacoplado...")
        self.is_running = False
        self.engine.stop()
