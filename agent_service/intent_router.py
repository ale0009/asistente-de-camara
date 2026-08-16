"""Enrutador Semántico de Intenciones para el Agente MCP.

Clasifica entradas de cualquier canal (texto, voz, eventos) en:
- `direct_answer`: Respuesta conversacional directa con LLM.
- `mcp_tool_call`: Invocación de herramienta estructurada MCP (Vault, Desktop, etc.).
- `celery_task`: Encolamiento de tarea pesada en segundo plano.
"""

import json
import logging
from typing import Dict, Any, List
from core.ollama_bridge import OllamaBridge

logger = logging.getLogger("NOVA.AgentIntentRouter")

class AgentIntentRouter:
    def __init__(self, ollama_bridge: OllamaBridge = None):
        self.ollama = ollama_bridge or OllamaBridge()

    def route(self, prompt: str, available_tools_schema: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza el prompt y determina la categoría de intención y parámetros."""
        tools_summary = [
            {"name": t["name"], "description": t["description"], "parameters": t.get("parameters", {})}
            for t in available_tools_schema
        ]

        system_prompt = f"""Eres el enrutador de intenciones del asistente agéntico local NOVA.
Dado un prompt de usuario, debes analizar si requiere invocar una herramienta MCP disponible o responder directamente.

HERRAMIENTAS MCP DISPONIBLES:
{json.dumps(tools_summary, indent=2, ensure_ascii=False)}

REGLAS DE CLASIFICACIÓN:
1. Si el usuario pide controlar la cámara (mover gimbal, tracking, zoom, presets, suspender/despertar, describir la escena con visión), leer/escribir notas, buscar en el Vault, abrir una app, ajustar volumen, tomar captura o buscar en la web, debes elegir "mcp_tool_call" indicando tool_name y los arguments exactos.
2. Si el usuario pide una tarea pesada de procesamiento de video o distilación de documentos largos, responde "celery_task".
3. En cualquier otro caso conversacional o de consulta general, responde "direct_answer".

DEBES RESPONDER ÚNICAMENTE UN JSON CON ESTA ESTRUCTURA EXACTA:
{{
  "category": "mcp_tool_call" | "celery_task" | "direct_answer",
  "tool_name": "nombre_de_la_tool_si_aplica" | null,
  "arguments": {{ ... }} | null,
  "reasoning": "Breve explicación de la decisión"
}}
"""

        try:
            response = self.ollama.query(
                prompt=f"Usuario: {prompt}",
                system=system_prompt,
                json_mode=True
            )

            result = json.loads(response)
            if "category" not in result:
                result["category"] = "direct_answer"
            return result

        except Exception as e:
            logger.warning(f"Error decodificando respuesta JSON del router de intención: {e}")
            return {
                "category": "direct_answer",
                "tool_name": None,
                "arguments": None,
                "reasoning": "Fallback por fallo en parsing JSON."
            }
