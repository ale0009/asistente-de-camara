import os
import sys
from unittest.mock import Mock, patch

import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.command_dispatcher import CommandDispatcher


def make_dispatcher(tmp_path, osc=None, system=None, ollama=None, apps=None):
    apps_path = tmp_path / "apps.yaml"
    apps_path.write_text(
        yaml.safe_dump({"apps": apps or {}}), encoding="utf-8"
    )
    config_path = tmp_path / "config.yaml"
    config_path.write_text("{}", encoding="utf-8")

    return CommandDispatcher(
        osc_controller=osc or Mock(),
        system_controller=system or Mock(),
        ollama_bridge=ollama,
        intent_router=None,
        config_path=str(config_path),
        apps_path=str(apps_path),
    )


def test_camera_command_matches_and_executes(tmp_path):
    osc = Mock()
    dispatcher = make_dispatcher(tmp_path, osc=osc)

    reply = dispatcher.process_command("sígueme")

    osc.track_human.assert_called_once()
    assert "sígueme" in reply


def test_camera_command_matches_as_substring(tmp_path):
    osc = Mock()
    dispatcher = make_dispatcher(tmp_path, osc=osc)

    dispatcher.process_command("nova, por favor sígueme ahora")

    osc.track_human.assert_called_once()


def test_system_command_executes_and_returns_action_result(tmp_path):
    system = Mock()
    system.change_volume.return_value = "Volumen subido"
    dispatcher = make_dispatcher(tmp_path, system=system)

    reply = dispatcher.process_command("sube el volumen")

    system.change_volume.assert_called_once_with(True)
    assert reply == "Volumen subido"


def test_open_app_launches_existing_executable(tmp_path):
    fake_exe = tmp_path / "fake_blender.exe"
    fake_exe.write_text("", encoding="utf-8")
    dispatcher = make_dispatcher(tmp_path, apps={"blender": [str(fake_exe)]})

    with patch("subprocess.Popen") as mock_popen:
        reply = dispatcher._open_app("blender")

    mock_popen.assert_called_once()
    assert "blender" in reply.lower()


def test_open_app_unknown_app(tmp_path):
    dispatcher = make_dispatcher(tmp_path, apps={"blender": ["C:\\nope.exe"]})

    reply = dispatcher._open_app("una app que no existe")

    assert "no tengo registrada" in reply.lower()


def test_direct_ollama_query_includes_identity(tmp_path):
    ollama = Mock()
    ollama.query_stream.return_value = ["Respuesta", " breve."]
    dispatcher = make_dispatcher(tmp_path, ollama=ollama)

    reply = dispatcher.process_command("pregúntale a ollama qué hora es")
    sentences = list(reply)

    assert sentences == ["Respuesta breve."]
    sent_prompt = ollama.query_stream.call_args[0][0]
    assert "NOVA" in sent_prompt
    assert "qué hora es" in sent_prompt


def test_stream_sentences_segmentation(tmp_path):
    dispatcher = make_dispatcher(tmp_path)
    tokens = ["Hola", " mundo", ".", " ¿Cómo ", "estás", "?", " Bien", "!\nTodo", " ok"]
    sentences = list(dispatcher._stream_sentences(tokens))
    assert sentences == ["Hola mundo.", "¿Cómo estás?", "Bien!", "Todo ok"]


def test_falls_back_to_intent_router_for_free_form_text(tmp_path):
    router = Mock()
    router.route.return_value = "Ruteado por intención"
    dispatcher = make_dispatcher(tmp_path)
    dispatcher.intent_router = router

    reply = dispatcher.process_command("cuéntame un chiste")

    router.route.assert_called_once()
    assert reply == "Ruteado por intención"


def test_camera_preset_commands(tmp_path):
    osc = Mock()
    dispatcher = make_dispatcher(tmp_path, osc=osc)

    reply = dispatcher.process_command("posición 1")

    osc.trigger_preset.assert_called_once_with(1)
    assert "posición 1" in reply


def test_scene_modes_commands(tmp_path):
    osc = Mock()
    system = Mock()
    dispatcher = make_dispatcher(tmp_path, osc=osc, system=system)

    reply_pres = dispatcher.process_command("modo presentación")
    osc.wake_camera.assert_called_once()
    osc.track_human.assert_called_once()
    osc.set_zoom.assert_called_once_with(0.0)
    assert "Modo Presentación" in reply_pres

    reply_work = dispatcher.process_command("modo trabajo")
    osc.stop_tracking.assert_called_once()
    osc.gimbal_reset.assert_called_once()
    assert "Modo Trabajo" in reply_work

    reply_rest = dispatcher.process_command("modo descanso")
    osc.sleep_camera.assert_called_once()
    system.mute_volume.assert_called_once()
    assert "Modo Descanso" in reply_rest


def test_obs_commands(tmp_path):
    dispatcher = make_dispatcher(tmp_path)
    reply = dispatcher.process_command("inicia grabación")
    assert "OBS Studio" in reply
