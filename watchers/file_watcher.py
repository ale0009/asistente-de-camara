"""Observador de Archivos (File Watcher) para NOVA / Segundo Cerebro (Fase 3).

Monitorea cambios de archivos en caliente dentro de E:\\proyectos\\ y el Vault de Obsidian,
publicando eventos de modificación al Agent Loop de FastAPI para actualizar el contexto agéntico.
"""

import os
import json
import time
import logging
import threading
from typing import List, Optional

logger = logging.getLogger("NOVA.FileWatcher")

class FileWatcherService:
    def __init__(
        self,
        watch_paths: Optional[List[str]] = None,
        agent_url: str = "http://127.0.0.1:8000/v1/agent/interact",
        poll_interval_sec: float = 2.0
    ):
        self.watch_paths = watch_paths or [
            "E:\\proyectos\\Camara inteligente",
            "D:\\Documentos\\Obsidian Vault"
        ]
        self.agent_url = agent_url
        self.poll_interval_sec = poll_interval_sec
        self.is_running = False
        self.snapshot = {}

    def _take_snapshot(self):
        new_snapshot = {}
        for path in self.watch_paths:
            if not os.path.exists(path):
                continue
            for root, _, files in os.walk(path):
                # Evitar carpetas pesadas o temporales
                if any(ignored in root for ignored in [".git", "__pycache__", "venv", ".pytest_cache", "node_modules"]):
                    continue
                for f in files:
                    full_p = os.path.join(root, f)
                    try:
                        mtime = os.path.getmtime(full_p)
                        new_snapshot[full_p] = mtime
                    except Exception:
                        pass
        return new_snapshot

    def _notify_agent(self, changed_path: str):
        logger.info(f"Watcher: Cambio detectado en archivo: '{changed_path}'")
        import urllib.request

        payload = json.dumps({
            "prompt": f"Evento de sistema: El archivo '{changed_path}' fue modificado o creado.",
            "channel": "file_watcher_event"
        }).encode("utf-8")

        headers = {"Content-Type": "application/json"}

        try:
            req = urllib.request.Request(self.agent_url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=5) as resp:
                logger.info(f"Watcher: Evento notificado al Agent Loop.")
        except Exception as e:
            logger.warning(f"Watcher: No se pudo notificar evento al Agent Loop: {e}")

    def _watch_loop(self):
        self.snapshot = self._take_snapshot()
        while self.is_running:
            time.sleep(self.poll_interval_sec)
            current = self._take_snapshot()

            for filepath, mtime in current.items():
                if filepath not in self.snapshot or self.snapshot[filepath] != mtime:
                    self._notify_agent(filepath)

            self.snapshot = current

    def start(self):
        logger.info(f"Iniciando File Watcher en rutas: {self.watch_paths}")
        self.is_running = True
        self.watcher_thread = threading.Thread(target=self._watch_loop, daemon=True, name="NOVA-FileWatcher")
        self.watcher_thread.start()

    def stop(self):
        logger.info("Deteniendo File Watcher...")
        self.is_running = False
