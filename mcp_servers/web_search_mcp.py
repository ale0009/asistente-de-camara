"""Servidor MCP para Búsqueda Web y Lectura de Documentos Online.

Proporciona herramientas estandarizadas para extracción de texto limpio desde URLs
y búsquedas web integradas.
"""

import logging
from typing import Dict, Any, List
from core.web_reader import WebReader

logger = logging.getLogger("NOVA.WebSearchMCPServer")

class WebSearchMCPServer:
    def __init__(self, web_reader: WebReader = None):
        self.web_reader = web_reader or WebReader()

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "web_read_page",
                "description": "Extrae el texto limpio en formato Markdown/texto de una URL pública.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL de la página web a leer."
                        }
                    },
                    "required": ["url"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "web_read_page":
            url = arguments.get("url", "")
            content = self.web_reader.read_url(url)
            if content and not content.startswith("Error"):
                return {"success": True, "url": url, "content": content[:2000]}
            return {"success": False, "url": url, "error": content or "No se pudo leer la URL."}
        else:
            return {"success": False, "error": f"Herramienta Web desconocida: {tool_name}"}
