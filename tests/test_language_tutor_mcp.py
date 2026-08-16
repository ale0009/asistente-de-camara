import pytest
from unittest.mock import MagicMock
from mcp_servers.language_tutor_mcp import LanguageTutorMCPServer

class TestLanguageTutorMCPServer:
    def setup_method(self):
        self.mock_ollama = MagicMock()
        self.mock_voice = MagicMock()
        self.mock_voice.tts_voice = "es-CO-SalomeNeural"
        self.server = LanguageTutorMCPServer(
            ollama_bridge=self.mock_ollama,
            voice_engine=self.mock_voice
        )

    def test_get_tools_schema(self):
        schemas = self.server.get_tools_schema()
        names = [s["name"] for s in schemas]
        assert "language_start_session" in names
        assert "language_get_status" in names
        assert "language_end_session" in names
        assert "language_converse" in names

    def test_start_session_english(self):
        self.mock_ollama.query.return_value = "Hello! I am NOVA, your English tutor. What is your favorite hobby?"
        res = self.server.execute_tool("language_start_session", {
            "language": "en",
            "topic": "hobbies",
            "level": "intermediate"
        })
        assert res["success"] is True
        assert res["session"]["language"] == "en"
        assert res["session"]["voice"] == "en-US-JennyNeural"
        assert self.mock_voice.tts_voice == "en-US-JennyNeural"

    def test_start_session_unsupported_language(self):
        res = self.server.execute_tool("language_start_session", {"language": "de"})
        assert res["success"] is False
        assert "no soportado" in res["error"]

    def test_converse_and_get_status(self):
        self.mock_ollama.query.return_value = "Bonjour! Comment vas-tu?"
        self.server.execute_tool("language_start_session", {"language": "fr", "topic": "voyages"})

        status_res = self.server.execute_tool("language_get_status", {})
        assert status_res["success"] is True
        assert status_res["active"] is True
        assert status_res["session"]["language"] == "fr"

        conv_res = self.server.execute_tool("language_converse", {"user_message": "Je vais bien, merci!"})
        assert conv_res["success"] is True
        assert conv_res["language"] == "fr"

    def test_end_session(self):
        self.server.execute_tool("language_start_session", {"language": "ja", "topic": "anime"})
        assert self.server.active_session is not None

        res_end = self.server.execute_tool("language_end_session", {})
        assert res_end["success"] is True
        assert self.server.active_session is None
        assert self.mock_voice.tts_voice == "es-CO-SalomeNeural"

    def test_start_session_french_project_context(self):
        self.mock_ollama.query.return_value = "Bonjour! Parlons de votre addon Blender."
        res = self.server.execute_tool("language_start_session", {
            "language": "fr",
            "topic": "Addon Blender Asset Extractor",
            "project_context": "Projet d'extraction d'assets 3D en Python.",
            "level": "advanced"
        })
        assert res["success"] is True
        assert res["session"]["language"] == "fr"
        assert res["session"]["voice"] == "fr-FR-DeniseNeural"
        assert "Projet d'extraction" in res["session"]["system_prompt"]
        assert self.mock_voice.tts_voice == "fr-FR-DeniseNeural"

    def test_start_session_chinese_project_context(self):
        self.mock_ollama.query.return_value = "你好！我们来讨论一下你的智能相机项目。"
        res = self.server.execute_tool("language_start_session", {
            "language": "zh",
            "topic": "智能相机系统",
            "project_context": "基于MediaPipe手势与OSC控制的智能相机。",
            "level": "intermediate"
        })
        assert res["success"] is True
        assert res["session"]["language"] == "zh"
        assert res["session"]["voice"] == "zh-CN-XiaoxiaoNeural"
        assert "MediaPipe" in res["session"]["system_prompt"]
        assert self.mock_voice.tts_voice == "zh-CN-XiaoxiaoNeural"

