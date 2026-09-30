# -*- coding: utf-8 -*-
"""
Manejador de Línea de Comandos para NOVA (core/cli_handler.py).
Interfaz de usuario en terminal rápida, determinista y colorida para desarrolladores.
"""
import os
import sys
import time
import subprocess
from pathlib import Path

from core.ipc_server import send_ipc_command, DEFAULT_SOCKET_PATH


CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"


def ensure_daemon_running():
    """Verifica si el daemon está vivo; si no, lo inicia en segundo plano automáticamente."""
    if not os.path.exists(DEFAULT_SOCKET_PATH):
        proj_dir = Path(__file__).resolve().parent.parent
        venv_python = proj_dir / ".venv" / "bin" / "python"
        daemon_script = proj_dir / "core" / "daemon.py"
        
        # Lanzar daemon en background desvinculado
        subprocess.Popen(
            [str(venv_python), "-m", "core.daemon"],
            cwd=str(proj_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        # Esperar hasta 2 segundos a que el socket exista
        for _ in range(20):
            if os.path.exists(DEFAULT_SOCKET_PATH):
                break
            time.sleep(0.1)


def cmd_ping():
    ensure_daemon_running()
    res = send_ipc_command({"action": "ping"})
    if res.get("status") == "success":
        result = res.get("result", {})
        telem = result.get("telemetry", {})
        print(f"{GREEN}✓ NOVA Daemon 2.0 activo{RESET} (Uptime: {result.get('uptime_seconds', 0)}s)")
        print(f"  CPU: {telem.get('cpu_percent')}% | RAM: {telem.get('ram_percent')}% | GPU: {telem.get('gpu_temp_c')}°C | VRAM: {telem.get('gpu_vram_used_mb')}/{telem.get('gpu_vram_total_mb')} MB")
    else:
        print(f"{RED}✗ Error conectando con el daemon:{RESET} {res.get('message')}")


def cmd_fix():
    ensure_daemon_running()
    print(f"{CYAN}🔍 Analizando último fallo en terminal con IA local...{RESET}")
    res = send_ipc_command({"action": "fix"}, timeout=25.0)
    if res.get("status") == "success":
        diag = res.get("result", {})
        if not diag.get("success"):
            print(f"{YELLOW}ℹ {diag.get('message')}{RESET}")
            return

        print(f"\n{BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
        print(f"{RED}Comando fallido:{RESET} `{diag.get('cmd_original')}` {YELLOW}(código {diag.get('exit_code')}){RESET}")
        print(f"{BOLD}Causa:{RESET} {diag.get('causa')}")
        cmd_fix = diag.get('comando_corregido', '')
        if cmd_fix:
            print(f"\n{GREEN}{BOLD}Comando corregido sugerido:{RESET}")
            print(f"  {BOLD}{CYAN}{cmd_fix}{RESET}")
        if diag.get('accion_inmediata'):
            print(f"  ↳ {diag.get('accion_inmediata')}")
        print(f"{BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")
    else:
        print(f"{RED}✗ Error:{RESET} {res.get('message')}")


def cmd_standup():
    ensure_daemon_running()
    print(f"{CYAN}📂 Escaneando actividad Git en ~/Datos/Projects y sincronizando Obsidian...{RESET}")
    res = send_ipc_command({"action": "standup"})
    if res.get("status") == "success":
        result = res.get("result", {})
        print(f"\n{GREEN}✓ {result.get('status_msg')}{RESET}")
        print(f"  Total de Commits de hoy: {BOLD}{result.get('total_commits')}{RESET}")
        print(f"  Repositorios con actividad: {BOLD}{result.get('projects_count')}{RESET}")
        print(f"  Archivo actualizado: {CYAN}{result.get('file_path')}{RESET}\n")
    else:
        print(f"{RED}✗ Error:{RESET} {res.get('message')}")


def cmd_inspect(mode="auto"):
    ensure_daemon_running()
    print(f"{CYAN}📐 Selecciona el área con el ratón en tu pantalla...{RESET}")
    res = send_ipc_command({"action": "inspect_region", "mode": mode}, timeout=45.0)
    if res.get("status") == "success":
        result = res.get("result", {})
        if not result.get("success"):
            print(f"{YELLOW}ℹ {result.get('message')}{RESET}")
            return
        print(f"\n{GREEN}✓ {result.get('message')}{RESET}")
        print(f"\n{BOLD}--- Contenido extraído ---{RESET}")
        print(result.get("result", ""))
        print(f"{BOLD}--------------------------{RESET}\n")
    else:
        print(f"{RED}✗ Error:{RESET} {res.get('message')}")


def cmd_ask(prompt: str):
    ensure_daemon_running()
    res = send_ipc_command({"action": "ask", "text": prompt}, timeout=25.0)
    if res.get("status") == "success":
        print(f"\n{CYAN}{BOLD}NOVA:{RESET} {res.get('result', '')}\n")
    else:
        print(f"{RED}✗ Error:{RESET} {res.get('message')}")


def cmd_telemetry():
    ensure_daemon_running()
    res = send_ipc_command({"action": "telemetry"})
    if res.get("status") == "success":
        t = res.get("result", {})
        print(f"\n{BOLD}🛡 TELEMETRÍA DE ESTACIÓN DE TRABAJO (HP Pavilion){RESET}")
        print(f"  Procesador CPU:  {GREEN}{t.get('cpu_percent')}%{RESET}")
        print(f"  Memoria RAM:     {CYAN}{t.get('ram_percent')}% usado{RESET}")
        print(f"  GPU GTX 1050:    {YELLOW}{t.get('gpu_temp_c')} °C{RESET} (VRAM: {t.get('gpu_vram_used_mb')} / {t.get('gpu_vram_total_mb')} MB)")
        print(f"  Batería:         {GREEN}{t.get('battery_percent')}%{RESET}\n")
    else:
        print(f"{RED}✗ Error:{RESET} {res.get('message')}")


def cmd_blender():
    ensure_daemon_running()
    print(f"{CYAN}🎨 Preparando VRAM de GTX 1050 y lanzando Blender con PRIME offload...{RESET}")
    res = send_ipc_command({"action": "blender"})
    if res.get("status") == "success":
        print(f"{GREEN}✓ {res.get('result')}{RESET}")
    else:
        print(f"{RED}✗ Error:{RESET} {res.get('message')}")


def cmd_projects():
    ensure_daemon_running()
    res = send_ipc_command({"action": "projects"})
    if res.get("status") == "success":
        data = res.get("result", {})
        projs = data.get("projects", [])
        print(f"\n{BOLD}🌐 INVENTARIO MASTER DE PROYECTOS ({len(projs)} activos en Obsidian){RESET}")
        for p in projs:
            print(f"  - {CYAN}{BOLD}{p['name']}{RESET} (`{p['code']}`): {p['desc'][:65]}...")
        print("")
    else:
        print(f"{RED}✗ Error:{RESET} {res.get('message')}")


def cmd_open_project(name: str):
    ensure_daemon_running()
    res = send_ipc_command({"action": "open_project", "name": name, "mode": "code"})
    if res.get("status") == "success":
        print(f"{GREEN}✓ {res.get('result', {}).get('message')}{RESET}")
    else:
        print(f"{RED}✗ Error:{RESET} {res.get('message')}")


def show_help():
    print(f"""
{BOLD}{CYAN}NOVA 2.0 — Copiloto de Estación de Trabajo Linux (CLI){RESET}

{BOLD}USO:{RESET}
  nova                         Abre la paleta de comandos Spotlight HUD
  nova fix                     Diagnostica y sugiere solución al último comando fallido
  nova standup                 Sincroniza commits de hoy en ~/Datos/Projects con Obsidian
  nova inspect [diagram|ocr]   Captura interactiva de región y copia resultado al portapapeles
  nova ask "<pregunta>"        Consulta rápida al modelo local de código
  nova telemetry | status      Muestra telemetría de CPU, RAM, GPU y temperaturas
  nova blender                 Libera VRAM de la GTX 1050 y lanza Blender con PRIME offload
  nova projects                Lista los 17 proyectos documentados en Obsidian
  nova open <proyecto>         Abre el proyecto directamente en VS Code
  nova daemon                  Inicia el servicio en segundo plano manualmente
""")


def main():
    args = sys.argv[1:]
    if not args:
        # Abrir HUD Spotlight
        proj_dir = Path(__file__).resolve().parent.parent
        venv_python = proj_dir / ".venv" / "bin" / "python"
        hud_script = proj_dir / "ui" / "spotlight_hud.py"
        subprocess.Popen([str(venv_python), str(hud_script)], cwd=str(proj_dir))
        return

    subcmd = args[0].lower()

    if subcmd in ["help", "--help", "-h"]:
        show_help()
    elif subcmd == "daemon":
        from core.daemon import main as daemon_main
        daemon_main()
    elif subcmd == "fix":
        cmd_fix()
    elif subcmd in ["standup", "daily", "sync"]:
        cmd_standup()
    elif subcmd in ["inspect", "captura", "roi"]:
        mode = args[1].lower() if len(args) > 1 else "auto"
        cmd_inspect(mode)
    elif subcmd in ["ask", "pregunta"]:
        prompt = " ".join(args[1:]) if len(args) > 1 else ""
        if not prompt:
            print(f"{YELLOW}Uso: nova ask \"tu consulta aquí\"{RESET}")
            return
        cmd_ask(prompt)
    elif subcmd in ["status", "telemetry", "estado"]:
        cmd_telemetry()
    elif subcmd == "blender":
        cmd_blender()
    elif subcmd in ["projects", "proyectos"]:
        cmd_projects()
    elif subcmd in ["open", "abre"]:
        if len(args) < 2:
            print(f"{YELLOW}Uso: nova open <nombre_proyecto>{RESET}")
            return
        cmd_open_project(args[1])
    else:
        # Si se le pasa texto libre, tratarlo como prompt directo
        cmd_ask(" ".join(args))


if __name__ == "__main__":
    main()
