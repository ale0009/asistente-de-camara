"""
voice_engine.py — Motor de Voz de NOVA
=======================================
100% LOCAL — Sin API keys, sin pagos, sin internet.

Stack:
  - Wake Word : openWakeWord  (modelos ONNX preentrenados, gratis)
  - STT       : openai-whisper (local, modelo "small" en español)
  - TTS       : edge-tts       (síntesis local via es-CO-SalomeNeural)

Flujo:
  1. openWakeWord escucha en bucle frames de 1280 muestras a 16 kHz.
  2. Cuando detecta "hey_nova" (o el modelo más cercano disponible),
     llama a on_wake_word_detected().
  3. Se graba audio con VAD (webrtcvad) hasta detectar silencio.
  4. Whisper transcribe el audio a texto.
  5. Se llama a on_command_recognized(text).
  6. NOVA responde hablando via edge-tts (TTS offline usando MS Edge voices).
"""

import asyncio
import logging
import os
import struct
import tempfile
import threading
import time
import wave

import edge_tts
import numpy as np
import pyaudio
import webrtcvad
import whisper
from openwakeword.model import Model as WakeWordModel

logger = logging.getLogger(__name__)

# ─── Constantes de audio ───────────────────────────────────────────────────────
SAMPLE_RATE = 16000          # Hz requerido por openWakeWord y Whisper
CHANNELS    = 1              # Mono
FORMAT      = pyaudio.paInt16
OWW_CHUNK   = 1280           # muestras por frame (openWakeWord lo requiere)
VAD_FRAME_MS = 30            # ms por frame para webrtcvad (10, 20 o 30)
VAD_FRAME_SAMPLES = int(SAMPLE_RATE * VAD_FRAME_MS / 1000)  # 480 muestras

# Umbral de activación del wake word (0.0 - 1.0)
WAKE_THRESHOLD = 0.5

# Silencio máximo antes de cortar la grabación del comando (segundos)
SILENCE_LIMIT_SEC = 1.5


class VoiceEngine:
    """
    Motor de voz totalmente local para NOVA.
    No requiere ninguna API key ni conexión a internet.
    """

    def __init__(self, config: dict):
        self.config = config
        self.tts_voice = config.get("tts_voice", "es-CO-SalomeNeural")
        self.stt_model_size = config.get("stt_model", "small")
        self.language = config.get("stt_language", "es")

        # Modelos (se cargan en initialize_models para no bloquear el constructor)
        self.oww_model: WakeWordModel | None = None
        self.stt_model = None
        self.vad = webrtcvad.Vad(3)  # agresividad máxima

        # PyAudio
        self.pa: pyaudio.PyAudio | None = None
        self.stream: pyaudio.Stream | None = None

        # Estado
        self.is_running = False
        self._listen_thread: threading.Thread | None = None

        # Callbacks (se asignan desde main.py)
        self.on_wake_word_detected = None
        self.on_command_recognized = None

    # ──────────────────────────────────────────────────────────────────────────
    # Inicialización de modelos pesados (ejecutar en hilo separado si se desea)
    # ──────────────────────────────────────────────────────────────────────────
    def initialize_models(self):
        """Carga Whisper y openWakeWord. Llamar antes de start_listening()."""
        # 1. Whisper STT
        logger.info("Cargando modelo Whisper '%s'...", self.stt_model_size)
        self.stt_model = whisper.load_model(self.stt_model_size)
        logger.info("Whisper listo.")

        # 2. openWakeWord — intentamos con el modelo de "hey jarvis" incluido
        #    (el más parecido a "nova"). Si el usuario quiere entrenar "hey nova"
        #    puede subir el .onnx a assets/nova.onnx y reemplazar la lista.
        oww_models = self.config.get("wake_word_models", [])
        if not oww_models:
            # Modelos preentrenados incluidos en el paquete de openWakeWord
            oww_models = ["hey_jarvis"]   # Fallback gratuito incluido por defecto

        logger.info("Cargando openWakeWord con modelos: %s", oww_models)
        try:
            self.oww_model = WakeWordModel(
                wakeword_models=oww_models,
                inference_framework="onnx",
            )
            logger.info("openWakeWord listo. Di '%s' para activar NOVA.",
                        oww_models[0])
        except Exception as exc:
            logger.error("Error cargando openWakeWord: %s", exc)
            logger.warning("El Wake Word quedará desactivado. "
                           "NOVA aún funciona con los botones del panel.")

        # 3. PyAudio
        self.pa = pyaudio.PyAudio()

    # ──────────────────────────────────────────────────────────────────────────
    # Escucha en segundo plano
    # ──────────────────────────────────────────────────────────────────────────
    def start_listening(self):
        if not self.pa:
            logger.error("Llama a initialize_models() antes de start_listening().")
            return

        self.is_running = True
        self._listen_thread = threading.Thread(
            target=self._listen_loop, daemon=True, name="NOVA-ListenThread"
        )
        self._listen_thread.start()
        logger.info("Escucha de wake word iniciada.")

    def _open_stream(self) -> pyaudio.Stream:
        mic_index = self.config.get("mic_index", None)
        if mic_index is not None:
            logger.info("Usando micrófono específico (índice %s)", mic_index)
            
        return self.pa.open(
            rate=SAMPLE_RATE,
            channels=CHANNELS,
            format=FORMAT,
            input=True,
            input_device_index=mic_index,
            frames_per_buffer=OWW_CHUNK,
        )

    def _listen_loop(self):
        """Bucle principal: detecta wake word → graba comando → procesa con Whisper."""
        stream = self._open_stream()
        logger.info("Stream de audio abierto.")

        try:
            while self.is_running:
                raw = stream.read(OWW_CHUNK, exception_on_overflow=False)
                audio_np = np.frombuffer(raw, dtype=np.int16)

                # openWakeWord (requiere float32 normalizado)
                if self.oww_model:
                    audio_f32 = audio_np.astype(np.float32) / 32768.0
                    predictions = self.oww_model.predict(audio_f32)

                    triggered = any(
                        score >= WAKE_THRESHOLD
                        for score in predictions.values()
                    )

                    if triggered:
                        model_name = max(predictions, key=predictions.get)
                        logger.info("¡Wake word detectado! modelo=%s score=%.2f",
                                    model_name, predictions[model_name])
                        stream.stop_stream()

                        if self.on_wake_word_detected:
                            self.on_wake_word_detected()

                        # Grabar y transcribir el comando
                        command_text = self._record_and_transcribe(stream)
                        if command_text:
                            if self.on_command_recognized:
                                self.on_command_recognized(command_text)

                        stream.start_stream()
        except Exception as exc:
            logger.error("Error en el bucle de escucha: %s", exc)
        finally:
            stream.close()

    # ──────────────────────────────────────────────────────────────────────────
    # Grabación con VAD + Whisper STT
    # ──────────────────────────────────────────────────────────────────────────
    def _record_and_transcribe(self, stream: pyaudio.Stream) -> str:
        """
        Graba frames de audio usando VAD (webrtcvad) hasta detectar silencio,
        luego transcribe con Whisper y devuelve el texto.
        """
        logger.info("Escuchando comando... (habla ahora)")
        stream.start_stream()

        recorded_frames: list[bytes] = []
        silence_frames = 0
        max_silence_frames = int(SILENCE_LIMIT_SEC * 1000 / VAD_FRAME_MS)
        speaking_started = False

        # Leemos frames del tamaño que exige webrtcvad (VAD_FRAME_SAMPLES)
        read_size = VAD_FRAME_SAMPLES

        try:
            while True:
                raw = stream.read(read_size, exception_on_overflow=False)
                recorded_frames.append(raw)

                is_speech = self.vad.is_speech(raw, SAMPLE_RATE)

                if is_speech:
                    speaking_started = True
                    silence_frames = 0
                elif speaking_started:
                    silence_frames += 1
                    if silence_frames > max_silence_frames:
                        break  # Silencio detectado tras hablar
                else:
                    # Aún no empezó a hablar, esperamos un máximo de 3 segundos
                    if len(recorded_frames) > (3000 / VAD_FRAME_MS):
                        logger.info("Timeout: no se detectó voz en 3 segundos.")
                        return ""
        except Exception as exc:
            logger.error("Error durante grabación de comando: %s", exc)
            return ""

        stream.stop_stream()

        if not recorded_frames or not speaking_started:
            logger.info("No se detectó habla en el audio grabado.")
            return ""

        # Guardar en archivo temporal para Whisper
        audio_bytes = b"".join(recorded_frames)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(self.pa.get_sample_size(FORMAT))
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio_bytes)

        # Transcripción con Whisper
        try:
            logger.info("Transcribiendo con Whisper...")
            result = self.stt_model.transcribe(
                tmp_path,
                language=self.language,
                fp16=False,
            )
            text = result.get("text", "").strip()
            logger.info("Whisper dijo: '%s'", text)
            return text
        except Exception as exc:
            logger.error("Error en Whisper: %s", exc)
            return ""
        finally:
            os.unlink(tmp_path)

    # ──────────────────────────────────────────────────────────────────────────
    # TTS con edge-tts (sin internet — usa los motores de Windows)
    # ──────────────────────────────────────────────────────────────────────────
    def speak(self, text: str):
        """Sintetiza voz y la reproduce. No bloquea el hilo principal."""
        threading.Thread(
            target=self._speak_sync, args=(text,), daemon=True,
            name="NOVA-TTS"
        ).start()

    def _speak_sync(self, text: str):
        async def _run():
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                communicate = edge_tts.Communicate(text, self.tts_voice)
                await communicate.save(tmp_path)
                # Reproducir con el reproductor por defecto de Windows
                os.startfile(tmp_path)
                # Esperar un momento para que el reproductor cargue antes de borrar
                time.sleep(3)
            except Exception as exc:
                logger.error("Error en edge-tts: %s", exc)
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

        asyncio.run(_run())

    # ──────────────────────────────────────────────────────────────────────────
    # Limpieza
    # ──────────────────────────────────────────────────────────────────────────
    def stop(self):
        self.is_running = False
        if self._listen_thread and self._listen_thread.is_alive():
            self._listen_thread.join(timeout=2)
        if self.pa:
            self.pa.terminate()
        logger.info("Motor de voz detenido.")


# ──────────────────────────────────────────────────────────────────────────────
# Test rápido de escucha (ejecutar directamente con: python -m core.voice_engine)
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import yaml

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    with open("config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    engine = VoiceEngine(cfg.get("voice", {}))
    engine.initialize_models()

    def _on_wake():
        print(">>> ¡Wake word detectado!")

    def _on_cmd(text):
        print(f">>> Comando: '{text}'")
        engine.speak(f"Recibí el comando: {text}")

    engine.on_wake_word_detected = _on_wake
    engine.on_command_recognized = _on_cmd
    engine.start_listening()

    print("Escuchando... (Ctrl+C para salir)")
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        engine.stop()
