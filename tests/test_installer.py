import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import setup_installer

class TestInstaller(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_ensure_config_creates_file(self):
        config_path = os.path.join(self.temp_dir.name, "config.yaml")
        with patch.object(setup_installer, "CONFIG_PATH", config_path):
            setup_installer.ensure_config()
            self.assertTrue(os.path.exists(config_path))

    def test_ensure_vbs_launcher_creates_file(self):
        vbs_path = os.path.join(self.temp_dir.name, "test_launcher.vbs")
        with patch.object(setup_installer, "VBS_LAUNCHER_PATH", vbs_path):
            setup_installer.ensure_vbs_launcher()
            self.assertTrue(os.path.exists(vbs_path))

    @patch("agent_service.audit_logger.AgentAuditLogger")
    def test_ensure_sqlite_db(self, mock_audit):
        setup_installer.ensure_sqlite_db()
        mock_audit.assert_called_once()

if __name__ == "__main__":
    unittest.main()
