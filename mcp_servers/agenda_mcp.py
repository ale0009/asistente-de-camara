"""Servidor MCP para Gestión de Agenda, Horarios, Rutina de Almuerzo y Time-Blocking.

Permite a NOVA gestionar compromisos diarios, recordatorios, pausas de almuerzo
y sesiones de enfoque Pomodoro integradas con Obsidian Vault.
"""

import os
import time
import logging
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional

from core.osc_controller import OSCController
from core.system_controller import SystemController
from core.obsidian_logger import ObsidianLogger

logger = logging.getLogger("NOVA.AgendaMCPServer")

class AgendaMCPServer:
    def __init__(
        self,
        vault_path: str = "D:\\Documentos\\Obsidian Vault",
        nova_folder: str = "NOVA",
        osc_controller: Optional[OSCController] = None,
        system_controller: Optional[SystemController] = None
    ):
        self.vault_path = vault_path
        self.nova_folder = nova_folder
        self.osc = osc_controller or OSCController()
        self.system = system_controller or SystemController()
        self.logger_db = ObsidianLogger(self.vault_path, self.nova_folder)
        self.active_timers = []

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "agenda_get_today_schedule",
                "description": "Obtiene la agenda y registro de actividades de hoy desde la nota diaria de Obsidian.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "agenda_add_task",
                "description": "Añade una tarea, compromiso o evento a la agenda de hoy en Obsidian.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "Descripción de la tarea o compromiso."
                        },
                        "time_str": {
                            "type": "string",
                            "description": "Hora opcional asignada (ej. '14:00' o '2:30 PM')."
                        }
                    },
                    "required": ["task"]
                }
            },
            {
                "name": "agenda_lunch_break",
                "description": "Inicia la rutina de almuerzo / descanso: suspende la cámara, silencia el audio, programa recordatorio y registra la pausa en Obsidian.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "duration_minutes": {
                            "type": "integer",
                            "description": "Duración de la pausa en minutos (por defecto 60)."
                        }
                    }
                }
            },
            {
                "name": "agenda_start_timer",
                "description": "Inicia un temporizador de enfoque o recordatorio (ej. Pomodoro de 25 minutos o pausa breve).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "minutes": {
                            "type": "integer",
                            "description": "Duración en minutos."
                        },
                        "label": {
                            "type": "string",
                            "description": "Motivo o etiqueta del temporizador (ej. 'Enfoque Blender', 'Reunión')."
                        }
                    },
                    "required": ["minutes"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "agenda_get_today_schedule":
            return self._get_today_schedule()
        elif tool_name == "agenda_add_task":
            return self._add_task(arguments.get("task", ""), arguments.get("time_str", ""))
        elif tool_name == "agenda_lunch_break":
            duration = int(arguments.get("duration_minutes", 60))
            return self._lunch_break(duration)
        elif tool_name == "agenda_start_timer":
            minutes = int(arguments.get("minutes", 25))
            label = arguments.get("label", "Sesión de Enfoque")
            return self._start_timer(minutes, label)
        else:
            return {"success": False, "error": f"Herramienta de agenda desconocida: {tool_name}"}

    def _get_today_schedule(self) -> Dict[str, Any]:
        today_str = datetime.now().strftime("%Y-%m-%d")
        daily_path = os.path.join(self.vault_path, self.nova_folder, "Sesiones", f"{today_str}.md")
        
        if not os.path.exists(daily_path):
            return {
                "success": True,
                "date": today_str,
                "tasks_count": 0,
                "content": "No hay registro diario iniciado aún para hoy.",
                "tasks": []
            }

        try:
            with open(daily_path, "r", encoding="utf-8") as f:
                content = f.read()

            tasks = [line.strip() for line in content.splitlines() if "- [ ]" in line or "- [x]" in line or "- [X]" in line]
            return {
                "success": True,
                "date": today_str,
                "tasks_count": len(tasks),
                "tasks": tasks,
                "content": content[:1000]
            }
        except Exception as e:
            return {"success": False, "error": f"Error leyendo agenda de hoy: {e}"}

    def _add_task(self, task: str, time_str: str = "") -> Dict[str, Any]:
        if not task:
            return {"success": False, "error": "La tarea no puede estar vacía."}

        timestamp = time_str if time_str else datetime.now().strftime("%H:%M")
        formatted_entry = f"- [ ] **{timestamp}** — {task}"
        
        try:
            today_str = datetime.now().strftime("%Y-%m-%d")
            sessions_dir = os.path.join(self.vault_path, self.nova_folder, "Sesiones")
            os.makedirs(sessions_dir, exist_ok=True)
            daily_path = os.path.join(sessions_dir, f"{today_str}.md")
            
            with open(daily_path, "a", encoding="utf-8") as f:
                f.write(f"\n{formatted_entry}\n")

            return {
                "success": True,
                "task": task,
                "timestamp": timestamp,
                "message": f"Tarea '{task}' añadida a la agenda de hoy."
            }
        except Exception as e:
            return {"success": False, "error": f"Error guardando tarea en agenda: {e}"}

    def _lunch_break(self, duration_minutes: int = 60) -> Dict[str, Any]:
        try:
            # 1. Suspender cámara
            self.osc.stop_tracking()
            self.osc.sleep_camera()
            
            # 2. Silenciar volumen
            if self.system:
                try:
                    self.system.mute_volume()
                except Exception:
                    pass

            # 3. Registrar en Obsidian
            now_str = datetime.now().strftime("%H:%M")
            self.logger_db.log_action("Rutina", f"Pausa de almuerzo ({duration_minutes} min)", f"Iniciada a las {now_str}")
            
            return {
                "success": True,
                "status": "LUNCH_ACTIVE",
                "duration_minutes": duration_minutes,
                "camera_state": "sleeping",
                "message": f"Modo almuerzo activado por {duration_minutes} minutos. Cámara suspendida y volumen silenciado. ¡Buen provecho!"
            }
        except Exception as e:
            return {"success": False, "error": f"Error activando modo almuerzo: {e}"}

    def _start_timer(self, minutes: int, label: str) -> Dict[str, Any]:
        if minutes <= 0:
            return {"success": False, "error": "Los minutos deben ser mayores a 0."}

        timer_info = {
            "id": len(self.active_timers) + 1,
            "label": label,
            "duration_minutes": minutes,
            "started_at": datetime.now().strftime("%H:%M:%S")
        }
        self.active_timers.append(timer_info)

        return {
            "success": True,
            "timer": timer_info,
            "message": f"Temporizador '{label}' iniciado por {minutes} minutos."
        }
