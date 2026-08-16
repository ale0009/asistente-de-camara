"""Servidor MCP para Obsidian Vault.

Proporciona herramientas estandarizadas para búsqueda, lectura y creación de notas
en el Vault de Obsidian, aplicando reglas duras de protección (OverwriteError) sobre
archivos críticos (Charter.md, ADRs, Actas).
"""

import os
import glob
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger("NOVA.VaultMCPServer")

class OverwriteError(PermissionError):
    """Excepción arrojada cuando se intenta sobreescribir un archivo estratégico protegido."""
    pass

PROTECTED_KEYWORDS = ["charter", "adr", "acta", "actas", "hito", "hitos", "intent_note"]

class ObsidianVaultMCPServer:
    def __init__(self, vault_path: str = "D:\\Documentos\\Obsidian Vault"):
        # `resolve()` también normaliza `..` y enlaces simbólicos. Guardar la
        # raíz normalizada permite comprobar de forma fiable que una petición
        # no escape del vault (por ejemplo: ../../Users/... ).
        self._vault_root = Path(vault_path).expanduser().resolve()
        self.vault_path = str(self._vault_root)

    def _resolve_note_path(self, relative_path: str) -> Path:
        """Resuelve una nota y garantiza que permanezca dentro del vault.

        Las rutas proceden de una herramienta que puede ser elegida por el
        modelo, por lo que no basta con documentar que sean relativas: debe
        validarse antes de leer, crear directorios o escribir.
        """
        if not isinstance(relative_path, str) or not relative_path.strip():
            raise ValueError("La ruta de la nota debe ser una ruta relativa no vacía.")

        candidate_input = Path(relative_path)
        if candidate_input.is_absolute():
            raise ValueError("No se permiten rutas absolutas fuera del Vault.")

        candidate = (self._vault_root / candidate_input).resolve()
        try:
            candidate.relative_to(self._vault_root)
        except ValueError as exc:
            raise ValueError("La ruta solicitada intenta salir del Vault de Obsidian.") from exc

        if candidate.suffix.lower() != ".md":
            raise ValueError("Solo se permiten notas Markdown (.md) dentro del Vault.")

        return candidate

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
            },
            {
                "name": "vault_list_projects",
                "description": "Escanea el Vault de Obsidian y lista todos los proyectos documentados, carpetas de trabajo y notas maestras.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "vault_summarize_project",
                "description": "Analiza las notas de un proyecto específico en Obsidian y genera una síntesis ejecutiva de su estado, arquitectura y avances.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_name": {
                            "type": "string",
                            "description": "Nombre o palabra clave del proyecto a analizar (ej. 'Blender', 'NOVA', 'Cámara')."
                        }
                    },
                    "required": ["project_name"]
                }
            },
            {
                "name": "vault_scan_pending_tasks",
                "description": "Escanea recursivamente las notas del Vault para extraer todas las tareas pendientes de tipo checklist (- [ ]).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filter_folder": {
                            "type": "string",
                            "description": "Subcarpeta opcional para acotar la búsqueda de tareas (ej. 'NOVA' o 'Proyectos')."
                        }
                    }
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
        elif tool_name == "vault_list_projects":
            return self._list_projects()
        elif tool_name == "vault_summarize_project":
            return self._summarize_project(arguments.get("project_name", ""))
        elif tool_name == "vault_scan_pending_tasks":
            return self._scan_pending_tasks(arguments.get("filter_folder", ""))
        else:
            return {"success": False, "error": f"Herramienta desconocida: {tool_name}"}

    def _read_note(self, relative_path: str) -> Dict[str, Any]:
        try:
            full_path = self._resolve_note_path(relative_path)
        except ValueError as exc:
            logger.warning("Lectura de vault bloqueada: %s", exc)
            return {"success": False, "error": str(exc)}

        if not full_path.exists():
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

        try:
            full_path = self._resolve_note_path(relative_path)
        except ValueError as exc:
            logger.warning("Escritura de vault bloqueada: %s", exc)
            return {"success": False, "error": str(exc)}

        full_path.parent.mkdir(parents=True, exist_ok=True)

        if full_path.exists() and not overwrite:
            return {"success": False, "error": f"La nota '{relative_path}' ya existe. Debe pasar overwrite=True para reemplazarla."}

        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "message": f"Nota '{relative_path}' guardada exitosamente."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _search(self, query: str) -> Dict[str, Any]:
        if not self._vault_root.exists():
            return {"success": False, "results": [], "warning": "Vault no encontrado."}

        matches = []
        query_lower = query.lower()
        search_pattern = os.path.join(self.vault_path, "**", "*.md")

        for file_path in glob.glob(search_pattern, recursive=True):
            try:
                resolved_file = Path(file_path).resolve()
                # Un enlace simbólico Markdown dentro del vault no debe dar
                # acceso a contenido fuera de él.
                resolved_file.relative_to(self._vault_root)
                with resolved_file.open("r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if query_lower in content.lower():
                        rel_path = os.path.relpath(resolved_file, self.vault_path)
                        matches.append({"path": rel_path, "snippet": content[:200] + "..."})
            except (OSError, ValueError):
                continue

        return {"success": True, "query": query, "count": len(matches), "results": matches[:10]}

    def _list_projects(self) -> Dict[str, Any]:
        """Escanea el Vault para encontrar proyectos, carpetas clave y notas centrales."""
        if not self._vault_root.exists():
            return {"success": False, "projects": [], "error": "Vault no encontrado."}

        projects = []
        try:
            # 1. Carpetas de primer nivel como proyectos potenciales
            for item in self._vault_root.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    md_files = list(item.glob("**/*.md"))
                    if md_files:
                        projects.append({
                            "name": item.name,
                            "type": "folder_project",
                            "note_count": len(md_files),
                            "path": item.name
                        })

            # 2. Notas en la raíz del Vault
            for item in self._vault_root.glob("*.md"):
                projects.append({
                    "name": item.stem,
                    "type": "master_document",
                    "note_count": 1,
                    "path": item.name
                })
        except Exception as e:
            return {"success": False, "error": f"Error listando proyectos: {e}"}

        return {
            "success": True,
            "count": len(projects),
            "projects": projects
        }

    def _summarize_project(self, project_name: str) -> Dict[str, Any]:
        """Recopila y resume el estado de un proyecto analizando sus notas."""
        if not self._vault_root.exists():
            return {"success": False, "error": "Vault no encontrado."}

        project_clean = project_name.strip().lower()
        if not project_clean:
            return {"success": False, "error": "Debes especificar el nombre del proyecto."}

        matched_files = []
        for file_path in self._vault_root.glob("**/*.md"):
            rel = file_path.relative_to(self._vault_root)
            if project_clean in str(rel).lower() or project_clean in file_path.stem.lower():
                matched_files.append(file_path)

        if not matched_files:
            return {
                "success": False,
                "project": project_name,
                "error": f"No se encontraron notas o carpetas para el proyecto '{project_name}' en el Vault."
            }

        compiled_snippets = []
        total_tasks_pending = 0
        total_tasks_completed = 0

        for fpath in matched_files[:6]:
            try:
                with fpath.open("r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                rel_name = str(fpath.relative_to(self._vault_root))
                # Extraer tareas
                for line in content.splitlines():
                    if "- [ ]" in line:
                        total_tasks_pending += 1
                    elif "- [x]" in line or "- [X]" in line:
                        total_tasks_completed += 1

                # Extraer encabezados y resumen inicial
                headers = [line.strip() for line in content.splitlines() if line.startswith("#")]
                preview = content[:500].strip()

                compiled_snippets.append({
                    "file": rel_name,
                    "headers": headers[:5],
                    "preview": preview
                })
            except Exception:
                continue

        summary_text = (
            f"Proyecto '{project_name}': {len(matched_files)} notas encontradas. "
            f"Tareas pendientes: {total_tasks_pending}, completadas: {total_tasks_completed}. "
            f"Archivos principales: {', '.join(s['file'] for s in compiled_snippets[:3])}."
        )

        return {
            "success": True,
            "project": project_name,
            "files_analyzed": len(matched_files),
            "tasks_pending": total_tasks_pending,
            "tasks_completed": total_tasks_completed,
            "summary": summary_text,
            "details": compiled_snippets
        }

    def _scan_pending_tasks(self, filter_folder: str = "") -> Dict[str, Any]:
        """Escanea todas las notas en busca de tareas pendientes (- [ ])."""
        if not self._vault_root.exists():
            return {"success": False, "tasks": [], "error": "Vault no encontrado."}

        target_dir = self._vault_root
        if filter_folder:
            try:
                target_dir = (self._vault_root / filter_folder).resolve()
                target_dir.relative_to(self._vault_root)
            except Exception:
                target_dir = self._vault_root

        pending_tasks = []
        for file_path in target_dir.glob("**/*.md"):
            try:
                rel_path = str(file_path.relative_to(self._vault_root))
                with file_path.open("r", encoding="utf-8", errors="ignore") as f:
                    for line_idx, line in enumerate(f, start=1):
                        if "- [ ]" in line:
                            task_desc = line.split("- [ ]", 1)[1].strip()
                            if task_desc:
                                pending_tasks.append({
                                    "task": task_desc,
                                    "file": rel_path,
                                    "line": line_idx
                                })
            except Exception:
                continue

        return {
            "success": True,
            "total_pending": len(pending_tasks),
            "tasks": pending_tasks[:30]
        }
