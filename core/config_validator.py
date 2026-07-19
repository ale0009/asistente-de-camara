"""
config_validator.py — Validación mínima de config.yaml al arrancar NOVA.

main.py y los motores de core/ acceden a varias claves de config.yaml por
índice directo (self.config['camera']['camera_index'], etc.) en vez de con
.get() con default. Si falta una clave, eso revienta con un KeyError crudo
en medio de NovaAssistant.__init__, sin ningún mensaje que le diga al
usuario qué corregir. Esta validación corre justo después de cargar el
YAML y convierte esos posibles KeyError en una lista de errores legibles
ANTES de que el resto del arranque los toque.

No se usa una librería de schema (pydantic, cerberus, etc.) a propósito:
para un dict anidado de este tamaño, mantenido por una sola persona, sería
más código y una dependencia nueva por un beneficio marginal frente a un
puñado de checks explícitos.
"""

import re

_RESOLUTION_RE = re.compile(r"^\d+x\d+$")


def validate_config(cfg: dict) -> list:
    """Devuelve una lista de mensajes de error (vacía si config.yaml está bien).

    No lanza excepciones — el llamador decide qué hacer con la lista
    (loggear y salir, en el caso de main.py).
    """
    errors = []

    if not isinstance(cfg, dict):
        return ["config.yaml está vacío o no es un mapa YAML válido."]

    # ─── Secciones que main.py necesita como dict no-nulo ──────────────────
    for section in ("camera", "voice", "gestures", "obsidian"):
        value = cfg.get(section)
        if value is None:
            errors.append(f"Falta la sección '{section}:' en config.yaml.")
        elif not isinstance(value, dict):
            errors.append(f"La sección '{section}:' debe ser un mapa (clave: valor), no {type(value).__name__}.")

    camera = cfg.get("camera") or {}
    if isinstance(camera, dict):
        if camera.get("camera_index") is None:
            errors.append("Falta camera.camera_index en config.yaml.")
        resolution = camera.get("resolution")
        if resolution is None:
            errors.append("Falta camera.resolution en config.yaml.")
        elif not _RESOLUTION_RE.match(str(resolution)):
            errors.append(
                f"camera.resolution debe tener formato 'anchoxalto' (ej. 640x360); valor actual: '{resolution}'."
            )
        if camera.get("osc_host") is None:
            errors.append("Falta camera.osc_host en config.yaml.")
        if camera.get("osc_port") is None:
            errors.append("Falta camera.osc_port en config.yaml.")

    obsidian = cfg.get("obsidian") or {}
    if isinstance(obsidian, dict):
        if not obsidian.get("vault_path"):
            errors.append("Falta obsidian.vault_path en config.yaml.")
        if not obsidian.get("nova_folder"):
            errors.append("Falta obsidian.nova_folder en config.yaml.")
        if obsidian.get("log_voice_commands") is None:
            errors.append("Falta obsidian.log_voice_commands en config.yaml (usa true o false).")
        if obsidian.get("log_gestures") is None:
            errors.append("Falta obsidian.log_gestures en config.yaml (usa true o false).")

    return errors
