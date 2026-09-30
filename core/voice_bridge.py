# -*- coding: utf-8 -*-
"""
Puente de Voz Local para NOVA (core/voice_bridge.py).
Integra Whisper GPU int8 (transcripción) y Kokoro/Piper (síntesis de voz)
utilizando el entorno preconfigurado en ~/Datos/Projects/voz-local.
"""
import os
import re
import sys
import time
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("NOVA.VoiceBridge")

VOZ_DIR = Path.home() / "Datos" / "Projects" / "voz-local"
HABLAR_BIN = Path.home() / ".local" / "bin" / "hablar"
TEMP_AUDIO = Path("/tmp/nova_voice_prompt.wav")


class VoiceBridge:
    def __init__(self, ollama_bridge=None, memory=None):
        from core.ollama_bridge import OllamaBridge
        from core.episodic_memory import EpisodicMemory

        self.ollama = ollama_bridge or OllamaBridge()
        self.memory = memory or EpisodicMemory()

    @staticmethod
    def clean_text_for_speech(text: str) -> str:
        """Limpia sintaxis de Markdown, URLs, bloques de código y emojis para que el TTS suene natural."""
        # 1. Eliminar bloques de código ```...```
        text = re.sub(r'```[\s\S]*?```', 'bloque de código omitido', text)
        # 2. Eliminar código inline `...`
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # 3. Eliminar enlaces markdown [texto](url)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        # 4. Eliminar enlaces wiki [[nota]]
        text = re.sub(r'\[\[([^\|\]]+)(?:\|[^\]]+)?\]\]', r'\1', text)
        # 5. Eliminar encabezados y negritas
        text = re.sub(r'#{1,6}\s*', '', text)
        text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
        # 6. Eliminar viñetas y caracteres especiales
        text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'https?://\S+', '', text)
        # 7. Normalizar espacios
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def speak(self, text: str, wait: bool = False):
        """Sintetiza y reproduce texto en voz alta usando el comando neuronal 'hablar'."""
        clean = self.clean_text_for_speech(text)
        if not clean:
            return

        # Limitar longitud para evitar alocuciones de más de 30 segundos
        if len(clean) > 400:
            clean = clean[:400] + "... y más detalles en pantalla."

        try:
            cmd = [str(HABLAR_BIN), clean]
            if wait:
                subprocess.run(cmd, check=False)
            else:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            logger.error(f"Error reproduciendo voz con 'hablar': {e}")

    def record_microphone(self, output_path: Path = TEMP_AUDIO, duration_seconds: int = 5) -> bool:
        """Graba audio desde el micrófono predeterminado con PipeWire (16kHz mono)."""
        output_path.unlink(missing_ok=True)
        try:
            logger.info(f"Grabando micrófono durante {duration_seconds}s en {output_path}...")
            proc = subprocess.Popen(
                ["pw-record", "--channels", "1", "--rate", "16000", str(output_path)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            time.sleep(duration_seconds)
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()

            if output_path.exists() and output_path.stat().st_size > 4000:
                return True
        except Exception as e:
            logger.error(f"Error grabando con pw-record: {e}")
        return False

    def transcribe(self, audio_path: Path = TEMP_AUDIO) -> str:
        """Transcribe un archivo WAV usando Whisper small GPU int8 en voz-local."""
        if not audio_path.exists():
            return ""

        try:
            logger.info("Transcribiendo con Whisper small GPU int8...")
            res = subprocess.run(
                ["uv", "run", "voz.py", "transcribir", str(audio_path)],
                cwd=str(VOZ_DIR), capture_output=True, text=True, timeout=15
            )
            if res.returncode == 0:
                texto = res.stdout.strip()
                logger.info(f"Transcripción exitosa: '{texto}'")
                return texto
        except Exception as e:
            logger.error(f"Error transcribiendo audio con voz.py: {e}")
        return ""

    def process_voice_query(self, duration_seconds: int = 5) -> Dict[str, Any]:
        """Flujo completo de Push-to-Talk: graba, transcribe, consulta y responde con voz."""
        t0 = time.time()
        ok = self.record_microphone(duration_seconds=duration_seconds)
        if not ok:
            return {"success": False, "message": "No se detectó audio en el micrófono."}

        transcription = self.transcribe()
        if not transcription:
            return {"success": False, "message": "No se pudo transcribir el audio."}

        # Modelo por defecto según MAQUINA.md: granite4:tiny-h (mejor calidad en español)
        prompt = (
            "Eres NOVA, el copiloto local de la estación de trabajo de Mario. "
            "Responde a su consulta de voz en español de forma directa, técnica, amable y concisa (máximo 2 o 3 frases breves), "
            "óptima para ser leída por un sintetizador de voz sin sintaxis compleja:\n\n"
            f"Consulta: {transcription}"
        )

        reply = self.ollama.query(prompt, model="granite4:tiny-h", max_tokens=150)
        clean_reply = self.clean_text_for_speech(reply)

        # Alocución en segundo plano
        self.speak(clean_reply, wait=False)

        # Registrar en memoria episódica
        self.memory.log_event("voice", "user_talk", transcription, clean_reply, "voz,whisper,kokoro")

        total_time = round(time.time() - t0, 2)
        return {
            "success": True,
            "transcription": transcription,
            "response": clean_reply,
            "latency_seconds": total_time
        }
