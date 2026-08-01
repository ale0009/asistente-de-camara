# -*- coding: utf-8 -*-
import os
import sys
from unittest.mock import Mock, patch

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
    # Caso 1: Sin dispatcher (ej: standalone / fallback simple)
    router, ollama, files, dispatcher = make_router('{"action": "answer"}')
    router.dispatcher = None
    ollama.query.side_effect = [
        '{"action": "answer"}', # primera llamada para clasificar
        "Soy NOVA, tu asistente local" # segunda llamada para la respuesta
    ]

    reply = router.route("¿qué eres?")
    assert reply == "Soy NOVA, tu asistente local"
    
    # Caso 2: Con dispatcher (flujo real con streaming de voz)
    router, ollama, files, dispatcher = make_router('{"action": "answer"}')
    ollama.query.return_value = '{"action": "answer"}'
    ollama.query_stream.return_value = ["Soy ", "NOVA"]
    dispatcher._stream_sentences.side_effect = lambda tokens: ["Soy NOVA"]

    reply_stream = router.route("¿qué eres?")
    
    # Consumir el generador
    if not isinstance(reply_stream, str):
        reply_stream = " ".join(list(reply_stream))
        
    assert reply_stream == "Soy NOVA"
    ollama.query_stream.assert_called_once()



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


def test_route_read_document():
    router, ollama, files, dispatcher = make_router('{"action": "read_document", "target": "reporte_addons", "question": "¿qué dice?"}')
    files.read_document = Mock(return_value="--- Documento 'reporte_addons.md' ---\nAddons instalados")
    
    # Mockear query_stream para retornar un iterador de tokens
    ollama.query_stream.return_value = ["En el reporte ", "dice que hay ", "addons instalados."]
    
    # Mockear _stream_sentences en el dispatcher
    dispatcher._stream_sentences.side_effect = lambda tokens: ["En el reporte dice que hay addons instalados."]

    reply = router.route("qué dice mi reporte de addons")

    # Consumir el generador/iterable si no es un string
    if not isinstance(reply, str):
        reply = " ".join(list(reply))

    files.read_document.assert_called_once_with("reporte_addons")
    assert "addons instalados" in reply.lower()


@patch('core.intent_router.DDGS')
def test_research_action_runs_agentic_workflow(mock_ddgs_class, tmp_path):
    # Setup DDGS mock
    mock_ddgs = Mock()
    mock_ddgs.text.return_value = [
        {"title": "Avance Fusión", "href": "http://example.com/1", "body": "Record de energia en fusion nuclear"},
        {"title": "Reactor Nuclear 2026", "href": "http://example.com/2", "body": "Nuevos reactores tokamak"}
    ]
    # Configure mock context manager
    mock_ddgs_class.return_value.__enter__.return_value = mock_ddgs

    router, ollama, files, dispatcher = make_router('{"action": "research", "topic": "fusion nuclear"}')
    files.vault_path = str(tmp_path)
    
    ollama.query.side_effect = [
        '{"action": "research", "topic": "fusion nuclear"}', # clasificacion
        "termino 1\ntermino 2", # sub-queries
        "# Reporte de Fusión Nuclear\nAvances importantes..." # reporte markdown
    ]
    ollama.query_stream.return_value = ["Investigación terminada."]
    dispatcher._stream_sentences.side_effect = lambda tokens: ["Investigación terminada."]

    reply = router.route("investiga sobre fusion nuclear")

    # Consumir el generador
    if not isinstance(reply, str):
        reply_list = list(reply)
        reply = " ".join(reply_list)

    assert "investigación" in reply.lower()
    # Verificar que se creó el reporte en el vault ficticio
    report_file = tmp_path / "NOVA" / "Investigaciones" / "Investigacion - fusion nuclear.md"
    assert report_file.exists()
    assert "Avances importantes" in report_file.read_text(encoding="utf-8")
