import tempfile
import pytest
from unittest.mock import MagicMock
from mcp_servers.agenda_mcp import AgendaMCPServer

class TestAgendaMCPServer:
    def setup_method(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self.temp_dir = self._temp_dir.name
        self.mock_osc = MagicMock()
        self.mock_system = MagicMock()
        self.server = AgendaMCPServer(
            vault_path=str(self.temp_dir),
            nova_folder="NOVA",
            osc_controller=self.mock_osc,
            system_controller=self.mock_system
        )

    def teardown_method(self):
        self._temp_dir.cleanup()

    def test_get_tools_schema(self):
        schemas = self.server.get_tools_schema()
        names = [s["name"] for s in schemas]
        assert "agenda_get_today_schedule" in names
        assert "agenda_add_task" in names
        assert "agenda_lunch_break" in names
        assert "agenda_start_timer" in names

    def test_add_task_and_get_schedule(self):
        res_add = self.server.execute_tool("agenda_add_task", {
            "task": "Revisar arquitectura NOVA",
            "time_str": "15:30"
        })
        assert res_add["success"] is True
        assert "Revisar arquitectura NOVA" in res_add["message"]

        res_sched = self.server.execute_tool("agenda_get_today_schedule", {})
        assert res_sched["success"] is True
        assert res_sched["tasks_count"] >= 1

    def test_lunch_break(self):
        res = self.server.execute_tool("agenda_lunch_break", {"duration_minutes": 45})
        assert res["success"] is True
        assert res["status"] == "LUNCH_ACTIVE"
        assert res["duration_minutes"] == 45
        self.mock_osc.sleep_camera.assert_called_once()
        self.mock_system.mute_volume.assert_called_once()

    def test_start_timer(self):
        res = self.server.execute_tool("agenda_start_timer", {"minutes": 25, "label": "Pomodoro"})
        assert res["success"] is True
        assert res["timer"]["duration_minutes"] == 25
        assert res["timer"]["label"] == "Pomodoro"

    def test_start_timer_invalid_minutes(self):
        res = self.server.execute_tool("agenda_start_timer", {"minutes": 0})
        assert res["success"] is False
