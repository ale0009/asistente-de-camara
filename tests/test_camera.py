import os
import sys
import threading
import time
from unittest.mock import MagicMock, Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core.camera as camera_module
from core.camera import CameraController, find_camera_index_by_name


def test_find_camera_index_by_name_matches():
    fake_graph = Mock()
    fake_graph.get_input_devices.return_value = [
        "OBSBOT Virtual Camera",
        "OBSBOT Tiny 3 Lite StreamCamera",
        "OBS Virtual Camera",
    ]
    with patch("pygrabber.dshow_graph.FilterGraph", return_value=fake_graph), \
         patch("pythoncom.CoInitialize") as mock_init, \
         patch("pythoncom.CoUninitialize") as mock_uninit:
        index = find_camera_index_by_name("OBSBOT Tiny 3 Lite")

    assert index == 1
    # COM debe inicializarse/liberarse en el hilo que llama, sin importar cuál sea.
    mock_init.assert_called_once()
    mock_uninit.assert_called_once()


def test_find_camera_index_by_name_no_match_falls_back_to_none():
    fake_graph = Mock()
    fake_graph.get_input_devices.return_value = ["OBS Virtual Camera"]
    with patch("pygrabber.dshow_graph.FilterGraph", return_value=fake_graph), \
         patch("pythoncom.CoInitialize"), patch("pythoncom.CoUninitialize"):
        index = find_camera_index_by_name("OBSBOT Tiny 3 Lite")

    assert index is None


def test_find_camera_index_by_name_empty_input_returns_none():
    assert find_camera_index_by_name("") is None
    assert find_camera_index_by_name(None) is None


def test_find_camera_index_by_name_releases_com_even_on_enum_failure():
    with patch("pygrabber.dshow_graph.FilterGraph", side_effect=RuntimeError("boom")), \
         patch("pythoncom.CoInitialize") as mock_init, \
         patch("pythoncom.CoUninitialize") as mock_uninit:
        index = find_camera_index_by_name("OBSBOT")

    assert index is None
    mock_init.assert_called_once()
    mock_uninit.assert_called_once()


def test_capture_loop_detects_disconnect_and_reconnects():
    """Simula una cámara que deja de responder y luego vuelve, y confirma
    que _capture_loop avisa (on_camera_disconnected/on_camera_reconnected)
    y reabre el dispositivo solo, en vez de congelarse para siempre."""
    good_cap = MagicMock()
    good_cap.isOpened.return_value = True
    good_cap.read.return_value = (True, "frame1")

    reopened_cap = MagicMock()
    reopened_cap.isOpened.return_value = True
    reopened_cap.read.return_value = (True, "frame2")

    opened = {"n": 0}

    def fake_video_capture(_index, _backend):
        opened["n"] += 1
        return good_cap if opened["n"] == 1 else reopened_cap

    cam = CameraController(camera_index=0, width=640, height=360)
    events = []
    cam.on_camera_disconnected = lambda: events.append("disconnected")
    cam.on_camera_reconnected = lambda: events.append("reconnected")

    with patch.object(camera_module, "RECONNECT_AFTER_FAILURES", 3), \
         patch.object(camera_module, "RECONNECT_RETRY_DELAY_SEC", 0.01), \
         patch("core.camera.find_camera_index_by_name", return_value=None), \
         patch("cv2.waitKey", return_value=-1), \
         patch("cv2.VideoCapture", side_effect=fake_video_capture):
        try:
            cam.start()
            for _ in range(50):
                if cam.get_frame() == "frame1":
                    break
                time.sleep(0.02)
            assert cam.get_frame() == "frame1"

            # Simular que la cámara deja de responder
            good_cap.read.return_value = (False, None)

            for _ in range(100):
                if events == ["disconnected", "reconnected"]:
                    break
                time.sleep(0.02)

            # Estas aserciones deben correr ANTES de cam.stop(): stop() limpia
            # current_frame a None a propósito (ver core/camera.py), así que
            # comprobar el frame después de detener la cámara daría un falso
            # negativo.
            assert events == ["disconnected", "reconnected"]
            assert cam.get_frame() == "frame2"
        finally:
            cam.stop()


def test_stop_waits_for_in_flight_reopen_before_releasing():
    """Si stop() se llama mientras _capture_loop está a mitad de reabrir el
    dispositivo, debe esperar (no dejar un cv2.VideoCapture huérfano sin
    liberar) — ver core/camera.py::stop, join(timeout=6.0)."""
    slow_cap = MagicMock()
    slow_cap.isOpened.return_value = True
    slow_cap.read.return_value = (True, "frame")

    release_event_order = []

    def slow_video_capture(_index, _backend):
        time.sleep(0.3)  # simula una apertura de cámara lenta
        return slow_cap

    slow_cap.release.side_effect = lambda: release_event_order.append("released")

    cam = CameraController(camera_index=0, width=640, height=360)
    cam.is_running = True
    cam._thread = None

    with patch("core.camera.find_camera_index_by_name", return_value=None), \
         patch("cv2.VideoCapture", side_effect=slow_video_capture):
        cam._thread = threading.Thread(target=cam._capture_loop, daemon=True)
        cam.is_running = True
        cam._thread.start()
        time.sleep(0.05)  # dejar que _capture_loop entre a la apertura lenta

        cam.stop()

    assert cam.cap is None


def test_get_available_cameras_mocks(monkeypatch):
    from core.camera import get_available_cameras
    
    mock_filter_graph = MagicMock()
    mock_filter_graph.return_value.get_input_devices.return_value = ["OBSBOT Tiny 3 Lite", "Cámara Integrada"]
    
    monkeypatch.setattr("pygrabber.dshow_graph.FilterGraph", mock_filter_graph)
    monkeypatch.setattr("pythoncom.CoInitialize", lambda: None)
    monkeypatch.setattr("pythoncom.CoUninitialize", lambda: None)
    
    cams = get_available_cameras()
    assert cams == {0: "OBSBOT Tiny 3 Lite", 1: "Cámara Integrada"}


def test_set_camera_updates_config_and_releases(tmp_path, monkeypatch):
    temp_config = tmp_path / "config.yaml"
    temp_config.write_text("camera:\n  camera_index: 0\n  camera_name: 'OBSBOT'", encoding="utf-8")
    
    monkeypatch.chdir(tmp_path)
    
    cam = CameraController(camera_index=0)
    cam.is_running = True
    mock_cap = MagicMock()
    cam.cap = mock_cap
    
    success = cam.set_camera(1, "Nueva Cámara")
    
    assert success is True
    assert cam.camera_index == 1
    assert cam.device_name == "Nueva Cámara"
    mock_cap.release.assert_called_once()
    assert cam.cap is None
    
    import yaml
    with open("config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    assert cfg["camera"]["camera_index"] == 1
    assert cfg["camera"]["camera_name"] == "Nueva Cámara"
