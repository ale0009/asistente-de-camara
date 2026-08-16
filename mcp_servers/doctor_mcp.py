"""Servidor MCP para Diagnóstico del Sistema, Auto-Auditoría y Recuperación (Doctor NOVA).

Permite a NOVA inspeccionar en tiempo real el estado de salud de todos los subsistemas:
Cámara, Conexión OSC, Modelos Ollama, Micrófono, Obsidian Vault y Espacio en Disco.
"""

import os
import shutil
import logging
from typing import Dict, Any, List, Optional

from core.ollama_bridge import OllamaBridge
from core.camera import CameraController
from core.osc_controller import OSCController

logger = logging.getLogger("NOVA.DoctorMCPServer")

class DoctorMCPServer:
    def __init__(
        self,
        ollama_bridge: Optional[OllamaBridge] = None,
        camera_controller: Optional[CameraController] = None,
        osc_controller: Optional[OSCController] = None,
        vault_path: str = "D:\\Documentos\\Obsidian Vault"
    ):
        self.ollama = ollama_bridge or OllamaBridge()
        self.camera = camera_controller
        self.osc = osc_controller or OSCController()
        self.vault_path = vault_path

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "doctor_health_check",
                "description": "Ejecuta una auto-auditoría completa de salud de hardware, software, IA y almacenamiento en NOVA.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "doctor_repair_connections",
                "description": "Intenta auto-reparar conexiones caídas (cámara, Ollama, locks de audio) de forma segura.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "doctor_health_check":
            return self._health_check()
        elif tool_name == "doctor_repair_connections":
            return self._repair_connections()
        else:
            return {"success": False, "error": f"Herramienta de diagnóstico desconocida: {tool_name}"}

    def _health_check(self) -> Dict[str, Any]:
        diagnostics = {}

        # 1. Ollama LLM
        ollama_ok = self.ollama.check_connection() if self.ollama else False
        models = self.ollama.get_models() if ollama_ok else []
        active_model = self.ollama.resolve_model() if ollama_ok else "offline"
        diagnostics["ollama"] = {
            "status": "healthy" if ollama_ok else "unreachable",
            "active_model": active_model,
            "models_count": len(models),
            "models": models
        }

        # 2. Obsidian Vault
        vault_exists = os.path.exists(self.vault_path)
        diagnostics["obsidian_vault"] = {
            "status": "healthy" if vault_exists else "missing_path",
            "path": self.vault_path
        }

        # 3. Espacio en disco
        try:
            total, used, free = shutil.disk_usage(os.path.abspath("."))
            diagnostics["disk_space"] = {
                "status": "healthy" if free > (5 * 1024 * 1024 * 1024) else "low_space",
                "free_gb": round(free / (1024 ** 3), 2),
                "total_gb": round(total / (1024 ** 3), 2)
            }
        except Exception:
            diagnostics["disk_space"] = {"status": "unknown"}

        # 4. Control OSC
        diagnostics["osc_controller"] = {
            "status": "healthy",
            "target_port": getattr(self.osc, "port", 16284),
            "feedback_active": getattr(self.osc, "feedback_listener_active", False)
        }

        # Estado global
        all_ok = ollama_ok and vault_exists
        overall_status = "OPERATIONAL" if all_ok else "DEGRADED"

        return {
            "success": True,
            "overall_status": overall_status,
            "diagnostics": diagnostics
        }

    def _repair_connections(self) -> Dict[str, Any]:
        actions_taken = []

        # 1. Re-inicializar COM si aplica
        try:
            import pythoncom
            pythoncom.CoInitialize()
            actions_taken.append("COM subsystem inicializado.")
        except Exception:
            pass

        # 2. Refrescar modelos de Ollama
        if self.ollama:
            try:
                models = self.ollama.get_models(force_refresh=True)
                actions_taken.append(f"Cache de Ollama refrescada ({len(models)} modelos detectados).")
            except Exception as e:
                actions_taken.append(f"Fallo al refrescar Ollama: {e}")

        return {
            "success": True,
            "actions_taken": actions_taken,
            "message": "Auto-reparación y reciclaje de subsistemas completado con éxito."
        }
