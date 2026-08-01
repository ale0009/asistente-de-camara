# Bitácora de Desarrollo del Proyecto NOVA

> Registro histórico de iteraciones, decisiones técnicas, diagnóstico de errores y estado de verificación del proyecto **NOVA (Asistente de Cámara Inteligente)**.

---

## Ronda 5 — Suite de Innovación Avanzada, RAG Obsidian y Empaquetado Portable .exe (2026-07-19)

**Qué se hizo:**
- **RAG Local & Conexión con Obsidian Vault (`core/file_tools.py` & `core/intent_router.py`):** Implementación de búsqueda sintáctica y semántica sobre notas `.md` del Vault de Obsidian y archivos del sistema. Permitir que NOVA lea y responda preguntas analizando documentos locales en carpetas autorizadas (`assistant.allowed_folders`).
- **Ecualizador / Onda de Audio Reactiva en Tiempo Real (`core/voice_engine.py` & `ui/panel_widget.py`):** Evaluación del nivel de presión sonora RMS en vivo desde el hilo de PyAudio y animación fluida de la pastilla cian de audio al ritmo de la voz.
- **Zoom Continuo por Pellizco Dinámico (`core/gesture_engine.py` & `main.py`):** Medición de distancia euclidiana proporcional entre pulgar e índice a 30 FPS para controlar el zoom analógico de la OBSBOT (0-100%).
- **Modos de Escena Inteligentes en Bandeja del Sistema (`ui/tray_app.py`):** Submenú contextual para alternar con un clic entre *Modo Presentación*, *Modo Trabajo* y *Modo Descanso*.
- **Presets de Cámara OSC (`core/command_dispatcher.py`):** Atajos de voz para invocar posiciones preestablecidas 1, 2 y 3.
- **Modelo ONNX Custom 'Hey Nova' (`core/voice_engine.py`):** Soporte de carga prioritaria para `assets/nova.onnx`.
- **Script y Compilación Autónoma PyInstaller (`build_exe.py`):** Creación del empaquetador distribuible que compila todo el proyecto a un ejecutable portable en `dist/NOVA/NOVA.exe`.
- **61 Tests Unitarios Pasando al 100% (`tests/`):** Cobertura de pruebas completa sin fallos.

---

## Ronda 4 — Estabilización Formal de Código y Resolución de Hardware (2026-07-19)

**Qué se hizo:**
- **Validación de Configuración al Arrancar (`core/config_validator.py`):** Creación del módulo validador para prevenir `KeyError` crudos si falta alguna clave en `config.yaml`.
- **Logging a Archivo Rotativo (`logs/nova.log`):** Implementación de `RotatingFileHandler` de 2MB para evitar pérdida de tracebacks al ejecutar NOVA en segundo plano sin consola visible.
- **Resguardo del Hilo de Voz:** Captura y notificación por UI si el micrófono configurado no existe o no se puede abrir (`on_voice_engine_failed`).
- **Cierre Ordenado e Idempotente (`main.py::stop()`):** Garantizar la ejecución de `osc.sleep_camera()` al salir de la aplicación para mitigar calentamiento del hardware.
- **Thread-Affinity PyQt6:** Sustituir accesos directos al panel desde hilos secundarios por `update_video_frame_safe` apoyado en `QTimer.singleShot` y cerrojo `_panel_lock`.
- **Reconexión Automática de Cámara y Manejo de COM (`core/camera.py`):** Incorporar `pythoncom.CoInitialize()` y `CoUninitialize()` en la enumeración de dispositivos con `pygrabber` para evitar errores `[WinError -2147221008]`.

---

## Ronda 3 — Autonomía e Identidad del Asistente (2026-07-05)

**Qué se hizo:**
- **Identidad de NOVA (`core/persona.py`):** Constante `NOVA_IDENTITY` con la descripción del asistente, inyectada en el clasificador de intenciones para evitar respuestas genéricas del LLM.
- **Enrutador de Intenciones Inteligente (`core/intent_router.py`):** Soporte para acciones estructuradas `run_command` y `open_app` cuando los comandos de voz no coinciden exactamente de forma literal.
- **Detección de Cámara OBSBOT por Nombre (`core/camera.py`):** Uso de `pygrabber` para resolver dinámicamente el índice de dispositivo de "OBSBOT Tiny 3 Lite", evitando fallos por reordenamiento de Windows.
- **Suite de Pruebas Iniciales (`tests/`):** Incorporación de 26 tests con mocks para la validación de comandos, respuestas HTTP de Ollama y lógica del dispatcher.

---

## Ronda 2 — Optimización de Latencia Ollama y Corrección de Audio (2026-07-04 / 2026-07-05)

**Qué se hizo:**
- **Optimización de Latencia Ollama (`core/ollama_bridge.py`):** Solución a demoras de 20+ segundos mediante `"keep_alive": "10m"`, `"think": false` y límite de tokens `num_predict`. Reducción demostrada de tiempo de respuesta a ~1.3 segundos.
- **Motor TTS Robusto (`core/voice_engine.py`):** Reemplazo de reproductor externo por `pygame.mixer` con inicialización por hilo, eliminando cortes de audio y garantizando la reproducción fluida.

---

## Ronda 1 — Construcción del Prototipo Inicial (2026-07-04)

**Qué se hizo:**
- **Migración a MediaPipe Tasks (Python 3.13):** Implementación de `HandLandmarker` para resolver la incompatibilidad de MediaPipe Legacy en Python 3.13.
- **Panel Flotante PyQt6:** Diseño de interfaz gráfica transparente con efecto Glassmorphic.
- **Controlador OSC UDP:** Implementación de la capa de comunicación UDP con OBSBOT Center.
