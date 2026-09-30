# -*- coding: utf-8 -*-
"""
Sincronizador Automático Git -> Obsidian Standup (core/git_obsidian_sync.py).
Escanea los repositorios en ~/Datos/Projects, agrupa los commits y estado de ramas del día
y genera o actualiza la nota diaria de Obsidian (Daily Notes/YYYY-MM-DD.md) con enlaces bidireccionales.
"""
import os
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger("NOVA.GitObsidianSync")

DEFAULT_PROJECTS_DIR = Path.home() / "Datos" / "Projects"
DEFAULT_VAULT_DIR = Path.home() / "Datos" / "Vault-Obsidian"


class GitObsidianSync:
    def __init__(self, projects_dir: Path = DEFAULT_PROJECTS_DIR, vault_dir: Path = DEFAULT_VAULT_DIR):
        self.projects_dir = Path(projects_dir)
        self.vault_dir = Path(vault_dir)

    def scan_git_activity_today(self) -> Dict[str, Any]:
        """
        Escanea todos los subdirectorios con .git dentro de projects_dir
        y extrae los commits realizados desde las 00:00 de hoy.
        """
        activity = {}
        total_commits = 0

        if not self.projects_dir.exists():
            return {"total_commits": 0, "projects": {}}

        # Buscar carpetas git de primer y segundo nivel
        candidate_dirs = [d for d in self.projects_dir.iterdir() if d.is_dir()]
        
        for pdir in candidate_dirs:
            git_dir = pdir / ".git"
            if not git_dir.exists():
                continue

            repo_name = pdir.name
            try:
                # 1. Obtener rama actual
                branch_proc = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=pdir, capture_output=True, text=True, timeout=3
                )
                current_branch = branch_proc.stdout.strip() if branch_proc.returncode == 0 else "main"

                # 2. Obtener commits de hoy
                # Formato: hash abreviado | autor | mensaje
                log_proc = subprocess.run(
                    ["git", "log", "--since=midnight", "--format=%h | %s", "--no-merges"],
                    cwd=pdir, capture_output=True, text=True, timeout=4
                )
                commits = []
                if log_proc.returncode == 0 and log_proc.stdout.strip():
                    for line in log_proc.stdout.strip().split("\n"):
                        if "|" in line:
                            h, msg = line.split("|", 1)
                            commits.append({"hash": h.strip(), "message": msg.strip()})

                # 3. Obtener estado de cambios no commiteados
                status_proc = subprocess.run(
                    ["git", "status", "-s"],
                    cwd=pdir, capture_output=True, text=True, timeout=3
                )
                uncommitted = len(status_proc.stdout.strip().split("\n")) if status_proc.stdout.strip() else 0

                if commits or uncommitted > 0:
                    activity[repo_name] = {
                        "branch": current_branch,
                        "commits": commits,
                        "uncommitted_files": uncommitted,
                        "path": str(pdir)
                    }
                    total_commits += len(commits)

            except Exception as e:
                logger.debug(f"Error inspeccionando repo {repo_name}: {e}")

        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_commits": total_commits,
            "projects_count": len(activity),
            "projects": activity
        }

    def generate_standup_markdown(self, activity_data: Dict[str, Any]) -> str:
        """Convierte los datos de actividad Git en un bloque Markdown limpio para Obsidian."""
        date_str = activity_data.get("date", datetime.now().strftime("%Y-%m-%d"))
        projects = activity_data.get("projects", {})
        total = activity_data.get("total_commits", 0)

        lines = [
            f"## 🚀 Actividad de Desarrollo (Git Auto-Standup — {date_str})",
            f"> [!summary] Resumen Automático de Código",
            f"> **Total de Commits:** {total} | **Repositorios con actividad:** {len(projects)}\n"
        ]

        if not projects:
            lines.append("No se registraron commits en los repositorios locales durante el día de hoy.\n")
            return "\n".join(lines)

        for name, data in projects.items():
            branch = data.get("branch", "main")
            commits = data.get("commits", [])
            uncommitted = data.get("uncommitted_files", 0)

            lines.append(f"### 📂 [[{name}]] (`rama: {branch}`)")
            if commits:
                for c in commits:
                    lines.append(f"- `{c['hash']}` {c['message']}")
            else:
                lines.append("- *(Sin commits confirmados hoy)*")

            if uncommitted > 0:
                lines.append(f"- ⚠️ *{uncommitted} archivo(s) con cambios pendientes de commit.*")
            lines.append("")

        return "\n".join(lines)

    def sync_to_obsidian_daily_note(self) -> Dict[str, Any]:
        """
        Escribe o actualiza la sección de Standup en la nota diaria de Obsidian.
        Busca en: ~/Datos/Vault-Obsidian/Daily Notes/YYYY-MM-DD.md
        Si la carpeta Daily Notes no existe, la crea.
        """
        activity = self.scan_git_activity_today()
        date_str = activity.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        daily_dir = self.vault_dir / "Daily Notes"
        daily_dir.mkdir(parents=True, exist_ok=True)
        daily_file = daily_dir / f"{date_str}.md"

        standup_md = self.generate_standup_markdown(activity)

        header_tag = "## 🚀 Actividad de Desarrollo (Git Auto-Standup"

        if daily_file.exists():
            content = daily_file.read_text(encoding="utf-8")
            if header_tag in content:
                # Reemplazar sección existente previa
                import re
                pattern = rf"{re.escape(header_tag)}.*?(?=\n## |\Z)"
                updated_content = re.sub(pattern, standup_md.strip(), content, flags=re.DOTALL)
                daily_file.write_text(updated_content, encoding="utf-8")
                status_msg = f"Sección de standup actualizada en {daily_file.name}"
            else:
                # Añadir al final de la nota existente
                updated_content = content.rstrip() + "\n\n" + standup_md
                daily_file.write_text(updated_content, encoding="utf-8")
                status_msg = f"Standup añadido a {daily_file.name}"
        else:
            # Crear nueva nota diaria con Frontmatter
            full_note = (
                f"---\n"
                f"fecha: {date_str}\n"
                f"tipo: diario-desarrollo\n"
                f"tags: [diario, standup, git, devlog, nova]\n"
                f"---\n"
                f"# 📅 Nota Diaria — {date_str}\n\n"
                f"{standup_md}\n"
            )
            daily_file.write_text(full_note, encoding="utf-8")
            status_msg = f"Nueva nota diaria creada en {daily_file.name}"

        # Resumen corto para voz o notificación
        total = activity.get("total_commits", 0)
        proj_count = activity.get("projects_count", 0)
        speech_summary = f"Standup sincronizado: {total} commits en {proj_count} proyectos registrados en Obsidian."

        return {
            "success": True,
            "status_msg": status_msg,
            "speech_summary": speech_summary,
            "total_commits": total,
            "projects_count": proj_count,
            "file_path": str(daily_file)
        }
