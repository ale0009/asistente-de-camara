# -*- coding: utf-8 -*-
"""
Aplicación de Bandeja del Sistema (Taskbar Companion) para NOVA 2.0 (ui/tray_app.py).
Permite acceso instantáneo de 1 clic a todas las herramientas del copiloto:
- Fix de terminal
- Refactor/explicación de portapapeles
- Captura e inspección visual
- Git Standup automático
- Ingesta de notas rápidas a Obsidian
- Lanzador de 17 proyectos
- Control de VRAM para Blender y refrigeración Turbo Fan
"""
import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List

from PyQt6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QInputDialog,
    QLineEdit, QMessageBox
)
from PyQt6.QtGui import QIcon, QAction, QPixmap
from PyQt6.QtCore import Qt, QTimer, QLockFile, QDir

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.ipc_server import send_ipc_command, DEFAULT_SOCKET_PATH

logger = logging.getLogger("NOVA.TrayApp")

LOCK_FILE = os.path.join(QDir.tempPath(), "nova_tray.lock")
ICON_PATH = str(ROOT_DIR / "assets" / "nova_icon.png")
ICON_SVG = str(ROOT_DIR / "assets" / "nova.svg")


class NovaTrayApp:
    def __init__(self, app: QApplication):
        self.app = app
        self.hud_instance = None
        self.projects_cache: List[Dict[str, Any]] = []
        self.dirty_projects_cache: List[Dict[str, Any]] = []

        self.tray = QSystemTrayIcon(self.app)
        self._setup_icon()
        self._build_context_menu()
        self._setup_timers()

        # Conectar eventos de clic en el icono de la bandeja
        self.tray.activated.connect(self._on_tray_activated)

    def _setup_icon(self):
        """Carga el icono oficial del tema KDE o genera un fallback."""
        icon = QIcon.fromTheme("nova")
        if icon.isNull():
            if os.path.exists(ICON_SVG):
                icon = QIcon(ICON_SVG)
            elif os.path.exists(ICON_PATH):
                icon = QIcon(ICON_PATH)
            else:
                pixmap = QPixmap(32, 32)
                pixmap.fill(Qt.GlobalColor.cyan)
                icon = QIcon(pixmap)
        self.tray.setIcon(icon)
        self.app.setWindowIcon(icon)
        self.tray.setToolTip("NOVA 2.0 — Copiloto de Estación de Trabajo Linux")

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        """Clic izquierdo: abre / alterna la paleta Spotlight HUD."""
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.toggle_spotlight_hud()

    def toggle_spotlight_hud(self):
        """Abre o enfoca la paleta Spotlight HUD."""
        try:
            from ui.spotlight_hud import SpotlightHUD
            if self.hud_instance is None or not self.hud_instance.isVisible():
                self.hud_instance = SpotlightHUD()
                self.hud_instance.show()
                self.hud_instance.activateWindow()
                self.hud_instance.raise_()
            else:
                self.hud_instance.close()
                self.hud_instance = None
        except Exception as e:
            logger.error(f"Error al alternar Spotlight HUD: {e}")
            subprocess.Popen([sys.executable, "-m", "core.cli_handler"])

    def _build_context_menu(self):
        """Construye el menú contextual nativo de 1 clic."""
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #0b1120;
                color: #e2e8f0;
                border: 1px solid rgba(0, 229, 255, 0.35);
                border-radius: 8px;
                padding: 6px;
                font-family: 'Inter', sans-serif;
                font-size: 11px;
            }
            QMenu::item {
                padding: 6px 24px 6px 10px;
                border-radius: 5px;
            }
            QMenu::item:selected {
                background-color: rgba(0, 229, 255, 0.20);
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: rgba(255, 255, 255, 0.10);
                margin: 4px 6px;
            }
        """)

        # Cabecera de estado
        self.header_action = QAction("🛡 NOVA 2.0 Copiloto (Conectando...)")
        self.header_action.setEnabled(False)
        menu.addAction(self.header_action)
        menu.addSeparator()

        # 1. Acciones Rápidas de Código
        a_fix = QAction("🔧 Diagnosticar último fallo en terminal", menu)
        a_fix.triggered.connect(self.action_fix)
        menu.addAction(a_fix)

        a_refactor = QAction("📋 Refactorizar portapapeles con IA", menu)
        a_refactor.triggered.connect(self.action_clipboard_refactor)
        menu.addAction(a_refactor)

        a_explain = QAction("💡 Explicar contenido del portapapeles", menu)
        a_explain.triggered.connect(self.action_clipboard_explain)
        menu.addAction(a_explain)

        a_inspect = QAction("📐 Capturar pantalla y analizar (OCR / Diagrama)", menu)
        a_inspect.triggered.connect(self.action_inspect)
        menu.addAction(a_inspect)

        menu.addSeparator()

        # 2. Ecosistema Obsidian & Git
        a_standup = QAction("🚀 Sincronizar Git Standup de hoy con Obsidian", menu)
        a_standup.triggered.connect(self.action_standup)
        menu.addAction(a_standup)

        a_note = QAction("📝 Nota rápida a Obsidian (00_Inbox)", menu)
        a_note.triggered.connect(self.action_quick_note)
        menu.addAction(a_note)

        # Submenú dinámico de Proyectos
        self.projects_menu = QMenu("🌐 Mis Proyectos (17)", menu)
        menu.addMenu(self.projects_menu)
        self._refresh_projects_menu()

        menu.addSeparator()

        # 3. Hardware y Rendimiento (GTX 1050 3GB Pascal)
        a_blender = QAction("🎨 Lanzar Blender (libera VRAM de Ollama)", menu)
        a_blender.triggered.connect(self.action_blender)
        menu.addAction(a_blender)

        a_fan = QAction("🌀 Alternar Turbo Fan (Ventilador)", menu)
        a_fan.triggered.connect(self.action_toggle_fan)
        menu.addAction(a_fan)

        a_telem = QAction("📊 Telemetría de Estación de Trabajo", menu)
        a_telem.triggered.connect(self.action_telemetry)
        menu.addAction(a_telem)

        menu.addSeparator()

        # 4. Sistema y Salida
        a_spotlight = QAction("🔍 Abrir paleta Spotlight (Meta + Espacio)", menu)
        a_spotlight.triggered.connect(self.toggle_spotlight_hud)
        menu.addAction(a_spotlight)

        a_restart = QAction("🔄 Reiniciar Demonio de NOVA", menu)
        a_restart.triggered.connect(self.action_restart_daemon)
        menu.addAction(a_restart)

        a_quit = QAction("🚪 Salir de NOVA Tray", menu)
        a_quit.triggered.connect(self.app.quit)
        menu.addAction(a_quit)

        self.tray.setContextMenu(menu)

    def _setup_timers(self):
        """Temporizador periódico para actualizar telemetría en cabecera y estado de repositorios."""
        self.timer = QTimer(self.app)
        self.timer.timeout.connect(self._update_telemetry_header)
        self.timer.start(5000) # cada 5 segundos
        self._update_telemetry_header()

        # Temporizador para refrescar proyectos y cambios git cada 30 segundos
        self.git_timer = QTimer(self.app)
        self.git_timer.timeout.connect(self._refresh_projects_menu)
        self.git_timer.start(30000)

    def _update_telemetry_header(self):
        """Actualiza el texto de la cabecera del menú con telemetría viva."""
        res = send_ipc_command({"action": "telemetry"}, timeout=2.0)
        if res.get("status") == "success":
            telem = res.get("result", {})
            cpu = telem.get("cpu_percent", 0)
            ram = telem.get("ram_percent", 0)
            vram_used = telem.get("gpu_vram_used_mb", 0)
            vram_tot = telem.get("gpu_vram_total_mb", 3072)
            gpu_temp = telem.get("gpu_temp_c", 0)
            self.header_action.setText(f"🛡 NOVA · CPU: {cpu}% · RAM: {ram}% · GPU: {gpu_temp}°C ({vram_used}/{vram_tot} MB)")
        else:
            self.header_action.setText("🛡 NOVA Copiloto (Demonio desconectado)")

    def _refresh_projects_menu(self):
        """Consulta proyectos e indicadores git al daemon y reconstruye el submenú."""
        res_projs = send_ipc_command({"action": "projects"}, timeout=3.0)
        res_dirty = send_ipc_command({"action": "dirty_projects"}, timeout=3.0)

        dirty_map = {}
        if res_dirty.get("status") == "success":
            for d in res_dirty.get("result", {}).get("dirty_projects", []):
                dirty_map[d["name"]] = d["uncommitted_count"]

        if res_projs.get("status") == "success":
            self.projects_cache = res_projs.get("result", {}).get("projects", [])
            self.projects_menu.clear()

            for p in self.projects_cache:
                pname = p["name"]
                dirty_count = dirty_map.get(pname, 0)
                
                # Indicador de cambios pendientes
                badge = f" [● {dirty_count} cambios]" if dirty_count > 0 else ""
                proj_sub = self.projects_menu.addMenu(f"📂 {pname}{badge}")

                act_code = QAction("💻 Abrir en VS Code", proj_sub)
                act_code.triggered.connect(lambda chk, n=pname: self._open_project(n, "code"))
                proj_sub.addAction(act_code)

                act_term = QAction("🖥 Abrir Terminal (Konsole)", proj_sub)
                act_term.triggered.connect(lambda chk, n=pname: self._open_project(n, "terminal"))
                proj_sub.addAction(act_term)

                act_dir = QAction("📁 Abrir Carpeta", proj_sub)
                act_dir.triggered.connect(lambda chk, n=pname: self._open_project(n, "folder"))
                proj_sub.addAction(act_dir)

    def _open_project(self, name: str, mode: str):
        send_ipc_command({"action": "open_project", "name": name, "mode": mode})

    # Acciones de 1 Clic
    def action_fix(self):
        subprocess.Popen([
            "konsole", "-e", "bash", "-c",
            "nova fix; echo ''; read -p 'Presiona Enter para cerrar...'"
        ])

    def action_clipboard_refactor(self):
        send_ipc_command({"action": "clipboard_refactor"})

    def action_clipboard_explain(self):
        send_ipc_command({"action": "clipboard_explain"})

    def action_inspect(self):
        subprocess.Popen(["nova", "inspect"])

    def action_standup(self):
        subprocess.Popen([
            "konsole", "-e", "bash", "-c",
            "nova standup; echo ''; read -p 'Presiona Enter para cerrar...'"
        ])

    def action_quick_note(self):
        text, ok = QInputDialog.getText(
            None, "NOVA — Nota Rápida a Obsidian",
            "Escribe tu idea, tarea o apunte (se guardará en 00_Inbox):",
            QLineEdit.EchoMode.Normal, ""
        )
        if ok and text.strip():
            send_ipc_command({"action": "quick_note", "content": text.strip()})

    def action_blender(self):
        send_ipc_command({"action": "blender"})

    def action_toggle_fan(self):
        send_ipc_command({"action": "turbo_fan", "mode": "alternar"})

    def action_telemetry(self):
        subprocess.Popen([
            "konsole", "-e", "bash", "-c",
            "nova status; echo ''; read -p 'Presiona Enter para cerrar...'"
        ])

    def action_restart_daemon(self):
        try:
            subprocess.run(["systemctl", "--user", "restart", "nova.service"], check=True)
            self.tray.showMessage(
                "NOVA 2.0", "Demonio de fondo reiniciado exitosamente.",
                QSystemTrayIcon.MessageIcon.Information, 3000
            )
        except Exception as e:
            logger.error(f"Error reiniciando daemon: {e}")

    def show(self):
        self.tray.show()


def main():
    qapp = QApplication(sys.argv)
    qapp.setQuitOnLastWindowClosed(False)
    qapp.setApplicationName("NOVA Copilot Tray")
    qapp.setDesktopFileName("nova")

    # Bloqueo de instancia única con manejo de bloqueos obsoletos (stale locks)
    lock = QLockFile(LOCK_FILE)
    lock.setStaleLockTime(2000)
    if not lock.tryLock(150):
        lock.removeStaleLockFile()
        if not lock.tryLock(150):
            print("La aplicación de bandeja de NOVA ya está en ejecución.")
            return 0

    tray_app = NovaTrayApp(qapp)
    tray_app.show()
    return qapp.exec()


if __name__ == "__main__":
    sys.exit(main())
