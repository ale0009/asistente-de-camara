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
from core.clipboard_copilot import ClipboardCopilot
from core.quick_note import QuickNoteIngester
from core.voice_bridge import VoiceBridge
from core.todo_radar import TodoRadar

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
        self.clipboard = ClipboardCopilot(ollama_bridge=self.ollama)
        self.quick_note = QuickNoteIngester()
        self.voice = VoiceBridge(ollama_bridge=self.ollama, memory=self.memory)
        self.todo_radar = TodoRadar()

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
        self.ipc.register_handler("clipboard_refactor", self._handle_clipboard_refactor)
        self.ipc.register_handler("clipboard_explain", self._handle_clipboard_explain)
        self.ipc.register_handler("quick_note", self._handle_quick_note)
        self.ipc.register_handler("dirty_projects", self._handle_dirty_projects)
        self.ipc.register_handler("turbo_fan", self._handle_turbo_fan)
        self.ipc.register_handler("voice_query", self._handle_voice_query)
        self.ipc.register_handler("speak", self._handle_speak)
        self.ipc.register_handler("todo_radar", self._handle_todo_radar)

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
        mode = req.get("mode", "code") # code, terminal, folder, obsidian

        vault_projs = Path.home() / "Datos" / "Vault-Obsidian" / "proyectos"
        target_dir = Path.home() / "Datos" / "Projects" / name

        # 1. Modo Obsidian: abrir directamente la nota o carpeta en Obsidian
        if mode == "obsidian":
            target_obs = None
            if vault_projs.exists():
                for p in vault_projs.iterdir():
                    if name.lower() in p.name.lower():
                        target_obs = p
                        break
            if target_obs:
                overview_files = list(target_obs.glob("*Overview*.md")) + list(target_obs.glob("*MOC*.md")) + list(target_obs.glob("*.md"))
                if overview_files:
                    subprocess.Popen(["obsidian", str(overview_files[0])])
                    return {"success": True, "message": f"Abierto en Obsidian: {overview_files[0].name}", "path": str(overview_files[0])}
                else:
                    subprocess.Popen(["xdg-open", str(target_obs)])
                    return {"success": True, "message": f"Carpeta de notas abierta: {target_obs.name}", "path": str(target_obs)}
            return {"success": False, "message": f"No se encontró documentación para '{name}' en Obsidian."}

        # 2. Modos de Código, Terminal o Carpeta
        if not target_dir.exists():
            # Buscar coincidencia parcial en ~/Datos/Projects
            candidates = list((Path.home() / "Datos" / "Projects").glob(f"*{name}*"))
            if candidates:
                target_dir = candidates[0]
            else:
                # Si no existe en Projects pero sí en Obsidian, abrir su documentación en Obsidian
                if vault_projs.exists():
                    for p in vault_projs.iterdir():
                        if name.lower() in p.name.lower():
                            overview_files = list(p.glob("*Overview*.md")) + list(p.glob("*MOC*.md")) + list(p.glob("*.md"))
                            if overview_files:
                                subprocess.Popen(["obsidian", str(overview_files[0])])
                                return {"success": True, "message": f"El código no está en ~/Datos/Projects. Abriendo su nota en Obsidian: {overview_files[0].name}", "path": str(overview_files[0])}

                return {"success": False, "message": f"Proyecto '{name}' no encontrado en ~/Datos/Projects ni en Obsidian."}

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

    async def _handle_clipboard_refactor(self, req: Dict[str, Any]) -> Dict[str, Any]:
        return self.clipboard.refactor()

    async def _handle_clipboard_explain(self, req: Dict[str, Any]) -> Dict[str, Any]:
        return self.clipboard.explain()

    async def _handle_quick_note(self, req: Dict[str, Any]) -> Dict[str, Any]:
        content = req.get("content", "").strip()
        title = req.get("title", "")
        return self.quick_note.save_note(content=content, title=title)

    async def _handle_dirty_projects(self, req: Dict[str, Any]) -> Dict[str, Any]:
        dirty = self.git_sync.get_dirty_projects()
        return {"dirty_projects": dirty}

    async def _handle_turbo_fan(self, req: Dict[str, Any]) -> Dict[str, Any]:
        mode = req.get("mode", "alternar")
        flag = f"--{mode}" if not mode.startswith("--") else mode
        try:
            proc = subprocess.run(["turbo-fan", flag], capture_output=True, text=True, timeout=4)
            return {"success": proc.returncode == 0, "output": proc.stdout.strip()}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def _handle_voice_query(self, req: Dict[str, Any]) -> Dict[str, Any]:
        duration = int(req.get("duration", 5))
        return self.voice.process_voice_query(duration_seconds=duration)

    async def _handle_speak(self, req: Dict[str, Any]) -> Dict[str, Any]:
        text = req.get("text", "")
        self.voice.speak(text)
        return {"success": True}

    async def _handle_todo_radar(self, req: Dict[str, Any]) -> Dict[str, Any]:
        data = self.todo_radar.scan_all_projects()
        report_path = self.todo_radar.generate_obsidian_report(data)
        return {
            "success": True,
            "total_items": data["total_items"],
            "projects_count": data["projects_count"],
            "report_path": str(report_path)
        }

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
