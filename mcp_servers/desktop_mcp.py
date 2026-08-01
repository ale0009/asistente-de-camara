"""Servidor MCP para Control de Escritorio y Sistema Operativo Windows.

Proporciona herramientas estandarizadas para lanzamiento de aplicaciones, control
de volumen, capturas de pantalla y gestión de ventanas.
"""

import os
import logging
from typing import Dict, Any, List
from core.system_controller import SystemController

logger = logging.getLogger("NOVA.DesktopMCPServer")

class DesktopControlMCPServer:
    def __init__(self, system_controller: SystemController = None):
        self.system = system_controller or SystemController()

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "desktop_launch_app",
                "description": "Abre una aplicación registrada en Windows por su nombre (ej. blender, figma, vscode).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "app_name": {
                            "type": "string",
                            "description": "Nombre de la aplicación."
                        }
                    },
                    "required": ["app_name"]
                }
            },
            {
                "name": "desktop_set_volume",
                "description": "Ajusta el volumen principal del sistema en Windows (0 a 100).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "level": {
                            "type": "integer",
                            "description": "Porcentaje de volumen (0-100)."
                        }
                    },
                    "required": ["level"]
                }
            },
            {
                "name": "desktop_take_screenshot",
                "description": "Toma una captura de pantalla completa del escritorio y la guarda localmente.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "desktop_launch_app":
            app_name = arguments.get("app_name", "")
            success = self.system.open_app(app_name)
            return {"success": success, "message": f"Aplicación '{app_name}' iniciada." if success else f"No se pudo abrir '{app_name}'."}

        elif tool_name == "desktop_set_volume":
            level = int(arguments.get("level", 50))
            self.system.set_volume(level)
            return {"success": True, "message": f"Volumen ajustado al {level}%."}

        elif tool_name == "desktop_take_screenshot":
            filepath = self.system.take_screenshot()
            if filepath:
                return {"success": True, "filepath": filepath}
            return {"success": False, "error": "No se pudo tomar la captura de pantalla."}

        else:
            return {"success": False, "error": f"Herramienta desconocida: {tool_name}"}
