"""Gestor de Clientes MCP (Model Context Protocol).

Descubre, registra y ejecuta herramientas desde servidores MCP independientes
(Vault, Desktop, n8n, Git, WebSearch), consolidando sus esquemas JSON-Schema para el Agent Loop.
"""

import logging
from typing import Dict, Any, List

from mcp_servers.vault_mcp import ObsidianVaultMCPServer
from mcp_servers.desktop_mcp import DesktopControlMCPServer
from mcp_servers.n8n_mcp import N8NAutomationMCPServer
from mcp_servers.git_mcp import GitMCPServer
from mcp_servers.web_search_mcp import WebSearchMCPServer

logger = logging.getLogger("NOVA.MCPClientManager")

class MCPClientManager:
    def __init__(self):
        self.servers = {}
        self._register_default_servers()

    def _register_default_servers(self):
        self.servers["vault"] = ObsidianVaultMCPServer()
        self.servers["desktop"] = DesktopControlMCPServer()
        self.servers["n8n"] = N8NAutomationMCPServer()
        self.servers["git"] = GitMCPServer()
        self.servers["web"] = WebSearchMCPServer()
        logger.info("Servidores MCP 'vault', 'desktop', 'n8n', 'git' y 'web' registrados correctamente.")

    def register_server(self, name: str, server_instance: Any):
        self.servers[name] = server_instance
        logger.info(f"Servidor MCP '{name}' registrado.")

    def get_all_tools_schema(self) -> List[Dict[str, Any]]:
        """Consolida las herramientas de todos los servidores MCP registrados."""
        all_tools = []
        for server_name, server in self.servers.items():
            try:
                schemas = server.get_tools_schema()
                for s in schemas:
                    s["_server"] = server_name
                all_tools.extend(schemas)
            except Exception as e:
                logger.error(f"Error obteniendo esquemas del servidor MCP '{server_name}': {e}")
        return all_tools

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Busca y ejecuta la herramienta especificada en el servidor MCP correspondiente."""
        for server_name, server in self.servers.items():
            schemas = server.get_tools_schema()
            tool_names = [s["name"] for s in schemas]
            if tool_name in tool_names:
                logger.info(f"Ejecutando tool '{tool_name}' en el servidor MCP '{server_name}'...")
                return server.execute_tool(tool_name, arguments)

        err_msg = f"Herramienta MCP '{tool_name}' no encontrada en ningún servidor registrado."
        logger.error(err_msg)
        return {"success": False, "error": err_msg}
