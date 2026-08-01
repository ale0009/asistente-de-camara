import os
import unittest
from unittest.mock import MagicMock

from agent_service.agent_loop import AgentLoop
from agent_service.mcp_client import MCPClientManager
from agent_service.audit_logger import AgentAuditLogger
from mcp_servers.vault_mcp import OverwriteError

class TestAgentLoop(unittest.TestCase):
    def setUp(self):
        self.mock_ollama = MagicMock()
        self.mock_router = MagicMock()
        self.mock_mcp = MagicMock()
        self.mock_audit = MagicMock()

        self.mock_mcp.get_all_tools_schema.return_value = [
            {"name": "vault_read_note", "description": "Read note", "parameters": {}}
        ]

        self.agent_loop = AgentLoop(
            mcp_manager=self.mock_mcp,
            intent_router=self.mock_router,
            audit_logger=self.mock_audit,
            ollama_bridge=self.mock_ollama
        )

    def test_process_interaction_direct_answer(self):
        self.mock_router.route.return_value = {
            "category": "direct_answer",
            "tool_name": None,
            "arguments": None
        }
        self.mock_ollama.query.return_value = "Hola, soy NOVA."

        res = self.agent_loop.process_interaction("Hola", source_channel="test")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["category"], "direct_answer")
        self.assertEqual(res["response_text"], "Hola, soy NOVA.")
        self.mock_audit.log_interaction.assert_called_once()

    def test_process_interaction_mcp_tool_call_success(self):
        self.mock_router.route.return_value = {
            "category": "mcp_tool_call",
            "tool_name": "vault_read_note",
            "arguments": {"relative_path": "test.md"}
        }
        self.mock_mcp.execute_tool.return_value = {"success": True, "content": "Contenido nota"}

        res = self.agent_loop.process_interaction("Lee la nota test.md")
        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["category"], "mcp_tool_call")
        self.assertIn("ejecutada con éxito", res["response_text"])

    def test_process_interaction_mcp_tool_call_protected_overwrite(self):
        self.mock_router.route.return_value = {
            "category": "mcp_tool_call",
            "tool_name": "vault_write_note",
            "arguments": {"relative_path": "Charter.md", "content": "Modificación"}
        }
        self.mock_mcp.execute_tool.side_effect = OverwriteError("ACCESO DENEGADO (OverwriteError)")

        res = self.agent_loop.process_interaction("Sobreescribe el Charter.md")
        self.assertEqual(res["status"], "PROTECTED_BLOCKED")
        self.assertIn("OverwriteError", res["response_text"])

    def test_process_interaction_stream_direct_answer(self):
        self.mock_router.route.return_value = {
            "category": "direct_answer",
            "tool_name": None,
            "arguments": None
        }
        self.mock_ollama.query_stream.return_value = ["Hola, ", "soy ", "NOVA. ", "¡Bienvenido!"]

        chunks = list(self.agent_loop.process_interaction_stream("Hola", source_channel="test_stream"))
        
        # Debe haber eventos de oraciones + evento final de completion
        self.assertTrue(len(chunks) >= 2)
        sentence_events = [c for c in chunks if c.get("type") == "sentence_chunk"]
        completion_events = [c for c in chunks if c.get("type") == "completion"]

        self.assertTrue(len(sentence_events) > 0)
        self.assertEqual(len(completion_events), 1)
        self.assertEqual(completion_events[0]["status"], "SUCCESS")


if __name__ == "__main__":
    unittest.main()

