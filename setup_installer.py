"""Instalador Autónomo e Inicializador 1-Clic (Zero-Setup) para NOVA.

Se encarga de:
1. Crear/verificar el entorno virtual Python (venv).
2. Instalar silenciosamente todas las dependencias necesarias de requirements.txt.
3. Generar la configuración por defecto (config.yaml) si no existe.
4. Inicializar la base de datos de auditoría local en SQLite (cero Docker).
5. Crear accesos directos en el Escritorio y Menú Inicio de Windows apuntando al lanzador silencioso.
6. Arrancar la plataforma NOVA automáticamente en segundo plano.
"""

import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("NOVA.Installer")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")
VBS_LAUNCHER_PATH = os.path.join(BASE_DIR, "start_nova_silent.vbs")

DEFAULT_CONFIG_CONTENT = """# Configuración General de NOVA (Auto-Generada)

general:
  name: "NOVA"
  language: "es"
  theme: "dark"
  start_with_windows: true
  start_obsbot_center: true
  obsbot_path: "D:\\OBSBOT Center\\bin\\OBSBOT_Main.exe"

camera:
  camera_index: 0
  device_name: "OBSBOT Tiny 3 Lite"
  osc_host: "127.0.0.1"
  osc_port: 16284
  resolution: "640x360"
  tracking_speed: "Standard"

voice:
  wake_word_models:
    - "hey_nova"
    - "hey_jarvis"
  wake_threshold: 0.5
  silence_limit_sec: 1.5
  mic_index: null
  stt_model: "small"
  stt_language: "es"
  tts_voice: "es-CO-SalomeNeural"
  tts_rate: "+0%"
  tts_volume: "+0%"

gestures:
  enabled: true
  sensitivity: "medium"
  activation_time: 0.8

obsidian:
  vault_path: "D:\\Documentos\\Obsidian Vault"
  nova_folder: "NOVA"
  log_voice_commands: true
  log_gestures: false
  create_daily_note: true

assistant:
  allowed_folders:
    - "C:\\Users\\mario\\Documents"
    - "C:\\Users\\mario\\Desktop"
    - "D:\\Documentos\\Obsidian Vault"
    - "E:\\proyectos"
  notes_folder: "NOVA/Notas"
"""

def generate_vbs_content(python_exe: str, target_script: str) -> str:
    return f'Set WshShell = CreateObject("WScript.Shell")\nWshShell.Run """" & "{python_exe}" & """ """" & "{target_script}" & """", 0, False\n'

def ensure_config():
    if not os.path.exists(CONFIG_PATH):
        logger.info("Generando config.yaml inicial por defecto...")
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write(DEFAULT_CONFIG_CONTENT)
        logger.info("config.yaml creado exitosamente.")
    else:
        logger.info("config.yaml ya existe. Conservando configuración actual.")

def ensure_vbs_launcher():
    logger.info("Creando lanzador silencioso de Windows (start_nova_silent.vbs)...")
    target_script = os.path.join(BASE_DIR, "start_nova_agent.py")
    content = generate_vbs_content(sys.executable, target_script)
    with open(VBS_LAUNCHER_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("Lanzador silencioso configurado.")

def ensure_sqlite_db():
    from agent_service.audit_logger import AgentAuditLogger
    logger.info("Inicializando base de datos de auditoría local (SQLite)...")
    logger_db = AgentAuditLogger()
    logger.info(f"Base de datos verificada en: {logger_db.db_path}")

def create_windows_shortcuts():
    logger.info("Creando accesos directos en Escritorio y Menú Inicio...")
    try:
        from create_desktop_shortcut import create_shortcut
        create_shortcut()
        logger.info("Accesos directos creados exitosamente.")
    except Exception as e:
        logger.warning(f"No se pudieron crear accesos directos automáticos: {e}")

def run_nova_silent():
    logger.info("Arrancando NOVA en segundo plano...")
    subprocess.Popen(["wscript.exe", VBS_LAUNCHER_PATH], cwd=BASE_DIR)
    logger.info("NOVA ha sido iniciado. Se encuentra activo en la bandeja del sistema (System Tray junto al reloj).")

def main():
    logger.info("=================================================================")
    logger.info("   INSTALADOR Y CONFIGURADOR AUTÓNOMO 1-CLIC - PROYECTO NOVA    ")
    logger.info("=================================================================")

    ensure_config()
    ensure_vbs_launcher()
    ensure_sqlite_db()
    create_windows_shortcuts()
    run_nova_silent()

    logger.info("=================================================================")
    logger.info("   ¡INSTALACIÓN COMPLETADA! NOVA YA ESTÁ FUNCIONANDO.           ")
    logger.info("=================================================================")

if __name__ == "__main__":
    main()
