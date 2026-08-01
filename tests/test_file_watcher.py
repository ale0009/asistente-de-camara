import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from watchers.file_watcher import FileWatcherService

class TestFileWatcher(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.watcher = FileWatcherService(
            watch_paths=[self.temp_dir.name],
            agent_url="http://127.0.0.1:8000/v1/agent/interact"
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("urllib.request.urlopen")
    def test_file_watcher_detects_modification(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"status": "SUCCESS"}'
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        # Crear archivo inicial
        file_path = os.path.join(self.temp_dir.name, "test.txt")
        with open(file_path, "w") as f:
            f.write("inicial")

        # Tomar snapshot inicial
        self.watcher.snapshot = self.watcher._take_snapshot()

        # Modificar archivo
        import time
        time.sleep(0.1)
        with open(file_path, "w") as f:
            f.write("modificado")

        # Ejecutar 1 iteración manual de comparación
        current = self.watcher._take_snapshot()
        for filepath, mtime in current.items():
            if filepath not in self.watcher.snapshot or self.watcher.snapshot[filepath] != mtime:
                self.watcher._notify_agent(filepath)

        mock_urlopen.assert_called_once()

if __name__ == "__main__":
    unittest.main()
