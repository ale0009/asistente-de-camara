import sys
import logging
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QCoreApplication

# Importar la función que crea el panel flotante
from ui.panel_widget import launch_panel

logger = logging.getLogger(__name__)

class NovaTrayApp:
    """Aplicación que vive en la bandeja del sistema y lanza el panel flotante de NOVA."""
    def __init__(self, app: QApplication, dispatcher=None):
        self.app = app
        self.dispatcher = dispatcher
        self.tray_icon = QSystemTrayIcon(self.app)
        
        # Icono de la bandeja (se reemplazará cuando haya un asset definitivo)
        try:
            self.tray_icon.setIcon(QIcon("assets/nova_icon.png"))
        except Exception as e:
            logger.warning(f"No se pudo cargar el icono de la bandeja: {e}")
        self.tray_icon.setToolTip("NOVA - Asistente IA")
        
        # Menú contextual
        self.menu = QMenu()
        self.action_panel = QAction("Abrir panel principal")
        self.action_panel.triggered.connect(self.show_panel)
        self.menu.addAction(self.action_panel)
        
        self.action_test_ui = QAction("Simular 'NOVA escuchando' (Prueba)")
        self.action_test_ui.triggered.connect(self.test_listening_ui)
        self.menu.addAction(self.action_test_ui)
        
        self.menu.addSeparator()
        self.action_exit = QAction("Salir")
        self.action_exit.triggered.connect(self.exit_app)
        self.menu.addAction(self.action_exit)
        self.tray_icon.setContextMenu(self.menu)

        # También abrir el panel con click o doble click
        self.tray_icon.activated.connect(self.on_tray_activated)

    def on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.show_panel()

    def start(self):
        self.tray_icon.show()
        logger.info("NovaTrayApp iniciada en la bandeja del sistema")

    def show_panel(self):
        if self.dispatcher:
            launch_panel(self.dispatcher)
            logger.info("Panel flotante lanzado mediante dispatcher.")
        else:
            logger.warning("Dispatcher no configurado; no se puede abrir el panel.")

    def test_listening_ui(self):
        import ui.panel_widget as pw
        pw.show_listening()
        # Ocultar automáticamente después de 3 segundos para la prueba
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, pw.hide_listening)
        logger.info("Prueba de interfaz de escucha disparada manualmente.")

    def exit_app(self):
        logger.info("Saliendo de NOVA...")
        QCoreApplication.quit()

def run_ui(dispatcher=None):
    """Arranca la QApplication y la bandeja. Se pasa opcionalmente el dispatcher.
    El dispatcher proviene de main.py y contiene toda la lógica de comandos.
    """
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    nova_tray = NovaTrayApp(app, dispatcher)
    nova_tray.start()
    return app.exec()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    sys.exit(run_ui())
