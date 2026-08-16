import pytest
from unittest.mock import MagicMock
from mcp_servers.camera_mcp import CameraMCPServer

class TestCameraMCPServer:
    def setup_method(self):
        self.mock_osc = MagicMock()
        self.mock_camera = MagicMock()
        self.mock_ollama = MagicMock()
        self.server = CameraMCPServer(
            osc_controller=self.mock_osc,
            camera_controller=self.mock_camera,
            ollama_bridge=self.mock_ollama
        )

    def test_get_tools_schema(self):
        schemas = self.server.get_tools_schema()
        tool_names = [s["name"] for s in schemas]
        assert "camera_wake_sleep" in tool_names
        assert "camera_set_tracking" in tool_names
        assert "camera_set_zoom" in tool_names
        assert "camera_move_gimbal" in tool_names
        assert "camera_trigger_preset" in tool_names
        assert "camera_set_scene_mode" in tool_names
        assert "camera_describe_scene" in tool_names

    def test_execute_camera_wake_sleep(self):
        res_wake = self.server.execute_tool("camera_wake_sleep", {"action": "wake"})
        assert res_wake["success"] is True
        self.mock_osc.wake_camera.assert_called_once()

        res_sleep = self.server.execute_tool("camera_wake_sleep", {"action": "sleep"})
        assert res_sleep["success"] is True
        self.mock_osc.sleep_camera.assert_called_once()

    def test_execute_camera_set_tracking(self):
        res_on = self.server.execute_tool("camera_set_tracking", {"enabled": True})
        assert res_on["success"] is True
        self.mock_osc.track_human.assert_called_once()

        res_off = self.server.execute_tool("camera_set_tracking", {"enabled": False})
        assert res_off["success"] is True
        self.mock_osc.stop_tracking.assert_called_once()

    def test_execute_camera_set_zoom(self):
        res = self.server.execute_tool("camera_set_zoom", {"level": 75.5})
        assert res["success"] is True
        assert res["zoom_level"] == 75.5
        self.mock_osc.set_zoom.assert_called_with(75.5)

    def test_execute_camera_move_gimbal(self):
        self.server.execute_tool("camera_move_gimbal", {"direction": "left"})
        self.mock_osc.look_left.assert_called_once()

        self.server.execute_tool("camera_move_gimbal", {"direction": "right"})
        self.mock_osc.look_right.assert_called_once()

        self.server.execute_tool("camera_move_gimbal", {"direction": "up"})
        self.mock_osc.look_up.assert_called_once()

        self.server.execute_tool("camera_move_gimbal", {"direction": "down"})
        self.mock_osc.look_down.assert_called_once()

        self.server.execute_tool("camera_move_gimbal", {"direction": "reset"})
        self.mock_osc.gimbal_reset.assert_called_once()

    def test_execute_camera_trigger_preset(self):
        res = self.server.execute_tool("camera_trigger_preset", {"preset_number": 2})
        assert res["success"] is True
        assert res["preset"] == 2
        self.mock_osc.trigger_preset.assert_called_with(2)

    def test_execute_camera_set_scene_mode(self):
        res_pres = self.server.execute_tool("camera_set_scene_mode", {"mode": "presentation"})
        assert res_pres["success"] is True
        self.mock_osc.wake_camera.assert_called()
        self.mock_osc.track_human.assert_called()

        res_work = self.server.execute_tool("camera_set_scene_mode", {"mode": "work"})
        assert res_work["success"] is True
        self.mock_osc.stop_tracking.assert_called()
        self.mock_osc.gimbal_reset.assert_called()

        res_rest = self.server.execute_tool("camera_set_scene_mode", {"mode": "rest"})
        assert res_rest["success"] is True
        self.mock_osc.sleep_camera.assert_called()

    def test_execute_camera_describe_scene_with_frame(self):
        import numpy as np
        self.mock_camera.current_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        self.mock_ollama.query_vision.return_value = "Veo una persona sentada frente al computador."

        res = self.server.execute_tool("camera_describe_scene", {"question": "¿Qué ves?"})
        assert res["success"] is True
        assert "persona" in res["description"]
        self.mock_ollama.query_vision.assert_called_once()

    def test_execute_camera_describe_scene_no_frame(self):
        self.mock_camera.current_frame = None
        res = self.server.execute_tool("camera_describe_scene", {"question": "¿Qué ves?"})
        assert res["success"] is False
        assert "no está capturando" in res["error"]

    def test_execute_unknown_tool(self):
        res = self.server.execute_tool("unknown_camera_tool", {})
        assert res["success"] is False
        assert "desconocida" in res["error"]
