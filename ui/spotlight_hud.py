# -*- coding: utf-8 -*-
"""
Paleta de Comandos Efímera y Copiloto Scratchpad para NOVA 2.0 (ui/spotlight_hud.py).
Ofrece modo dual con transición instantánea:
- Modo 0: Buscador y lanzador de proyectos / atajos (Spotlight estilo Raycast).
- Modo 1: Scratchpad y Chat de IA interactivo con streaming en tiempo real (QThread),
  resaltado Markdown, copia de código y guardado directo en Obsidian Inbox.
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QListWidget, QListWidgetItem, QLabel, QGraphicsDropShadowEffect,
    QStackedWidget, QTextBrowser, QTextEdit, QPushButton
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QEvent
from PyQt6.QtGui import QColor, QFont, QKeyEvent, QClipboard

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from core.ipc_server import send_ipc_command
from core.ollama_bridge import OllamaBridge

# Paleta Estética Glassmorphism Cyberpunk / Catppuccin
BG_COLOR = "rgba(10, 15, 29, 0.96)"
BORDER_COLOR = "rgba(0, 229, 255, 0.40)"
ACCENT_CYAN = "#00e5ff"
ACCENT_CYAN_HOVER = "#33eeff"
BG_INPUT = "rgba(255, 255, 255, 0.05)"
TEXT_WHITE = "#ffffff"
TEXT_DIM = "rgba(255, 255, 255, 0.60)"
CODE_BG = "#0d1117"


class StreamWorker(QThread):
    """Hilo secundario para streaming de tokens desde Ollama sin bloquear la UI."""
    token_received = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, prompt: str, model: str = None, system: str = None):
        super().__init__()
        self.prompt = prompt
        self.model = model
        self.system = system
        self.bridge = OllamaBridge()

    def run(self):
        full_reply = ""
        try:
            for token in self.bridge.query_stream(self.prompt, model=self.model, max_tokens=600):
                full_reply += token
                self.token_received.emit(token)
            self.finished.emit(full_reply)
        except Exception as e:
            self.error.emit(str(e))


class PromptTextEdit(QTextEdit):
    """QTextEdit especializado: Enter envía, Shift+Enter añade salto de línea."""
    returnPressed = pyqtSignal()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.returnPressed.emit()
                event.accept()
        else:
            super().keyPressEvent(event)


class SpotlightHUD(QWidget):
    def __init__(self, initial_mode: str = "search", initial_query: str = ""):
        super().__init__()
        self.projects: List[Dict[str, Any]] = []
        self.current_worker = None
        self.full_response_text = ""
        self.active_model_name = "qwen2.5-coder:1.5b"

        self._init_window()
        self._build_ui()
        self._load_projects()

        if initial_mode == "chat" or initial_mode == "scratchpad":
            self.switch_to_scratchpad(initial_query)
        elif initial_query:
            self.input_field.setText(initial_query)

    def _init_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setFixedSize(680, 480)

        # Centrar en tercio superior de la pantalla principal
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = screen.top() + int(screen.height() * 0.14)
        self.move(x, y)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)

        # Contenedor Card Principal con Borde Cyan y Sombra Suave
        self.card = QWidget(self)
        self.card.setObjectName("card")
        self.card.setStyleSheet(f"""
            QWidget#card {{
                background: {BG_COLOR};
                border: 1.5px solid {BORDER_COLOR};
                border-radius: 14px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 229, 255, 60))
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(10)

        # QStackedWidget para alternar entre Buscador (0) y Scratchpad IA (1)
        self.stack = QStackedWidget()
        self.page_search = self._create_search_page()
        self.page_scratchpad = self._create_scratchpad_page()

        self.stack.addWidget(self.page_search)
        self.stack.addWidget(self.page_scratchpad)

        card_layout.addWidget(self.stack)
        root.addWidget(self.card)

    def _create_search_page(self) -> QWidget:
        """Página 0: Buscador difuso y lanzador de proyectos y acciones rápidas."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Barra superior de búsqueda
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        icon_label = QLabel("⚡")
        icon_label.setStyleSheet(f"font-size: 18px; color: {ACCENT_CYAN}; background: transparent; border: none;")
        top_bar.addWidget(icon_label)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Buscar proyecto, comando o presiona Tab para chatear con la IA...")
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background: {BG_INPUT};
                border: 1px solid rgba(0, 229, 255, 0.25);
                border-radius: 8px;
                color: {TEXT_WHITE};
                font: 500 13px 'Inter', sans-serif;
                padding: 9px 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ACCENT_CYAN};
                background: rgba(0, 229, 255, 0.08);
            }}
        """)
        self.input_field.textChanged.connect(self._on_search_changed)
        top_bar.addWidget(self.input_field)

        btn_chat_mode = QPushButton("💬 Chat IA (Tab)")
        btn_chat_mode.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0, 229, 255, 0.12);
                border: 1px solid rgba(0, 229, 255, 0.35);
                border-radius: 6px;
                color: {ACCENT_CYAN};
                font: 600 11px 'Inter', sans-serif;
                padding: 8px 12px;
            }}
            QPushButton:hover {{
                background: rgba(0, 229, 255, 0.25);
                color: #ffffff;
            }}
        """)
        btn_chat_mode.clicked.connect(lambda: self.switch_to_scratchpad(self.input_field.text()))
        top_bar.addWidget(btn_chat_mode)

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
                padding: 7px 10px;
                margin-bottom: 4px;
            }}
            QListWidget::item:selected {{
                background: rgba(0, 229, 255, 0.18);
                border: 1px solid {ACCENT_CYAN};
                color: #ffffff;
            }}
            QListWidget::item:hover {{
                background: rgba(0, 229, 255, 0.09);
            }}
        """)
        self.results_list.itemActivated.connect(self._execute_selected)
        layout.addWidget(self.results_list)

        # Footer con atajos
        footer = QHBoxLayout()
        footer.setContentsMargins(2, 4, 2, 0)
        footer_hints = QLabel("Enter: Ejecutar  •  Tab: Chat/Scratchpad  •  Esc: Salir  •  [F] Fix Error  •  [G] Standup")
        footer_hints.setStyleSheet(f"font: 400 9px 'JetBrains Mono', monospace; color: {TEXT_DIM}; background: transparent; border: none;")
        footer.addWidget(footer_hints)
        layout.addLayout(footer)

        return page

    def _create_scratchpad_page(self) -> QWidget:
        """Página 1: Copiloto interactivo con streaming Markdown y atajos de productividad."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Cabecera de Scratchpad
        header = QHBoxLayout()
        header.setSpacing(8)

        btn_back = QPushButton("← Buscador (Esc)")
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                color: {TEXT_WHITE};
                font: 500 11px 'Inter', sans-serif;
                padding: 5px 10px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.12);
            }}
        """)
        btn_back.clicked.connect(self.switch_to_search)
        header.addWidget(btn_back)

        self.model_badge = QLabel("⚡ Modelo: qwen2.5-coder:1.5b (Local)")
        self.model_badge.setStyleSheet(f"""
            background: rgba(0, 229, 255, 0.10);
            border: 1px solid rgba(0, 229, 255, 0.25);
            border-radius: 6px;
            color: {ACCENT_CYAN};
            font: 600 10px 'JetBrains Mono', monospace;
            padding: 4px 8px;
        """)
        header.addWidget(self.model_badge)

        header.addStretch()

        self.status_label = QLabel("Listo")
        self.status_label.setStyleSheet(f"font: 400 10px 'Inter', sans-serif; color: {TEXT_DIM};")
        header.addWidget(self.status_label)

        btn_clear = QPushButton("🧹 Limpiar")
        btn_clear.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 6px;
                color: {TEXT_DIM};
                font: 500 10px 'Inter', sans-serif;
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                color: #ffffff;
                border-color: rgba(255, 255, 255, 0.35);
            }}
        """)
        btn_clear.clicked.connect(self._clear_scratchpad)
        header.addWidget(btn_clear)

        layout.addLayout(header)

        # Área de visualización de respuesta (QTextBrowser)
        self.response_viewer = QTextBrowser()
        self.response_viewer.setOpenExternalLinks(True)
        self.response_viewer.setStyleSheet(f"""
            QTextBrowser {{
                background: rgba(5, 10, 20, 0.75);
                border: 1px solid rgba(0, 229, 255, 0.20);
                border-radius: 8px;
                color: #e2e8f0;
                font: 400 12px 'Inter', 'JetBrains Mono', sans-serif;
                padding: 12px;
                line-height: 1.5;
            }}
        """)
        layout.addWidget(self.response_viewer)

        # Barra de acciones sobre el resultado
        action_bar = QHBoxLayout()
        action_bar.setSpacing(8)

        self.btn_copy = QPushButton("📋 Copiar Respuesta")
        self.btn_copy.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0, 229, 255, 0.12);
                border: 1px solid rgba(0, 229, 255, 0.30);
                border-radius: 6px;
                color: {ACCENT_CYAN};
                font: 600 11px 'Inter', sans-serif;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background: rgba(0, 229, 255, 0.25);
                color: #ffffff;
            }}
        """)
        self.btn_copy.clicked.connect(self._copy_response)
        action_bar.addWidget(self.btn_copy)

        self.btn_save_obsidian = QPushButton("📝 Guardar en Obsidian Inbox")
        self.btn_save_obsidian.setStyleSheet(f"""
            QPushButton {{
                background: rgba(147, 51, 234, 0.15);
                border: 1px solid rgba(168, 85, 247, 0.40);
                border-radius: 6px;
                color: #d8b4fe;
                font: 600 11px 'Inter', sans-serif;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background: rgba(147, 51, 234, 0.30);
                color: #ffffff;
            }}
        """)
        self.btn_save_obsidian.clicked.connect(self._save_to_obsidian)
        action_bar.addWidget(self.btn_save_obsidian)

        action_bar.addStretch()

        btn_fix_shortcut = QPushButton("🔧 Diagnosticar Terminal")
        btn_fix_shortcut.setStyleSheet(f"""
            QPushButton {{
                background: rgba(245, 158, 11, 0.12);
                border: 1px solid rgba(245, 158, 11, 0.35);
                border-radius: 6px;
                color: #fbbf24;
                font: 500 11px 'Inter', sans-serif;
                padding: 6px 10px;
            }}
            QPushButton:hover {{
                background: rgba(245, 158, 11, 0.25);
                color: #ffffff;
            }}
        """)
        btn_fix_shortcut.clicked.connect(self._diagnose_terminal_into_scratchpad)
        action_bar.addWidget(btn_fix_shortcut)

        layout.addLayout(action_bar)

        # Caja de entrada multilínea de prompt
        input_container = QHBoxLayout()
        input_container.setSpacing(8)

        self.prompt_input = PromptTextEdit()
        self.prompt_input.setPlaceholderText("Pregunta a NOVA, pega un fragmento de código o error... (Enter envía, Shift+Enter nueva línea)")
        self.prompt_input.setFixedHeight(56)
        self.prompt_input.setStyleSheet(f"""
            QTextEdit {{
                background: {BG_INPUT};
                border: 1px solid rgba(0, 229, 255, 0.25);
                border-radius: 8px;
                color: {TEXT_WHITE};
                font: 500 12px 'Inter', sans-serif;
                padding: 6px 10px;
            }}
            QTextEdit:focus {{
                border: 1px solid {ACCENT_CYAN};
                background: rgba(0, 229, 255, 0.08);
            }}
        """)
        self.prompt_input.returnPressed.connect(self._send_prompt)
        input_container.addWidget(self.prompt_input)

        self.btn_send = QPushButton("Enviar ⚡")
        self.btn_send.setFixedHeight(56)
        self.btn_send.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT_CYAN};
                border: none;
                border-radius: 8px;
                color: #030712;
                font: 700 12px 'Inter', sans-serif;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background: {ACCENT_CYAN_HOVER};
            }}
            QPushButton:disabled {{
                background: rgba(255, 255, 255, 0.15);
                color: rgba(255, 255, 255, 0.40);
            }}
        """)
        self.btn_send.clicked.connect(self._send_prompt)
        input_container.addWidget(self.btn_send)

        layout.addLayout(input_container)

        return page

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
            ("💬 [C] Abrir Scratchpad / Chat Copiloto interactivo", "action_scratchpad"),
        ]
        for title, key in actions:
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.results_list.addItem(item)

        # 2. Cargar proyectos de Obsidian vía IPC
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

        # Atajos directos
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
        elif query in ["c", "chat", "?"]:
            item = QListWidgetItem("💬 Cambiar a Scratchpad / Chat Copiloto")
            item.setData(Qt.ItemDataRole.UserRole, "action_scratchpad")
            self.results_list.addItem(item)

        # Filtrar proyectos de Obsidian
        matched_projects = [p for p in self.projects if query in p['name'].lower() or query in p.get('code', '').lower()]
        for p in matched_projects:
            item = QListWidgetItem(f"📂 Abrir en VS Code: {p['name']}")
            item.setData(Qt.ItemDataRole.UserRole, f"project_{p['name']}")
            self.results_list.addItem(item)

        # Opción para preguntar a la IA
        if query and not matched_projects:
            item = QListWidgetItem(f"🤖 Preguntar a NOVA Scratchpad: \"{text}\" (Tab o Enter)")
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
        if not key:
            return

        if key == "action_scratchpad":
            self.switch_to_scratchpad()
            return
        elif key.startswith("ask_"):
            prompt = key.replace("ask_", "")
            self.switch_to_scratchpad(initial_prompt=prompt)
            return

        # Para acciones del sistema, ocultar y despachar
        self.hide()
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

        QApplication.quit()

    def switch_to_scratchpad(self, initial_prompt: str = ""):
        """Transiciona al modo Scratchpad interactivo."""
        self.stack.setCurrentIndex(1)
        self.setFixedSize(680, 520)
        self.prompt_input.setFocus()
        if initial_prompt:
            self.prompt_input.setPlainText(initial_prompt)
            self._send_prompt()

    def switch_to_search(self):
        """Regresa a la paleta de búsqueda."""
        self.stack.setCurrentIndex(0)
        self.setFixedSize(680, 480)
        self.input_field.setFocus()

    def _send_prompt(self):
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt or (self.current_worker and self.current_worker.isRunning()):
            return

        self.btn_send.setEnabled(False)
        self.status_label.setText("Pensando...")
        self.response_viewer.setMarkdown(f"**Tú:** {prompt}\n\n---\n\n**NOVA:** ")
        self.full_response_text = ""

        # Iniciar streaming en hilo secundario
        self.current_worker = StreamWorker(prompt=prompt, model=self.active_model_name)
        self.current_worker.token_received.connect(self._on_token_received)
        self.current_worker.finished.connect(self._on_stream_finished)
        self.current_worker.error.connect(self._on_stream_error)
        self.current_worker.start()

        self.prompt_input.clear()

    def _on_token_received(self, token: str):
        self.full_response_text += token
        # Actualizar visualizador con Markdown enriquecido
        self.response_viewer.setMarkdown(self.full_response_text)
        sb = self.response_viewer.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_stream_finished(self, full_text: str):
        self.status_label.setText("Completado")
        self.btn_send.setEnabled(True)
        self.prompt_input.setFocus()
        # Notificar en segundo plano al daemon para registro en memoria episódica
        try:
            send_ipc_command({
                "action": "log_memory",
                "category": "hud_scratchpad",
                "content": full_text[:120]
            })
        except Exception:
            pass

    def _on_stream_error(self, err_msg: str):
        self.status_label.setText("Error")
        self.btn_send.setEnabled(True)
        self.response_viewer.append(f"\n\n**[Error]:** {err_msg}")

    def _copy_response(self):
        """Copia la respuesta generada al portapapeles con feedback temporal."""
        if not self.full_response_text:
            return
        clipboard = QApplication.clipboard()
        clipboard.setText(self.full_response_text)
        self.btn_copy.setText("✓ ¡Copiado!")
        QTimer.singleShot(1800, lambda: self.btn_copy.setText("📋 Copiar Respuesta"))

    def _save_to_obsidian(self):
        """Guarda la respuesta en la bandeja de entrada de notas de Obsidian (~/Datos/Vault-Obsidian/00_Inbox/)."""
        if not self.full_response_text:
            return
        try:
            from core.quick_note import QuickNoteIngester
            ingester = QuickNoteIngester()
            note_content = f"# Nota rápida desde NOVA Scratchpad\n\n{self.full_response_text}"
            res = ingester.save_note(note_content, source="hud_scratchpad")
            if res.get("success"):
                self.btn_save_obsidian.setText("✓ ¡Guardado en Obsidian!")
                QTimer.singleShot(2200, lambda: self.btn_save_obsidian.setText("📝 Guardar en Obsidian Inbox"))
            else:
                self.btn_save_obsidian.setText("⚠ Error al guardar")
        except Exception as e:
            self.status_label.setText(f"Error: {e}")

    def _diagnose_terminal_into_scratchpad(self):
        """Carga el último error de terminal directamente en el scratchpad para análisis."""
        res = send_ipc_command({"action": "fix"})
        if res.get("success"):
            diag = res.get("result", {})
            explanation = diag.get("explicacion", "Sin explicación")
            cmd = diag.get("comando_corregido", "")
            original = diag.get("cmd_original", "")
            text = f"### 🔧 Diagnóstico de Terminal\n- **Comando que falló:** `{original}`\n- **Comando sugerido:** `{cmd}`\n- **Causa:** {explanation}"
            self.full_response_text = text
            self.response_viewer.setMarkdown(text)
        else:
            self.response_viewer.setMarkdown("No se detectó ningún error reciente en el terminal.")

    def _clear_scratchpad(self):
        self.full_response_text = ""
        self.response_viewer.clear()
        self.prompt_input.clear()
        self.status_label.setText("Listo")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            if self.stack.currentIndex() == 1:
                # Si estamos en scratchpad y no hay texto, volver a buscador
                self.switch_to_search()
            else:
                self.close()
                QApplication.quit()
        elif event.key() == Qt.Key.Key_Tab and self.stack.currentIndex() == 0:
            # Tab en buscador conmuta inmediatamente a scratchpad con el texto actual
            current_query = self.input_field.text().strip()
            self.switch_to_scratchpad(current_query)
            event.accept()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.stack.currentIndex() == 0:
            self._execute_selected()
        elif event.key() == Qt.Key.Key_Down and self.stack.currentIndex() == 0:
            row = self.results_list.currentRow()
            if row < self.results_list.count() - 1:
                self.results_list.setCurrentRow(row + 1)
        elif event.key() == Qt.Key.Key_Up and self.stack.currentIndex() == 0:
            row = self.results_list.currentRow()
            if row > 0:
                self.results_list.setCurrentRow(row - 1)
        else:
            super().keyPressEvent(event)


def main():
    parser = argparse.ArgumentParser(description="NOVA 2.0 Spotlight HUD & Scratchpad")
    parser.add_argument("--chat", "--scratchpad", action="store_true", help="Abrir directamente en modo Scratchpad")
    parser.add_argument("--ask", type=str, default="", help="Pregunta directa para enviar a la IA")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    mode = "chat" if (args.chat or args.ask) else "search"
    hud = SpotlightHUD(initial_mode=mode, initial_query=args.ask)
    hud.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
