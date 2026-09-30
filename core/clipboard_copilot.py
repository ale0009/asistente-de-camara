# -*- coding: utf-8 -*-
"""
Copiloto de Portapapeles para NOVA (core/clipboard_copilot.py).
Permite refactorizar, explicar o corregir código y datos copiados al portapapeles
utilizando modelos locales (qwen2.5-coder:1.5b) sin abrir navegadores ni aplicaciones pesadas.
"""
import subprocess
import logging
from typing import Dict, Any, Optional

from core.ollama_bridge import OllamaBridge

logger = logging.getLogger("NOVA.ClipboardCopilot")

ICON_PATH = "/home/alejandro/Datos/Projects/asistente-de-camara/assets/nova_icon.png"
MODEL_CODER = "qwen2.5-coder:1.5b"
MODEL_CHAT = "granite4:tiny-h"


class ClipboardCopilot:
    def __init__(self, ollama_bridge: Optional[OllamaBridge] = None):
        self.ollama = ollama_bridge or OllamaBridge()

    def get_clipboard_text(self) -> str:
        """Obtiene el texto actual del portapapeles usando wl-paste."""
        try:
            res = subprocess.run(["wl-paste", "--no-newline"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception as e:
            logger.warning(f"Fallo al leer portapapeles con wl-paste: {e}")
        return ""

    def set_clipboard_text(self, text: str) -> bool:
        """Copia texto al portapapeles usando wl-copy."""
        try:
            proc = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE, text=True)
            proc.communicate(input=text, timeout=2)
            return proc.returncode == 0
        except Exception as e:
            logger.error(f"Fallo al escribir en portapapeles con wl-copy: {e}")
            return False

    def notify(self, title: str, message: str):
        """Emite una notificación sutil de escritorio."""
        try:
            subprocess.Popen([
                "notify-send", "-a", "NOVA Copilot",
                "-i", ICON_PATH,
                title, message,
                "-t", "4000"
            ])
        except Exception:
            pass

    def refactor(self) -> Dict[str, Any]:
        """Toma el código del portapapeles y genera una versión refactorizada y limpia."""
        text = self.get_clipboard_text()
        if not text:
            return {"success": False, "message": "El portapapeles está vacío o no contiene texto."}

        self.notify("NOVA: Refactorizando...", "Procesando código del portapapeles con IA local")

        prompt = (
            "Eres un experto en ingeniería de software. Refactoriza el siguiente código para que sea más limpio, "
            "óptimo, idiomático y robusto. Mantén el mismo lenguaje. Devuelve ÚNICAMENTE el bloque de código final "
            "o el código directo sin saludos ni introducciones:\n\n"
            f"```\n{text}\n```"
        )

        output = self.ollama.query(prompt, model=MODEL_CODER, max_tokens=700).strip()

        # Limpiar bloques markdown si están presentes
        if output.startswith("```") and output.endswith("```"):
            lines = output.splitlines()
            output = "\n".join(lines[1:-1]).strip()

        if output:
            self.set_clipboard_text(output)
            self.notify("✓ Código Refactorizado", "El código mejorado se ha copiado a tu portapapeles (Ctrl+V).")
            return {"success": True, "message": "Código refactorizado copiado al portapapeles.", "content": output}
        
        return {"success": False, "message": "No se pudo generar la refactorización."}

    def explain(self) -> Dict[str, Any]:
        """Explica el código o error del portapapeles en 3-4 viñetas concisas en español."""
        text = self.get_clipboard_text()
        if not text:
            return {"success": False, "message": "El portapapeles está vacío o no contiene texto."}

        self.notify("NOVA: Analizando...", "Explicando contenido del portapapeles")

        prompt = (
            "Analiza el siguiente fragmento de código, error o texto copiado del desarrollador. "
            "Explica exactamente qué hace o por qué ocurre en máximo 3 o 4 viñetas breves, claras y técnicas en español. "
            "Sé directo, sin rellenos:\n\n"
            f"{text[:2500]}"
        )

        explanation = self.ollama.query(prompt, model=MODEL_CHAT, max_tokens=500).strip()
        if explanation:
            # Copiar también la explicación al portapapeles
            self.set_clipboard_text(explanation)
            self.notify("✓ Explicación Lista", "Explicación generada y copiada al portapapeles.")
            return {"success": True, "message": "Explicación lista.", "content": explanation}

        return {"success": False, "message": "No se pudo generar la explicación."}
