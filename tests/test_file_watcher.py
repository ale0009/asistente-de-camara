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

    @patch("urllib.request.urlopen")
    def test_watcher_ignores_logs_and_database_files(self, mock_urlopen):
        logs_dir = os.path.join(self.temp_dir.name, "logs")
        os.makedirs(logs_dir)
        with open(os.path.join(logs_dir, "agent_audit.db"), "w") as f:
            f.write("evento interno")
        with open(os.path.join(self.temp_dir.name, "normal.md"), "w") as f:
            f.write("nota")

        snapshot = self.watcher._take_snapshot()

        self.assertEqual(len(snapshot), 1)
        self.assertTrue(next(iter(snapshot)).endswith("normal.md"))
        mock_urlopen.assert_not_called()

    @patch("urllib.request.urlopen")
    def test_watcher_applies_cooldown_per_file(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        path = os.path.join(self.temp_dir.name, "normal.md")
        self.watcher._notify_agent(path)
        self.watcher._notify_agent(path)

        mock_urlopen.assert_called_once()

if __name__ == "__main__":
    unittest.main()
