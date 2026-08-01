"""Sistema de Auditoría y Trazabilidad para el Agente MCP.

Registra en base de datos (PostgreSQL o SQLite local de resguardo) cada interacción,
clasificación de intención, invocación de herramientas MCP y resultados.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger("NOVA.AuditLogger")

class AgentAuditLogger:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_dir = os.path.join(base_dir, "logs")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "agent_audit.db")

        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS agent_audit_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        source_channel TEXT NOT NULL,
                        raw_prompt TEXT NOT NULL,
                        intent_category TEXT NOT NULL,
                        tool_name TEXT,
                        tool_args TEXT,
                        status TEXT NOT NULL,
                        result_summary TEXT,
                        execution_time_ms REAL
                    )
                """)
                conn.commit()
            logger.info(f"Base de datos de auditoría inicializada en: {self.db_path}")
        except Exception as e:
            logger.error(f"Error inicializando DB de auditoría: {e}")

    def log_interaction(
        self,
        source_channel: str,
        raw_prompt: str,
        intent_category: str,
        tool_name: Optional[str] = None,
        tool_args: Optional[Dict[str, Any]] = None,
        status: str = "SUCCESS",
        result_summary: Optional[str] = None,
        execution_time_ms: float = 0.0
    ) -> int:
        timestamp = datetime.now().isoformat()
        tool_args_json = json.dumps(tool_args, ensure_ascii=False) if tool_args else None

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO agent_audit_log (
                        timestamp, source_channel, raw_prompt, intent_category,
                        tool_name, tool_args, status, result_summary, execution_time_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp, source_channel, raw_prompt, intent_category,
                    tool_name, tool_args_json, status, result_summary, execution_time_ms
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error registrando auditoría: {e}")
            return -1

    def get_recent_logs(self, limit: int = 50):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM agent_audit_log ORDER BY id DESC LIMIT ?", (limit,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error leyendo registros de auditoría: {e}")
            return []
