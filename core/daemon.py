# -*- coding: utf-8 -*-
"""
Daemon Principal de NOVA (core/daemon.py).
Servicio en segundo plano sin ventana en reposo (0% CPU, <45MB RAM).
Orquesta el socket IPC, diagnóstico de terminal, Git Standup, gobernador de hardware y visión por región.
"""
import os
import sys
import json
import time
import asyncio
import logging
import signal
from pathlib import Path
from typing import Dict, Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.ipc_server import NovaIPCServer, DEFAULT_SOCKET_PATH
from core.ollama_bridge import OllamaBridge
from core.terminal_interceptor import TerminalInterceptor
from core.git_obsidian_sync import GitObsidianSync
from core.region_vision import RegionVision
from core.hardware_governor import HardwareGovernor
from core.episodic_memory import EpisodicMemory

# Configuración de logging
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "nova_daemon.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("NOVA.Daemon")


class NovaDaemon:
    def __init__(self, socket_path: str = DEFAULT_SOCKET_PATH):
        self.start_time = time.time()
        self.socket_path = socket_path

        # 1. Servicios Base
        self.ollama = OllamaBridge()
        self.memory = EpisodicMemory()
        
        # 2. Módulos de Estación de Trabajo
        self.terminal = TerminalInterceptor(ollama_bridge=self.ollama)
        self.git_sync = GitObsidianSync()
        self.vision = RegionVision(ollama_bridge=self.ollama)
        self.governor = HardwareGovernor()

        # 3. Servidor IPC
        self.ipc = NovaIPCServer(socket_path=self.socket_path)
        self._register_ipc_handlers()

        self._shutdown_event = asyncio.Event()

    def _register_ipc_handlers(self):
        """Mapea las acciones recibidas por el socket IPC con sus respectivos ejecutores."""
        self.ipc.register_handler("ping", self._handle_ping)
        self.ipc.register_handler("query", self._handle_query)
        self.ipc.register_handler("ask", self._handle_query)
        self.ipc.register_handler("fix", self._handle_fix)
        self.ipc.register_handler("standup", self._handle_standup)
        self.ipc.register_handler("inspect_region", self._handle_inspect_region)
        self.ipc.register_handler("telemetry", self._handle_telemetry)
        self.ipc.register_handler("blender", self._handle_blender)
        self.ipc.register_handler("projects", self._handle_projects)
        self.ipc.register_handler("open_project", self._handle_open_project)

    async def _handle_ping(self, req: Dict[str, Any]) -> Dict[str, Any]:
        uptime_sec = int(time.time() - self.start_time)
        return {
            "status": "online",
            "uptime_seconds": uptime_sec,
            "version": "2.0-workstation",
            "telemetry": self.governor.get_telemetry()
        }

    async def _handle_query(self, req: Dict[str, Any]) -> str:
        prompt = req.get("text", "").strip()
        if not prompt:
            return "Prompt vacío."
        # Usar modelo de código local ultra-rápido por defecto
        reply = self.ollama.query(prompt, model="qwen2.5-coder:1.5b", max_tokens=220)
        self.memory.log_event("query", "user_ask", prompt[:80], reply[:250], "cli,ia")
        return reply

    async def _handle_fix(self, req: Dict[str, Any]) -> Dict[str, Any]:
        diag = self.terminal.diagnose_last_error()
        if diag.get("success"):
            self.memory.log_event(
                "terminal", "fix_error", 
                f"Error en: {diag.get('cmd_original', '')}", 
                diag.get("comando_corregido", ""), 
                "terminal,debug"
            )
        return diag

    async def _handle_standup(self, req: Dict[str, Any]) -> Dict[str, Any]:
        result = self.git_sync.sync_to_obsidian_daily_note()
        if result.get("success"):
            self.memory.log_event(
                "git", "standup_sync", 
                result.get("speech_summary", "Standup sincronizado"), 
                result.get("file_path", ""), 
                "git,obsidian,standup"
            )
        return result

    async def _handle_inspect_region(self, req: Dict[str, Any]) -> Dict[str, Any]:
        mode = req.get("mode", "auto")
        res = self.vision.inspect_region(mode=mode)
        if res.get("success"):
            self.memory.log_event("vision", "region_roi", f"Modo: {mode}", res.get("result", "")[:200], "vision,clipboard")
        return res

    async def _handle_telemetry(self, req: Dict[str, Any]) -> Dict[str, Any]:
        return self.governor.get_telemetry()

    async def _handle_blender(self, req: Dict[str, Any]) -> str:
        res = self.governor.launch_blender()
        self.memory.log_event("system", "launch_blender", "Blender iniciado con PRIME offload", res, "blender,gpu")
        return res

    async def _handle_projects(self, req: Dict[str, Any]) -> Dict[str, Any]:
        vault_path = Path.home() / "Datos" / "Vault-Obsidian"
        master_path = vault_path / "proyectos" / "🌐 INVENTARIO MASTER DE PROYECTOS.md"
        projects = []
        if master_path.exists():
            import re
            content = master_path.read_text(encoding="utf-8")
            matches = re.findall(r'\|\s*\*\*([^*]+)\*\*\s*\|\s*`([^`]+)`\s*\|[^|]*\|\s*([^|]+)\|', content)
            for m in matches:
                projects.append({
                    "name": m[0].strip(),
                    "code": m[1].strip(),
                    "desc": m[2].strip()
                })
        return {"total": len(projects), "projects": projects}

    async def _handle_open_project(self, req: Dict[str, Any]) -> Dict[str, Any]:
        import subprocess
        name = req.get("name", "").strip()
        mode = req.get("mode", "code") # code, terminal, obsidian
        target_dir = Path.home() / "Datos" / "Projects" / name

        if not target_dir.exists():
            # Buscar coincidencia parcial
            candidates = list((Path.home() / "Datos" / "Projects").glob(f"*{name}*"))
            if candidates:
                target_dir = candidates[0]
            else:
                return {"success": False, "message": f"Proyecto '{name}' no encontrado en ~/Datos/Projects."}

        if mode == "code":
            subprocess.Popen(["code", str(target_dir)])
            msg = f"Abierto en VS Code: {target_dir.name}"
        elif mode == "terminal":
            subprocess.Popen(["konsole", "--workdir", str(target_dir)])
            msg = f"Terminal abierta en: {target_dir.name}"
        else:
            subprocess.Popen(["xdg-open", str(target_dir)])
            msg = f"Carpeta abierta: {target_dir.name}"

        return {"success": True, "message": msg, "path": str(target_dir)}

    async def run(self):
        """Inicia el servidor IPC y se mantiene activo en segundo plano."""
        logger.info("Iniciando NOVA Workstation Daemon 2.0...")
        await self.ipc.start()
        
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self._shutdown_event.set)
            except NotImplementedError:
                pass

        logger.info("NOVA Daemon listo. Esperando eventos e invocaciones IPC...")
        await self._shutdown_event.wait()
        
        logger.info("Deteniendo NOVA Daemon...")
        await self.ipc.stop()


def main():
    daemon = NovaDaemon()
    try:
        asyncio.run(daemon.run())
    except KeyboardInterrupt:
        logger.info("Daemon terminado por interrupción de teclado.")


if __name__ == "__main__":
    main()
