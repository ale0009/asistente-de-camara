"""Servidor MCP para Control de Cámara OBSBOT y Visión Multimodal.

Proporciona herramientas estandarizadas para control mecánico PTZ (OSC UDP),
modos de escena, tracking inteligente y descripción visual en vivo con Moondream.
"""

import logging
from typing import Dict, Any, List, Optional
from core.osc_controller import OSCController
from core.camera import CameraController
from core.ollama_bridge import OllamaBridge

logger = logging.getLogger("NOVA.CameraMCPServer")

class CameraMCPServer:
    def __init__(
        self,
        osc_controller: Optional[OSCController] = None,
        camera_controller: Optional[CameraController] = None,
        ollama_bridge: Optional[OllamaBridge] = None
    ):
        self.osc = osc_controller or OSCController()
        self.camera = camera_controller
        self.ollama = ollama_bridge or OllamaBridge()

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "camera_wake_sleep",
                "description": "Despierta o suspende la cámara física OBSBOT para ahorro de energía y privacidad.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["wake", "sleep"],
                            "description": "Acción a realizar: 'wake' para encender/despertar, 'sleep' para suspender."
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "camera_set_tracking",
                "description": "Activa o desactiva el seguimiento inteligente de personas (AI tracking / lock) en la cámara.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "enabled": {
                            "type": "boolean",
                            "description": "True para activar seguimiento, False para pausarlo/desactivarlo."
                        }
                    },
                    "required": ["enabled"]
                }
            },
            {
                "name": "camera_set_zoom",
                "description": "Ajusta el nivel de zoom digital/analógico de la cámara de 0 a 100 por ciento.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "level": {
                            "type": "number",
                            "description": "Porcentaje de zoom deseado (0.0 a 100.0)."
                        }
                    },
                    "required": ["level"]
                }
            },
            {
                "name": "camera_move_gimbal",
                "description": "Mueve el gimbal motorizado de la cámara en una dirección ('left', 'right', 'up', 'down') o lo centra ('reset').",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "direction": {
                            "type": "string",
                            "enum": ["left", "right", "up", "down", "reset"],
                            "description": "Dirección del movimiento del gimbal."
                        }
                    },
                    "required": ["direction"]
                }
            },
            {
                "name": "camera_trigger_preset",
                "description": "Mueve la cámara a una posición preestablecida guardada (Preset 1, 2 o 3).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "preset_number": {
                            "type": "integer",
                            "enum": [1, 2, 3],
                            "description": "Número del preset de cámara (1, 2 o 3)."
                        }
                    },
                    "required": ["preset_number"]
                }
            },
            {
                "name": "camera_set_scene_mode",
                "description": "Configura un modo de escena de cámara completo: 'presentation' (despierta y activa tracking), 'work' (centra gimbal y pausa tracking), o 'rest' (suspende cámara).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mode": {
                            "type": "string",
                            "enum": ["presentation", "work", "rest"],
                            "description": "Modo de escena: 'presentation', 'work' o 'rest'."
                        }
                    },
                    "required": ["mode"]
                }
            },
            {
                "name": "camera_describe_scene",
                "description": "Captura el frame en vivo de la cámara y ejecuta inferencia visual con IA para responder preguntas sobre la escena.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Pregunta o instrucción de observación (ej. 'describe qué hay en la mesa', 'qué ves')."
                        }
                    }
                }
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "camera_wake_sleep":
            action = arguments.get("action", "wake")
            if action == "wake":
                self.osc.wake_camera()
                return {"success": True, "message": "Cámara despertada exitosamente."}
            else:
                self.osc.sleep_camera()
                return {"success": True, "message": "Cámara suspendida exitosamente."}

        elif tool_name == "camera_set_tracking":
            enabled = bool(arguments.get("enabled", True))
            if enabled:
                self.osc.track_human()
                return {"success": True, "message": "Seguimiento inteligente activado."}
            else:
                self.osc.stop_tracking()
                return {"success": True, "message": "Seguimiento inteligente pausado."}

        elif tool_name == "camera_set_zoom":
            level = float(arguments.get("level", 0.0))
            level_clamped = max(0.0, min(100.0, level))
            self.osc.set_zoom(level_clamped)
            return {"success": True, "zoom_level": level_clamped, "message": f"Zoom ajustado al {int(level_clamped)}%."}

        elif tool_name == "camera_move_gimbal":
            direction = arguments.get("direction", "reset")
            if direction == "left":
                self.osc.look_left()
            elif direction == "right":
                self.osc.look_right()
            elif direction == "up":
                self.osc.look_up()
            elif direction == "down":
                self.osc.look_down()
            else:
                self.osc.gimbal_reset()
            return {"success": True, "direction": direction, "message": f"Gimbal movido hacia '{direction}'."}

        elif tool_name == "camera_trigger_preset":
            preset = int(arguments.get("preset_number", 1))
            self.osc.trigger_preset(preset)
            return {"success": True, "preset": preset, "message": f"Posición preset {preset} activada."}

        elif tool_name == "camera_set_scene_mode":
            mode = arguments.get("mode", "presentation")
            if mode == "presentation":
                self.osc.wake_camera()
                self.osc.track_human()
                self.osc.set_zoom(0.0)
                return {"success": True, "mode": mode, "message": "Modo Presentación activado (cámara despierta y tracking encendido)."}
            elif mode == "work":
                self.osc.stop_tracking()
                self.osc.gimbal_reset()
                return {"success": True, "mode": mode, "message": "Modo Trabajo activado (tracking pausado y gimbal centrado)."}
            elif mode == "rest":
                self.osc.stop_tracking()
                self.osc.sleep_camera()
                return {"success": True, "mode": mode, "message": "Modo Descanso activado (cámara suspendida)."}
            else:
                return {"success": False, "error": f"Modo de escena desconocido: '{mode}'."}

        elif tool_name == "camera_describe_scene":
            question = arguments.get("question", "Describe brevemente en español lo que ves en la escena.")
            frame = getattr(self.camera, "current_frame", None) if self.camera else None
            if frame is None:
                return {
                    "success": False,
                    "error": "La cámara no está capturando video actualmente o no está inicializada."
                }
            try:
                description = self.ollama.query_vision(question, frame, model="moondream")
                return {"success": True, "question": question, "description": description}
            except Exception as e:
                logger.error(f"Error en visión multimodal: {e}")
                return {"success": False, "error": f"Error ejecutando visión multimodal: {e}"}

        else:
            return {"success": False, "error": f"Herramienta de cámara desconocida: '{tool_name}'."}
