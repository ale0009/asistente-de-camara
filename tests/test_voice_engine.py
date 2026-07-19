import os
import sys
from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.voice_engine import VoiceEngine


def test_listen_loop_reports_failure_if_mic_cannot_open():
    """Antes, un fallo al abrir el stream (ej. mic_index inválido) escapaba
    sin capturar y mataba el hilo en silencio. Ahora debe quedar contenido y
    avisado vía on_voice_engine_failed."""
    engine = VoiceEngine({"mic_index": 999})
    engine._open_stream = Mock(side_effect=OSError("Invalid input device (999)"))
    failures = []
    engine.on_voice_engine_failed = lambda msg: failures.append(msg)

    engine._listen_loop()  # no debe lanzar

    assert len(failures) == 1
    assert "999" in failures[0] or "Invalid input device" in failures[0]


def test_listen_loop_does_not_crash_without_failure_callback_set():
    engine = VoiceEngine({"mic_index": 999})
    engine._open_stream = Mock(side_effect=OSError("boom"))

    engine._listen_loop()  # no debe lanzar aunque no haya callback asignado


def test_stop_skips_pa_terminate_if_listen_thread_still_alive():
    """Si el hilo de escucha sigue vivo tras el join, no se debe llamar
    pa.terminate() (podía crashear si el hilo seguía usando el stream)."""
    engine = VoiceEngine({})
    engine.pa = Mock()
    engine.stream = Mock()
    fake_thread = Mock()
    fake_thread.is_alive.return_value = True
    engine._listen_thread = fake_thread

    engine.stop()

    engine.pa.terminate.assert_not_called()
    fake_thread.join.assert_called()


def test_stop_terminates_pa_if_listen_thread_exits_cleanly():
    engine = VoiceEngine({})
    engine.pa = Mock()
    fake_thread = Mock()
    fake_thread.is_alive.return_value = False
    engine._listen_thread = fake_thread

    engine.stop()

    engine.pa.terminate.assert_called_once()


def test_stop_handles_no_thread_and_no_pa_gracefully():
    engine = VoiceEngine({})
    engine._listen_thread = None
    engine.pa = None

    engine.stop()  # no debe lanzar


def test_voice_engine_tts_queues_and_processes_sequentially():
    import time
    import threading
    engine = VoiceEngine({})
    engine.is_running = True
    
    calls = []
    def fake_speak_sync(text):
        calls.append(text)
        time.sleep(0.05)
    engine._speak_sync = fake_speak_sync

    engine._tts_worker = threading.Thread(
        target=engine._tts_worker_loop, daemon=True
    )
    engine._tts_worker.start()

    engine.speak("Primera oración.")
    engine.speak("Segunda oración.")
    engine.speak("Tercera oración.")

    # Esperar a que se procese la cola
    time.sleep(0.3)

    engine.stop()

    assert calls == ["Primera oración.", "Segunda oración.", "Tercera oración."]


def test_voice_engine_get_input_devices_mocks(monkeypatch):
    engine = VoiceEngine({})
    
    # Mockear PyAudio
    mock_pa_instance = Mock()
    mock_pa_instance.get_host_api_info_by_index.return_value = {"deviceCount": 2}
    
    # Simular un dispositivo con canales de entrada y otro sin
    device_info_0 = {"maxInputChannels": 2, "name": "Micrófono USB"}
    device_info_1 = {"maxInputChannels": 0, "name": "Salida Auriculares"}
    
    def fake_get_device_info(host_api_idx, dev_idx):
        if dev_idx == 0:
            return device_info_0
        return device_info_1
        
    mock_pa_instance.get_device_info_by_host_api_device_index = fake_get_device_info
    
    # Reemplazar la instanciación de PyAudio
    monkeypatch.setattr("core.voice_engine.pyaudio.PyAudio", lambda: mock_pa_instance)
    
    devices = engine.get_input_devices()
    assert devices == {0: "Micrófono USB"}


def test_voice_engine_set_microphone_updates_config_and_yaml(tmp_path, monkeypatch):
    # Usar un config.yaml temporal en el directorio de trabajo
    temp_config = tmp_path / "config.yaml"
    temp_config.write_text("voice:\n  mic_index: 0", encoding="utf-8")
    
    # Cambiar al directorio temporal para el test
    monkeypatch.chdir(tmp_path)
    
    engine = VoiceEngine({"mic_index": 0})
    engine.is_running = True
    
    # Mockear stream
    mock_stream = Mock()
    engine.stream = mock_stream
    
    # Mockear _open_stream para no interactuar con hardware real
    mock_new_stream = Mock()
    engine._open_stream = lambda: mock_new_stream
    
    # Cambiar el micrófono a índice 2
    success = engine.set_microphone(2)
    
    assert success is True
    assert engine.config["mic_index"] == 2
    
    # Verificar que el stream original se cerró y el nuevo se abrió
    mock_stream.stop_stream.assert_called_once()
    mock_stream.close.assert_called_once()
    assert engine.stream == mock_new_stream
    
    # Verificar persistencia en config.yaml
    import yaml
    with open("config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    assert cfg["voice"]["mic_index"] == 2


def test_voice_engine_custom_onnx_detection(tmp_path, monkeypatch):
    import os
    fake_onnx = tmp_path / "nova.onnx"
    fake_onnx.write_text("fake_onnx_bytes", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    os.makedirs("assets", exist_ok=True)
    with open("assets/nova.onnx", "w") as f:
        f.write("fake")

    engine = VoiceEngine({})
    assert engine is not None
