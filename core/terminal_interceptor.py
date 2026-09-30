# -*- coding: utf-8 -*-
"""
Interceptor y Diagnóstico de Errores de Terminal para NOVA (core/terminal_interceptor.py).
Captura comandos fallidos y salidas de error (stderr), generando diagnósticos instantáneos
y comandos corregidos con modelos locales de código (Qwen2.5-Coder o Granite).
"""
import os
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("NOVA.TerminalInterceptor")

ERROR_BUFFER_FILE = "/tmp/nova_last_error.json"
BASH_HOOK_DIR = Path.home() / ".local" / "share" / "nova"
BASH_HOOK_FILE = BASH_HOOK_DIR / "bash_hook.sh"


class TerminalInterceptor:
    def __init__(self, ollama_bridge=None, buffer_file: str = ERROR_BUFFER_FILE):
        self.ollama = ollama_bridge
        self.buffer_file = Path(buffer_file)
        self._ensure_bash_hook_installed()

    def _ensure_bash_hook_installed(self):
        """Genera el script de integración para ~/.bashrc si no existe."""
        try:
            BASH_HOOK_DIR.mkdir(parents=True, exist_ok=True)
            hook_content = """# NOVA Terminal Error Interceptor Hook
# Este hook registra discretamente comandos que fallan para diagnóstico inmediato con 'nova fix' o Super+E

nova_preexec() {
    export _NOVA_LAST_CMD="$1"
    export _NOVA_CMD_TIME="$(date +%s)"
}

nova_precmd() {
    local exit_code=$?
    if [ $exit_code -ne 0 ] && [ -n "$_NOVA_LAST_CMD" ]; then
        local current_dir="$(pwd)"
        local timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
        
        # Guardar en buffer JSON para el asistente
        python3 -c "
import json, sys
data = {
    'cmd': sys.argv[1],
    'exit_code': int(sys.argv[2]),
    'cwd': sys.argv[3],
    'timestamp': sys.argv[4]
}
with open('/tmp/nova_last_error.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
" "$_NOVA_LAST_CMD" "$exit_code" "$current_dir" "$timestamp" 2>/dev/null &
    fi
}

# Registrar hooks en Bash
if [[ -z "$_NOVA_HOOK_LOADED" ]]; then
    trap 'nova_preexec "$BASH_COMMAND"' DEBUG
    PROMPT_COMMAND="nova_precmd${PROMPT_COMMAND:+; $PROMPT_COMMAND}"
    export _NOVA_HOOK_LOADED=1
fi
"""
            BASH_HOOK_FILE.write_text(hook_content, encoding="utf-8")
            logger.info(f"Hook de shell generado en: {BASH_HOOK_FILE}")
        except Exception as e:
            logger.error(f"Error generando hook de bash: {e}")

    def get_last_error(self) -> Optional[Dict[str, Any]]:
        """Lee el último error registrado en el buffer temporal."""
        if not self.buffer_file.exists():
            return None
        try:
            content = self.buffer_file.read_text(encoding="utf-8")
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error leyendo buffer de error: {e}")
            return None

    def record_manual_error(self, cmd: str, exit_code: int, error_output: str, cwd: str = None):
        """Permite registrar un error manualmente desde pipelines o subprocesos."""
        data = {
            "cmd": cmd,
            "exit_code": exit_code,
            "error_output": error_output,
            "cwd": cwd or os.getcwd(),
            "timestamp": str(subprocess.check_output(["date", "+%Y-%m-%d %H:%M:%S"], text=True).strip())
        }
        self.buffer_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def diagnose_last_error(self, model: str = "qwen2.5-coder:1.5b") -> Dict[str, Any]:
        """
        Analiza el último error y devuelve un diagnóstico estructurado:
        - causa (1 o 2 oraciones)
        - comando_sugerido (el comando listo para copiar/ejecutar)
        - explicacion
        """
        err_data = self.get_last_error()
        if not err_data:
            return {
                "success": False,
                "message": "No hay ningún comando fallido registrado recientemente en el terminal."
            }

        cmd = err_data.get("cmd", "")
        exit_code = err_data.get("exit_code", 1)
        cwd = err_data.get("cwd", "")
        error_output = err_data.get("error_output", "")

        prompt = f"""Eres un ingeniero experto en Linux Fedora, terminal Bash y desarrollo de software.
Analiza este comando fallido y su contexto:
- Directorio de trabajo: {cwd}
- Comando ejecutado: `{cmd}`
- Código de salida: {exit_code}
{f'- Salida de error: {error_output}' if error_output else ''}

Responde ÚNICAMENTE en este formato JSON exacto sin bloques markdown ni texto adicional:
{{
  "causa": "Explicación directa en español de qué falló (máximo 2 oraciones)",
  "comando_corregido": "comando exacto sugerido para resolverlo",
  "accion_inmediata": "explicación breve de qué hace el comando sugerido"
}}"""

        diagnosis = {
            "cmd_original": cmd,
            "exit_code": exit_code,
            "cwd": cwd,
            "timestamp": err_data.get("timestamp", ""),
            "causa": "Error al ejecutar el comando.",
            "comando_corregido": cmd,
            "accion_inmediata": "Revisar sintaxis y permisos."
        }

        if self.ollama:
            try:
                # Usar modelo de código local ultra-rápido (~43 tok/s)
                raw_resp = self.ollama.query(prompt, model=model, json_mode=True, max_tokens=220)
                parsed = json.loads(raw_resp)
                diagnosis.update(parsed)
                diagnosis["success"] = True
                return diagnosis
            except Exception as e:
                logger.error(f"Fallo al invocar Ollama para diagnóstico: {e}")

        # Fallback determinista si Ollama no está activo
        diagnosis["causa"] = f"El comando terminó con código de salida {exit_code}."
        diagnosis["success"] = True
        return diagnosis
