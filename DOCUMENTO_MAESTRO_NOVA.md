# DOCUMENTO MAESTRO DE ESPECIFICACIÓN INTEGRAL — PROYECTO NOVA
## Asistente Local de Cámara Inteligente, Control Multimodal y Arquitectura Agéntica MCP

> **Fecha de Emisión:** 16 de Agosto de 2026  
> **Versión del Sistema:** 3.3.0 (Arquitectura Modular Dinámica MCP Hot-Plug, Segundo Cerebro & Tutor Políglota de Proyectos)  
> **Repositorio de Origen:** `E:\proyectos\Camara inteligente`  
> **Estado de Calidad:** 135 Tests Unitarios Pasando al 100% | Lanzador Unificado `start_nova_agent.py` Operativo  

---

## ÍNDICE DEL DOCUMENTO

1. **RESUMEN EJECUTIVO Y DECLARACIÓN DE PROPÓSITO**
2. **MATRIZ DE ALCANCE E INTEGRACIÓN AGÉNTICA (TU PI, TUA, TWIZ)**
3. **DESGLOSE EXHAUSTIVO MÓDULO POR MÓDULO**
   - 3.1. Lanzador Unificado: `start_nova_agent.py`
   - 3.2. Orquestación Agéntica FastAPI: `agent_service/main.py`, `agent_loop.py` & `intent_router.py`
   - 3.3. Gestión Dinámica MCP & Auditoría: `agent_service/mcp_client.py` (Auto-descubrimiento y Hot-Reload) & `agent_service/audit_logger.py`
   - 3.4. Servidores MCP Modulares:
     - `mcp_servers/vault_mcp.py` (Segundo Cerebro, Inteligencia de Proyectos y Extractor de Tareas)
     - `mcp_servers/agenda_mcp.py` (Gestor de Agenda Diaria, Rutina de Almuerzo y Pomodoro)
     - `mcp_servers/language_tutor_mcp.py` (Tutor Políglota EN, FR, ZH, JA con cambio dinámico de voces TTS)
     - `mcp_servers/doctor_mcp.py` (Auto-Diagnóstico de Salud del Sistema y Auto-Reparación)
     - `mcp_servers/camera_mcp.py` (Control PTZ OSC y Visión Moondream)
     - `mcp_servers/desktop_mcp.py`, `n8n_mcp.py`, `git_mcp.py` & `web_search_mcp.py`
   - 3.5. Percepción Visual y Gestual: `core/camera.py` & `core/gesture_engine.py`
   - 3.6. Percepción Auditiva y Canal Desacoplado: `core/voice_engine.py` & `voice_service/voice_client.py`
   - 3.7. Observadores en Tiempo Real: `watchers/file_watcher.py`
   - 3.8. Control Mecánico OSC: `core/osc_controller.py`
   - 3.9. Sistema Operativo y Control Local: `core/system_controller.py`
   - 3.10. Inferencia Local e Identidad: `core/ollama_bridge.py` & `core/persona.py`
   - 3.11. RAG y Log de Sesión: `core/file_tools.py` & `core/obsidian_logger.py`
   - 3.12. Interfaz de Usuario: `ui/panel_widget.py` & `ui/tray_app.py`
   - 3.13. Pruebas y Empaquetado: `build_exe.py` & `tests/`
4. **REQUERIMIENTOS FUNCIONALES (RF) Y NO FUNCIONALES (RNF)**
5. **CASOS DE USO (CU) Y CASOS DE IMPLEMENTACIÓN (CI)**
6. **ESTUDIO DE FOCUS GROUP Y PERFILES DE USUARIO OBJETIVO**
7. **ESTADO PRESENTE Y ROADMAP DE IMPLEMENTACIONES FUTURAS**
8. **GUÍA DE ARRANQUE Y MANTENIMIENTO**

---

## 1. RESUMEN EJECUTIVO Y DECLARACIÓN DE PROPÓSITO

### ¿Qué es NOVA Versión 3.1.0?
NOVA es una **plataforma agéntica multimodal local basada en Model Context Protocol (MCP)**, diseñada para conectar la percepción sensorial del usuario (voz, gestos de cámara y cambios de archivos) con motores de inferencia local (Ollama `qwen3:8b`), servicios de automatización (n8n), repositorios Git y herramientas del sistema operativo Windows.

### Propósito Fundamental
Ofrecer una experiencia de asistencia agéntica inteligente de latencia ultrabaja (<1.5s), 100% privada y soberana, con trazabilidad completa en base de datos (`agent_audit_log`) y protección estricta de documentos estratégicos mediante la excepción `OverwriteError`.

---

## 2. MATRIZ DE ALCANCE E INTEGRACIÓN AGÉNTICA (TU PI, TUA, TWIZ)

### 2.1. TU PI (Términos del Usuario y Principios de Integración)
- **Privacidad Soberana:** Procesamiento local absoluto. Ningún dato de voz, imagen, código o notas abandona la máquina local.
- **Estandarización Abierta (MCP):** Herramientas desacopladas expuestas mediante esquemas JSON-Schema que funcionan independientemente del modelo LLM utilizado.
- **Protección Dura de Documentos Críticos:** Los documentos de intención (`Charter.md`, `ADRs`, `Actas`) están blindados y arrojaran `OverwriteError` si el agente intenta modificarlos.

### 2.2. TUA (Términos de Uso y Arquitectura)
- **Gobernanza de Hardware:** Inferencia optimizada para NVIDIA RTX 5060 (8GB VRAM) manteniendo `keep_alive: 10m` y `think: false`.
- **Concurrencia Multi-Servicio:** Servicios desacoplados comunicados mediante FastAPI (REST / WebSockets).

### 2.3. TWIZ (Técnicas y Wording de Interacción Zero-Latency)
- **Procesamiento Asíncrono de Voz:** Transcripción Whisper STT a latencia reducida en GPU y respuestas por streaming.
- **Auditoría Transparente:** Registro automático en base de datos SQLite/Postgres de cada prompt, intención clasificada, herramienta MCP ejecutada y tiempo en ms.

---

## 3. DESGLOSE EXHAUSTIVO MÓDULO POR MÓDULO

### 3.1. Lanzador Unificado: `start_nova_agent.py`
- **Finalidad:** Arrancar todos los subsistemas de la plataforma agéntica en una sola instrucción.
- **Para qué es:** Facilitar el inicio de FastAPI, File Watcher y la UI PyQt6 simultáneamente.
- **Cómo lo hace:** Lanza Uvicorn en segundo plano, instancia `FileWatcherService` e invoca `NovaAssistant.start()`.
- **De qué forma lo hace:** Proceso Python con manejo de señales de apagado limpio.
- **Por qué lo hace:** Elimina la necesidad de abrir múltiples consolas manualmente.
- **Para qué lo hace:** Proveer una experiencia de inicio sin fricción con un solo comando.

### 3.2. Orquestación Agéntica FastAPI: `agent_service/main.py`, `agent_loop.py` & `intent_router.py`
- **`main.py`:** API REST (`/v1/agent/interact`) y canal WebSocket (`/v1/agent/ws`).
- **`agent_loop.py`:** Motor agéntico orquestador (`Input -> Router -> MCP -> Audit`).
- **`intent_router.py`:** Clasificador semántico en Ollama `qwen3:8b`.

### 3.3. Gestión MCP & Auditoría: `agent_service/mcp_client.py` & `agent_service/audit_logger.py`
- **`mcp_client.py`:** Consolidador de los 5 servidores MCP.
- **`audit_logger.py`:** Trazabilidad SQL en `agent_audit_log`.

### 3.4. Servidores MCP Modulares (`mcp_servers/`)
1. **`camera_mcp.py`:** OBSBOT Camera & Vision MCP (`camera_wake_sleep`, `camera_set_tracking`, `camera_set_zoom`, `camera_move_gimbal`, `camera_trigger_preset`, `camera_set_scene_mode`, `camera_describe_scene`).
2. **`vault_mcp.py`:** Obsidian Vault MCP (`vault_search`, `vault_read_note`, `vault_write_note`) con `OverwriteError`.
3. **`desktop_mcp.py`:** Windows Desktop MCP (`desktop_launch_app`, `desktop_set_volume`, `desktop_take_screenshot`).
4. **`n8n_mcp.py`:** n8n Automation MCP (`n8n_trigger_workflow`).
5. **`git_mcp.py`:** Git Repository MCP (`git_status`, `git_recent_commits`).
6. **`web_search_mcp.py`:** Web Search MCP (`web_read_page`).

### 3.5. Percepción Visual y Gestual: `core/camera.py` & `core/gesture_engine.py`
- Captura OpenCV DirectShow a 30 FPS, enumeración `pygrabber` y procesamiento MediaPipe Tasks (`HandLandmarker`).

### 3.6. Percepción Auditiva y Canal Desacoplado: `core/voice_engine.py` & `voice_service/voice_client.py`
- openWakeWord + Whisper STT + TTS desacoplado en `VoiceServiceChannel`.

### 3.7. Observadores en Tiempo Real: `watchers/file_watcher.py`
- Monitoreo en caliente de `E:\proyectos\` y Obsidian Vault.

### 3.8. Control Mecánico OSC: `core/osc_controller.py`
- Datagramas UDP OSC hacia OBSBOT Center (`127.0.0.1:16284`).

### 3.9. Sistema Operativo y Control Local: `core/system_controller.py`
- Control nativo de Windows (procesos por PID, volumen, capturas).

### 3.10. Inferencia Local e Identidad: `core/ollama_bridge.py` & `core/persona.py`
- Cliente Ollama HTTP e inyección de `NOVA_IDENTITY`.

### 3.11. RAG y Log de Sesión: `core/file_tools.py` & `core/obsidian_logger.py`
- Búsqueda sintáctica y log diario Markdown.

### 3.12. Interfaz de Usuario: `ui/panel_widget.py` & `ui/tray_app.py`
- Panel Glassmorphism PyQt6 y menú contextual System Tray.

### 3.13. Pruebas y Empaquetado: `build_exe.py` & `tests/`
- Script PyInstaller y **84 tests unitarios pasando al 100%**.

---

## 4. GUÍA DE ARRANQUE Y MANTENIMIENTO

### Comando de Inicio Único:
```powershell
.\venv\Scripts\python.exe start_nova_agent.py
```

### Ejecutar Suite Completa de Tests (84/84):
```powershell
.\venv\Scripts\python.exe -m pytest tests/ -v
```

---
*Fin del Documento Maestro de Especificación Integral (Versión 3.1.0).*
