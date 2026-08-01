import json
import unittest
from unittest.mock import MagicMock, patch
from voice_service.voice_client import VoiceServiceChannel

class TestVoiceServiceChannel(unittest.TestCase):
    @patch("voice_service.voice_client.VoiceEngine")
    def test_voice_service_init(self, mock_voice_engine):
        channel = VoiceServiceChannel(agent_url="http://127.0.0.1:8000/v1/agent/interact")
        self.assertEqual(channel.agent_url, "http://127.0.0.1:8000/v1/agent/interact")
        mock_voice_engine.assert_called_once()

    @patch("voice_service.voice_client.VoiceEngine")
    @patch("urllib.request.urlopen")
    def test_command_recognized_sends_payload(self, mock_urlopen, mock_voice_engine):
        mock_response = MagicMock()
        payload_data = json.dumps({"response_text": "Respuesta agentica ok"}).encode("utf-8")
        mock_response.read.return_value = payload_data
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        channel = VoiceServiceChannel()
        channel._on_command_recognized("abre blender")

        import time
        time.sleep(0.2)

        mock_urlopen.assert_called_once()
        channel.engine.speak.assert_called_with("Respuesta agentica ok")

if __name__ == "__main__":
    unittest.main()
