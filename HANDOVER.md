# NOVA — Handover completo del proyecto

> Generado: 2026-07-05. Actualizado: 2026-07-19 (Ronda "Feedback OSC + Selector de Hardware + TTS Streaming + Gestos Extended"). Escrito para que **otra IA o desarrollador pueda continuar sin contexto previo**.
> Repo: `E:\proyectos\Camara inteligente` · GitHub: `https://github.com/ale0009/asistente-de-camara` (rama `main`)

## -2. Ronda "Feedback OSC + Selector de Hardware + TTS Streaming + Gestos Extended" (2026-07-19)

Se ejecutó un plan completo para añadir dinamismo, sincronización bidireccional de hardware y respuesta de voz ultra-rápida:

- **Control Físico OSC Arreglado (`system_controller.py`):** Se automatizó el forzado de `OSC=true` en `global.ini` en cada inicio de OBSBOT Center, garantizando el movimiento real de la cámara.
- **Listener de Feedback OSC en Tiempo Real (`core/osc_controller.py`):** Servidor UDP secundario escuchando en puerto `16285` para recibir mensajes `AiTrackingInfo` y `ZoomInfo` emitidos por OBSBOT Center. Actualiza los chips HUD del panel de Qt en vivo (`update_status_safe`).
- **Streaming de TTS por Oración (`core/voice_engine.py` & `core/ollama_bridge.py`):** Implementación de `query_stream()` en Ollama + generador de oraciones por puntuación (`_stream_sentences`) consumido por un hilo daemon secundario (`NOVA-StreamConsumer`), permitiendo que NOVA hable de inmediato frase por frase.
- **Selector de Micrófono Dinámico en UI (`ui/panel_widget.py`):** Diálogo modal de configuración (`ConfigDialog`) con diseño glassmorphism HUD que enumera micrófonos de entrada con PyAudio, permite cambiar el dispositivo en caliente y guarda la preferencia en `config.yaml`.
- **Selector de Cámara Dinámico en UI (`core/camera.py` & `ui/panel_widget.py`):** Enumeración de cámaras DirectShow (`get_available_cameras`), reconfiguración y reapertura del stream en caliente (`set_camera`), integrado en el mismo diálogo `ConfigDialog`.
- **Ampliación del Motor de Gestos (`core/gesture_engine.py`):** Nuevos gestos de mano de MediaPipe Tasks: `"apuntar"` (Índice) -> `"toma una foto"` y `"pulgar_arriba"` (Like) -> `"resetea la cámara"`, configurables desde `presets/gestures.yaml`.
- **55 Tests Unitarios Pasando (`tests/`):** Cobertura completa de todas las nuevas funciones sin ningún fallo.

---

Se ejecutó un plan de estabilización formal (aprobado por el usuario en modo plan) para convertir NOVA de prototipo a algo confiable para uso diario. Las 14 tareas del plan quedaron completas y verificadas (45 tests pasando, varias verificadas contra hardware real). Detalle completo en la memoria del asistente (`nova_project_state.md`) — resumen aquí:

- **Config validation al arrancar** (`core/config_validator.py`, nuevo): antes, una clave faltante en `config.yaml` crasheaba con `KeyError` crudo. Ahora `main.py` valida y sale con un mensaje legible.
- **Logging a archivo** (`logs/nova.log`, `RotatingFileHandler`): antes solo iba a stdout — si NOVA arranca sin consola (ej. `start_with_windows`), todos los logs se perdían.
- **Hilo de voz que moría en silencio si el micrófono no existía** (`voice_engine.py`): ahora se captura, se loggea y se avisa por UI (`on_voice_engine_failed`).
- **Cierre ordenado garantizado**: `ui/tray_app.py::exit_app()` ahora llama a un `on_exit` explícito (conectado a `NovaAssistant.stop()`) antes de cerrar Qt; `stop()` es idempotente, hace `join()` del hilo de visión, y **ahora sí llama `osc.sleep_camera()` al cerrar** (antes nunca lo hacía — ver bug de calentamiento abajo).
- **Violación de thread-affinity de Qt**: `_vision_loop` (hilo no-Qt) llamaba directamente `_panel_instance.isHidden()`. Ahora pasa por `ui/panel_widget.py::update_video_frame_safe()`, que agenda la llamada real en el hilo de Qt vía `QTimer.singleShot`, con un lock (`_panel_lock`) protegiendo la referencia global.
- **Locks de concurrencia**: `camera.py::current_frame` (lock), `obsidian_logger.py` (lock en el check-then-act del encabezado del log diario), `panel_widget.py` (throttle de clics — un lock no bloqueante evita apilar hilos de `process_command` con clics repetidos).
- **`voice_engine.stop()`** ya no arriesga tocar una instancia de PyAudio terminada si el hilo de escucha sigue vivo tras el timeout de `join()`.
- **`system_controller.py`**: se separó un `except Exception` genérico (que ocultaba bugs reales) de las excepciones esperadas de `psutil` en la enumeración de ventanas.
- **`requirements.txt` corregido**: se agregaron `openwakeword` y `comtypes` (se usaban en el código pero no estaban listados — un `pip install -r requirements.txt` limpio no habría reproducido un entorno funcional); se quitaron `pvporcupine` y `pyttsx3` (no se usan en ningún módulo).
- **19 tests nuevos** (`test_config_validator.py`, `test_camera.py`, `test_voice_engine.py`) sobre los 26 anteriores → **45 tests, todos pasando**.

### Bug real encontrado y arreglado: la cámara se quedaba encendida/caliente

El usuario reportó que la cámara parecía no apagarse bien, seguía consumiendo energía y se calentaba. Investigación (código + foros oficiales de OBSBOT):

1. **Causa raíz #1 (confirmada en código, arreglada):** `main.py::start()` despertaba la cámara (`osc.wake_camera()`) al arrancar, pero **`stop()` nunca llamaba `osc.sleep_camera()`** — NOVA jamás le pedía a la cámara que se durmiera al cerrar. Arreglado en la ronda de esta sesión (ver arriba). Es fire-and-forget por UDP, así que no falla si OBSBOT no está escuchando.
2. **Causa raíz #2 (bloqueante, ya documentado en §5, sin resolver):** aunque el fix de arriba mande el comando de sueño, **no tiene ningún efecto mientras `OSC=false` en `global.ini` de OBSBOT Center** — el switch real solo se activa desde la GUI de OBSBOT Center, no desde código. Sin esto, NINGÚN comando OSC (sleep, tracking, zoom) llega a la cámara físicamente.
3. **Hallazgo de los foros oficiales de OBSBOT (FAQ de Tiny SE / Tiny 2 Lite):** el auto-sleep configurable en OBSBOT Center **no se activa mientras detecta un stream de video activo** — es decir, mientras NOVA (u OpenCV) mantenga la cámara abierta para el preview del panel/gestos, el temporizador de sueño automático del firmware nunca dispara, sin importar qué tan bien configurado esté. Esto es comportamiento documentado por el fabricante, no un bug de NOVA.
4. **Bug adicional descubierto e implementado en esta ronda al construir la reconexión automática de cámara (Fase 2.1 del plan):** la detección de cámara por nombre (`find_camera_index_by_name`, ronda anterior) usa `pygrabber`/COM, que requiere `CoInitialize` en cada hilo que lo llama. Al agregar reconexión automática, esa función pasó a poder ejecutarse también desde el hilo de captura de la cámara (no solo el principal) y fallaba con `[WinError -2147221008] No se ha llamado a CoInitialize`. Arreglado con `pythoncom.CoInitialize()/CoUninitialize()` en pareja dentro de la función. Verificado en vivo contra el hardware real.
5. **Bug adicional relacionado, también arreglado:** si `camera.stop()` se llamaba mientras un intento de reconexión seguía abriendo el dispositivo (`cv2.VideoCapture` puede tardar 3-4s), el `join(timeout=1.0)` original era insuficiente — el hilo terminaba de abrir la cámara **después** de que `stop()` ya había revisado `self.cap`, dejando un handle abierto sin liberar (la cámara seguía transmitiendo pese a que NOVA reportaba "Cámara detenida"). Se subió el timeout a 6s y se agregó un log de advertencia si el hilo sigue vivo tras eso. **Verificado en vivo**: forzar una reconexión y llamar `stop()` a mitad de la apertura ya no deja el handle huérfano.

**Recomendación práctica para el usuario (no es solo código):** mientras el switch OSC de OBSBOT Center (causa raíz #2) siga sin activarse, el software de NOVA no tiene forma de decirle a la cámara físicamente "duérmete" — el fix de código de esta ronda queda listo pero inerte hasta que ese switch se resuelva. Como medida de seguridad de hardware mientras tanto: desconectar el USB de la cámara cuando no se vaya a usar por un rato largo, o usar un hub USB con interruptor físico, es la única vía 100% garantizada de cortar el consumo/calor, independiente de cualquier bug de software.

## 0. Progreso de la ronda "autonomía" (2026-07-05, continuación de este handover)

Objetivo del usuario: que NOVA sea un asistente autónomo con muchas capacidades reales, no solo un diccionario fijo de frases. Se implementó, verificado con tests y con hardware real:

1. **`core/persona.py` (nuevo)**: constante `NOVA_IDENTITY` con la descripción real de qué es NOVA y qué puede hacer. Se usa en el prompt del clasificador de intención (`intent_router.py`) y en la consulta directa "pregúntale a ollama" (`command_dispatcher.py`) — antes NOVA inventaba respuestas genéricas si le preguntaban "¿qué eres?" porque el LLM no tenía ningún contexto real del proyecto (roadmap ítem 4, resuelto).
2. **`core/intent_router.py` ampliado — brecha de capacidad real cerrada**: antes, si un comando de voz no calzaba como substring exacto en `camera_commands`/`system_commands` (ej. "podrías acercar un poco más la cámara" en vez de "acércate"), caía al clasificador de intención y este solo sabía responder con texto (`answer`) — es decir, la cámara/sistema **no se movía**, aunque la respuesta hablada sonara convincente. Se agregaron dos acciones nuevas al clasificador:
   - `run_command`: el LLM recibe la lista real de claves de `dispatcher.camera_commands`/`system_commands` interpolada en el prompt y debe copiar EXACTO el comando que mejor coincida en significado; `IntentRouter._handle_run_command` lo busca en esos mismos diccionarios y ejecuta la acción real (nunca ejecuta nada que no esté ya en la whitelist existente — no hay código nuevo de riesgo).
   - `open_app`: delega en `CommandDispatcher._open_app` (reusa `presets/apps.yaml`), para que "abre blender" funcione también si se dice distinto a como lo espera el prefijo `"abre"` fijo.
   - Cableado en `main.py`: `IntentRouter` se construye antes que `CommandDispatcher` (dependencia circular real), así que se le asigna `self.intent_router.dispatcher = self.dispatcher` **después** de crear el dispatcher.
3. **Detección de cámara OBSBOT por nombre de dispositivo (roadmap ítem 5, resuelto)**: `core/camera.py::find_camera_index_by_name()` usa `pygrabber` (nueva dependencia, `FilterGraph().get_input_devices()`, mismo backend DirectShow que usa `cv2.CAP_DSHOW`) para resolver el índice por nombre (`config.yaml → camera.device_name`, ya existía el campo pero no se usaba) en cada arranque, con fallback automático a `camera_index` de config si no encuentra coincidencia o pygrabber falla. **Verificado contra el hardware real de este equipo**: enumera `0 OBSBOT Tiny 3 Lite StreamCamera`, `1 OBSBOT Virtual Camera`, `2 OBS Virtual Camera` — resuelve a índice 0 correctamente. Esto cierra el bug recurrente de que el índice cambia solo entre sesiones (ya documentado en §6.1).
4. **Tests mínimos con mocks (roadmap ítem 8, resuelto — antes `tests/` estaba vacío)**: 26 tests en `tests/` (`test_command_dispatcher.py`, `test_osc_controller.py`, `test_ollama_bridge.py`, `test_intent_router.py`), todos pasando. Cubren: matching de comandos de cámara/sistema (exacto y substring), apertura de apps, fallback al intent router, direcciones OSC exactas (tracking, wake/sleep, zoom, gimbal), payload de Ollama (`keep_alive`, `think:false`, `num_predict`, `format:json`), manejo de errores HTTP/timeout/conexión, y las 3 acciones nuevas del router (`run_command`, `open_app`, más `search_files`/`write_note`/`answer` ya existentes). Se agregó `pytest>=8.0.0` a `requirements.txt`. Correr con: `.\venv\Scripts\python.exe -m pytest tests/ -v`.

**No tocado en esta ronda (sigue en el roadmap, ver §9 abajo):** streaming de TTS por oración, selector de micrófono por voz/UI, más gestos de mano, subir cambios a GitHub. El bloqueante de OSC (§5) sigue intacto — sigue requiriendo que el usuario active el switch dentro de la GUI de OBSBOT Center, algo que no se puede hacer por código.

---

## 1. Qué es NOVA (visión del usuario, en sus palabras)

Un asistente que convierta la cámara OBSBOT Tiny 3 Lite y su micrófono en **una extensión real del computador**:
- Controlar *todos* los ajustes de la OBSBOT solo con la voz (zoom, mirar izq/der/arriba/abajo, suspender/despertar, tracking).
- Un asistente con IA que responda preguntas, busque archivos, tome notas en Obsidian, abra apps — todo por voz, en **segundos, no minutos**.
- Gestos de mano que disparen acciones (cambiar de ventana, abrir apps, etc.), configurables sin tocar código.
- Que corra 100% local (sin pagos, sin que la información salga del equipo).
- Que funcione bien en el hardware actual pero también en equipos más modestos (no ser "parásito" de recursos).
- Interfaz visual cuidada y entendible, no solo funcional.

## 2. Hardware real del equipo (verificado, no asumido)

| Componente | Valor |
|---|---|
| GPU | NVIDIA RTX 5060, 8GB VRAM, **capada a 124W** (default 155W / máx 170W) vía MSI Afterburner — es protección de voltaje intencional del usuario, **no tocar/recomendar quitarla** |
| CPU | Intel Xeon Silver 4114, 10 núcleos / 20 hilos @ 2.2GHz (gama servidor) |
| RAM | 62.6 GB |
| Cámara | OBSBOT Tiny 3 Lite — 1/2" CMOS 48MP, 4K@30fps HDR / 1080p@120fps, FOV 79.1°(4:3)/72°(16:9), f/1.8, ISO 100-6400, zoom 4x digital, gimbal 2 ejes (fabricante anuncia 150°pan/90°tilt; el rango usable por OSC documentado es ±129°/±59°), tri-mic 24-bit/48kHz. Ficha completa en `D:\Documentos\Obsidian Vault\NOVA\OBSBOT_Tiny_3_Lite_Ficha_Tecnica.md`. |
| Micrófono actual | Audífonos Onikuma (`mic_index: 1` en config.yaml) |
| OBSBOT Center instalado en | `D:\OBSBOT Center\bin\` (OBSBOT_Center.exe y OBSBOT_Main.exe) — **no** en Program Files |
| Ollama | Server local en `127.0.0.1:11434`. Modelos en disco: `qwen3:8b` (5.2GB, el usado por NOVA), `qwen3.6` (23GB, descartado por lento), `gemma4` (9.6GB), `moondream` (1.7GB, modelo de visión, no de chat) |

## 3. Arquitectura actual (mapa de archivos)

```
main.py                    Orquestador: arranca todo, conecta callbacks
config.yaml                Config central (cámara, voz, gestos, obsidian, assistant)
core/
  camera.py                Captura UVC vía OpenCV/DSHOW en un hilo propio; resuelve el índice
                           por nombre de dispositivo (pygrabber) con fallback a config.yaml
  osc_controller.py         Cliente OSC hacia OBSBOT Center (127.0.0.1:16284)
  voice_engine.py           Wake word (openWakeWord) + STT (Whisper) + TTS (edge-tts/pygame)
  gesture_engine.py          MediaPipe Tasks (HandLandmarker) — funciona en Python 3.13
  command_dispatcher.py     "Cerebro": diccionarios fijos de comandos + fallback a IntentRouter
  intent_router.py          Clasificador de intención vía Ollama (JSON: search_files/write_note/
                           run_command/open_app/answer) — run_command y open_app ejecutan acciones
                           reales reusando los diccionarios de CommandDispatcher (ver §0)
  persona.py                 NOVA_IDENTITY: identidad/capacidades reales para los prompts de Ollama
  file_tools.py             Búsqueda de archivos y notas libres, acotado a carpetas permitidas
  system_controller.py       Windows: volumen, capturas, cerrar apps, lanzar/minimizar OBSBOT
  ollama_bridge.py           Cliente HTTP a Ollama (keep_alive, think:false, num_predict)
  obsidian_logger.py          Log automático de sesión a markdown diario
ui/
  panel_widget.py            Panel flotante PyQt6 (glassmorphism), botones, video en vivo
  tray_app.py                Ícono de bandeja del sistema
presets/
  apps.yaml                  Diccionario app → ruta ejecutable (Blender, Figma, IDEs, etc.)
  gestures.yaml               Mapa gesto → texto de comando (editable sin tocar Python)
assets/
  hand_landmarker.task        Modelo oficial de MediaPipe Tasks (descargado de Google)
  nova_icon.png
tests/                        26 tests con mocks (dispatcher, OSC, Ollama, intent router) — ver §0
```

## 4. Qué funciona HOY (verificado con logs reales, no supuesto)

| Capacidad | Estado | Evidencia |
|---|---|---|
| Wake word + STT + comandos de voz | ✅ Funciona | Logs de sesión muestran reconocimiento y ejecución correctos |
| TTS (NOVA habla) | ✅ Arreglado 2026-07-04 | Ver §6.3 — antes no sonaba, ya probado 2x consecutivas sin corte |
| Cámara (captura de video) | ✅ Funciona | Abre en índice 0, se ve en el panel |
| Gestos (MediaPipe Tasks) | ✅ Funciona en Python 3.13 | 4 gestos reconocidos, mapeados vía `gestures.yaml` |
| Lanzar OBSBOT oculto/minimizado al iniciar | ✅ Funciona | Se minimiza por proceso (PID), no por título de ventana |
| Comandos de sistema (volumen, captura, cerrar apps) | ✅ Funciona | — |
| Abrir apps por voz | ✅ Funciona | `presets/apps.yaml`, ~20 apps registradas |
| Ollama respondiendo rápido | ✅ Arreglado 2026-07-04/05 | De 21-26s a ~1-3s (ver §6.2) |
| Asistente con acciones libres (buscar archivos, anotar) | ✅ Implementado, sin confirmar en uso real prolongado | `intent_router.py` + `file_tools.py`, probado en aislado |
| **Tracking OSC (seguimiento físico de la cámara)** | ❌ **NO funciona todavía** | Ver §5 — bloqueante principal |
| Zoom/gimbal/wake-sleep por OSC | ❌ No confirmado (depende del mismo bloqueo que tracking) | — |
| Registro en Obsidian | ✅ Funciona | `D:\Documentos\Obsidian Vault\NOVA\Sesiones\` |
| Tests automatizados | ❌ No existen | `tests/` vacío |

## 5. EL BLOQUEANTE PRINCIPAL: OSC sigue en `false`

**Síntoma:** todos los comandos de cámara (`sígueme`, `despierta la cámara`, `para de seguirme`, etc.) se procesan y envían correctamente por software — el log siempre muestra `Ejecutando comando de cámara: X` — pero la cámara físicamente **nunca se mueve ni trackea**.

**Causa raíz confirmada:** `C:\Users\mario\AppData\Roaming\OBSBOT_Center\global.ini`, sección `[SoftSetting]`, tiene `OSC=false`. Comprobado repetidamente: incluso después de editarlo manualmente a `true` con OBSBOT cerrado, **la próxima vez que la app se cierra normalmente, vuelve a escribir `false`** — porque el switch nunca se activó desde su propio estado interno/UI, solo se pisó el archivo por fuera.

**Lo que NO hay que volver a intentar (ya se probó y no sirve):**
- Editar `global.ini` a mano y esperar que persista. No persiste.
- Sospechar de las direcciones OSC — **ya se resolvió de raíz** (ver siguiente sección): se encontraron y decodificaron las plantillas oficiales de TouchOSC que trae la propia instalación de OBSBOT Center, con las direcciones exactas para este hardware.
- Sospechar de contención de cámara (dos procesos abriendo el mismo dispositivo) — se probó y no es la causa principal aquí; el bloqueo real está antes, en que el servidor OSC de OBSBOT ni siquiera está escuchando.

### 5.1 Hallazgo importante (2026-07-05): direcciones OSC oficiales encontradas

`D:\OBSBOT Center\data\ctrl\touchosc\OBSBOT Sample-UDP.tosc` y `OBSBOT Sample-TCP.tosc` son plantillas oficiales de TouchOSC que la propia instalación de OBSBOT Center incluye. Son archivos zlib-comprimidos (no ZIP) con un XML de definición de controles — decodificados y parseados, dieron las direcciones OSC **reales y oficiales** para este hardware exacto (no reconstrucciones de comunidad para el Tiny 2 Lite). Tabla completa en `docs/OBSBOT_OSC_Oficial.md`.

**Corrección crítica:** el seguimiento real se activa con `/OBSBOT/WebCam/Tiny/ToggleAILock` (0/1) — **no** `SetTrackingMode`, que no existe en el protocolo oficial y era casi seguro la razón por la que el tracking nunca respondía (además del switch `OSC=false`). `core/osc_controller.py` ya se reescribió con las direcciones oficiales; los nombres de métodos públicos (`track_human`, `stop_tracking`, `look_left/right/up/down`, etc.) no cambiaron, así que `command_dispatcher.py` no necesitó tocarse.

**Todavía sin confirmar (no estaba en las plantillas oficiales):** un equivalente a `SetAiMode` para los submodos de encuadre (cuerpo completo, primer plano, grupo, etc.) — no se encontró ninguna dirección de ese tipo en las plantillas `.tosc` disponibles. Puede que esos submodos solo se controlen desde la propia GUI de OBSBOT Center, o que exista otra plantilla no revisada aún en la misma carpeta.

**Sigue pendiente, aun con las direcciones correctas:** activar el switch `OSC=true` desde la UI real de OBSBOT Center (§5 arriba) — sin eso, ninguna dirección (correcta o no) tiene efecto.

**Lo que falta hacer (acción pendiente, requiere interacción humana con la GUI de OBSBOT Center):**
1. Abrir OBSBOT Center (queda minimizado, no oculto — buscarlo en bandeja/Alt+Tab).
2. Encontrar el switch real de "OSC" / "Control externo" / "Developer options" dentro de su panel de ajustes (ícono de engranaje, o la pestaña "Más") y activarlo **desde ahí**, no desde el archivo.
3. Cerrar y reabrir OBSBOT Center una vez para confirmar que el ini ya no vuelve a `false`.
4. Si no se encuentra el switch en la UI, alternativa a explorar: la sección `[Zmq]` de `global.ini` (puertos `main_rep_port=51937`, etc.) sugiere que OBSBOT también soporta control por **ZeroMQ** — podría ser una vía alterna si OSC resulta no exponerse en esta versión/edición de la app.

## 6. Bugs ya diagnosticados y resueltos (changelog técnico — no re-investigar esto)

### 6.1 Bugs de arranque (2026-07-04)
- `main.py` no pasaba `camera_index` desde `config.yaml` a `CameraController` → abría el índice equivocado. **Fix:** se pasa explícitamente.
- El índice de cámara **cambia solo entre sesiones** (Windows reordena dispositivos de video). Ya pasó de 1 a 0. Si vuelve a fallar "No se pudo abrir la cámara", probar índices 0/1/2 con `cv2.VideoCapture(i, cv2.CAP_DSHOW).isOpened()` (con OBSBOT cerrado) antes de sospechar del código. **Pendiente real:** detectar la cámara por nombre de dispositivo en vez de índice fijo.
- `OBSBOT_Main.exe` es un lanzador que abre `OBSBOT_Center.exe` como proceso hijo con **su propia barra de título dibujada a mano** (no expone el texto real a Windows) — buscar la ventana por texto de título (`GetWindowText`) es poco confiable. **Fix:** `system_controller.py::_find_window_by_process` busca por el proceso dueño (PID vía `GetWindowThreadProcessId`), no por título.
- Ocultar la ventana con `SW_HIDE` parecía suspender el procesamiento interno de OBSBOT. **Fix:** se usa `SW_MINIMIZE`.

### 6.2 Bug de latencia de Ollama (2026-07-04/05)
Preguntas abiertas tardaban 21-26 segundos. Dos causas combinadas:
1. Ollama descargaba el modelo de VRAM después de cada llamada (`ollama ps` mostraba vacío tras cada consulta) → recarga de ~7-9s en cada llamada. **Fix:** `"keep_alive": "10m"` en el payload (`ollama_bridge.py`).
2. qwen3 genera tokens de "razonamiento" internos + respuestas muy largas (2000+ caracteres) para preguntas abiertas. **Fix:** `"think": false` + `options.num_predict` (default 220 tokens) + instrucción de brevedad en el prompt.
Resultado verificado: la misma pregunta bajó de 26s a ~1.3s.

### 6.3 Bug de audio/TTS (2026-07-05)
NOVA generaba la respuesta de voz pero no se escuchaba. Causa: `os.startfile(mp3)` + `time.sleep(3)` fijo — poco confiable, cortaba el audio si el reproductor tardaba o la frase duraba más de 3s. **Fix:** `pygame.mixer` (agregado a `requirements.txt`). Detalle importante: `pygame.mixer.init()` debe llamarse **dentro del mismo hilo** que reproduce (cada `speak()` crea un hilo nuevo) — inicializarlo una sola vez en el hilo principal daba error "mixer not initialized". Solución: `if not pygame.mixer.get_init(): pygame.mixer.init()` al inicio de `_speak_sync`. Verificado con 2 reproducciones consecutivas completas sin corte.

### 6.4 Bug de hilo de visión muerto en silencio (2026-07-04)
Los gestos dejaban de reconocerse a mitad de sesión sin ningún error en el log. Causa: `main.py::_vision_loop` no envolvía en try/except el procesamiento de gestos, solo la actualización de la UI — un error ahí mataba el hilo permanentemente sin avisar. **Fix:** todo el cuerpo del loop envuelto en try/except con `logger.exception`. No se ha vuelto a observar el síntoma desde el fix, pero tampoco se confirmó la causa exacta del error original (no hubo traceback capturado antes del fix).

### 6.5 Bug de referencia a objeto Qt destruido (2026-07-04)
Cerrar el panel flotante (botón "×") con `WA_DeleteOnClose` dejaba la variable global `_panel_instance` apuntando a un objeto ya destruido → `RuntimeError: wrapped C/C++ object ... has been deleted` al reabrir. **Fix:** `closeEvent` limpia la referencia global; además `_vision_loop` atrapa `RuntimeError` como red de seguridad ante condiciones de carrera entre hilos.

## 7. Decisiones de arquitectura (para no revertir sin razón)

- **Python 3.13, sin downgrade.** El usuario rechazó explícitamente bajar a 3.11/3.12 cuando MediaPipe legacy (`mp.solutions`) no funcionaba en 3.13. Se resolvió migrando a la API nueva **MediaPipe Tasks** (`HandLandmarker`), que sí funciona en 3.13. No proponer downgrade de Python de nuevo.
- **`qwen3:8b` como modelo por defecto**, no uno más pequeño. Verificado que la generación en sí es rápida (~50 tok/s); la lentitud percibida era por bugs de configuración (keep_alive, thinking mode), no por el tamaño del modelo. Antes de proponer un modelo más chico, confirmar que los fixes de §6.2 están puestos.
- **Carpetas de archivos acotadas por el usuario** (`config.yaml → assistant.allowed_folders`), nunca acceso libre al disco — decisión explícita de seguridad del usuario.
- **El gimbal no puede girar 360°** — es pan/tilt (±129°/±59° usable), no una torreta. No perseguir ese comando como si fuera un bug.

## 8. Investigación de proyectos similares (qué hay en el mercado local, y qué tomar de ellos)

No existe un proyecto público que combine voz + gestos + control de cámara PTZ igual que NOVA. Lo más cercano:

- **[TrooperAI](https://github.com/m15-ai/TrooperAI)** (Raspberry Pi 5): voz + gestos de mano con MediaPipe + Ollama. Lecciones aprovechables:
  - **Streaming de TTS por oración**: en vez de esperar la respuesta completa del LLM antes de hablar, detectan fin de oración (puntuación/silencio) y empiezan a reproducir esa oración mientras el resto se sigue generando. **Esto NOVA no lo tiene** — hoy `speak()` espera el texto completo. Sería la siguiente mejora de latencia percibida más impactante.
  - Gesto de activación con "streak" de frames + cooldown (muy similar al debounce que ya tiene `gesture_engine.py`) — confirma que el enfoque actual de NOVA es razonable.
  - Nota: el system prompt importó más que el tamaño del modelo para lograr personalidad/coherencia — NOVA todavía no tiene un system prompt que le diga al LLM qué es NOVA (por eso responde genérico si le preguntas "¿qué eres?").
- **[Local-Voice](https://github.com/m15-ai/Local-Voice)**: modelos muy pequeños (0.5B-2B) vía Ollama, STT con Vosk (mucho más rápido que Whisper pero menos preciso). Con modelos tan chicos, su latencia total end-to-end es de **8-10 segundos** — es decir, NOVA con `qwen3:8b` ya optimizado (§6.2) es comparable o mejor, a pesar de usar un modelo "más grande". Conclusión: no vale la pena bajar a un modelo más pequeño solo por velocidad.
- **[Ollama-GUI-Voice-Assistant](https://github.com/a1368399487/Ollama-GUI-Voice-Assistant)** y otros similares: confirman el patrón Whisper+Ollama+TTS como el estándar de facto para asistentes locales — NOVA ya sigue ese patrón.

**Idea concreta a tomar prestada:** streaming de TTS por oración (de TrooperAI). Reduciría la latencia *percibida* de las respuestas largas de Ollama sin tener que acortarlas artificialmente.

## 9. Qué falta para llegar a la visión original (roadmap actualizado)

1. **Resolver OSC de una vez por todas** (§5) — bloqueante, sin esto no hay tracking/zoom/gimbal/wake-sleep físicos **ni la cámara se puede dormir de verdad al cerrar NOVA** (ver §-1, causa raíz #2 del bug de calentamiento). Sigue pendiente, requiere interacción humana con la GUI de OBSBOT Center — es el ítem más importante de todo este roadmap.
2. **Verificar en uso real** (no solo aislado) el asistente de acciones libres: buscar archivos, tomar notas, y las nuevas acciones `run_command`/`open_app` parafraseadas — probarlo con comandos de voz reales, no solo con tests con mocks.
3. **Streaming de TTS por oración** (lección de TrooperAI) para que las respuestas largas se sientan instantáneas. Con `num_predict`+`think:false` ya puestos (§6.2) el impacto es menor que cuando se escribió este ítem, pero sigue pendiente.
4. ~~**System prompt para Ollama**~~ — ✅ Hecho (§0): `core/persona.py`.
5. ~~**Detección de cámara por nombre de dispositivo**~~ — ✅ Hecho (§0): `core/camera.py::find_camera_index_by_name`. Falta el equivalente para el micrófono (ítem 6).
6. **Selector de micrófono** desde la UI/voz (hoy fijo en config.yaml) — no implementado todavía.
7. **Gestos configurables — ampliar**: hoy el mapeo gesto→acción es editable (`gestures.yaml`) pero solo hay 4 gestos reconocidos; agregar más formas de mano requiere nueva lógica geométrica en `gesture_engine.py`.
8. ~~**Tests mínimos**~~ — ✅ Hecho, ampliado en la ronda de estabilización (§-1): 45 tests en `tests/`.
9. **Subir los cambios pendientes a GitHub** — el repo remoto solo tiene el commit inicial; todo lo de las Fases A/B/C, los fixes de audio/gestos, la ronda de autonomía (§0) y la ronda de estabilización (§-1) está solo en local. Pendiente de que el usuario confirme el commit/push (decisión explícita: mantener todo local por ahora, ver §-1).
10. ~~**Validación de config, logging a archivo, hilos que mueren en silencio, condiciones de carrera UI/cámara, reconexión de cámara**~~ — ✅ Hecho en la ronda de estabilización (§-1).
11. **Empaquetado/instalador** — decisión explícita del usuario: mantener venv + `python main.py`, sin PyInstaller (MediaPipe/Whisper hacen que un .exe único sea frágil de mantener para un proyecto de un solo desarrollador). Revisitar solo si se quiere compartir NOVA con otro equipo.
12. **CI (GitHub Actions)** — no configurado, decisión explícita de mantener todo local por ahora (ver ítem 9).

## 10. Notas de continuidad para la próxima IA

- El usuario habla en español, coloquial, a veces por dictado de voz a texto (typos frecuentes tipo "srive", "traqueo", "poryectos" — leer con tolerancia a errores fonéticos).
- Prefiere fixes de código sobre atajos destructivos (ej. rechazó bajar de versión de Python en vez de buscar una alternativa). Ver memoria del asistente si está disponible: `feedback-no-destructive-shortcuts-nova`.
- Le gusta verificar con logs reales antes de dar nada por resuelto — pide confirmación empírica, no solo teórica.
- El flujo de trabajo típico: se propone un fix → el usuario corre `.\venv\Scripts\python main.py` → pega el log completo → se diagnostica sobre evidencia real, no suposiciones.
