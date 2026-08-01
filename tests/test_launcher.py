import unittest
from unittest.mock import patch, MagicMock
import start_nova_agent

class TestUnifiedLauncher(unittest.TestCase):
    @patch("subprocess.Popen")
    def test_start_agent_service(self, mock_popen):
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc
        proc = start_nova_agent.start_agent_service()
        self.assertEqual(proc, mock_proc)
        mock_popen.assert_called_once()

    @patch("watchers.file_watcher.FileWatcherService.start")
    def test_start_file_watcher(self, mock_start):
        watcher = start_nova_agent.start_file_watcher()
        mock_start.assert_called_once()
        watcher.stop()

if __name__ == "__main__":
    unittest.main()
