import os
import sys

def create_shortcut():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
    start_menu = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs")
    
    python_exe = sys.executable
    target_script = os.path.join(base_dir, "start_nova_agent.py")

    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")

        # 1. Escritorio
        sc1_path = os.path.join(desktop, "NOVA Assistant.lnk")
        sc1 = shell.CreateShortcut(sc1_path)
        sc1.TargetPath = python_exe
        sc1.Arguments = f'"{target_script}"'
        sc1.WorkingDirectory = base_dir
        sc1.Description = "NOVA - Asistente Agéntico de Cámara Inteligente"
        sc1.Save()
        print(f"Acceso directo de Escritorio creado: {sc1_path}")

        # 2. Menú Inicio
        sc2_path = os.path.join(start_menu, "NOVA Assistant.lnk")
        sc2 = shell.CreateShortcut(sc2_path)
        sc2.TargetPath = python_exe
        sc2.Arguments = f'"{target_script}"'
        sc2.WorkingDirectory = base_dir
        sc2.Description = "NOVA - Asistente Agéntico de Cámara Inteligente"
        sc2.Save()
        print(f"Acceso directo de Menú Inicio creado: {sc2_path}")

    except Exception as e:
        print(f"Error creando accesos directos: {e}")

if __name__ == "__main__":
    create_shortcut()
