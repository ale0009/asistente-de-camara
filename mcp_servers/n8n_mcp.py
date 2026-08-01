"""Servidor MCP para Automatización y Webhooks en n8n.

Permite al agente NOVA disparar flujos de trabajo cross-app (email, calendarios,
mensajería, bases de datos) ejecutados en la plataforma n8n.
"""

import json
import logging
import urllib.request
from typing import Dict, Any, List

logger = logging.getLogger("NOVA.N8NMCPServer")

class N8NAutomationMCPServer:
    def __init__(self, n8n_base_url: str = "http://localhost:5678"):
        self.n8n_base_url = n8n_base_url.rstrip("/")

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "n8n_trigger_workflow",
                "description": "Dispara un flujo de trabajo de automatización n8n mediante un webhook con datos JSON.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "webhook_path": {
                            "type": "string",
                            "description": "Ruta relativa del webhook de n8n (ej. 'webhook/notificar-slack' o 'webhook-test/sync')."
                        },
                        "payload": {
                            "type": "object",
                            "description": "Diccionario con los datos a enviar al flujo de n8n."
                        }
                    },
                    "required": ["webhook_path", "payload"]
                }
            },
            {
                "name": "n8n_send_notification",
                "description": "Envía una notificación o resumen rápido al canal de automatizaciones prediseñado en n8n.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Título o asunto de la notificación."
                        },
                        "message": {
                            "type": "string",
                            "description": "Cuerpo del mensaje o resumen."
                        },
                        "priority": {
                            "type": "string",
                            "description": "Nivel de prioridad: 'low', 'normal', 'high'."
                        }
                    },
                    "required": ["title", "message"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "n8n_trigger_workflow":
            webhook_path = arguments.get("webhook_path", "").lstrip("/")
            payload = arguments.get("payload", {})
            return self._trigger_webhook(webhook_path, payload)
        elif tool_name == "n8n_send_notification":
            title = arguments.get("title", "")
            message = arguments.get("message", "")
            priority = arguments.get("priority", "normal")
            payload = {
                "source": "NOVA_AGENT",
                "title": title,
                "message": message,
                "priority": priority
            }
            return self._trigger_webhook("webhook/nova-notification", payload)
        else:
            return {"success": False, "error": f"Herramienta n8n desconocida: {tool_name}"}


    def _trigger_webhook(self, webhook_path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.n8n_base_url}/{webhook_path}"
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        try:
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_text = resp.read().decode("utf-8")
                try:
                    resp_json = json.loads(resp_text)
                except Exception:
                    resp_json = {"raw": resp_text}
                return {
                    "success": True,
                    "url": url,
                    "status_code": resp.status,
                    "response": resp_json
                }
        except Exception as e:
            logger.warning(f"Error conectando con webhook n8n ({url}): {e}")
            return {
                "success": False,
                "url": url,
                "error": f"No se pudo contactar al servidor n8n: {e}"
            }
