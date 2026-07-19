"""
ui/panel_widget.py — Panel Flotante Principal de NOVA
======================================================
Diseño: Glassmorphism · Dark Mode · Cian Eléctrico #00e5ff
Basado en mockup aprobado por el usuario (variante 1a).
"""

import logging
import threading
from datetime import datetime

import cv2
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation,
    QEasingCurve, QRect, QPoint, QSize, QMetaObject, Q_ARG
)
from PyQt6.QtGui import (
    QColor, QFont, QIcon, QImage, QPainter, QPainterPath,
    QPen, QPixmap, QLinearGradient, QRadialGradient, QBrush
)
from PyQt6.QtWidgets import (
    QApplication, QGraphicsDropShadowEffect, QGridLayout,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget,
    QDialog, QComboBox
)

logger = logging.getLogger(__name__)

# ─── Paleta de colores (variante Cian Eléctrico) ──────────────────────────────
ACC       = "#00e5ff"
ACC_08    = "rgba(0,229,255,0.08)"
ACC_15    = "rgba(0,229,255,0.15)"
ACC_25    = "rgba(0,229,255,0.25)"
ACC_50    = "rgba(0,229,255,0.50)"
ACC_90    = "rgba(0,229,255,0.90)"
BG_PANEL  = "rgba(4,10,24,0.87)"
BG_LOG    = "rgba(0,0,0,0.42)"
BG_CANVAS = "#060f1e"
TEXT_DIM  = "rgba(190,210,255,0.58)"
TEXT_ACC  = "rgba(0,229,255,0.90)"


# Se elimina CameraThread ya que el feed viene de main.py


# ─── Widget individual para el indicador de estado parpadeante ───────────────
class PulsingDot(QWidget):
    def __init__(self, color="#00e5ff", parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.setFixedSize(8, 8)
        self._opacity = 1.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(600)
        self._growing = False

    def _tick(self):
        self._opacity = 0.35 if self._opacity > 0.5 else 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor(self.color)
        color.setAlphaF(self._opacity)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 8, 8)


# ─── Barra de onda de voz animada ────────────────────────────────────────────
class AudioWave(QWidget):
    def __init__(self, color="#00e5ff", bars=8, parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.bars = bars
        self.setFixedSize(bars * 5, 16)
        self._heights = [0.15] * bars
        self._targets = [0.15] * bars
        self._active = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(60)

    def set_active(self, active: bool):
        self._active = active

    def _animate(self):
        import random
        for i in range(self.bars):
            if self._active:
                self._targets[i] = random.uniform(0.25, 1.0)
            else:
                self._targets[i] = 0.15
            self._heights[i] += (self._targets[i] - self._heights[i]) * 0.35
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width() // self.bars
        for i, h in enumerate(self._heights):
            bar_h = int(self.height() * h)
            y = (self.height() - bar_h) // 2
            color = QColor(self.color)
            color.setAlphaF(0.35 + h * 0.6)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(i * w + 1, y, w - 2, bar_h, 2, 2)


class ConfigDialog(QDialog):
    """
    Diálogo modal de configuración con diseño glassmorphism HUD y glow cian.
    Permite seleccionar el micrófono activo y guardarlo en caliente.
    """
    def __init__(self, dispatcher, parent=None):
        super().__init__(parent)
        self.dispatcher = dispatcher
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(320, 280)
        
        self._drag_pos = None
        self._build_ui()

    def _build_ui(self):
        # Contenedor con borde y fondo glassmorphism
        container = QWidget(self)
        container.setFixedSize(320, 280)
        container.setObjectName("container")
        container.setStyleSheet(f"""
            QWidget#container {{
                background: rgba(4, 10, 24, 0.95);
                border: 1px solid rgba(0, 229, 255, 0.35);
                border-radius: 12px;
            }}
        """)
        
        # Sombra con resplandor cian sutil
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 229, 255, 60))
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Título
        title = QLabel("CONFIGURACIÓN DE NOVA")
        title.setStyleSheet("font: 700 11px 'Inter'; color: #ffffff; letter-spacing: 1px; background: transparent; border: none;")
        layout.addWidget(title)

        # Separador fino
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background: rgba(0, 229, 255, 0.15);")
        layout.addWidget(separator)

        # Label Micrófono
        label_mic = QLabel("Micrófono de entrada:")
        label_mic.setStyleSheet(f"font: 600 9px 'Inter'; color: {TEXT_DIM}; background: transparent; border: none;")
        layout.addWidget(label_mic)

        # ComboBox para micrófonos
        self.combo_mic = QComboBox()
        self.combo_mic.setFixedHeight(28)
        self.combo_mic.setStyleSheet(f"""
            QComboBox {{
                background: rgba(0, 0, 0, 0.5);
                border: 1px solid rgba(0, 229, 255, 0.2);
                border-radius: 6px;
                color: #ffffff;
                padding-left: 8px;
                font: 500 10px 'Inter';
            }}
            QComboBox:hover {{
                border: 1px solid rgba(0, 229, 255, 0.45);
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left-width: 0px;
                border-style: solid;
            }}
            QComboBox QAbstractItemView {{
                background: #040a18;
                border: 1px solid rgba(0, 229, 255, 0.35);
                border-radius: 6px;
                color: #ffffff;
                selection-background-color: rgba(0, 229, 255, 0.25);
                selection-color: #ffffff;
                outline: 0px;
            }}
        """)
        layout.addWidget(self.combo_mic)

        # Cargar micrófonos
        self.devices = {}
        if self.dispatcher and hasattr(self.dispatcher, 'voice') and self.dispatcher.voice:
            try:
                self.devices = self.dispatcher.voice.get_input_devices()
                current_mic = self.dispatcher.voice.config.get("mic_index", None)
                
                for idx, name in self.devices.items():
                    self.combo_mic.addItem(f"{idx}: {name[:32]}", idx)
                    if current_mic == idx:
                        self.combo_mic.setCurrentIndex(self.combo_mic.count() - 1)
            except Exception as e:
                logger.error(f"Error cargando micrófonos en ConfigDialog: {e}")
        
        if self.combo_mic.count() == 0:
            self.combo_mic.addItem("No se encontraron micrófonos", None)
            self.combo_mic.setEnabled(False)

        # Label Cámara
        label_cam = QLabel("Cámara de video:")
        label_cam.setStyleSheet(f"font: 600 9px 'Inter'; color: {TEXT_DIM}; background: transparent; border: none;")
        layout.addWidget(label_cam)

        # ComboBox para cámaras
        self.combo_cam = QComboBox()
        self.combo_cam.setFixedHeight(28)
        self.combo_cam.setStyleSheet(self.combo_mic.styleSheet())
        layout.addWidget(self.combo_cam)

        # Cargar cámaras
        self.cameras = {}
        if self.dispatcher and hasattr(self.dispatcher, 'camera') and self.dispatcher.camera:
            try:
                self.cameras = self.dispatcher.camera.get_available_cameras()
                current_cam_idx = getattr(self.dispatcher.camera, 'camera_index', 0)
                
                for idx, name in self.cameras.items():
                    self.combo_cam.addItem(f"{idx}: {name[:32]}", (idx, name))
                    if current_cam_idx == idx:
                        self.combo_cam.setCurrentIndex(self.combo_cam.count() - 1)
            except Exception as e:
                logger.error(f"Error cargando cámaras en ConfigDialog: {e}")

        if self.combo_cam.count() == 0:
            self.combo_cam.addItem("No se encontraron cámaras", None)
            self.combo_cam.setEnabled(False)

        layout.addStretch()

        # Botones inferiores (Guardar / Cancelar)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setFixedHeight(28)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.07);
                border-radius: 6px;
                color: {TEXT_DIM};
                font: 600 10px 'Inter';
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.08);
                color: #ffffff;
            }}
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Guardar")
        btn_save.setFixedHeight(28)
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0, 229, 255, 0.15);
                border: 1px solid rgba(0, 229, 255, 0.28);
                border-radius: 6px;
                color: {ACC};
                font: 600 10px 'Inter';
            }}
            QPushButton:hover {{
                background: rgba(0, 229, 255, 0.25);
                border: 1px solid rgba(0, 229, 255, 0.55);
            }}
        """)
        btn_save.clicked.connect(self._on_save)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    # Permitir arrastrar la ventana
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def _on_save(self):
        # Guardar Micrófono
        selected_mic_idx = self.combo_mic.currentData()
        if selected_mic_idx is not None and self.dispatcher and hasattr(self.dispatcher, 'voice') and self.dispatcher.voice:
            try:
                self.dispatcher.voice.set_microphone(selected_mic_idx)
            except Exception as e:
                logger.error(f"Error al cambiar micrófono en ConfigDialog: {e}")

        # Guardar Cámara
        selected_cam_data = self.combo_cam.currentData()
        if selected_cam_data is not None and self.dispatcher and hasattr(self.dispatcher, 'camera') and self.dispatcher.camera:
            try:
                cam_idx, cam_name = selected_cam_data
                self.dispatcher.camera.set_camera(cam_idx, cam_name)
            except Exception as e:
                logger.error(f"Error al cambiar cámara en ConfigDialog: {e}")

        from ui.panel_widget import show_toast
        show_toast("Configuración", "Preferencias de hardware actualizadas.", success=True)
        self.accept()


# ─── Panel Flotante Principal ─────────────────────────────────────────────────
class FloatingPanel(QWidget):
    """
    Panel glassmorphism de 340×520px que se abre desde la bandeja.
    Incluye: header, feed de cámara, log de acciones, grid de botones.
    """

    def __init__(self, dispatcher=None, parent=None):
        super().__init__(parent)
        self.dispatcher = dispatcher
        self._drag_pos = None
        # Evita que clics repetidos rápidos apilen hilos/llamadas concurrentes
        # a process_command — antes cada clic lanzaba un hilo nuevo sin límite.
        self._dispatch_busy = threading.Lock()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setFixedSize(340, 524)

        self._build_ui()
        self._position_near_tray()

        # Animación de entrada
        self._anim_in()

    # ── Construcción del UI ────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Card contenedor con fondo de vidrio
        self.card = QWidget(self)
        self.card.setObjectName("card")
        self.card.setStyleSheet(self._stylesheet())
        self.card.setFixedSize(340, 524)
        root.addWidget(self.card)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        card_layout.addWidget(self._build_header())
        card_layout.addWidget(self._build_video())
        card_layout.addWidget(self._build_log())
        card_layout.addWidget(self._build_buttons())

        # Sombra exterior con glow cian
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(48)
        shadow.setOffset(0, 16)
        shadow.setColor(QColor(0, 0, 0, 200))
        self.card.setGraphicsEffect(shadow)

    def _build_header(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(52)
        w.setStyleSheet(f"""
            background: transparent;
            border-bottom: 1px solid rgba(0,229,255,0.10);
        """)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(8)

        # Logo N
        logo = QLabel()
        logo.setFixedSize(28, 28)
        logo.setStyleSheet(f"""
            background: rgba(0,229,255,0.08);
            border: 1px solid rgba(0,229,255,0.28);
            border-radius: 7px;
            color: {ACC};
            font: 700 12px 'Inter';
            qproperty-alignment: AlignCenter;
        """)
        logo.setText("N")
        lay.addWidget(logo)

        # Título
        title = QLabel("NOVA")
        title.setStyleSheet("font: 700 12px 'Inter'; color: #ffffff; letter-spacing: 2px; background: transparent; border: none;")
        lay.addWidget(title)

        lay.addStretch()

        # Badge de estado
        badge = QWidget()
        badge.setFixedHeight(24)
        badge.setStyleSheet(f"""
            background: rgba(0,229,255,0.08);
            border: 1px solid rgba(0,229,255,0.18);
            border-radius: 12px;
        """)
        b_lay = QHBoxLayout(badge)
        b_lay.setContentsMargins(8, 0, 10, 0)
        b_lay.setSpacing(5)

        self.status_dot = PulsingDot(ACC)
        b_lay.addWidget(self.status_dot)

        self.status_label = QLabel("Escuchando")
        self.status_label.setStyleSheet(f"font: 500 10px 'Inter'; color: {ACC_90}; background: transparent; border: none;")
        b_lay.addWidget(self.status_label)
        lay.addWidget(badge)

        # Cerrar
        btn_close = QPushButton("×")
        btn_close.setFixedSize(20, 20)
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: rgba(255,255,255,0.28);
                font: 300 17px 'Inter';
            }
            QPushButton:hover { color: #ff5555; }
        """)
        btn_close.clicked.connect(self.close)
        lay.addWidget(btn_close)
        return w

    def _build_video(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 10, 12, 6)
        lay.setSpacing(0)

        # Contenedor de video con esquinas HUD
        vid_container = QWidget()
        vid_container.setFixedSize(316, 178)
        vid_container.setStyleSheet("""
            background: #0d162e;
            border-radius: 8px;
        """)
        vid_lay = QVBoxLayout(vid_container)
        vid_lay.setContentsMargins(0, 0, 0, 0)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setFixedSize(316, 178)
        self.video_label.setStyleSheet("background: #0d162e; border-radius: 8px;")
        vid_lay.addWidget(self.video_label)

        # Chips de estado encima del video
        self.chip_tracking = QLabel("▶ Tracking: Humano")
        self.chip_tracking.setStyleSheet(f"""
            background: rgba(0,0,0,0.76);
            border: 1px solid rgba(0,229,255,0.28);
            border-radius: 4px;
            color: {ACC_90};
            font: 500 9px 'JetBrains Mono';
            padding: 3px 7px;
        """)

        self.chip_zoom = QLabel("⊕ Zoom: 1.0x")
        self.chip_zoom.setStyleSheet(f"""
            background: rgba(0,0,0,0.76);
            border: 1px solid rgba(0,229,255,0.15);
            border-radius: 4px;
            color: {ACC_50};
            font: 500 9px 'JetBrains Mono';
            padding: 3px 7px;
        """)

        # Overlay encima del label de video
        chips_bar = QWidget(vid_container)
        chips_bar.setGeometry(8, 152, 300, 20)
        chips_bar.setStyleSheet("background: transparent;")
        chips_h = QHBoxLayout(chips_bar)
        chips_h.setContentsMargins(0, 0, 0, 0)
        chips_h.setSpacing(5)
        chips_h.addWidget(self.chip_tracking)
        chips_h.addWidget(self.chip_zoom)
        chips_h.addStretch()

        lay.addWidget(vid_container, alignment=Qt.AlignmentFlag.AlignCenter)
        return w

    def _build_log(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 2, 12, 8)
        lay.setSpacing(0)

        self.log_list = QListWidget()
        self.log_list.setFixedHeight(76)
        self.log_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.log_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.log_list.setStyleSheet(f"""
            QListWidget {{
                background: rgba(0,0,0,0.42);
                border: 1px solid rgba(255,255,255,0.05);
                border-radius: 8px;
                padding: 4px 8px;
            }}
            QListWidget::item {{
                color: {TEXT_DIM};
                font: 400 9px 'JetBrains Mono';
                padding: 2px 0;
                border-bottom: 1px solid rgba(255,255,255,0.03);
            }}
        """)
        lay.addWidget(self.log_list)
        self.add_log("Sistema", "NOVA iniciada")
        return w

    def _build_buttons(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 0, 12, 14)

        grid = QGridLayout()
        grid.setSpacing(5)

        buttons_data = [
            ("☀", "Despertar", "wake",     False),
            ("⊙", "Trackear",  "track",    True),
            ("■", "Parar",     "stop",     False),
            ("◉", "Captura",   "snap",     False),
            ("⊘", "Silencio",  "mute",     False),
            ("♪+", "Vol+",    "vol_up",   False),
            ("♪−", "Vol−",    "vol_dn",   False),
            ("✦", "Config",   "config",   False),
            ("◈", "Obsidian", "obsidian", False),
            ("?", "Ayuda",    "help",     False),
        ]

        for idx, (icon, label, cmd, primary) in enumerate(buttons_data):
            btn = self._make_button(icon, label, cmd, primary)
            grid.addWidget(btn, idx // 3, idx % 3)

        lay.addLayout(grid)
        return w

    def _make_button(self, icon: str, label: str, cmd: str, primary: bool) -> QPushButton:
        btn = QPushButton()
        btn.setFixedSize(98, 52)

        if primary:
            style = f"""
                QPushButton {{
                    background: rgba(0,229,255,0.15);
                    border: 1px solid rgba(0,229,255,0.28);
                    border-radius: 8px;
                }}
                QPushButton:hover {{
                    background: rgba(0,229,255,0.25);
                    border: 1px solid rgba(0,229,255,0.55);
                }}
            """
            icon_color = ACC
            label_color = ACC
        elif cmd == "stop":
            style = """
                QPushButton {
                    background: rgba(255,55,55,0.06);
                    border: 1px solid rgba(255,55,55,0.16);
                    border-radius: 8px;
                }
                QPushButton:hover { background: rgba(255,55,55,0.14); }
            """
            icon_color = "rgba(255,90,90,0.82)"
            label_color = "rgba(255,255,255,0.45)"
        elif cmd == "obsidian":
            style = """
                QPushButton {
                    background: rgba(100,70,200,0.07);
                    border: 1px solid rgba(100,70,200,0.18);
                    border-radius: 8px;
                }
                QPushButton:hover { background: rgba(100,70,200,0.16); }
            """
            icon_color = "rgba(148,110,240,0.85)"
            label_color = "rgba(255,255,255,0.42)"
        else:
            style = """
                QPushButton {
                    background: rgba(255,255,255,0.03);
                    border: 1px solid rgba(255,255,255,0.07);
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background: rgba(0,229,255,0.07);
                    border: 1px solid rgba(0,229,255,0.18);
                }
            """
            icon_color = "rgba(160,190,255,0.62)"
            label_color = "rgba(255,255,255,0.42)"

        btn.setStyleSheet(style)

        inner = QVBoxLayout(btn)
        inner.setContentsMargins(0, 8, 0, 6)
        inner.setSpacing(3)
        inner.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ic = QLabel(icon)
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setStyleSheet(f"color: {icon_color}; font: 600 14px 'Inter'; background: transparent; border: none;")

        lb = QLabel(label)
        lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lb.setStyleSheet(f"color: {label_color}; font: 500 8px 'Inter'; background: transparent; border: none;")

        inner.addWidget(ic)
        inner.addWidget(lb)

        btn.clicked.connect(lambda _, c=cmd, l=label: self._on_button(c, l))
        return btn

    def _open_config_dialog(self):
        dialog = ConfigDialog(self.dispatcher, self)
        dialog.exec()

    # ── Lógica ────────────────────────────────────────────────────────────
    def _on_button(self, cmd: str, label: str):
        if cmd == "config":
            self._open_config_dialog()
            return

        mapping = {
            "wake":     "despierta la cámara",
            "track":    "sígueme",
            "stop":     "para de seguirme",
            "snap":     "captura de pantalla",
            "mute":     "silencia",
            "vol_up":   "sube el volumen",
            "vol_dn":   "baja el volumen",
            "config":   "abrir configuración",
            "obsidian": "abre obsidian",
            "help":     "pregúntale a ollama ¿cómo usar NOVA?",
        }
        voice_cmd = mapping.get(cmd, cmd)
        if not self.dispatcher:
            self.add_log("UI", f"[sin dispatcher] {label}")
            return

        if not self._dispatch_busy.acquire(blocking=False):
            logger.info(f"Clic ignorado (comando anterior aún en curso): {label}")
            self.add_log("UI", f"Espera, procesando el comando anterior…")
            return

        threading.Thread(
            target=self._dispatch, args=(voice_cmd, label), daemon=True
        ).start()

    def _dispatch(self, cmd: str, label: str):
        try:
            resp = self.dispatcher.process_command(cmd)
            self.add_log("CMD", f"{label} → {resp[:40]}")
        except Exception as e:
            self.add_log("ERR", str(e)[:40])
        finally:
            self._dispatch_busy.release()

    def add_log(self, source: str, text: str):
        """Añade una fila al log. Hilo-seguro via QTimer."""
        def _do():
            now = datetime.now().strftime("%H:%M")
            item = QListWidgetItem(f"[{now}] {source}: {text}")
            item.setForeground(QColor(ACC if source in ("CMD","VOZ") else TEXT_DIM))
            self.log_list.insertItem(0, item)
            if self.log_list.count() > 8:
                self.log_list.takeItem(self.log_list.count() - 1)
        QTimer.singleShot(0, _do)

    def update_status(self, tracking: str, zoom: float):
        """Actualiza los chips de estado del video."""
        self.chip_tracking.setText(f"▶ Tracking: {tracking}")
        self.chip_zoom.setText(f"⊕ Zoom: {zoom:.1f}x")

    # ── Cámara ────────────────────────────────────────────────────────────
    def update_video_frame(self, frame_bgr):
        """Recibe un frame BGR de OpenCV (numpy array) y lo pinta en la UI."""
        if frame_bgr is None:
            return
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(img).scaled(
            316, 178,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        # Actualizar en el hilo principal de UI
        QMetaObject.invokeMethod(self.video_label, "setPixmap", Qt.ConnectionType.QueuedConnection, Q_ARG(QPixmap, pix))

    # ── Estilo QSS ────────────────────────────────────────────────────────
    def _stylesheet(self) -> str:
        return f"""
        QWidget#card {{
            background: rgba(4,10,24,0.87);
            border: 1px solid rgba(0,229,255,0.26);
            border-radius: 16px;
        }}
        """

    # ── Posición y animación ──────────────────────────────────────────────
    def _position_near_tray(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 12,
                  screen.bottom() - self.height() - 12)

    def _anim_in(self):
        self.setWindowOpacity(0)
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(220)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    # ── Arrastrar sin bordes ──────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def closeEvent(self, event):
        super().closeEvent(event)
        global _panel_instance
        with _panel_lock:
            if _panel_instance is self:
                _panel_instance = None


# ─── Overlay de Escucha (Pill Widget) ─────────────────────────────────────────
class ListeningOverlay(QWidget):
    """
    Pastilla horizontal que aparece en la esquina superior derecha
    cuando NOVA detecta el wake word.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(240, 56)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 16, 0)
        lay.setSpacing(10)

        # Icono mic
        mic = QLabel("🎙")
        mic.setStyleSheet(f"""
            font: 18px 'Inter';
            color: {ACC};
            background: rgba(0,229,255,0.12);
            border: 1px solid rgba(0,229,255,0.32);
            border-radius: 18px;
            padding: 5px 7px;
        """)
        mic.setFixedSize(36, 36)
        mic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(mic)

        right = QVBoxLayout()
        right.setSpacing(4)

        lbl = QLabel("NOVA escuchando...")
        lbl.setStyleSheet(f"font: 600 11px 'Inter'; color: #ffffff; background: transparent;")
        right.addWidget(lbl)

        self.wave = AudioWave(ACC, bars=10)
        self.wave.set_active(True)
        right.addWidget(self.wave)
        lay.addLayout(right)

        self.setStyleSheet(f"""
            QWidget {{
                background: rgba(3,8,22,0.92);
                border: 1px solid rgba(0,229,255,0.30);
                border-radius: 28px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 229, 255, 40))
        self.setGraphicsEffect(shadow)

        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 16, screen.top() + 16)

        self._auto_hide = QTimer(self)
        self._auto_hide.setSingleShot(True)
        self._auto_hide.timeout.connect(self.hide)

    def show_listening(self, timeout_ms: int = 5000):
        self.wave.set_active(True)
        self.show()
        self._auto_hide.start(timeout_ms)

    def hide_listening(self):
        self.wave.set_active(False)
        self.hide()


# ─── Toast de Confirmación ────────────────────────────────────────────────────
class ToastNotification(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(300)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 12, 16, 12)
        lay.setSpacing(12)

        self.icon_lbl = QLabel("✓")
        self.icon_lbl.setFixedSize(32, 32)
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setStyleSheet("""
            background: rgba(0,215,120,0.12);
            border: 1.5px solid rgba(0,215,120,0.40);
            border-radius: 16px;
            color: #00d578;
            font: 700 13px 'Inter';
        """)
        lay.addWidget(self.icon_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(3)
        self.title_lbl = QLabel("Acción completada")
        self.title_lbl.setStyleSheet("font: 600 11px 'Inter'; color: #ffffff; background: transparent;")
        self.body_lbl = QLabel("")
        self.body_lbl.setStyleSheet(f"font: 400 10px 'Inter'; color: {TEXT_DIM}; background: transparent;")
        self.body_lbl.setWordWrap(True)
        text_col.addWidget(self.title_lbl)
        text_col.addWidget(self.body_lbl)
        lay.addLayout(text_col)

        self.setStyleSheet("""
            QWidget {
                background: rgba(8,12,24,0.93);
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 12px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.setGraphicsEffect(shadow)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

    def show_message(self, title: str, body: str, duration_ms: int = 3500, success: bool = True):
        self.title_lbl.setText(title)
        self.body_lbl.setText(body)
        if success:
            self.icon_lbl.setText("✓")
            self.icon_lbl.setStyleSheet("""
                background: rgba(0,215,120,0.12);
                border: 1.5px solid rgba(0,215,120,0.40);
                border-radius: 16px; color: #00d578; font: 700 13px 'Inter';
            """)
        else:
            self.icon_lbl.setText("✕")
            self.icon_lbl.setStyleSheet("""
                background: rgba(255,60,60,0.12);
                border: 1.5px solid rgba(255,60,60,0.40);
                border-radius: 16px; color: #ff4444; font: 700 13px 'Inter';
            """)
        self.adjustSize()
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 16,
                  screen.bottom() - self.height() - 64)
        self.show()
        self._hide_timer.start(duration_ms)


# ─── API pública ──────────────────────────────────────────────────────────────
_panel_instance: FloatingPanel | None = None
_toast_instance: ToastNotification | None = None
_listening_instance: ListeningOverlay | None = None
# Protege _panel_instance: se escribe desde el hilo de Qt (launch_panel/
# closeEvent) y se lee desde el hilo de visión de main.py (vía
# update_video_frame_safe más abajo).
_panel_lock = threading.Lock()

def launch_panel(dispatcher=None) -> FloatingPanel:
    global _panel_instance
    with _panel_lock:
        if _panel_instance and not _panel_instance.isHidden():
            _panel_instance.raise_()
            _panel_instance.activateWindow()
            return _panel_instance
        _panel_instance = FloatingPanel(dispatcher)
        _panel_instance.show()
        return _panel_instance

def update_video_frame_safe(frame_bgr):
    """Punto de entrada seguro para hilos que no son el de Qt (ej. el hilo de
    visión en main.py) para actualizar el video del panel.

    Antes, ese hilo llamaba directamente a `_panel_instance.isHidden()` y
    `.update_video_frame()` fuera del hilo de Qt — una violación de las
    reglas de thread-affinity de Qt (comportamiento indefinido, no solo el
    `RuntimeError` de objeto-ya-destruido que sí se capturaba). Aquí solo se
    lee la referencia bajo lock; la llamada real a métodos de Qt se agenda
    en el hilo de Qt vía QTimer.singleShot, igual que show_toast/show_listening.
    """
    with _panel_lock:
        panel = _panel_instance
    if panel is None:
        return

    def _do():
        try:
            if not panel.isHidden():
                panel.update_video_frame(frame_bgr)
        except RuntimeError:
            # El panel se cerró (objeto Qt destruido) justo entre la lectura
            # de la referencia y su uso ya dentro del hilo de Qt.
            pass
    QTimer.singleShot(0, QApplication.instance(), _do)

def update_status_safe(tracking: str, zoom: float):
    """Punto de entrada seguro para hilos para actualizar la barra de estado/chips HUD."""
    with _panel_lock:
        panel = _panel_instance
    if panel is None:
        return

    def _do():
        try:
            if not panel.isHidden():
                panel.update_status(tracking, zoom)
        except RuntimeError:
            pass
    QTimer.singleShot(0, QApplication.instance(), _do)

def show_toast(title: str, body: str, success: bool = True):
    def _do():
        global _toast_instance
        if _toast_instance is None:
            _toast_instance = ToastNotification()
        _toast_instance.show_message(title, body, success=success)
    QTimer.singleShot(0, QApplication.instance(), _do)

def show_listening(timeout_ms: int = 5000):
    def _do():
        global _listening_instance
        if _listening_instance is None:
            _listening_instance = ListeningOverlay()
        _listening_instance.show_listening(timeout_ms)
    QTimer.singleShot(0, QApplication.instance(), _do)

def hide_listening():
    def _do():
        global _listening_instance
        if _listening_instance is not None:
            _listening_instance.hide_listening()
    QTimer.singleShot(0, QApplication.instance(), _do)


# ─── Test standalone ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.DEBUG)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    class MockDispatcher:
        def process_command(self, text):
            print(f"[MOCK] Comando recibido: '{text}'")
            return f"OK: {text}"

    panel = launch_panel(MockDispatcher())
    panel.show()

    # Demo toast a los 2s
    QTimer.singleShot(2000, lambda: show_toast("Blender abierto", "Blender 5.1.2 iniciando..."))

    sys.exit(app.exec())
