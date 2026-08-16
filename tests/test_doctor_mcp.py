import tempfile
import pytest
from unittest.mock import MagicMock
from mcp_servers.doctor_mcp import DoctorMCPServer

class TestDoctorMCPServer:
    def setup_method(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self.temp_dir = self._temp_dir.name
        self.mock_ollama = MagicMock()
        self.mock_camera = MagicMock()
        self.mock_osc = MagicMock()
        self.server = DoctorMCPServer(
            ollama_bridge=self.mock_ollama,
            camera_controller=self.mock_camera,
            osc_controller=self.mock_osc,
            vault_path=str(self.temp_dir)
        )

    def teardown_method(self):
        self._temp_dir.cleanup()

    def test_get_tools_schema(self):
        schemas = self.server.get_tools_schema()
        names = [s["name"] for s in schemas]
        assert "doctor_health_check" in names
        assert "doctor_repair_connections" in names

    def test_health_check_healthy(self):
        self.mock_ollama.check_connection.return_value = True
        self.mock_ollama.get_models.return_value = ["qwen3:8b", "moondream:latest"]
        self.mock_ollama.resolve_model.return_value = "qwen3:8b"

        res = self.server.execute_tool("doctor_health_check", {})
        assert res["success"] is True
        assert res["overall_status"] == "OPERATIONAL"
        assert res["diagnostics"]["ollama"]["status"] == "healthy"
        assert res["diagnostics"]["obsidian_vault"]["status"] == "healthy"

    def test_health_check_degraded_when_ollama_offline(self):
        self.mock_ollama.check_connection.return_value = False
        res = self.server.execute_tool("doctor_health_check", {})
        assert res["success"] is True
        assert res["overall_status"] == "DEGRADED"
        assert res["diagnostics"]["ollama"]["status"] == "unreachable"

    def test_repair_connections(self):
        self.mock_ollama.get_models.return_value = ["qwen3:8b"]
        res = self.server.execute_tool("doctor_repair_connections", {})
        assert res["success"] is True
        assert len(res["actions_taken"]) >= 1
