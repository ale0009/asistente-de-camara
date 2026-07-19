"""
Script de compilación y empaquetado autónomo para NOVA usando PyInstaller.

Genera un ejecutable ejecutable (.exe) de Windows en la carpeta dist/NOVA.
Uso:
    python build_exe.py
"""

import os
import sys
import subprocess

def build():
    print("=== Iniciando compilación de NOVA con PyInstaller ===")

    # Asegurar que pyinstaller está instalado
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller no encontrado, instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "NOVA",
        "--add-data", "config.yaml;.",
        "--add-data", "presets;presets",
        "--add-data", "assets;assets",
        "--add-data", "docs;docs",
        "main.py"
    ]

    print(f"Ejecutando comando: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    print("\n¡Compilación completada! El ejecutable se encuentra en dist/NOVA/NOVA.exe")

if __name__ == "__main__":
    build()
