# MAPA Arquitectónico del Proyecto NOVA — Fuente Raíz para Desarrollo

> **Regla de oro:** Este archivo es la fuente principal de lectura técnica del proyecto NOVA. Describe la arquitectura de software, el mapa de archivos, el modelo de hilos, los flujos de datos, los servidores MCP y la configuración del sistema. Debe actualizarse tras cada modificación estructural.
> Última actualización: **Fase Agéntica MCP (Agent Loop FastAPI, Servidores MCP Vault & Desktop, Canal de Voz Desacoplado, Watchers de Archivos y Auditoría en Base de Datos)**.

---

## 1. Visión General y Arquitectura Agéntica MCP

NOVA combina percepción multimodal en tiempo real (voz y gestos) con la ejecución autónoma de acciones mediante el estándar **MCP (Model Context Protocol)** y un servicio de orquestación desacoplado en **FastAPI**.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                CAPA DE ENTRADA (Percepción)                            │
│  · Voz: openWakeWord → Whisper STT → VoiceServiceChannel (`voice_service/`)           │
│  · Visión/Gestos: MediaPipe Tasks (30 FPS) → Camera & Gesture Engine (`core/`)        │
│  · Watchers: Watchdog en caliente (`watchers/file_watcher.py`)                         │
│  · UI: Panel PyQt6 / System Tray (`ui/`)                                               │
└───────────────────────────────────────────────────┬────────────────────────────────────┘
                                                    │ REST / WebSocket (`/v1/agent/interact`)
┌───────────────────────────────────────────────────▼────────────────────────────────────┐
│                             CAPA DE ORQUESTACIÓN ("NOVA Agent Loop")                    │
│  · Servicio FastAPI (`agent_service/main.py`)                                          │
│  · AgentLoop & Router de Intención (`agent_service/agent_loop.py`)                      │
│  · Registro de Auditoría SQLite/Postgres (`agent_service/audit_logger.py`)             │
└───────┬───────────────────────────────────────────┬────────────────────────────────────┘
        │ Tool Calls (MCP Protocol over Python API) │ Tareas Pesadas
┌───────▼──────────────────────────────────┐      ┌─▼────────────────────────────────────┐
│      CAPA DE HERRAMIENTAS (MCP Servers)  │      │     CAPA DE EJECUCIÓN (Workers)      │
│  · Obsidian Vault MCP Server             │      │  · Celery Workers                    │
│  · Desktop Control MCP Server (SO/Apps)   │      │  · VRAMLock Manager (RTX 5060 8GB)   │
│  · Filesystem & Git MCP Server           │      └──────────────────────────────────────┘
└──────────────────────────────────────────┘
```

---

## 2. Mapa de Archivos y Responsabilidades

| Componente | Archivo | Responsabilidad Principal |
|---|---|---|
| **Orquestador Agéntico** | `agent_service/main.py` | Servicio FastAPI que expone la API REST (`/v1/agent/interact`, `/v1/agent/tools`, `/v1/agent/audit`) y el canal WebSocket. |
| **Agent Loop** | `agent_service/agent_loop.py` | Motor de decisión que procesa entradas, clasifica intenciones, invoca herramientas MCP y audita resultados. |
| **Router de Intención** | `agent_service/intent_router.py` | Clasificador semántico respaldado en Ollama `qwen3:8b` (Respuestas directas vs. MCP Tool Calls vs. Celery Tasks). |
| **Gestor MCP** | `agent_service/mcp_client.py` | Cliente MCP que descubre herramientas y despacha su ejecución síncrona/asíncrona. |
| **Auditoría DB** | `agent_service/audit_logger.py` | Registro de trazabilidad en base de datos SQLite/Postgres (`agent_audit_log`). |
| **MCP Vault Server** | `mcp_servers/vault_mcp.py` | Servidor MCP para Obsidian Vault. Incluye protección estricta `OverwriteError` para documentos estratégicos (`Charter.md`, `ADRs`, `Actas`). |
| **MCP Desktop Server** | `mcp_servers/desktop_mcp.py` | Servidor MCP para control de Windows (lanzamiento de apps, volumen y capturas). |
| **Canal de Voz** | `voice_service/voice_client.py` | Servicio de voz desacoplado que envía audio transcrito al Agent Loop de FastAPI y sintetiza la respuesta con TTS. |
| **Watcher de Archivos**| `watchers/file_watcher.py` | Observador en tiempo real de cambios en `E:\proyectos\` y el Vault de Obsidian. |
| **Orquestador UI** | `main.py` | Punto de entrada principal de la aplicación con GUI PyQt6. |
| **Percepción Visión** | `core/camera.py` | Captura OpenCV DirectShow a 30 FPS con reconexión automática `pygrabber`. |
| **Control OSC** | `core/osc_controller.py` | Cliente UDP OSC hacia OBSBOT Center (puerto 16284). |
| **Percepción Audio** | `core/voice_engine.py` | openWakeWord, Whisper STT local y síntesis de voz edge-tts/pygame. |
| **Percepción Gestos** | `core/gesture_engine.py` | MediaPipe Tasks (`HandLandmarker`) a 30 FPS con zoom por pellizco. |
| **Despachador** | `core/command_dispatcher.py` | Cerebro de acciones en lista blanca e integración con hardware. |
| **Pruebas** | `tests/` | Suite de 79 tests unitarios pasando al 100%. |

---

## 3. Modelo de Hilos y Concurrencia

NOVA opera en una arquitectura multi-hilo y multi-servicio desacoplada:

```
─────────────────────────────────────────────────────────────────────────────
 Hilo Principal (Qt GUI Thread)
 └── `main.py` -> `run_ui()` -> `QApplication.exec()`
     ├── Renderizado del Panel Flotante PyQt6 (Glassmorphism)
     └── Notificaciones Toast y Onda de Audio Reactiva

 Servicio 1: FastAPI Agent Service (`agent_service/main.py`)
 └── Uvicorn / FastAPI en puerto 8000 -> AgentLoop & MCP Manager

 Servicio 2: Canal de Voz Desacoplado (`voice_service/voice_client.py`)
 └── `VoiceEngine` -> PyAudio -> openWakeWord -> Whisper -> POST /v1/agent/interact

 Servicio 3: File Watcher (`watchers/file_watcher.py`)
 └── Monitoreo en caliente de `E:\proyectos\` & Obsidian Vault -> POST /v1/agent/interact

 Hilo 4: Captura de Cámara & Visión MediaPipe (`core/camera.py` & `gesture_engine.py`)
 └── Captura OpenCV DirectShow (30 FPS) -> MediaPipe HandLandmarker
─────────────────────────────────────────────────────────────────────────────
```

---

## 4. Matriz de Comandos y Protocolo OSC

El control de la cámara **OBSBOT Tiny 3 Lite** se realiza mediante datagramas UDP OSC hacia OBSBOT Center (`127.0.0.1:16284`).

### Direcciones OSC Oficiales
- **Seguimiento Humano (Tracking):** `/OBSBOT/WebCam/Tiny/ToggleAILock` (Payload int: `1` = Activar, `0` = Desactivar).
- **Zoom Dinámico:** `/OBSBOT/WebCam/Tiny/SetZoom` (Payload float: `0.0` a `100.0`).
- **Movimiento Gimbal:** `/OBSBOT/WebCam/Tiny/SetPanTilt` (Payload float: pan `[-129, 129]`, tilt `[-59, 59]`).
- **Modos Standby/Wake:** `/OBSBOT/WebCam/Tiny/Sleep` (Payload int: `1` = Suspender, `0` = Despertar).

---

## 5. Recetas Rápidas de Mantenimiento

- **Ejecutar Suite Completa de Tests:**
  ```powershell
  .\venv\Scripts\python.exe -m pytest tests/ -v
  ```
- **Arrancar Servicio FastAPI Agéntico:**
  ```powershell
  .\venv\Scripts\python.exe -m uvicorn agent_service.main:app --reload --port 8000
  ```
