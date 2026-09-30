# -*- coding: utf-8 -*-
"""
core/episodic_memory.py — Memoria Episódica Local y Continua de NOVA
====================================================================
Almacena eventos, observaciones visuales, comandos y decisiones en una
base de datos SQLite ligera y soberana (100% local, cero telemetría externa).
Sincroniza resúmenes episódicos con la bóveda de Obsidian del usuario.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path.home() / "Datos" / "Vault-Obsidian" / "NOVA" / "nova_memory.db"

class EpisodicMemory:
    """
    Gestor de memoria episódica en SQLite para registrar la actividad del usuario,
    observaciones de la cámara, decisiones tomadas y enlaces con proyectos y Hana.
    """
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self):
        """Inicializa las tablas e índices si no existen."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS episodes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        session_id TEXT NOT NULL,
                        source TEXT NOT NULL,
                        action TEXT NOT NULL,
                        summary TEXT NOT NULL,
                        details TEXT,
                        tags TEXT
                    );
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_episodes_time ON episodes(timestamp);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_episodes_source ON episodes(source);")
                conn.commit()
            logger.info(f"Memoria episódica conectada en: {self.db_path}")
        except Exception as e:
            logger.error(f"Error inicializando base de datos de memoria episódica: {e}")

    def log_event(self, source: str, action: str, summary: str, details: Optional[Any] = None, tags: Optional[str] = None) -> int:
        """Registra un nuevo episodio en la memoria continua."""
        now_iso = datetime.now().isoformat()
        details_str = json.dumps(details, ensure_ascii=False) if isinstance(details, (dict, list)) else str(details or "")
        
        try:
            with self._get_connection() as conn:
                cur = conn.execute("""
                    INSERT INTO episodes (timestamp, session_id, source, action, summary, details, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (now_iso, self.session_id, source, action, summary, details_str, tags or ""))
                conn.commit()
                return cur.lastrowid
        except Exception as e:
            logger.error(f"Error registrando episodio en memoria: {e}")
            return -1

    def get_recent_events(self, limit: int = 10, source: Optional[str] = None) -> List[Dict]:
        """Recupera los eventos más recientes registrados."""
        query = "SELECT id, timestamp, session_id, source, action, summary, details, tags FROM episodes"
        params = []
        if source:
            query += " WHERE source = ?"
            params.append(source)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        results = []
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(query, params)
                for r in cur.fetchall():
                    results.append(dict(r))
        except Exception as e:
            logger.error(f"Error consultando episodios recientes: {e}")
        return results

    def search_memory(self, query_str: str, limit: int = 5) -> List[Dict]:
        """Busca episodios relevantes por coincidencia de texto en resumen o detalles."""
        sql = """
            SELECT id, timestamp, source, action, summary, details, tags
            FROM episodes
            WHERE summary LIKE ? OR details LIKE ? OR tags LIKE ?
            ORDER BY id DESC LIMIT ?
        """
        pattern = f"%{query_str}%"
        results = []
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(sql, (pattern, pattern, pattern, limit))
                for r in cur.fetchall():
                    results.append(dict(r))
        except Exception as e:
            logger.error(f"Error buscando en memoria episódica: {e}")
        return results

    def get_daily_summary(self, date_str: Optional[str] = None) -> str:
        """Genera un resumen en lenguaje natural de la actividad de una fecha específica (por defecto hoy)."""
        target_date = date_str or datetime.now().strftime("%Y-%m-%d")
        sql = """
            SELECT source, action, summary, timestamp
            FROM episodes
            WHERE timestamp LIKE ?
            ORDER BY id ASC
        """
        pattern = f"{target_date}%"
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(sql, (pattern,))
                rows = cur.fetchall()

            if not rows:
                return f"No hay actividad registrada en la memoria para el día {target_date}."

            total = len(rows)
            sources = {}
            for r in rows:
                src = r["source"]
                sources[src] = sources.get(src, 0) + 1

            summary_lines = [f"Actividad del día {target_date} ({total} eventos registrados):"]
            for src, count in sources.items():
                summary_lines.append(f"- {src.capitalize()}: {count} eventos")

            summary_lines.append("\nÚltimas acciones destacadas:")
            for r in rows[-5:]:
                t_short = r["timestamp"][11:16]
                summary_lines.append(f"  [{t_short}] {r['summary']}")

            return "\n".join(summary_lines)
        except Exception as e:
            logger.error(f"Error generando resumen diario: {e}")
            return f"Hubo un error al compilar el resumen del día: {e}"

    def export_to_obsidian(self, vault_path: Optional[Path] = None, date_str: Optional[str] = None) -> str:
        """Exporta el reporte estructurado de episodios a una nota en la bóveda de Obsidian."""
        v_path = Path(vault_path) if vault_path else Path.home() / "Datos" / "Vault-Obsidian"
        target_date = date_str or datetime.now().strftime("%Y-%m-%d")
        out_dir = v_path / "NOVA" / "Memoria"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"Memoria_{target_date}.md"

        events = []
        sql = "SELECT timestamp, source, action, summary, details, tags FROM episodes WHERE timestamp LIKE ? ORDER BY id ASC"
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute(sql, (f"{target_date}%",))
                events = [dict(r) for r in cur.fetchall()]
        except Exception as e:
            return f"Error leyendo base de datos: {e}"

        if not events:
            return "No hay eventos para exportar hoy."

        md = [
            "---",
            f"fecha: {target_date}",
            "tipo: memoria-episodica",
            "tags: [nova, memoria, sesiones, telemetria]",
            "---",
            f"# 🧠 Registro de Memoria Episódica — NOVA ({target_date})",
            "",
            "> [!info] Resumen de Sesión Soberana",
            f"> Total de episodios capturados: **{len(events)}**",
            "",
            "## ⏱️ Cronología de Eventos y Observaciones",
            "| Hora | Canal | Acción | Resumen |",
            "|---|---|---|---|"
        ]

        for ev in events:
            hora = ev["timestamp"][11:19]
            md.append(f"| `{hora}` | **{ev['source']}** | `{ev['action']}` | {ev['summary']} |")

        md.append("\n## 🔍 Detalle Extendido de Observaciones")
        for ev in events:
            if ev.get("details") and len(str(ev["details"])) > 10:
                hora = ev["timestamp"][11:19]
                md.append(f"\n### [{hora}] {ev['action']} ({ev['source']})")
                md.append(f"**Resumen:** {ev['summary']}")
                md.append(f"```text\n{ev['details']}\n```")

        try:
            out_file.write_text("\n".join(md), encoding="utf-8")
            logger.info(f"Memoria diaria exportada a Obsidian: {out_file}")
            return f"Memoria sincronizada con Obsidian: {out_file.name}"
        except Exception as e:
            logger.error(f"Error escribiendo nota de memoria en Obsidian: {e}")
            return f"Error guardando en Obsidian: {e}"
