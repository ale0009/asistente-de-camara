# -*- coding: utf-8 -*-
"""
Gobernador Inteligente de Hardware y VRAM para NOVA (core/hardware_governor.py).
Supervisa la GPU GTX 1050 (3 GB VRAM), previene colisiones térmicas y OOM liberando
Ollama antes de lanzar Blender o ComfyUI, y orquesta turbo-fan y centinela.
"""
import os
import re
import json
import logging
import subprocess
from typing import Dict, Any, List

logger = logging.getLogger("NOVA.HardwareGovernor")


class HardwareGovernor:
    def __init__(self, ollama_host: str = "http://127.0.0.1:11434"):
        self.ollama_host = ollama_host

    def get_telemetry(self) -> Dict[str, Any]:
        """Obtiene métricas en tiempo real de CPU, RAM, GPU y temperaturas vía Centinela y nvidia-smi."""
        telemetry = {
            "cpu_percent": 0.0,
            "ram_percent": 0.0,
            "gpu_temp_c": 40,
            "gpu_vram_used_mb": 0,
            "gpu_vram_total_mb": 3072,
            "battery_percent": 100,
            "status": "normal"
        }

        # 1. Intentar con centinela estado
        try:
            res = subprocess.run(["centinela", "estado"], capture_output=True, text=True, timeout=3)
            out = res.stdout
            if out:
                cpu_m = re.search(r'CPU Total\s*:\s*([\d\.]+)%', out)
                ram_m = re.search(r'RAM Física\s*:\s*([\d\.]+)%', out)
                gpu_m = re.search(r'Temp / Uso\s*:\s*(\d+)°C.*?Carga GPU:\s*(\d+)%', out)
                bat_m = re.search(r'Batería\s*:\s*(\d+)%', out)

                if cpu_m: telemetry["cpu_percent"] = float(cpu_m.group(1))
                if ram_m: telemetry["ram_percent"] = float(ram_m.group(1))
                if gpu_m: telemetry["gpu_temp_c"] = int(gpu_m.group(1))
                if bat_m: telemetry["battery_percent"] = int(bat_m.group(1))
        except Exception as e:
            logger.debug(f"Error consultando centinela: {e}")

        # 2. VRAM exacta vía nvidia-smi
        try:
            smi_proc = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.used,memory.total,temperature.gpu", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=2
            )
            if smi_proc.returncode == 0 and smi_proc.stdout.strip():
                parts = [p.strip() for p in smi_proc.stdout.strip().split(",")]
                if len(parts) >= 3:
                    telemetry["gpu_vram_used_mb"] = int(parts[0])
                    telemetry["gpu_vram_total_mb"] = int(parts[1])
                    telemetry["gpu_temp_c"] = int(parts[2])
        except Exception:
            pass

        return telemetry

    def get_loaded_ollama_models(self) -> List[str]:
        """Consulta qué modelos están ocupando memoria VRAM/RAM en Ollama."""
        try:
            import requests
            resp = requests.get(f"{self.ollama_host}/api/ps", timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                return [m.get("name") for m in data.get("models", []) if m.get("name")]
        except Exception:
            pass
        return []

    def liberate_vram_for_heavy_app(self, app_name: str) -> Dict[str, Any]:
        """
        Detiene preventivamente modelos de Ollama si se va a abrir Blender, ComfyUI o Unity.
        Regla de MAQUINA.md: VRAM 3GB para todo. No caben Ollama + ComfyUI/Blender simultáneamente.
        """
        app_lower = app_name.lower()
        needs_liberation = any(k in app_lower for k in ["blender", "comfy", "unity", "unreal"])

        if not needs_liberation:
            return {"action_taken": "none", "liberated": False}

        loaded = self.get_loaded_ollama_models()
        stopped = []
        if loaded:
            logger.info(f"Liberando VRAM de Ollama ({loaded}) para dar paso a '{app_name}'...")
            for model in loaded:
                try:
                    subprocess.run(["ollama", "stop", model], capture_output=True, timeout=5)
                    stopped.append(model)
                except Exception as e:
                    logger.error(f"Error deteniendo modelo {model}: {e}")

        return {
            "action_taken": "ollama_stopped",
            "liberated": True,
            "models_stopped": stopped,
            "message": f"VRAM de GPU liberada (detenidos: {', '.join(stopped) if stopped else 'ninguno activo'})."
        }

    def set_turbo_fan(self, mode: str = "auto") -> bool:
        """Configura los ventiladores con turbo-fan (--turbo | --auto)."""
        turbo_bin = Path.home() / ".local" / "bin" / "turbo-fan"
        if not turbo_bin.exists():
            return False
        try:
            flag = "--turbo" if mode == "turbo" else "--auto"
            subprocess.run([str(turbo_bin), flag], capture_output=True, timeout=4)
            return True
        except Exception as e:
            logger.error(f"Error ajustando ventilador a {mode}: {e}")
            return False

    def launch_blender(self) -> str:
        """Libera VRAM y lanza Blender con aceleración NVIDIA dedicada (prime-run)."""
        lib_res = self.liberate_vram_for_heavy_app("blender")
        cmd = "/home/alejandro/.local/bin/prime-run blender"
        subprocess.Popen([cmd], shell=True)
        return f"Blender iniciado con PRIME offload en GTX 1050. {lib_res.get('message', '')}"
