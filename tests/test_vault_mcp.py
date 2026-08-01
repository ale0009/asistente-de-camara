import os
import tempfile
import unittest

from mcp_servers.vault_mcp import ObsidianVaultMCPServer, OverwriteError

class TestVaultMCPServer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.server = ObsidianVaultMCPServer(vault_path=self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_schema_exposed(self):
        schemas = self.server.get_tools_schema()
        tool_names = [s["name"] for s in schemas]
        self.assertIn("vault_read_note", tool_names)
        self.assertIn("vault_write_note", tool_names)
        self.assertIn("vault_search", tool_names)

    def test_write_and_read_normal_note(self):
        write_res = self.server.execute_tool("vault_write_note", {
            "relative_path": "Notas/normal.md",
            "content": "# Nota de prueba\nContenido normal."
        })
        self.assertTrue(write_res["success"])

        read_res = self.server.execute_tool("vault_read_note", {
            "relative_path": "Notas/normal.md"
        })
        self.assertTrue(read_res["success"])
        self.assertIn("# Nota de prueba", read_res["content"])

    def test_protected_intent_notes_raise_overwrite_error(self):
        protected_paths = [
            "Charter.md",
            "ADR_001_Aceptado.md",
            "Acta_de_cierre_2026.md",
            "Proyecto/hitos.md"
        ]

        for path in protected_paths:
            with self.assertRaises(OverwriteError):
                self.server.execute_tool("vault_write_note", {
                    "relative_path": path,
                    "content": "Intento de sobreescritura no autorizada."
                })

    def test_search_notes(self):
        self.server.execute_tool("vault_write_note", {
            "relative_path": "Documento.md",
            "content": "Este es un documento especial con código secreto 12345."
        })

        search_res = self.server.execute_tool("vault_search", {"query": "secreto"})
        self.assertTrue(search_res["success"])
        self.assertGreaterEqual(search_res["count"], 1)

if __name__ == "__main__":
    unittest.main()
