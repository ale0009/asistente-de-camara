import unittest
from unittest.mock import MagicMock, patch

from mcp_servers.n8n_mcp import N8NAutomationMCPServer
from mcp_servers.git_mcp import GitMCPServer
from mcp_servers.web_search_mcp import WebSearchMCPServer

class TestExtendedMCPServers(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_n8n_trigger_workflow_success(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"success": true, "id": "wf_123"}'
        mock_resp.status = 200
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        n8n_server = N8NAutomationMCPServer()
        res = n8n_server.execute_tool("n8n_trigger_workflow", {
            "webhook_path": "webhook/test",
            "payload": {"msg": "hola"}
        })
        self.assertTrue(res["success"])
        self.assertEqual(res["status_code"], 200)

    @patch("subprocess.run")
    def test_git_status_execution(self, mock_run):
        mock_res = MagicMock()
        mock_res.stdout = " M core/camera.py\n"
        mock_run.return_value = mock_res

        git_server = GitMCPServer()
        res = git_server.execute_tool("git_status", {})
        self.assertTrue(res["success"])
        self.assertIn("core/camera.py", res["output"])

    @patch("core.web_reader.WebReader.read_url")
    def test_web_search_read_page(self, mock_read_url):
        mock_read_url.return_value = "# Titulo Web\nContenido extraido."

        web_server = WebSearchMCPServer()
        res = web_server.execute_tool("web_read_page", {"url": "https://example.com"})
        self.assertTrue(res["success"])
        self.assertIn("Contenido extraido", res["content"])

if __name__ == "__main__":
    unittest.main()
