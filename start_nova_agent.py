"""Lanzador Unificado de NOVA / Segundo Cerebro (MCP Agent System).

Arranca en un solo comando:
1. El Servicio Agéntico FastAPI (`agent_service.main:app`) en segundo plano.
2. El Observador de Archivos en tiempo real (`watchers/file_watcher.py`).
3. El Orquestador de Interfaz Gráfica PyQt6 y Control de Cámara (`main.py`).
"""

import os
import sys
import time
import signal
import logging
import subprocess
import threading

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("NOVA.Launcher")

def start_agent_service():
    logger.info("Arrancando Servicio Agéntico FastAPI (Puerto 8000)...")
    cmd = [sys.executable, "-m", "uvicorn", "agent_service.main:app", "--port", "8000", "--host", "127.0.0.1"]
    return subprocess.Popen(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))

def start_file_watcher():
    logger.info("Arrancando Observador de Archivos (File Watcher)...")
    from watchers.file_watcher import FileWatcherService
    watcher = FileWatcherService()
    watcher.start()
    return watcher

def main():
    logger.info("==========================================================")
    logger.info("   Iniciando Plataforma Agéntica NOVA / Segundo Cerebro  ")
    logger.info("==========================================================")

    agent_proc = None
    watcher = None
    nova = None

    def _signal_handler(sig, frame):
        logger.info("Señal de interrupción recibida, cerrando servicios...")
        if watcher:
            watcher.stop()
        if agent_proc and agent_proc.poll() is None:
            agent_proc.terminate()
        if nova:
            nova.stop()
        sys.exit(0)

    try:
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)
    except Exception:
        pass

    # 1. Iniciar FastAPI Agent Service
    agent_proc = start_agent_service()
    time.sleep(1.5)

    # 2. Iniciar File Watcher
    watcher = start_file_watcher()

    # 3. Arrancar Orquestador Principal NOVA (PyQt6 + Cámara + Voz)
    try:
        from main import NovaAssistant
        nova = NovaAssistant()
        nova.start()
    except Exception as e:
        logger.error(f"Error ejecutando la aplicación principal de NOVA: {e}")
    finally:
        logger.info("Cerrando servicios de NOVA...")
        if watcher:
            watcher.stop()
        if agent_proc and agent_proc.poll() is None:
            agent_proc.terminate()
        logger.info("Plataforma NOVA apagada correctamente.")

if __name__ == "__main__":
    main()
