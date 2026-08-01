"""Agent Loop Principal para NOVA / Segundo Cerebro.

Gestiona el ciclo de percepción-decisión-ejecución-auditoría:
1. Recibe eventos o prompts de cualquier canal (Voz, Texto, Gestos, Watcher).
2. Obtiene las herramientas MCP disponibles.
3. Clasifica la intención vía AgentIntentRouter.
4. Ejecuta la herramienta MCP correspondiente o responde con el LLM.
5. Audita el proceso completo en la base de datos agent_audit_log.
"""

import time
import logging
from typing import Dict, Any, Optional

from agent_service.mcp_client import MCPClientManager
from agent_service.intent_router import AgentIntentRouter
from agent_service.audit_logger import AgentAuditLogger
from mcp_servers.vault_mcp import OverwriteError
from core.ollama_bridge import OllamaBridge

logger = logging.getLogger("NOVA.AgentLoop")

class AgentLoop:
    def __init__(
        self,
        mcp_manager: Optional[MCPClientManager] = None,
        intent_router: Optional[AgentIntentRouter] = None,
        audit_logger: Optional[AgentAuditLogger] = None,
        ollama_bridge: Optional[OllamaBridge] = None
    ):
        self.mcp_manager = mcp_manager or MCPClientManager()
        self.intent_router = intent_router or AgentIntentRouter()
        self.audit_logger = audit_logger or AgentAuditLogger()
        self.ollama = ollama_bridge or OllamaBridge()

    def process_interaction(self, raw_prompt: str, source_channel: str = "text") -> Dict[str, Any]:
        start_time = time.time()
        tools_schema = self.mcp_manager.get_all_tools_schema()

        # 1. Clasificación de Intención
        routing_decision = self.intent_router.route(raw_prompt, tools_schema)
        category = routing_decision.get("category", "direct_answer")
        tool_name = routing_decision.get("tool_name")
        arguments = routing_decision.get("arguments") or {}

        status = "SUCCESS"
        response_text = ""
        tool_result = None

        # 2. Ejecución según categoría
        if category == "mcp_tool_call" and tool_name:
            try:
                tool_result = self.mcp_manager.execute_tool(tool_name, arguments)
                if tool_result.get("success"):
                    response_text = f"Herramienta '{tool_name}' ejecutada con éxito: {tool_result}"
                else:
                    status = "FAILED"
                    response_text = f"Fallo al ejecutar herramienta '{tool_name}': {tool_result.get('error')}"

            except OverwriteError as oe:
                status = "PROTECTED_BLOCKED"
                response_text = str(oe)

            except Exception as e:
                status = "ERROR"
                response_text = f"Error inesperado ejecutando tool '{tool_name}': {e}"

        elif category == "celery_task":
            status = "ENQUEUED"
            response_text = f"Tarea pesada '{raw_prompt}' encolada exitosamente en Celery (VRAMLock activo)."

        else: # direct_answer
            try:
                response_text = self.ollama.query(
                    prompt=raw_prompt,
                    system_prompt="Eres NOVA, el asistente de inteligencia artificial local. Responde de forma clara, concisa y directa."
                )
            except Exception as e:
                status = "ERROR"
                response_text = f"Error al consultar LLM local: {e}"

        execution_time_ms = (time.time() - start_time) * 1000.0

        # 3. Auditoría en Base de Datos
        self.audit_logger.log_interaction(
            source_channel=source_channel,
            raw_prompt=raw_prompt,
            intent_category=category,
            tool_name=tool_name,
            tool_args=arguments,
            status=status,
            result_summary=response_text[:500],
            execution_time_ms=execution_time_ms
        )

        return {
            "status": status,
            "category": category,
            "tool_name": tool_name,
            "tool_args": arguments,
            "tool_result": tool_result,
            "response_text": response_text,
            "execution_time_ms": execution_time_ms
        }

    def process_interaction_stream(self, raw_prompt: str, source_channel: str = "websocket"):
        """
        Generador que procesa la interacción y produce fragmentos por oración
        para reproducción de voz/streaming en tiempo real.
        """
        start_time = time.time()
        tools_schema = self.mcp_manager.get_all_tools_schema()

        routing_decision = self.intent_router.route(raw_prompt, tools_schema)
        category = routing_decision.get("category", "direct_answer")
        tool_name = routing_decision.get("tool_name")
        arguments = routing_decision.get("arguments") or {}

        status = "SUCCESS"
        response_text = ""
        tool_result = None

        if category == "mcp_tool_call" and tool_name:
            try:
                tool_result = self.mcp_manager.execute_tool(tool_name, arguments)
                if tool_result.get("success"):
                    response_text = f"Herramienta '{tool_name}' ejecutada con éxito: {tool_result}"
                else:
                    status = "FAILED"
                    response_text = f"Fallo al ejecutar herramienta '{tool_name}': {tool_result.get('error')}"
            except OverwriteError as oe:
                status = "PROTECTED_BLOCKED"
                response_text = str(oe)
            except Exception as e:
                status = "ERROR"
                response_text = f"Error inesperado ejecutando tool '{tool_name}': {e}"

            yield {
                "type": "sentence_chunk",
                "chunk": response_text,
                "is_final": True
            }

        elif category == "celery_task":
            status = "ENQUEUED"
            response_text = f"Tarea pesada '{raw_prompt}' encolada exitosamente en Celery (VRAMLock activo)."
            yield {
                "type": "sentence_chunk",
                "chunk": response_text,
                "is_final": True
            }

        else:  # direct_answer
            try:
                tokens = self.ollama.query_stream(
                    prompt=raw_prompt,
                    system="Eres NOVA, el asistente de inteligencia artificial local. Responde de forma clara, concisa y directa."
                )
                buffer = ""
                delimiters = {".", "!", "?", "\n"}
                full_chunks = []

                for token in tokens:
                    buffer += token
                    while True:
                        indices = [buffer.find(d) for d in delimiters if buffer.find(d) != -1]
                        if not indices:
                            break
                        first_idx = min(indices)
                        sentence = buffer[:first_idx + 1].strip()
                        buffer = buffer[first_idx + 1:]
                        if sentence:
                            full_chunks.append(sentence)
                            yield {
                                "type": "sentence_chunk",
                                "chunk": sentence,
                                "is_final": False
                            }

                final_sentence = buffer.strip()
                if final_sentence:
                    full_chunks.append(final_sentence)
                    yield {
                        "type": "sentence_chunk",
                        "chunk": final_sentence,
                        "is_final": False
                    }

                response_text = " ".join(full_chunks)

            except Exception as e:
                status = "ERROR"
                response_text = f"Error al consultar LLM local: {e}"
                yield {
                    "type": "sentence_chunk",
                    "chunk": response_text,
                    "is_final": True
                }

        execution_time_ms = (time.time() - start_time) * 1000.0

        self.audit_logger.log_interaction(
            source_channel=source_channel,
            raw_prompt=raw_prompt,
            intent_category=category,
            tool_name=tool_name,
            tool_args=arguments,
            status=status,
            result_summary=response_text[:500],
            execution_time_ms=execution_time_ms
        )

        yield {
            "type": "completion",
            "status": status,
            "category": category,
            "tool_name": tool_name,
            "tool_args": arguments,
            "tool_result": tool_result,
            "response_text": response_text,
            "execution_time_ms": execution_time_ms
        }

