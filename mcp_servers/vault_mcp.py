"""Servidor MCP para Obsidian Vault.

Proporciona herramientas estandarizadas para búsqueda, lectura y creación de notas
en el Vault de Obsidian, aplicando reglas duras de protección (OverwriteError) sobre
archivos críticos (Charter.md, ADRs, Actas).
"""

import os
import glob
import logging
from typing import Dict, Any, List

logger = logging.getLogger("NOVA.VaultMCPServer")

class OverwriteError(PermissionError):
    """Excepción arrojada cuando se intenta sobreescribir un archivo estratégico protegido."""
    pass

PROTECTED_KEYWORDS = ["charter", "adr", "acta", "actas", "hito", "hitos", "intent_note"]

class ObsidianVaultMCPServer:
    def __init__(self, vault_path: str = "D:\\Documentos\\Obsidian Vault"):
        self.vault_path = vault_path

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Devuelve los esquemas JSON-Schema de las herramientas que expone este servidor MCP."""
        return [
            {
                "name": "vault_read_note",
                "description": "Lee el contenido completo de una nota dentro del Vault de Obsidian.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "relative_path": {
                            "type": "string",
                            "description": "Ruta relativa de la nota (ej. 'NOVA/Notas/idea.md')."
                        }
                    },
                    "required": ["relative_path"]
                }
            },
            {
                "name": "vault_write_note",
                "description": "Crea o actualiza una nota en el Vault. Arroja OverwriteError si intenta modificar un documento estratégico protegido.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "relative_path": {
                            "type": "string",
                            "description": "Ruta relativa de la nota."
                        },
                        "content": {
                            "type": "string",
                            "description": "Contenido en Markdown."
                        },
                        "overwrite": {
                            "type": "boolean",
                            "description": "Flag para autorizar sobreescritura si la nota existe (no aplica a notas protegidas)."
                        }
                    },
                    "required": ["relative_path", "content"]
                }
            },
            {
                "name": "vault_search",
                "description": "Busca términos clave dentro de las notas del Vault de Obsidian.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Término o frase de búsqueda."
                        }
                    },
                    "required": ["query"]
                }
            }
        ]

    def is_protected(self, relative_path: str) -> bool:
        """Verifica si la nota corresponde a una Intent Note protegida."""
        basename = os.path.basename(relative_path).lower()
        return any(keyword in basename for keyword in PROTECTED_KEYWORDS)

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "vault_read_note":
            return self._read_note(arguments.get("relative_path", ""))
        elif tool_name == "vault_write_note":
            return self._write_note(
                arguments.get("relative_path", ""),
                arguments.get("content", ""),
                arguments.get("overwrite", False)
            )
        elif tool_name == "vault_search":
            return self._search(arguments.get("query", ""))
        else:
            return {"success": False, "error": f"Herramienta desconocida: {tool_name}"}

    def _read_note(self, relative_path: str) -> Dict[str, Any]:
        full_path = os.path.join(self.vault_path, relative_path)
        if not os.path.exists(full_path):
            return {"success": False, "error": f"La nota '{relative_path}' no existe en el Vault."}

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"success": True, "path": relative_path, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _write_note(self, relative_path: str, content: str, overwrite: bool = False) -> Dict[str, Any]:
        if self.is_protected(relative_path):
            err_msg = f"ACCESO DENEGADO (OverwriteError): La nota '{relative_path}' es un documento estratégico protegido (Charter/ADR/Acta) y jamás puede ser modificada por el agente."
            logger.error(err_msg)
            raise OverwriteError(err_msg)

        full_path = os.path.join(self.vault_path, relative_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        if os.path.exists(full_path) and not overwrite:
            return {"success": False, "error": f"La nota '{relative_path}' ya existe. Debe pasar overwrite=True para reemplazarla."}

        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "message": f"Nota '{relative_path}' guardada exitosamente."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _search(self, query: str) -> Dict[str, Any]:
        if not os.path.exists(self.vault_path):
            return {"success": False, "results": [], "warning": "Vault no encontrado."}

        matches = []
        query_lower = query.lower()
        search_pattern = os.path.join(self.vault_path, "**", "*.md")

        for file_path in glob.glob(search_pattern, recursive=True):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if query_lower in content.lower():
                        rel_path = os.path.relpath(file_path, self.vault_path)
                        matches.append({"path": rel_path, "snippet": content[:200] + "..."})
            except Exception:
                continue

        return {"success": True, "query": query, "count": len(matches), "results": matches[:10]}
