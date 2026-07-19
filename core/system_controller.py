import os
import time
import datetime
import logging
import threading
import subprocess
import pyautogui
import psutil
import win32gui
import win32con
import win32process
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

logger = logging.getLogger(__name__)

class SystemController:
    """
    Controlador para interactuar con el sistema operativo Windows.
    Permite subir/bajar volumen, tomar capturas de pantalla, 
    minimizar ventanas, etc.
    """
    def __init__(self):
        self.screenshots_dir = os.path.join(os.path.expanduser("~"), "Pictures", "NOVA_Screenshots")
        if not os.path.exists(self.screenshots_dir):
            os.makedirs(self.screenshots_dir)
            logger.info(f"Directorio de capturas creado en {self.screenshots_dir}")

    def take_screenshot(self) -> str:
        """Toma una captura de pantalla completa y la guarda."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(self.screenshots_dir, f"Captura_{timestamp}.png")
        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            logger.info(f"Captura guardada: {filename}")
            return f"Captura de pantalla guardada"
        except Exception as e:
            logger.error(f"Error tomando captura: {e}")
            return "Error al tomar la captura de pantalla"

    def change_volume(self, increase: bool = True, step: float = 0.1):
        """Aumenta o disminuye el volumen general del sistema simulando las teclas multimedia."""
        try:
            # step 0.1 ~ 10% = usualmente 5 pulsaciones de tecla (cada una es 2%)
            presses = max(1, int(step * 50))
            key = 'volumeup' if increase else 'volumedown'
            for _ in range(presses):
                pyautogui.press(key)
                
            action = "subido" if increase else "bajado"
            logger.info(f"Volumen {action} simulando tecla {key}")
            return f"Volumen {action}"
        except Exception as e:
            logger.error(f"Error cambiando volumen: {e}")
            return "Hubo un error cambiando el volumen"

    def mute_volume(self):
        """Silencia o reactiva el audio del sistema."""
        try:
            pyautogui.press('volumemute')
            logger.info("Tecla de Mute simulada")
            return "Audio silenciado o reactivado"
        except Exception as e:
            logger.error(f"Error silenciando volumen: {e}")
            return "Hubo un error con el control de audio"

    def close_application(self, app_name: str) -> str:
        """Intenta cerrar una aplicación buscando su nombre en los procesos."""
        app_name = app_name.lower()
        killed_any = False
        
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and app_name in proc.info['name'].lower():
                    proc.kill()
                    killed_any = True
            
            if killed_any:
                logger.info(f"Aplicación {app_name} cerrada.")
                return f"Aplicación {app_name} cerrada"
            else:
                return f"No encontré ninguna aplicación abierta llamada {app_name}"
        except Exception as e:
            logger.error(f"Error cerrando aplicación {app_name}: {e}")
            return f"Error al intentar cerrar {app_name}"

    def scroll(self, up: bool = True, amount: int = 500):
        """Simula scroll en la pantalla."""
        if up:
            pyautogui.scroll(amount)
        else:
            pyautogui.scroll(-amount)
        return "Desplazando pantalla"

    def type_text(self, text: str):
        """Escribe texto simulando teclado."""
        try:
            pyautogui.write(text, interval=0.01)
            return "Texto escrito"
        except Exception as e:
            logger.error(f"Error escribiendo texto: {e}")
            return "Error al escribir"

    def show_desktop(self):
        """Muestra el escritorio minimizando todas las ventanas."""
        pyautogui.hotkey('win', 'd')
        return "Mostrando escritorio"

    def next_window(self):
        """Cambia a la siguiente ventana activa."""
        pyautogui.hotkey('alt', 'tab')
        return "Siguiente ventana"

    def launch_obsbot_center(self, exe_path: str) -> bool:
        """Lanza el driver de OBSBOT en segundo plano y minimiza su ventana en cuanto aparece.

        OBSBOT_Main.exe termina abriendo la ventana de OBSBOT_Center.exe como un proceso
        aparte, por lo que minimizar solo la ventana del proceso lanzado (vía STARTUPINFO)
        no basta: hay que buscar la ventana ya abierta y minimizarla.
        """
        process_names = ("OBSBOT_Center.exe", "OBSBOT_Main.exe")
        process_name = os.path.basename(exe_path)
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and proc.info['name'].lower() == process_name.lower():
                logger.info(f"{process_name} ya está en ejecución, no se relanza.")
                threading.Thread(target=self._minimize_window_by_process, args=(process_names,), daemon=True).start()
                return True

        if not os.path.exists(exe_path):
            logger.error(f"No se encontró el ejecutable de OBSBOT en {exe_path}")
            return False

        # Asegurar OSC=true en global.ini antes de iniciar
        try:
            appdata = os.environ.get("APPDATA")
            if appdata:
                ini_path = os.path.join(appdata, "OBSBOT_Center", "global.ini")
                if os.path.exists(ini_path):
                    with open(ini_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    
                    in_soft_setting = False
                    modified = False
                    new_lines = []
                    for line in lines:
                        trimmed = line.strip()
                        if trimmed.startswith("[") and trimmed.endswith("]"):
                            in_soft_setting = (trimmed.lower() == "[softsetting]")
                        
                        if in_soft_setting and trimmed.startswith("OSC="):
                            if trimmed != "OSC=true":
                                new_lines.append("OSC=true\n")
                                modified = True
                                continue
                        new_lines.append(line)
                    
                    if modified:
                        with open(ini_path, "w", encoding="utf-8") as f:
                            f.writelines(new_lines)
                        logger.info("Forzado OSC=true en global.ini antes de iniciar OBSBOT.")
        except Exception as e:
            logger.error(f"Error forzando OSC=true en global.ini: {e}")

        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.Popen(
                [exe_path],
                cwd=os.path.dirname(exe_path),
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            logger.info(f"OBSBOT lanzado en segundo plano: {exe_path}")
            threading.Thread(target=self._minimize_window_by_process, args=(process_names,), daemon=True).start()
            return True
        except Exception as e:
            logger.error(f"Error lanzando OBSBOT ({exe_path}): {e}")
            return False

    def _minimize_window_by_process(self, process_names, timeout: float = 15.0, poll_interval: float = 0.5):
        """Busca por polling la ventana principal de alguno de los procesos y la minimiza.

        Buscar por título de ventana (win32gui.GetWindowText) resultó poco confiable:
        OBSBOT Center dibuja su propia barra de título (ventana sin marco), así que el
        título real reportado a Windows no siempre contiene "OBSBOT". Buscar por el
        proceso dueño de cada ventana (GetWindowThreadProcessId) es robusto sin importar
        el texto que la app decida mostrar.

        Usamos SW_MINIMIZE en vez de SW_HIDE: una ventana oculta con SW_HIDE dejaba de
        recibir foco/prioridad de Windows y el tracking de OBSBOT dejaba de responder a
        los comandos OSC.
        """
        elapsed = 0.0
        while elapsed < timeout:
            hwnd = self._find_window_by_process(process_names)
            if hwnd:
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                logger.info(f"Ventana de {process_names} (hwnd={hwnd}) minimizada.")
                return True
            time.sleep(poll_interval)
            elapsed += poll_interval
        logger.warning(f"No se encontró ventana de {process_names} para minimizar tras {timeout}s.")
        return False

    def _find_window_by_process(self, process_names):
        """Devuelve el hwnd visible más grande perteneciente a alguno de los procesos indicados."""
        wanted = {p.lower() for p in process_names}
        candidates = []

        def enum_handler(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc_name = psutil.Process(pid).name().lower()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Esperado: procesos que desaparecen o a los que no tenemos
                # acceso mientras se enumeran las ventanas — no son errores reales.
                return
            except Exception as e:
                # Antes esto se tragaba junto con los dos casos esperados de
                # arriba (el Exception genérico los hacía redundantes),
                # ocultando bugs reales de win32gui/win32process. Ahora se
                # loggea para que un fallo inesperado no desaparezca en silencio.
                logger.debug(f"Error inesperado inspeccionando ventana {hwnd}: {e}")
                return
            if proc_name not in wanted:
                return
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            area = max(0, right - left) * max(0, bottom - top)
            candidates.append((area, hwnd))

        win32gui.EnumWindows(enum_handler, None)
        if not candidates:
            return None
        # La ventana principal suele ser la más grande (evita popups/helpers diminutos)
        candidates.sort(key=lambda c: c[0], reverse=True)
        return candidates[0][1]

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    sys = SystemController()
    sys.change_volume(increase=True)
