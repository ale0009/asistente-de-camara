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

    def test_read_blocks_path_traversal(self):
        result = self.server.execute_tool("vault_read_note", {
            "relative_path": "../../fuera.md"
        })

        self.assertFalse(result["success"])
        self.assertIn("salir del Vault", result["error"])

    def test_write_blocks_absolute_and_non_markdown_paths(self):
        absolute = os.path.abspath(os.path.join(self.temp_dir.name, "..", "fuera.md"))
        absolute_result = self.server.execute_tool("vault_write_note", {
            "relative_path": absolute,
            "content": "No debe escribirse."
        })
        non_markdown_result = self.server.execute_tool("vault_write_note", {
            "relative_path": "Notas/secreto.txt",
            "content": "No debe escribirse."
        })

        self.assertFalse(absolute_result["success"])
        self.assertFalse(non_markdown_result["success"])
        self.assertIn("rutas absolutas", absolute_result["error"])
        self.assertIn("Markdown", non_markdown_result["error"])

    def test_list_and_summarize_projects(self):
        # Crear estructura de proyecto en el vault temporal
        self.server.execute_tool("vault_write_note", {
            "relative_path": "Blender/addons.md",
            "content": "# Proyecto Blender\n- [ ] Actualizar addon de materiales\n- [x] Configurar atajos"
        })
        self.server.execute_tool("vault_write_note", {
            "relative_path": "Blender/arquitectura.md",
            "content": "## Arquitectura de Render\nDetalles del motor."
        })

        list_res = self.server.execute_tool("vault_list_projects", {})
        self.assertTrue(list_res["success"])
        self.assertGreaterEqual(list_res["count"], 1)

        summary_res = self.server.execute_tool("vault_summarize_project", {"project_name": "Blender"})
        self.assertTrue(summary_res["success"])
        self.assertEqual(summary_res["project"], "Blender")
        self.assertEqual(summary_res["tasks_pending"], 1)
        self.assertEqual(summary_res["tasks_completed"], 1)

    def test_scan_pending_tasks(self):
        self.server.execute_tool("vault_write_note", {
            "relative_path": "Proyectos/Camara/tareas.md",
            "content": "- [ ] Implementar nuevo filtro\n- [ ] Calibrar tracking\n- [x] Probar OSC"
        })

        tasks_res = self.server.execute_tool("vault_scan_pending_tasks", {})
        self.assertTrue(tasks_res["success"])
        self.assertGreaterEqual(tasks_res["total_pending"], 2)

if __name__ == "__main__":
    unittest.main()

