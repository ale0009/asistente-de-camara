# -*- coding: utf-8 -*-
"""
Capturador Rápido de Notas para Obsidian Inbox (core/quick_note.py).
Permite guardar ideas, tareas pendientes o notas rápidas directamente en ~/Datos/Vault-Obsidian/00_Inbox/
sin necesidad de abrir la aplicación completa de Obsidian.
"""
import os
import re
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger("NOVA.QuickNote")

DEFAULT_INBOX_DIR = Path.home() / "Datos" / "Vault-Obsidian" / "00_Inbox"
ICON_PATH = "/home/alejandro/Datos/Projects/asistente-de-camara/assets/nova_icon.png"


class QuickNoteIngester:
    def __init__(self, inbox_dir: Path = DEFAULT_INBOX_DIR):
        self.inbox_dir = Path(inbox_dir)
        self.inbox_dir.mkdir(parents=True, exist_ok=True)

    def save_note(self, content: str, title: str = "") -> Dict[str, Any]:
        """Guarda una nota en Markdown con metadatos estructurados en 00_Inbox."""
        content = content.strip()
        if not content:
            return {"success": False, "message": "El contenido de la nota está vacío."}

        now = datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
        file_timestamp = now.strftime("%Y%m%d_%H%M%S")

        # Generar título si no se especificó
        if not title:
            first_line = content.splitlines()[0][:40]
            clean_title = re.sub(r'[^\w\s-]', '', first_line).strip()
            title = clean_title if clean_title else "Nota rápida"

        # Nombre de archivo seguro
        slug_title = re.sub(r'\s+', '_', title.lower())[:30]
        filename = f"{file_timestamp}_{slug_title}.md"
        file_path = self.inbox_dir / filename

        md_body = f"""---
fecha: {timestamp_str}
tipo: nota_rapida
tags:
  - inbox/rapido
  - nova
---

# {title}

{content}
"""

        try:
            file_path.write_text(md_body, encoding="utf-8")
            logger.info(f"Nota rápida guardada en {file_path}")

            # Notificación de escritorio
            try:
                subprocess.Popen([
                    "notify-send", "-a", "NOVA Copilot",
                    "-i", ICON_PATH,
                    "✓ Nota guardada en Obsidian",
                    f"Inbox: {filename}",
                    "-t", "3500"
                ])
            except Exception:
                pass

            return {"success": True, "message": f"Nota guardada en 00_Inbox/{filename}", "path": str(file_path)}
        except Exception as e:
            logger.error(f"Error escribiendo nota rápida: {e}")
            return {"success": False, "message": f"Error al escribir nota: {str(e)}"}
