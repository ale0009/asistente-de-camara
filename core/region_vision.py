# -*- coding: utf-8 -*-
"""
Visión por Región Bajo Demanda para NOVA (core/region_vision.py).
Permite seleccionar interactivamente un área de la pantalla con el ratón (Super+Shift+S),
la analiza con VLM local optimizado y copia el resultado directo al portapapeles.
"""
import os
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("NOVA.RegionVision")

TEMP_ROI_PATH = "/tmp/nova_roi.png"


class RegionVision:
    def __init__(self, ollama_bridge=None, temp_path: str = TEMP_ROI_PATH):
        self.ollama = ollama_bridge
        self.temp_path = Path(temp_path)

    def capture_screen_region(self) -> bool:
        """Invoca la herramienta nativa de KDE (spectacle -r) para selección interactiva de área."""
        if self.temp_path.exists():
            try:
                self.temp_path.unlink()
            except OSError:
                pass

        try:
            # -r: rectangular region
            # -b: background (no abrir la ventana GUI de Spectacle)
            # -n: non-notifying
            # -o: output file
            res = subprocess.run(
                ["spectacle", "-r", "-b", "-n", "-o", str(self.temp_path)],
                capture_output=True, timeout=30
            )
            return self.temp_path.exists() and self.temp_path.stat().st_size > 0
        except subprocess.TimeoutExpired:
            logger.warning("Selección de región cancelada o tiempo agotado.")
            return False
        except Exception as e:
            logger.error(f"Error al capturar región con spectacle: {e}")
            return False

    def copy_to_clipboard(self, text: str) -> bool:
        """Copia texto al portapapeles del sistema (Wayland wl-copy o X11 xclip)."""
        if not text:
            return False
        try:
            if shutil.which("wl-copy"):
                proc = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE, text=True)
                proc.communicate(input=text)
                return proc.returncode == 0
            elif shutil.which("xclip"):
                proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE, text=True)
                proc.communicate(input=text)
                return proc.returncode == 0
        except Exception as e:
            logger.error(f"Error copiando al portapapeles: {e}")
        return False

    def send_notification(self, title: str, message: str):
        """Emite una notificación nativa de escritorio KDE con notify-send."""
        try:
            subprocess.run(["notify-send", "-a", "NOVA Copilot", "-i", "camera-photo", title, message], check=False)
        except Exception:
            pass

    def inspect_region(self, mode: str = "auto") -> Dict[str, Any]:
        """
        Ejecuta el flujo completo:
        1. Selección interactiva de región.
        2. Inferencia VLM local ultra-rápida.
        3. Copiado directo al portapapeles y notificación.
        """
        if not self.capture_screen_region():
            return {
                "success": False,
                "message": "Captura de región cancelada."
            }

        import cv2
        image_bgr = cv2.imread(str(self.temp_path))
        if image_bgr is None:
            return {"success": False, "message": "No se pudo leer la imagen capturada."}

        # Prompt adaptado al modo
        if mode == "diagram":
            prompt = (
                "Analiza este diagrama o arquitectura. Extrae los nodos y relaciones "
                "y genera ÚNICAMENTE el código Mermaid válido dentro de ```mermaid ... ```."
            )
        elif mode == "ocr":
            prompt = (
                "Transcribe de forma fiel y exacta todo el texto, código o fórmulas "
                "presentes en esta imagen en formato Markdown limpio."
            )
        else: # auto
            prompt = (
                "Analiza esta región de pantalla de un entorno técnico. "
                "Si es un diagrama, genera el bloque Mermaid correspondiente. "
                "Si es código o un error, explica la causa y el fix exacto en 2 oraciones. "
                "Si es texto o documentación, devuélvelo en Markdown limpio."
            )

        if not self.ollama:
            return {"success": False, "message": "Ollama no está conectado para análisis visual."}

        result = self.ollama.query_vision(prompt, image_bgr)
        if not result or "No encontré" in result:
            result = "No se pudo extraer información clara de la región seleccionada."

        # Copiar al portapapeles automáticamente
        self.copy_to_clipboard(result)
        self.send_notification("NOVA Visión ✨", "Resultado copiado al portapapeles listo para pegar.")

        return {
            "success": True,
            "result": result,
            "mode": mode,
            "message": "Análisis completado y copiado al portapapeles."
        }
