import os
import datetime
import logging

logger = logging.getLogger(__name__)

class ObsidianLogger:
    """
    Escribe directamente en el Vault de Obsidian del usuario.
    Mantiene un diario automático de las interacciones con NOVA.
    """
    def __init__(self, vault_path: str, base_folder: str = "NOVA"):
        self.vault_path = vault_path
        self.base_folder = base_folder
        self.nova_path = os.path.join(self.vault_path, self.base_folder)
        self.sessions_path = os.path.join(self.nova_path, "Sesiones")
        
        self._ensure_folders_exist()

    def _ensure_folders_exist(self):
        """Verifica que las carpetas requeridas existan en el vault."""
        try:
            if not os.path.exists(self.nova_path):
                os.makedirs(self.nova_path)
            if not os.path.exists(self.sessions_path):
                os.makedirs(self.sessions_path)
        except Exception as e:
            logger.error(f"Error creando carpetas de Obsidian: {e}")

    def log_action(self, source: str, content: str, action_taken: str = ""):
        """
        Añade una entrada al archivo de log del día actual.
        source: 'Voz', 'Gesto', 'Sistema'
        content: Lo que dijo el usuario o el gesto detectado.
        """
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        file_path = os.path.join(self.sessions_path, f"{today}.md")
        
        # Crear archivo con encabezado si no existe
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# Registro de NOVA - {today}\n\n")
                f.write("> Log generado automáticamente por NOVA AI.\n\n")
                f.write("## Timeline\n\n")
        
        # Formatear la entrada
        log_entry = f"- **[{timestamp}]** `[{source}]` "
        if source == "Voz":
            log_entry += f'🗣️ "{content}"'
        elif source == "Gesto":
            log_entry += f'✋ Gesto detectado: {content}'
        else:
            log_entry += f'⚙️ {content}'
            
        if action_taken:
            log_entry += f" ➡️ *{action_taken}*"
            
        log_entry += "\n"
        
        # Añadir al final del archivo
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
            logger.debug(f"Obsidian Log actualizado: {today}.md")
        except Exception as e:
            logger.error(f"Error escribiendo en Obsidian: {e}")
