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


def cmd_clipboard_refactor():
    ensure_daemon_running()
    print(f"{CYAN}📋 Refactorizando código del portapapeles con IA local...{RESET}")
    res = send_ipc_command({"action": "clipboard_refactor"})
    if res.get("status") == "success":
        data = res.get("result", {})
        if data.get("success"):
            print(f"{GREEN}✓ {data.get('message')}{RESET}")
        else:
            print(f"{YELLOW}! {data.get('message')}{RESET}")
    else:
        print(f"{RED}✗ Error:{RESET} {res.get('message')}")


def cmd_clipboard_explain():
    ensure_daemon_running()
    print(f"{CYAN}📋 Analizando y explicando contenido del portapapeles...{RESET}")
    res = send_ipc_command({"action": "clipboard_explain"})
    if res.get("status") == "success":
        data = res.get("result", {})
        if data.get("success"):
            print(f"\n{BOLD}Explicación:{RESET}\n{data.get('content')}\n")
        else:
            print(f"{YELLOW}! {data.get('message')}{RESET}")
    else:
        print(f"{RED}✗ Error:{RESET} {res.get('message')}")


def cmd_quick_note(content: str):
    ensure_daemon_running()
    res = send_ipc_command({"action": "quick_note", "content": content})
    if res.get("status") == "success":
        data = res.get("result", {})
        if data.get("success"):
            print(f"{GREEN}✓ {data.get('message')}{RESET}")
        else:
            print(f"{YELLOW}! {data.get('message')}{RESET}")
    else:
        print(f"{RED}✗ Error:{RESET} {res.get('message')}")


def cmd_tray():
    proj_dir = Path(__file__).resolve().parent.parent
    venv_python = proj_dir / ".venv" / "bin" / "python"
    tray_script = proj_dir / "ui" / "tray_app.py"
    subprocess.Popen([str(venv_python), str(tray_script)], cwd=str(proj_dir))
    print(f"{GREEN}✓ Icono de NOVA iniciado en la barra de tareas.{RESET}")


def cmd_voice(duration: int = 5):
    ensure_daemon_running()
    print(f"{CYAN}🎤 Grabando tu voz ({duration}s)... Habla ahora.{RESET}")
    res = send_ipc_command({"action": "voice_query", "duration": duration}, timeout=25.0)
    if res.get("status") == "success":
        data = res.get("result", {})
        if data.get("success"):
            print(f"\n{BOLD}Tú dijiste:{RESET} \"{data.get('transcription')}\"")
            print(f"{BOLD}{GREEN}NOVA responde:{RESET} {data.get('response')}")
            print(f"{MAGENTA}(Latencia total: {data.get('latency_seconds')}s){RESET}\n")
        else:
            print(f"{YELLOW}! {data.get('message')}{RESET}")
    else:
        print(f"{RED}✗ Error:{RESET} {res.get('message')}")


def cmd_speak(text: str):
    ensure_daemon_running()
    send_ipc_command({"action": "speak", "text": text})


def cmd_todo_radar():
    ensure_daemon_running()
    print(f"{CYAN}📋 Escaneando comentarios TODO/FIXME en repositorios locales...{RESET}")
    res = send_ipc_command({"action": "todo_radar"}, timeout=15.0)
    if res.get("status") == "success":
        data = res.get("result", {})
        total = data.get("total_items", 0)
        projs = data.get("projects_count", 0)
        path = data.get("report_path", "")
        print(f"{GREEN}✓ Radar completado:{RESET} {total} tareas detectadas en {projs} proyectos.")
        print(f"  Reporte guardado en Obsidian: {CYAN}{path}{RESET}")
    else:
        print(f"{RED}✗ Error:{RESET} {res.get('message')}")


def show_help():
    print(f"""
{BOLD}{CYAN}NOVA 2.0 — Copiloto de Estación de Trabajo Linux (CLI){RESET}

{BOLD}USO:{RESET}
  nova                         Abre la paleta de comandos Spotlight HUD
  nova tray                    Inicia el icono en la bandeja del sistema (barra de tareas)
  nova talk | voice [segundos] Conversación por voz con Whisper GPU y Kokoro (Push-to-Talk)
  nova todos | radar           Genera el Radar de TODOs y Deuda Técnica en Obsidian
  nova fix                     Diagnostica y sugiere solución al último comando fallido
  nova standup                 Sincroniza commits de hoy en ~/Datos/Projects con Obsidian
  nova inspect [diagram|ocr]   Captura interactiva de región y copia resultado al portapapeles
  nova refactor                Refactoriza el código actualmente copiado en el portapapeles
  nova explain                 Explica en 3 viñetas el código/error del portapapeles
  nova note "<texto>"          Guarda una nota o idea rápida en Obsidian (00_Inbox)
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
    elif subcmd in ["tray", "bandeja"]:
        cmd_tray()
    elif subcmd in ["refactor", "refactorizar"]:
        cmd_clipboard_refactor()
    elif subcmd in ["explain", "explicar"]:
        cmd_clipboard_explain()
    elif subcmd in ["note", "nota"]:
        content = " ".join(args[1:]) if len(args) > 1 else ""
        if not content:
            print(f"{YELLOW}Uso: nova note \"tu idea o nota rápida\"{RESET}")
            return
        cmd_quick_note(content)
    elif subcmd in ["voice", "talk", "voz", "habla"]:
        dur = int(args[1]) if len(args) > 1 and args[1].isdigit() else 5
        cmd_voice(duration=dur)
    elif subcmd == "speak":
        text = " ".join(args[1:]) if len(args) > 1 else ""
        if text:
            cmd_speak(text)
    elif subcmd in ["todos", "radar", "deuda"]:
        cmd_todo_radar()
    else:
        # Si se le pasa texto libre, tratarlo como prompt directo
        cmd_ask(" ".join(args))


if __name__ == "__main__":
    main()
