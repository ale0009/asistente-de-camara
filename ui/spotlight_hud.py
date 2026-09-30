# -*- coding: utf-8 -*-
"""
Paleta de Comandos Efímera tipo Spotlight / Raycast para NOVA (ui/spotlight_hud.py).
Se abre en <50ms con atajo global, no deja ventanas fijas y desaparece con Escape o Enter.
"""
import os
import sys
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QListWidget, QListWidgetItem, QLabel, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.ipc_server import send_ipc_command

# Colores HUD Cyberpunk Glassmorphism
BG_COLOR = "rgba(4, 10, 24, 0.94)"
BORDER_COLOR = "rgba(0, 229, 255, 0.40)"
ACCENT_CYAN = "#00e5ff"
TEXT_DIM = "rgba(255, 255, 255, 0.55)"
TEXT_WHITE = "#ffffff"


class SpotlightHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.projects = []
        self._init_window()
        self._build_ui()
        self._load_projects()

    def _init_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setFixedSize(600, 380)

        # Centrar en tercio superior de pantalla
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = screen.top() + int(screen.height() * 0.16)
        self.move(x, y)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)

        # Contenedor Card Glassmorphism
        self.card = QWidget(self)
        self.card.setObjectName("card")
        self.card.setStyleSheet(f"""
            QWidget#card {{
                background: {BG_COLOR};
                border: 1.5px solid {BORDER_COLOR};
                border-radius: 14px;
            }}
        """)

        # Sombra con resplandor
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(35)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 229, 255, 65))
        self.card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(16, 14, 16, 12)
        layout.setSpacing(10)

        # Barra de búsqueda
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        icon_label = QLabel("⚡")
        icon_label.setStyleSheet(f"font-size: 18px; color: {ACCENT_CYAN}; background: transparent; border: none;")
        top_bar.addWidget(icon_label)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Buscar proyecto, comando o preguntar a la IA... (Esc para salir)")
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(0, 229, 255, 0.25);
                border-radius: 8px;
                color: {TEXT_WHITE};
                font: 500 13px 'Inter', sans-serif;
                padding: 8px 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ACCENT_CYAN};
                background: rgba(0, 229, 255, 0.08);
            }}
        """)
        self.input_field.textChanged.connect(self._on_search_changed)
        top_bar.addWidget(self.input_field)

        layout.addLayout(top_bar)

        # Lista de resultados
        self.results_list = QListWidget()
        self.results_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid rgba(255, 255, 255, 0.04);
                border-radius: 7px;
                color: {TEXT_WHITE};
                font: 500 11px 'Inter', sans-serif;
                padding: 6px 10px;
                margin-bottom: 4px;
            }}
            QListWidget::item:selected {{
                background: rgba(0, 229, 255, 0.16);
                border: 1px solid {ACCENT_CYAN};
                color: #ffffff;
            }}
            QListWidget::item:hover {{
                background: rgba(0, 229, 255, 0.08);
            }}
        """)
        self.results_list.itemActivated.connect(self._execute_selected)
        layout.addWidget(self.results_list)

        # Footer con atajos de acción
        footer = QHBoxLayout()
        footer.setContentsMargins(2, 4, 2, 0)
        footer_hints = QLabel("Enter: Ejecutar  •  Esc: Salir  •  [F] Fix Error  •  [G] Standup  •  [S] Captura  •  [B] Blender")
        footer_hints.setStyleSheet(f"font: 400 9px 'JetBrains Mono', monospace; color: {TEXT_DIM}; background: transparent; border: none;")
        footer.addWidget(footer_hints)
        layout.addLayout(footer)

        root.addWidget(self.card)

    def _load_projects(self):
        """Consulta proyectos al daemon y llena la lista inicial con acciones rápidas."""
        self.results_list.clear()
        
        # 1. Acciones rápidas predeterminadas
        actions = [
            ("🔧 [F] Diagnosticar y reparar último error en terminal", "action_fix"),
            ("🚀 [G] Sincronizar Git Standup de hoy con Obsidian", "action_standup"),
            ("📐 [S] Capturar región de pantalla y analizar con IA", "action_inspect"),
            ("🎨 [B] Lanzar Blender con GPU dedicada (libera VRAM)", "action_blender"),
            ("🛡 [T] Ver telemetría de hardware (CPU, RAM, GPU)", "action_telemetry"),
        ]
        for title, key in actions:
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.results_list.addItem(item)

        # 2. Cargar proyectos de Obsidian
        res = send_ipc_command({"action": "projects"})
        if res.get("status") == "success":
            self.projects = res.get("result", {}).get("projects", [])
            for p in self.projects:
                item = QListWidgetItem(f"📂 Proyecto: {p['name']} — {p.get('desc', '')[:45]}...")
                item.setData(Qt.ItemDataRole.UserRole, f"project_{p['name']}")
                self.results_list.addItem(item)

        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)

    def _on_search_changed(self, text: str):
        query = text.lower().strip()
        self.results_list.clear()

        # Atajos de una sola letra
        if query in ["f", "fix"]:
            item = QListWidgetItem("🔧 Ejecutar: Diagnosticar último error en terminal")
            item.setData(Qt.ItemDataRole.UserRole, "action_fix")
            self.results_list.addItem(item)
        elif query in ["g", "standup"]:
            item = QListWidgetItem("🚀 Ejecutar: Sincronizar Git Standup con Obsidian")
            item.setData(Qt.ItemDataRole.UserRole, "action_standup")
            self.results_list.addItem(item)
        elif query in ["s", "captura", "inspect"]:
            item = QListWidgetItem("📐 Ejecutar: Capturar región de pantalla")
            item.setData(Qt.ItemDataRole.UserRole, "action_inspect")
            self.results_list.addItem(item)
        elif query in ["b", "blender"]:
            item = QListWidgetItem("🎨 Ejecutar: Iniciar Blender con PRIME offload")
            item.setData(Qt.ItemDataRole.UserRole, "action_blender")
            self.results_list.addItem(item)

        # Filtrar proyectos
        matched_projects = [p for p in self.projects if query in p['name'].lower() or query in p.get('code', '').lower()]
        for p in matched_projects:
            item = QListWidgetItem(f"📂 Abrir en VS Code: {p['name']}")
            item.setData(Qt.ItemDataRole.UserRole, f"project_{p['name']}")
            self.results_list.addItem(item)

        # Opción de consultar a la IA directamente
        if query and not matched_projects:
            item = QListWidgetItem(f"🤖 Preguntar a IA local: \"{text}\"")
            item.setData(Qt.ItemDataRole.UserRole, f"ask_{text}")
            self.results_list.addItem(item)

        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)

    def _execute_selected(self, item: QListWidgetItem = None):
        if not item:
            item = self.results_list.currentItem()
        if not item:
            return

        key = item.data(Qt.ItemDataRole.UserRole)
        self.hide() # Ocultar de inmediato para dar feedback instantáneo

        if key == "action_fix":
            subprocess.Popen(["konsole", "-e", "bash", "-c", "nova fix; echo ''; read -p 'Presiona Enter para cerrar...'"])
        elif key == "action_standup":
            subprocess.Popen(["konsole", "-e", "bash", "-c", "nova standup; echo ''; read -p 'Presiona Enter para cerrar...'"])
        elif key == "action_inspect":
            subprocess.Popen(["nova", "inspect"])
        elif key == "action_blender":
            send_ipc_command({"action": "blender"})
        elif key == "action_telemetry":
            subprocess.Popen(["konsole", "-e", "bash", "-c", "nova status; echo ''; read -p 'Presiona Enter para cerrar...'"])
        elif key.startswith("project_"):
            pname = key.replace("project_", "")
            send_ipc_command({"action": "open_project", "name": pname, "mode": "code"})
        elif key.startswith("ask_"):
            prompt = key.replace("ask_", "")
            subprocess.Popen(["konsole", "-e", "bash", "-c", f"nova ask '{prompt}'; echo ''; read -p 'Presiona Enter para cerrar...'"])

        QApplication.quit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            QApplication.quit()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self._execute_selected()
        elif event.key() == Qt.Key.Key_Down:
            row = self.results_list.currentRow()
            if row < self.results_list.count() - 1:
                self.results_list.setCurrentRow(row + 1)
        elif event.key() == Qt.Key.Key_Up:
            row = self.results_list.currentRow()
            if row > 0:
                self.results_list.setCurrentRow(row - 1)
        else:
            super().keyPressEvent(event)


def main():
    app = QApplication(sys.argv)
    hud = SpotlightHUD()
    hud.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
