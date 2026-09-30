# -*- coding: utf-8 -*-
"""
Radar de Tareas y Deuda Técnica para Obsidian (core/todo_radar.py).
Escanea los repositorios locales en ~/Datos/Projects en busca de comentarios
TODO, FIXME, BUG, HACK y REFACTOR, generando una vista consolidada en Obsidian.
"""
import os
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger("NOVA.TodoRadar")

DEFAULT_PROJECTS_DIR = Path.home() / "Datos" / "Projects"
DEFAULT_VAULT_DIR = Path.home() / "Datos" / "Vault-Obsidian"

IGNORED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", "build", "dist",
    "target", ".cache", ".idea", ".vscode", "vendor", "env", "assets", "models",
    "llama.cpp", "third_party", "extern", "deps", "boveda"
}

VALID_EXTENSIONS = {
    ".py", ".rs", ".js", ".ts", ".jsx", ".tsx", ".dart", ".cpp", ".c", ".h",
    ".hpp", ".sh", ".bash", ".go", ".java", ".html", ".css", ".yaml", ".yml",
    ".sql", ".lua", ".toml"
}

PATTERN = re.compile(
    r'(?://|#|/\*|<!--|--|;|\*)\s*(TODO|FIXME|BUG|HACK|REFACTOR|OPTIMIZE)\b[:\s]*(.*)',
    re.IGNORECASE
)


class TodoRadar:
    def __init__(self, projects_dir: Path = DEFAULT_PROJECTS_DIR, vault_dir: Path = DEFAULT_VAULT_DIR):
        self.projects_dir = Path(projects_dir)
        self.vault_dir = Path(vault_dir)

    def scan_all_projects(self) -> Dict[str, Any]:
        """Escanea todos los proyectos buscando comentarios TODO/FIXME."""
        results = {}
        total_items = 0
        tag_counts = {"FIXME": 0, "BUG": 0, "TODO": 0, "HACK": 0, "REFACTOR": 0, "OPTIMIZE": 0}

        if not self.projects_dir.exists():
            return {"total": 0, "projects": {}, "tags": tag_counts}

        candidate_dirs = [d for d in self.projects_dir.iterdir() if d.is_dir() and d.name not in IGNORED_DIRS]

        for pdir in candidate_dirs:
            pname = pdir.name
            project_items = []

            for root, dirs, files in os.walk(pdir):
                # Filtrar carpetas ignoradas in-place
                dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]

                for f in files:
                    ext = Path(f).suffix.lower()
                    if ext not in VALID_EXTENSIONS:
                        continue

                    file_path = Path(root) / f
                    rel_file = file_path.relative_to(pdir)

                    try:
                        # Leer primeras líneas seguras de texto
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
                            for idx, line in enumerate(fh, start=1):
                                if len(line) > 500:
                                    continue
                                match = PATTERN.search(line)
                                if match:
                                    tag = match.group(1).upper()
                                    msg = match.group(2).strip()
                                    # Limpiar cierres de comentarios
                                    msg = re.sub(r'(\*/|-->|#|//).*$', '', msg).strip()
                                    if not msg:
                                        msg = "Tarea pendiente sin descripción"

                                    tag_normalized = tag if tag in tag_counts else "TODO"
                                    tag_counts[tag_normalized] = tag_counts.get(tag_normalized, 0) + 1

                                    project_items.append({
                                        "tag": tag_normalized,
                                        "file": str(rel_file),
                                        "line": idx,
                                        "message": msg[:140]
                                    })
                                    total_items += 1
                    except Exception as e:
                        logger.debug(f"Error leyendo {file_path}: {e}")

            if project_items:
                results[pname] = project_items

        return {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "total_items": total_items,
            "projects_count": len(results),
            "tag_counts": tag_counts,
            "projects": results
        }

    def generate_obsidian_report(self, data: Dict[str, Any]) -> Path:
        """Escribe o actualiza el archivo de radar en Obsidian."""
        radar_file = self.vault_dir / "proyectos" / "📋 RADAR DE TAREAS Y DEUDA TECNICA.md"
        radar_file.parent.mkdir(parents=True, exist_ok=True)

        date_str = data.get("date", datetime.now().strftime("%Y-%m-%d %H:%M"))
        total = data.get("total_items", 0)
        num_projs = data.get("projects_count", 0)
        tags = data.get("tag_counts", {})
        projects = data.get("projects", {})

        criticos = tags.get("FIXME", 0) + tags.get("BUG", 0)
        todos = tags.get("TODO", 0)
        mejoras = tags.get("HACK", 0) + tags.get("REFACTOR", 0) + tags.get("OPTIMIZE", 0)

        lines = [
            "---",
            "tags: [radar, tareas, todos, deuda-tecnica, gobernanza, automatizacion]",
            f"actualizado: {date_str}",
            "tipo: radar-codigo",
            "---",
            "",
            "# 📋 Radar de Tareas y Deuda Técnica del Ecosistema",
            "",
            "> [!summary] Telemetría Consolidada de Código Local",
            f"> **Total de Tareas Detectadas:** `{total}` | **Proyectos con Tareas:** `{num_projs}`",
            f"> 🔴 **Críticos (FIXME/BUG):** `{criticos}` | 🟡 **Pendientes (TODO):** `{todos}` | 🔵 **Mejoras (HACK/REFACTOR):** `{mejoras}`",
            "",
            "---",
            ""
        ]

        if not projects:
            lines.append("🎉 **¡Excelente! No se encontraron comentarios TODO ni FIXME pendientes en tus repositorios.**\n")
        else:
            # Ordenar proyectos alfabéticamente
            for pname in sorted(projects.keys()):
                items = projects[pname]
                lines.append(f"## 📂 [[{pname}]] ({len(items)} items)")
                lines.append("")

                for item in items:
                    tag = item["tag"]
                    icon = "🔴" if tag in ("FIXME", "BUG") else ("🟡" if tag == "TODO" else "🔵")
                    lines.append(f"- [ ] {icon} **{tag}** `{item['file']}:{item['line']}` — {item['message']}")
                lines.append("")

        radar_file.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"Reporte de radar de tareas escrito en: {radar_file}")
        return radar_file
