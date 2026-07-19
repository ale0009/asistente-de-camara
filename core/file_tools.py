import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

MAX_RESULTS = 20


class FileTools:
    """
    Acciones sobre el sistema de archivos disponibles para el asistente,
    acotadas a las carpetas que el usuario autorizó explícitamente en
    config.yaml (assistant.allowed_folders). Nunca opera fuera de esa lista.
    """
    def __init__(self, allowed_folders, vault_path: str = None, notes_folder: str = "NOVA/Notas"):
        self.allowed_folders = [
            os.path.abspath(os.path.expanduser(p)) for p in (allowed_folders or [])
        ]
        self.vault_path = vault_path
        self.notes_folder = notes_folder

    def search_files(self, query: str) -> list:
        """Busca archivos cuyo nombre contenga `query`, solo dentro de las carpetas permitidas."""
        query_lower = query.lower().strip()
        if not query_lower:
            return []

        matches = []
        for root_folder in self.allowed_folders:
            if not os.path.isdir(root_folder):
                logger.warning(f"Carpeta permitida no existe, se ignora: {root_folder}")
                continue
            for dirpath, _dirnames, filenames in os.walk(root_folder):
                for name in filenames:
                    if query_lower in name.lower():
                        matches.append(os.path.join(dirpath, name))
                        if len(matches) >= MAX_RESULTS:
                            return matches
        return matches

    def write_note(self, title: str, content: str) -> str:
        """Añade una nota libre al vault de Obsidian (distinta del log automático de sesión)."""
        if not self.vault_path:
            return None

        notes_dir = os.path.join(self.vault_path, self.notes_folder)
        os.makedirs(notes_dir, exist_ok=True)

        safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip() or "Nota de voz"
        file_path = os.path.join(notes_dir, f"{safe_title}.md")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"\n## {timestamp}\n{content}\n")

        logger.info(f"Nota escrita en {file_path}")
        return file_path

    def read_document(self, target: str) -> str:
        """Lee el contenido de un archivo Markdown o de texto si está en carpetas autorizadas o vault."""
        target_lower = target.lower().strip()
        
        search_dirs = list(self.allowed_folders)
        if self.vault_path and self.vault_path not in search_dirs:
            search_dirs.append(self.vault_path)

        for folder in search_dirs:
            if not os.path.isdir(folder):
                continue
            for dirpath, _dirnames, filenames in os.walk(folder):
                for name in filenames:
                    if target_lower in name.lower() or name.lower().startswith(target_lower):
                        file_path = os.path.join(dirpath, name)
                        try:
                            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read(4000)
                            logger.info(f"Documento leído para RAG: {file_path}")
                            return f"--- Documento '{name}' ---\n{content}"
                        except Exception as e:
                            logger.error(f"Error leyendo archivo {file_path}: {e}")
        return None
