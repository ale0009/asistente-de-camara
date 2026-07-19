import os
import sys
from unittest.mock import Mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.intent_router import IntentRouter


def make_router(ollama_reply: str):
    ollama = Mock()
    ollama.query.return_value = ollama_reply
    files = Mock()
    router = IntentRouter(ollama, files)
    dispatcher = Mock()
    dispatcher.camera_commands = {"sígueme": Mock(return_value=None)}
    dispatcher.system_commands = {"sube el volumen": Mock(return_value="Volumen subido")}
    dispatcher._open_app = Mock(return_value="Abriendo blender")
    router.dispatcher = dispatcher
    return router, ollama, files, dispatcher


def test_search_files_action_calls_file_tools():
    router, ollama, files, _ = make_router('{"action": "search_files", "query": "informe"}')
    files.search_files.return_value = ["C:/docs/informe.pdf"]

    reply = router.route("busca el informe")

    files.search_files.assert_called_once_with("informe")
    assert "informe.pdf" in reply


def test_write_note_action_calls_file_tools():
    router, ollama, files, _ = make_router(
        '{"action": "write_note", "title": "Idea", "content": "comprar pan"}'
    )
    files.write_note.return_value = "D:/vault/NOVA/Notas/Idea.md"

    reply = router.route("anota que debo comprar pan")

    files.write_note.assert_called_once_with("Idea", "comprar pan")
    assert "Idea.md" in reply


def test_run_command_executes_known_camera_command_by_paraphrase():
    router, ollama, files, dispatcher = make_router('{"action": "run_command", "command": "sígueme"}')

    router.route("podrías empezar a seguirme por favor")

    dispatcher.camera_commands["sígueme"].assert_called_once()


def test_run_command_rejects_unknown_command():
    router, ollama, files, dispatcher = make_router(
        '{"action": "run_command", "command": "vuela por la habitación"}'
    )

    reply = router.route("haz algo raro")

    assert "no pude identificar" in reply.lower()


def test_open_app_action_delegates_to_dispatcher():
    router, ollama, files, dispatcher = make_router('{"action": "open_app", "app_name": "blender"}')

    reply = router.route("abre por favor el programa de modelado 3d")

    dispatcher._open_app.assert_called_once_with("blender")
    assert reply == "Abriendo blender"


def test_answer_action_returns_text():
    router, ollama, files, _ = make_router('{"action": "answer", "text": "Soy NOVA"}')

    reply = router.route("¿qué eres?")

    assert reply == "Soy NOVA"


def test_invalid_json_falls_back_to_raw_text():
    router, ollama, files, _ = make_router("esto no es json")

    reply = router.route("algo raro")

    assert reply == "esto no es json"


def test_known_commands_are_interpolated_into_prompt():
    router, ollama, files, dispatcher = make_router('{"action": "answer", "text": "ok"}')

    router.route("hola")

    sent_prompt = ollama.query.call_args[0][0]
    assert "sígueme" in sent_prompt
    assert "sube el volumen" in sent_prompt
