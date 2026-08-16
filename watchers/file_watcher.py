"""Observador de Archivos (File Watcher) para NOVA / Segundo Cerebro (Fase 3).

Monitorea cambios de archivos en caliente dentro de E:\\proyectos\\ y el Vault de Obsidian,
publicando eventos de modificación al Agent Loop de FastAPI para actualizar el contexto agéntico.
"""

import os
import json
import time
import logging
import threading
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("NOVA.FileWatcher")

# Directorios y archivos generados que nunca deben disparar una interacción
# con el agente. En especial, `logs/agent_audit.db` se modifica cada vez que
# el agente atiende un evento: vigilarlo creaba un ciclo de autoeventos.
IGNORED_DIR_NAMES = {
    ".git", "__pycache__", "venv", ".pytest_cache", "node_modules",
    "logs", "build", "dist", ".gradle", ".idea",
}
IGNORED_FILE_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".log", ".tmp", ".pyc", ".pyo", ".wal", ".shm"}

class FileWatcherService:
    def __init__(
        self,
        watch_paths: Optional[List[str]] = None,
        agent_url: str = "http://127.0.0.1:8000/v1/agent/interact",
        poll_interval_sec: float = 2.0,
        event_cooldown_sec: float = 5.0,
        max_events_per_poll: int = 10,
    ):
        self.watch_paths = watch_paths or [
            "E:\\proyectos\\Camara inteligente",
            "D:\\Documentos\\Obsidian Vault"
        ]
        self.agent_url = agent_url
        self.poll_interval_sec = poll_interval_sec
        self.event_cooldown_sec = event_cooldown_sec
        self.max_events_per_poll = max_events_per_poll
        self.is_running = False
        self.snapshot = {}
        self._last_notified = {}

    @staticmethod
    def _should_ignore_path(path: Path) -> bool:
        """Indica si un archivo no debe formar parte de la observación."""
        parts = {part.casefold() for part in path.parts}
        if parts.intersection(IGNORED_DIR_NAMES):
            return True
        return path.suffix.casefold() in IGNORED_FILE_SUFFIXES

    def _can_notify(self, path: str) -> bool:
        now = time.monotonic()
        previous = self._last_notified.get(path)
        if previous is not None and now - previous < self.event_cooldown_sec:
            logger.debug("Watcher: evento omitido por cooldown: %s", path)
            return False
        self._last_notified[path] = now
        return True

    def _take_snapshot(self):
        new_snapshot = {}
        for path in self.watch_paths:
            if not os.path.exists(path):
                continue
            for root, dirs, files in os.walk(path):
                # Podar `dirs` evita descender a árboles enormes; hacer solo
                # `continue` no impedía que os.walk siguiera recorriéndolos.
                dirs[:] = [
                    directory for directory in dirs
                    if directory.casefold() not in IGNORED_DIR_NAMES
                ]
                for f in files:
                    full_path = Path(root, f)
                    if self._should_ignore_path(full_path):
                        continue
                    try:
                        stat = full_path.stat()
                        # ns + tamaño detecta escrituras rápidas que podían
                        # conservar el mismo mtime de resolución baja.
                        new_snapshot[str(full_path.resolve())] = (stat.st_mtime_ns, stat.st_size)
                    except OSError:
                        continue
        return new_snapshot

    def _notify_agent(self, changed_path: str):
        if not self._can_notify(changed_path):
            return False

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
            return True
        except Exception as e:
            logger.warning(f"Watcher: No se pudo notificar evento al Agent Loop: {e}")
            return False

    def _watch_loop(self):
        self.snapshot = self._take_snapshot()
        while self.is_running:
            time.sleep(self.poll_interval_sec)
            current = self._take_snapshot()

            changes = [
                filepath for filepath, mtime in current.items()
                if filepath not in self.snapshot or self.snapshot[filepath] != mtime
            ]
            if len(changes) > self.max_events_per_poll:
                logger.warning(
                    "Watcher: %s cambios detectados; se limitarán a %s en este ciclo.",
                    len(changes), self.max_events_per_poll,
                )

            for filepath in changes[:self.max_events_per_poll]:
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
