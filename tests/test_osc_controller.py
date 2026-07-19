import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.osc_controller import OSCController


def make_controller():
    with patch("core.osc_controller.udp_client.SimpleUDPClient") as mock_client_cls:
        controller = OSCController()
        return controller, mock_client_cls.return_value


def test_track_human_sends_ai_lock_on():
    controller, client = make_controller()
    controller.track_human()
    client.send_message.assert_called_once_with("/OBSBOT/WebCam/Tiny/ToggleAILock", 1)


def test_stop_tracking_sends_ai_lock_off():
    controller, client = make_controller()
    controller.stop_tracking()
    client.send_message.assert_called_once_with("/OBSBOT/WebCam/Tiny/ToggleAILock", 0)


def test_wake_and_sleep_use_same_address_opposite_values():
    controller, client = make_controller()
    controller.wake_camera()
    controller.sleep_camera()
    assert client.send_message.call_args_list[0].args == ("/OBSBOT/WebCam/General/WakeSleep", 1)
    assert client.send_message.call_args_list[1].args == ("/OBSBOT/WebCam/General/WakeSleep", 0)


def test_set_zoom_casts_to_int_within_range():
    controller, client = make_controller()
    controller.set_zoom(60.0)
    client.send_message.assert_called_once_with("/OBSBOT/WebCam/General/SetZoom", 60)


def test_gimbal_directions_use_dedicated_addresses():
    controller, client = make_controller()
    controller.look_left()
    controller.look_right()
    controller.look_up()
    controller.look_down()
    addresses = [call.args[0] for call in client.send_message.call_args_list]
    assert addresses == [
        "/OBSBOT/WebCam/General/SetGimbalLeft",
        "/OBSBOT/WebCam/General/SetGimbalRight",
        "/OBSBOT/WebCam/General/SetGimbalUp",
        "/OBSBOT/WebCam/General/SetGimbalDown",
    ]


def test_send_message_swallows_network_errors():
    controller, client = make_controller()
    client.send_message.side_effect = OSError("boom")
    controller.track_human()  # no debe lanzar excepción


def test_osc_controller_feedback_handlers():
    controller, client = make_controller()
    
    events = []
    def on_update(tracking, zoom):
        events.append((tracking, zoom))
        
    controller.on_status_updated = on_update
    
    controller._handle_tracking_feedback("/OBSBOT/WebCam/Tiny/AiTrackingInfo", 1)
    controller._handle_zoom_feedback("/OBSBOT/WebCam/General/ZoomInfo", 50.0)
    
    assert controller.current_tracking_state == "Humano"
    assert controller.current_zoom_level == 2.5
    assert len(events) == 2
    assert events[0] == ("Humano", 1.0)
    assert events[1] == ("Humano", 2.5)
    controller.stop()
