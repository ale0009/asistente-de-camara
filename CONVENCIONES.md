# Convenciones de Desarrollo — Proyecto NOVA

> Estándar de código, gobernanza de hardware y buenas prácticas de ingeniería para el asistente local de cámara inteligente NOVA.

---

## 1. Idioma y Estilo de Código

- **Lenguaje Principal:** Python 3.13.
- **Nombres de Variables y Funciones:** `snake_case` descriptivo en inglés/español consistente (`camera_index`, `process_command`, `speak_sync`).
- **Nombres de Clases:** `PascalCase` (`NovaAssistant`, `OSCController`, `VoiceEngine`, `GestureEngine`).
- **Constantes:** `MAYUSCULAS_CON_GUION_BAJO` (`DEFAULT_OSC_PORT`, `NOVA_IDENTITY`).
- **Documentación en Código:** Docstrings en español para todas las clases y métodos públicos, detallando argumentos, tipos esperados y efectos secundarios.
- **Formateo:** Adherencia a PEP8, sangría de 4 espacios (nunca tabuladores).

---

## 2. Estructura y Modularización

- **Un Módulo = Una Responsabilidad (`core/`):**
  - Cada archivo en `core/` atiende una sola capacidad de percepción, control o integración.
  - Ningún módulo de visión, audio u OSC debe importar directamente `PyQt6` / `PySide6` ni depender de componentes gráficos.
- **Separación de Lógica e Interfaz (`ui/`):**
  - La interfaz gráfica en `ui/` consume los callbacks del núcleo (`core/`).
  - La UI únicamente solicita acciones al `CommandDispatcher` o escucha callbacks thread-safe.
- **Configuración Externa (`config.yaml`, `presets/`):**
  - **Cero Hardcoding:** Rutas de ejecutables, mapeo de gestos, credenciales locales, umbrales y modelos se leen desde `config.yaml` o los YAML de `presets/`.

---

## 3. Concurrencia y Thread-Affinity en PyQt6

- **Regla de Oro de Qt:** **JAMÁS** manipular widgets ni métodos de GUI directamente desde hilos secundarios (como el bucle de visión de MediaPipe o el hilo de escucha de PyAudio/Whisper).
- **Comunicación Thread-Safe:**
  - Utilizar funciones envolventes seguras con `QTimer.singleShot` o señales/slots de Qt para actualizar la interfaz.
  - Proteger referencias globales a widgets (`_panel_instance`) mediante cerrojos de concurrencia (`threading.Lock`).
- **Cierre de Hilos:** Todos los hilos secundarios (`daemon=True`) deben responder a un flag de parada (`self.is_running`) y ser unidos ordenadamente (`thread.join(timeout=N)`) en la secuencia de apagado.

---

## 4. Manejo de Hardware y Dispositivos Local

- **Hardware Creado/Liberado de Forma Concurrente:**
  - OpenCV: `cv2.VideoCapture` debe cerrarse explícitamente en un bloque `finally` o dentro del método `stop()`.
  - Windows DirectShow / COM: En hilos secundarios que interactúen con enumeración de dispositivos (`pygrabber`), llamar explícitamente a `pythoncom.CoInitialize()` y `pythoncom.CoUninitialize()`.
- **Protección de Consumo y Calentamiento (OSC UDP):**
  - En la rutina de arranque (`start()`), enviar orden de despertar a la cámara (`wake_camera()`).
  - En la rutina de apagado (`stop()`), enviar obligatoriamente orden de suspensión (`sleep_camera()`).
  - La llamada OSC debe ser idempotente y no bloqueante (fire-and-forget).

---

## 5. Integración con LLM Local (Ollama)

- **Optimización de Latencia Percibida:**
  - Mantener los modelos cargados en VRAM con `"keep_alive": "10m"`.
  - Desactivar modos de razonamiento no requeridos (`"think": false`) para comandos de voz directos.
  - Acotar la salida con `num_predict` (p. ej. 220 tokens) y prompts de concisión estricta.
- **Respuestas en Streaming:**
  - Consumir generadores de texto por oraciones para alimentar el TTS gradualmente sin bloquear el hilo principal ni la percepción de voz.

---

## 6. Pruebas Automatizadas y Calidad

- **Cobertura de Pruebas con Mocks:**
  - Toda adición o modificación en `core/` debe contar con sus correspondientes tests unitarios en `tests/`.
  - Utilizar `unittest.mock` para simular la cámara física, servidores Ollama y sockets OSC UDP, permitiendo la ejecución de la suite en entornos CI o sin hardware conectado.
- **Comando de Verificación Estándar:**
  ```powershell
  .\venv\Scripts\python.exe -m pytest tests/ -v
  ```
