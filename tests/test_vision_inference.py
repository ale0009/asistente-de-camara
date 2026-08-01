import unittest
from unittest.mock import MagicMock, patch
import numpy as np

from core.ollama_bridge import OllamaBridge
from core.command_dispatcher import CommandDispatcher

class TestVisionInference(unittest.TestCase):
    @patch("requests.post")
    def test_query_vision_encoding_and_request(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": "Veo a una persona frente a la cámara."}
        mock_post.return_value = mock_resp

        ollama = OllamaBridge()
        dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)

        reply = ollama.query_vision("Describe la imagen", dummy_frame, model="moondream")
        self.assertEqual(reply, "Veo a una persona frente a la cámara.")
        
        mock_post.assert_called_once()
        kwargs = mock_post.call_args[1]
        payload = kwargs["json"]
        self.assertEqual(payload["model"], "moondream")
        self.assertEqual(payload["prompt"], "Describe la imagen")
        self.assertTrue(len(payload["images"]) == 1)
        self.assertTrue(isinstance(payload["images"][0], str))

    def test_dispatcher_vision_command(self):
        mock_osc = MagicMock()
        mock_camera = MagicMock()
        mock_ollama = MagicMock()

        mock_camera.current_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_ollama.query_vision.return_value = "Veo una taza roja sobre el escritorio."

        dispatcher = CommandDispatcher(
            osc_controller=mock_osc,
            camera_controller=mock_camera,
            ollama_bridge=mock_ollama
        )

        res = dispatcher.process_command("qué ves en la cámara")
        self.assertEqual(res, "Veo una taza roja sobre el escritorio.")
        mock_ollama.query_vision.assert_called_once()

if __name__ == "__main__":
    unittest.main()
