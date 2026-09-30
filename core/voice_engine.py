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

from __future__ import annotations

import asyncio
import logging
import os
import queue
import struct
import subprocess
import tempfile
import threading
import time
import wave

import edge_tts
import numpy as np
import pygame
import webrtcvad
from openwakeword.model import Model as WakeWordModel

try:
    import pyaudio
    HAS_PYAUDIO = True
    FORMAT = pyaudio.paInt16
except ImportError:
    HAS_PYAUDIO = False
    pyaudio = None
    FORMAT = 2

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False
    sd = None

try:
    import whisper
    HAS_WHISPER = True
except ImportError:
    HAS_WHISPER = False
    whisper = None

logger = logging.getLogger(__name__)

class SoundDeviceStreamAdapter:
    def __init__(self, sample_rate, channels, mic_index, chunk):
        self.sample_rate = sample_rate
        self.channels = channels
        self.mic_index = mic_index
        self.chunk = chunk
        self.stream = sd.RawInputStream(
            samplerate=sample_rate,
            channels=channels,
            dtype='int16',
            device=mic_index,
            blocksize=chunk
        )
        self.stream.start()

    def start_stream(self):
        if not self.stream.active:
            self.stream.start()

    def stop_stream(self):
        if self.stream.active:
            self.stream.stop()

    def read(self, num_frames, exception_on_overflow=False):
        data, _ = self.stream.read(num_frames)
        return bytes(data)

    def close(self):
        try:
            self.stream.stop()
            self.stream.close()
        except Exception:
            pass

# ─── Constantes de audio ───────────────────────────────────────────────────────
SAMPLE_RATE = 16000          # Hz requerido por openWakeWord y Whisper
CHANNELS    = 1              # Mono
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
        self.tts_queue = queue.Queue()
        self._tts_worker: threading.Thread | None = None

        # Callbacks (se asignan desde main.py)
        self.on_wake_word_detected = None
        self.on_command_recognized = None
        # Se dispara si el hilo de escucha no puede arrancar (ej. mic_index
        # inválido) — sin esto, el hilo moría en silencio y NOVA se quedaba
        # sin voz el resto de la sesión sin ningún aviso visible.
        self.on_voice_engine_failed = None

    # ──────────────────────────────────────────────────────────────────────────
    # Inicialización de modelos pesados (ejecutar en hilo separado si se desea)
    # ──────────────────────────────────────────────────────────────────────────
    def initialize_models(self):
        """Carga Whisper y openWakeWord. Llamar antes de start_listening()."""
        # 1. Whisper STT
        if HAS_WHISPER:
            try:
                logger.info("Cargando modelo Whisper '%s'...", self.stt_model_size)
                self.stt_model = whisper.load_model(self.stt_model_size)
                logger.info("Whisper listo.")
            except Exception as e:
                logger.warning("Fallo al cargar whisper nativo: %s. Se usará motor voz-local.", e)
                self.stt_model = None
        else:
            logger.info("whisper nativo no presente; se usará motor voz-local (GPU int8 / faster-whisper).")
            self.stt_model = None

        # 2. openWakeWord — verificar si existe assets/nova.onnx custom o usar el fallback
        custom_onnx = os.path.abspath("assets/nova.onnx")
        oww_models = self.config.get("wake_word_models", [])
        if os.path.isfile(custom_onnx):
            logger.info("Detectado modelo custom ONNX para 'Hey Nova' en: %s", custom_onnx)
            oww_models = [custom_onnx]
        elif not oww_models:
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

        # 3. Backend de Audio (PyAudio o sounddevice)
        if HAS_PYAUDIO:
            try:
                self.pa = pyaudio.PyAudio()
            except Exception as exc:
                logger.warning("PyAudio falló al iniciar: %s. Se usará sounddevice.", exc)
                self.pa = None
        else:
            self.pa = None

        # Callbacks para la UI
        self.on_wake_word_detected = None
        self.on_command_recognized = None
        self.on_voice_engine_failed = None
        self.on_audio_level_updated = None

    # ──────────────────────────────────────────────────────────────────────────
    # Escucha en segundo plano
    # ──────────────────────────────────────────────────────────────────────────
    def start_listening(self):
        if not self.pa and not HAS_SOUNDDEVICE:
            logger.error("No hay backend de audio disponible (ni PyAudio ni sounddevice).")
            return

        self.is_running = True
        self._listen_thread = threading.Thread(
            target=self._listen_loop, daemon=True, name="NOVA-ListenThread"
        )
        self._listen_thread.start()
        logger.info("Escucha de wake word iniciada.")

        # Iniciar worker de TTS
        self._tts_worker = threading.Thread(
            target=self._tts_worker_loop, daemon=True, name="NOVA-TTS-Worker"
        )
        self._tts_worker.start()
        logger.info("Worker de TTS iniciado.")

    def _open_stream(self):
        mic_index = self.config.get("mic_index", None)
        if mic_index is not None:
            logger.info("Usando micrófono específico (índice %s)", mic_index)
            
        if self.pa:
            return self.pa.open(
                rate=SAMPLE_RATE,
                channels=CHANNELS,
                format=FORMAT,
                input=True,
                input_device_index=mic_index,
                frames_per_buffer=OWW_CHUNK,
            )
        elif HAS_SOUNDDEVICE:
            return SoundDeviceStreamAdapter(SAMPLE_RATE, CHANNELS, mic_index, OWW_CHUNK)
        else:
            raise RuntimeError("No se encontró backend de audio para captura")

    def _listen_loop(self):
        """Bucle principal: detecta wake word → graba comando → procesa con Whisper."""
        logger.info("Bucle de escucha de voz iniciado.")
        consecutive_failures = 0

        while self.is_running:
            if not self.stream:
                try:
                    self.stream = self._open_stream()
                    logger.info("Stream de audio abierto/reabierto.")
                    consecutive_failures = 0
                except Exception as exc:
                    logger.error("No se pudo abrir el micrófono (mic_index=%s): %s",
                                 self.config.get("mic_index"), exc)
                    consecutive_failures += 1
                    if consecutive_failures == 1 and self.on_voice_engine_failed:
                        self.on_voice_engine_failed(str(exc))
                    time.sleep(2.0)
                    continue

            try:
                raw = self.stream.read(OWW_CHUNK, exception_on_overflow=False)
                audio_np = np.frombuffer(raw, dtype=np.int16)

                if self.on_audio_level_updated and len(audio_np) > 0:
                    rms = np.sqrt(np.mean(np.square(audio_np, dtype=np.float32)))
                    level = min(1.0, float(rms / 3500.0))
                    self.on_audio_level_updated(level)

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
                        
                        # Detener stream temporalmente para Whisper
                        self.stream.stop_stream()

                        if self.on_wake_word_detected:
                            self.on_wake_word_detected()

                        # Grabar y transcribir el comando
                        command_text = self._record_and_transcribe(self.stream)
                        if command_text:
                            if self.on_command_recognized:
                                self.on_command_recognized(command_text)

                        if self.stream:  # Podría haber sido cambiado a None en set_microphone
                            self.stream.start_stream()
            except Exception as exc:
                logger.warning("Error leyendo/procesando en stream de audio: %s. Reabriendo...", exc)
                try:
                    if self.stream:
                        self.stream.close()
                except Exception:
                    pass
                self.stream = None
                time.sleep(0.5)

        # Al salir, asegurar que cerramos el stream actual
        if self.stream:
            try:
                self.stream.close()
            except Exception:
                pass
            self.stream = None

    # ──────────────────────────────────────────────────────────────────────────
    # Grabación con VAD + Whisper STT
    # ──────────────────────────────────────────────────────────────────────────
    def _record_and_transcribe(self, stream) -> str:
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
                sampwidth = self.pa.get_sample_size(FORMAT) if self.pa else 2
                wf.setsampwidth(sampwidth)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(audio_bytes)

        # Transcripción con Whisper o voz-local
        try:
            if self.stt_model:
                logger.info("Transcribiendo con openai-whisper nativo...")
                result = self.stt_model.transcribe(
                    tmp_path,
                    language=self.language,
                    fp16=False,
                )
                text = result.get("text", "").strip()
            else:
                logger.info("Transcribiendo con voz-local (GPU int8)...")
                voz_local_dir = os.path.expanduser("~/Datos/Projects/voz-local")
                cmd = ["uv", "run", "--directory", voz_local_dir, "python", "voz.py", "transcribir", tmp_path]
                res = subprocess.run(cmd, capture_output=True, text=True, check=False)
                if res.returncode == 0:
                    text = res.stdout.strip()
                else:
                    logger.error("Error en voz-local: %s", res.stderr)
                    text = ""
            logger.info("Transcripción obtenida: '%s'", text)
            return text
        except Exception as exc:
            logger.error("Error en Whisper/transcripción: %s", exc)
            return ""
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    # ──────────────────────────────────────────────────────────────────────────
    # TTS con edge-tts (con fallback local a Kokoro/Piper via 'hablar')
    # ──────────────────────────────────────────────────────────────────────────
    def speak(self, text: str):
        """Agrega el texto a la cola de reproducción de voz."""
        if text and text.strip():
            self.tts_queue.put(text)

    def _tts_worker_loop(self):
        """Bucle consumidor en segundo plano para reproducir el audio de forma secuencial."""
        while True:
            try:
                # Si no está en ejecución y la cola está vacía, terminamos el hilo
                if not self.is_running and self.tts_queue.empty():
                    break
                text = self.tts_queue.get(timeout=0.5)
                if text is None:
                    self.tts_queue.task_done()
                    break
                self._speak_sync(text)
                self.tts_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error en bucle worker de TTS: {e}")

    def _speak_sync(self, text: str):
        async def _generate(path: str):
            communicate = edge_tts.Communicate(text, self.tts_voice)
            await communicate.save(path)

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            asyncio.run(_generate(tmp_path))

            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.music.unload()
        except Exception as exc:
            logger.warning("Fallo en edge-tts (%s), usando fallback local neuronal 'hablar'...", exc)
            try:
                subprocess.run(["hablar", text], check=False)
            except Exception as e2:
                logger.error("Error en fallback 'hablar': %s", e2)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def get_input_devices(self) -> dict:
        """Devuelve un diccionario de {index: name} de los micrófonos disponibles."""
        devices = {}
        if self.pa:
            pa_temp = self.pa
            try:
                info = pa_temp.get_host_api_info_by_index(0)
                numdevices = info.get('deviceCount', 0)
                for i in range(0, numdevices):
                    device_info = pa_temp.get_device_info_by_host_api_device_index(0, i)
                    if device_info.get('maxInputChannels', 0) > 0:
                        devices[i] = device_info.get('name')
            except Exception as e:
                logger.error(f"Error listando micrófonos en VoiceEngine: {e}")
        elif HAS_SOUNDDEVICE:
            try:
                devs = sd.query_devices()
                for i, d in enumerate(devs):
                    if d.get('max_input_channels', 0) > 0:
                        devices[i] = d.get('name', f"Dispositivo {i}")
            except Exception as e:
                logger.error(f"Error listando micrófonos con sounddevice: {e}")
        return devices

    def set_microphone(self, index: int) -> bool:
        """Establece el micrófono activo persistentemente y reinicia el stream en caliente."""
        logger.info(f"Cambiando micrófono al índice: {index}")
        self.config["mic_index"] = index

        # Guardar en config.yaml de forma permanente
        try:
            import yaml
            if os.path.exists("config.yaml"):
                with open("config.yaml", "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                
                if "voice" not in cfg:
                    cfg["voice"] = {}
                cfg["voice"]["mic_index"] = index
                
                with open("config.yaml", "w", encoding="utf-8") as f:
                    yaml.safe_dump(cfg, f, default_flow_style=False, allow_unicode=True)
                logger.info("config.yaml actualizado con el nuevo mic_index.")
        except Exception as e:
            logger.error(f"Error guardando mic_index en config.yaml: {e}")

        # Si el stream de escucha está corriendo, lo liberamos para que el hilo de escucha lo reabra
        if self.is_running and self.stream:
            logger.info("Liberando stream viejo para forzar reinicio en caliente...")
            try:
                old_stream = self.stream
                self.stream = None
                old_stream.stop_stream()
                old_stream.close()
                logger.info("Stream viejo cerrado exitosamente.")
                return True
            except Exception as e:
                logger.error(f"Error al liberar el stream viejo de micrófono: {e}")
                return False
        return True

    # ──────────────────────────────────────────────────────────────────────────
    # Limpieza
    # ──────────────────────────────────────────────────────────────────────────
    def stop(self):
        self.is_running = False

        # Desbloquear y cerrar el stream de micrófono de inmediato
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
        except Exception:
            pass

        # Detener worker de TTS enviando señal de parada
        if self.tts_queue:
            self.tts_queue.put(None)
            if self._tts_worker and self._tts_worker.is_alive():
                self._tts_worker.join(timeout=1.0)

        if self._listen_thread and self._listen_thread.is_alive():
            self._listen_thread.join(timeout=1.5)

        if self.pa:
            try:
                self.pa.terminate()
            except Exception:
                pass

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
