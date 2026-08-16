"""Servicio de Agencia FastAPI para NOVA / Segundo Cerebro.

Expone endpoints REST y WebSocket para interacción con el Agent Loop, consulta de herramientas MCP disponibles y auditoría.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent_service.agent_loop import AgentLoop
from agent_service.mcp_client import MCPClientManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NOVA.AgentService")

app = FastAPI(
    title="NOVA Agentic Service (MCP Architecture)",
    description="Servidor de agencia local desacoplado basado en Model Context Protocol (MCP)",
    version="3.2.0"
)

# Habilitar CORS para permitir conexión sin fricción desde el Web Command Center y dashboards locales
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent_loop = AgentLoop()
mcp_manager = agent_loop.mcp_manager

class InteractionRequest(BaseModel):
    prompt: str
    channel: Optional[str] = "api_text"

@app.get("/")
def read_root():
    return {
        "service": "NOVA Agentic Service",
        "status": "online",
        "version": "3.2.0",
        "architecture": "MCP (Model Context Protocol)"
    }

@app.get("/v1/health")
def health_check():
    """Chequeo de salud del servicio agéntico y conectividad con Ollama."""
    ollama_ok = agent_loop.ollama.check_connection() if agent_loop.ollama else False
    tools_count = len(mcp_manager.get_all_tools_schema())
    return {
        "status": "healthy" if ollama_ok else "degraded",
        "ollama_connected": ollama_ok,
        "active_model": agent_loop.ollama.resolve_model() if agent_loop.ollama else "unknown",
        "tools_registered": tools_count
    }

@app.post("/v1/agent/interact")
def interact(req: InteractionRequest):
    """Procesa una interacción del usuario pasando por el Agent Loop de MCP."""
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="El prompt no puede estar vacío.")

    result = agent_loop.process_interaction(req.prompt, source_channel=req.channel)
    return result

@app.get("/v1/agent/tools")
def list_tools():
    """Lista los esquemas de todas las herramientas MCP disponibles."""
    return {"tools": mcp_manager.get_all_tools_schema()}

@app.get("/v1/agent/audit")
def get_audit_logs(limit: int = 20):
    """Devuelve los últimos registros de auditoría almacenados en la base de datos."""
    return {"logs": agent_loop.audit_logger.get_recent_logs(limit=limit)}

@app.websocket("/v1/agent/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Cliente WebSocket conectado al Agent Service.")
    try:
        while True:
            data = await websocket.receive_text()
            for chunk in agent_loop.process_interaction_stream(data, source_channel="websocket"):
                await websocket.send_json(chunk)
    except Exception as e:
        logger.info(f"Conexión WebSocket cerrada: {e}")

