"""Servidor MCP para Git y Gestión de Repositorios.

Proporciona herramientas estandarizadas para consultar el estado del repositorio Git,
ramas activas y últimos commits en los proyectos de E:\\proyectos\\.
"""

import os
import logging
import subprocess
from typing import Dict, Any, List

logger = logging.getLogger("NOVA.GitMCPServer")

class GitMCPServer:
    def __init__(self, projects_root: str = "E:\\proyectos\\Camara inteligente"):
        self.projects_root = projects_root

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "git_status",
                "description": "Consulta el estado actual de Git (archivos modificados, staged, un-tracked).",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "git_recent_commits",
                "description": "Devuelve la lista de los últimos N commits del repositorio activo.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "count": {
                            "type": "integer",
                            "description": "Número de commits a recuperar (default 5)."
                        }
                    }
                }
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "git_status":
            return self._run_git(["status", "--short"])
        elif tool_name == "git_recent_commits":
            count = int(arguments.get("count", 5))
            return self._run_git(["log", f"-n{count}", "--oneline"])
        else:
            return {"success": False, "error": f"Herramienta Git desconocida: {tool_name}"}

    def _run_git(self, args: List[str]) -> Dict[str, Any]:
        if not os.path.exists(self.projects_root):
            return {"success": False, "error": f"Ruta del repositorio no encontrada: {self.projects_root}"}

        try:
            cmd = ["git"] + args
            result = subprocess.run(
                cmd,
                cwd=self.projects_root,
                capture_output=True,
                text=True,
                check=True
            )
            return {
                "success": True,
                "output": result.stdout.strip()
            }
        except subprocess.CalledProcessError as cpe:
            return {"success": False, "error": cpe.stderr.strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}
