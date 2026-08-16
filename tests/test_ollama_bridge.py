import os
import sys
from unittest.mock import Mock, patch

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ollama_bridge import OllamaBridge


def test_query_sends_keep_alive_thinking_off_and_num_predict():
    bridge = OllamaBridge()
    fake_response = Mock(status_code=200, json=lambda: {"response": "hola"})

    with patch("core.ollama_bridge.requests.post", return_value=fake_response) as mock_post:
        reply = bridge.query("hola")

    assert reply == "hola"
    payload = mock_post.call_args.kwargs["json"]
    assert payload["keep_alive"] == "10m"
    assert payload["think"] is False
    assert payload["options"]["num_predict"] == 220


def test_query_json_mode_sets_format_field():
    bridge = OllamaBridge()
    fake_response = Mock(status_code=200, json=lambda: {"response": "{}"})

    with patch("core.ollama_bridge.requests.post", return_value=fake_response) as mock_post:
        bridge.query("clasifica esto", json_mode=True)

    assert mock_post.call_args.kwargs["json"]["format"] == "json"


def test_query_handles_model_not_found():
    bridge = OllamaBridge()
    fake_response = Mock(status_code=404)

    with patch("core.ollama_bridge.requests.post", return_value=fake_response):
        reply = bridge.query("hola", model="modelo-inexistente")

    assert "modelo-inexistente" in reply


def test_query_handles_timeout():
    bridge = OllamaBridge()

    with patch("core.ollama_bridge.requests.post", side_effect=requests.exceptions.Timeout):
        reply = bridge.query("hola")

    assert "tardó demasiado" in reply


def test_query_handles_connection_error():
    bridge = OllamaBridge()

    with patch("core.ollama_bridge.requests.post", side_effect=requests.exceptions.ConnectionError):
        reply = bridge.query("hola")

    assert "no me pude conectar" in reply.lower()


def test_query_stream_success():
    bridge = OllamaBridge()
    fake_lines = [
        b'{"response": "Hola"}',
        b'{"response": ", "}',
        b'{"response": "mundo."}'
    ]
    fake_response = Mock(status_code=200)
    fake_response.iter_lines.return_value = fake_lines

    with patch("core.ollama_bridge.requests.post", return_value=fake_response) as mock_post:
        tokens = list(bridge.query_stream("hola"))

    assert tokens == ["Hola", ", ", "mundo."]
    payload = mock_post.call_args.kwargs["json"]
    assert payload["stream"] is True
    assert payload["keep_alive"] == "10m"
    assert payload["think"] is False


def test_resolve_model_finds_exact_match():
    bridge = OllamaBridge()
    with patch.object(bridge, "get_models", return_value=["qwen3:8b", "moondream:latest"]):
        resolved = bridge.resolve_model("qwen3:8b")
        assert resolved == "qwen3:8b"


def test_resolve_model_falls_back_when_missing():
    bridge = OllamaBridge()
    bridge.fallback_models = ["qwen3:4b", "hermes3:8b"]
    with patch.object(bridge, "get_models", return_value=["qwen3:4b", "moondream:latest"]):
        resolved = bridge.resolve_model("modelo_no_instalado")
        assert resolved == "qwen3:4b"


def test_resolve_model_picks_first_available_as_last_resort():
    bridge = OllamaBridge()
    bridge.fallback_models = ["hermes3:8b"]
    with patch.object(bridge, "get_models", return_value=["gemma4:latest"]):
        resolved = bridge.resolve_model("modelo_no_instalado")
        assert resolved == "gemma4:latest"

