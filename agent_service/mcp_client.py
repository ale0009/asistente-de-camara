"""Gestor de Clientes MCP (Model Context Protocol).

Descubre, registra y ejecuta herramientas dinámicamente desde servidores MCP independientes
en `mcp_servers/`, aislando fallos y consolidando sus esquemas JSON-Schema para el Agent Loop.
"""

import importlib
import inspect
import logging
import os
import pkgutil
from typing import Dict, Any, List

logger = logging.getLogger("NOVA.MCPClientManager")

class MCPClientManager:
    def __init__(self, auto_discover: bool = True):
        self.servers: Dict[str, Any] = {}
        if auto_discover:
            self.discover_and_register_servers()

    def discover_and_register_servers(self) -> int:
        """Descubre e instancia automáticamente todos los servidores MCP en mcp_servers/."""
        import mcp_servers
        package_path = os.path.dirname(mcp_servers.__file__)

        loaded_count = 0
        for _, module_name, _ in pkgutil.iter_modules([package_path]):
            if module_name.startswith("__"):
                continue
            try:
                module = importlib.import_module(f"mcp_servers.{module_name}")
                # Recargar módulo si ya existía para soportar hot-reloading
                importlib.reload(module)
                
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        inspect.isclass(attr)
                        and attr.__module__ == module.__name__
                        and (attr_name.endswith("MCPServer") or attr_name.endswith("Server"))
                        and hasattr(attr, "get_tools_schema")
                        and hasattr(attr, "execute_tool")
                    ):
                        server_key = module_name.replace("_mcp", "").replace("mcp_", "")
                        try:
                            instance = attr()
                            self.servers[server_key] = instance
                            loaded_count += 1
                            logger.info(f"Servidor MCP '{server_key}' ({attr_name}) cargado exitosamente.")
                        except Exception as inst_err:
                            logger.warning(f"Aislamiento de fallo: No se pudo instanciar '{attr_name}' en '{module_name}': {inst_err}")
            except Exception as mod_err:
                logger.error(f"Aislamiento de fallo: Error importando módulo MCP '{module_name}': {mod_err}")

        logger.info(f"Total de servidores MCP registrados: {len(self.servers)} ({', '.join(self.servers.keys())})")
        return len(self.servers)

    def reload_plugins(self) -> int:
        """Recarga en caliente todos los plugins y servidores MCP."""
        logger.info("Recargando servidores MCP en caliente...")
        self.servers.clear()
        return self.discover_and_register_servers()

    def register_server(self, name: str, server_instance: Any):
        """Registra manualmente un servidor o plugin MCP."""
        self.servers[name] = server_instance
        logger.info(f"Servidor MCP '{name}' registrado manualmente.")

    def list_plugins(self) -> List[Dict[str, Any]]:
        """Devuelve un resumen de todos los servidores MCP y sus herramientas."""
        plugin_list = []
        for server_name, server in self.servers.items():
            try:
                schemas = server.get_tools_schema()
                tool_names = [s.get("name") for s in schemas]
                plugin_list.append({
                    "name": server_name,
                    "class": server.__class__.__name__,
                    "tools_count": len(schemas),
                    "tools": tool_names
                })
            except Exception as e:
                plugin_list.append({
                    "name": server_name,
                    "class": server.__class__.__name__,
                    "error": str(e)
                })
        return plugin_list

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
            try:
                schemas = server.get_tools_schema()
                tool_names = [s["name"] for s in schemas]
                if tool_name in tool_names:
                    logger.info(f"Ejecutando tool '{tool_name}' en el servidor MCP '{server_name}'...")
                    return server.execute_tool(tool_name, arguments)
            except Exception as e:
                logger.error(f"Excepción en el servidor MCP '{server_name}' al evaluar '{tool_name}': {e}")

        err_msg = f"Herramienta MCP '{tool_name}' no encontrada en ningún servidor registrado."
        logger.error(err_msg)
        return {"success": False, "error": err_msg}
