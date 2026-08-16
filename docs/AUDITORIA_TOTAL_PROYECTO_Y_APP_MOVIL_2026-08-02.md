# Auditoría total de NOVA y app móvil

**Fecha:** 2026-08-02  
**Repositorio:** `E:\proyectos\Camara inteligente`  
**Rama:** `main` (remoto: `https://github.com/ale0009/asistente-de-camara.git`)  
**Alcance:** código, configuración, documentación, pruebas, integración OBSBOT, servicio de agente, UI de escritorio, Command Center web y aplicación Android.

> Este documento describe el estado comprobado en el árbol de trabajo. Distingue explícitamente entre lo que existe en código, lo que está probado automáticamente, lo que solo es interfaz/prototipo y lo que necesita validación física.

---

## 1. Objetivo original reconstruido

NOVA pretende ser un asistente personal multimodal, local y privado, donde la cámara OBSBOT y sus micrófonos se convierten en extensiones del computador. El usuario debe poder:

1. Hablarle a NOVA para controlar el computador, la cámara y aplicaciones.
2. Usar la OBSBOT mediante voz y gestos: seguimiento, despertar, suspensión, zoom, encuadre, giro y posiciones.
3. Ver la cámara y los estados importantes en una interfaz clara.
4. Preguntar a un modelo local y recibir una respuesta breve **en pantalla y por voz**.
5. Buscar archivos, abrir aplicaciones, capturar pantalla, crear notas en Obsidian y registrar actividades sin enviar información personal a terceros.
6. Extender esos controles a una app móvil y a una interfaz de Command Center sin duplicar la lógica.
7. Mantener consumo predecible de CPU, RAM y GPU, respetando los límites de energía del equipo.

La meta no es solo “una cámara que sigue”: es un sistema local de interacción por voz, visión y automatización con una cámara motorizada como sensor y actuador.

---

## 2. Resultado ejecutivo

El proyecto tiene una base de escritorio funcional y bastante más avanzada que las otras superficies. La apertura de cámara, voz, gestos, comandos clásicos, Ollama, Obsidian, captura y envío OSC están implementados. Las pruebas automáticas actuales pasan.

Sin embargo, todavía **no existe un producto unificado de punta a punta**. Hay cuatro piezas parcialmente independientes:

```text
             ┌─────────────────────────────────────┐
             │ NOVA clásico: main.py + PyQt6        │
             │ Voz / gestos / cámara / OSC          │
             │ Es la ruta que realmente usas hoy.   │
             └──────────────────┬──────────────────┘
                                │
                 (sin conexión efectiva de voz)
                                │
┌───────────────────────┐       ▼        ┌────────────────────────┐
│ agent_service FastAPI │  Herramientas  │ Adaptadores llamados    │
│ AgentLoop + watcher   │───────────────▶│ "MCP" internos         │
│ Servicio paralelo     │                │ escritorio/vault/git... │
└───────────────────────┘                └────────────────────────┘

┌──────────────────────────────┐       ┌──────────────────────────────┐
│ nova-command-center (React)  │       │ novaapp (Android Kotlin)     │
│ Panel visual, sin API real   │       │ Prototipo visual, sin enlace │
│ y con puerto distinto al UI  │       │ al PC, cámara u OSC          │
└──────────────────────────────┘       └──────────────────────────────┘
```

### Diagnóstico en una frase

**La base técnica existe, pero falta convertir varios prototipos y rutas paralelas en un único sistema observable, seguro y validado con hardware real.**

---

## 3. Inventario del proyecto

| Área | Ubicación | Estado comprobado | Propósito |
|---|---|---|---|
| Aplicación de escritorio | `main.py`, `core/`, `ui/` | Implementada y ejecutada | Ruta principal de NOVA: cámara, voz, gestos, OSC, panel y comandos. |
| Control OBSBOT | `core/osc_controller.py`, `core/system_controller.py` | Implementado; falta aceptación física | Envía OSC a `127.0.0.1:16284`, inicia OBSBOT Center y gestiona ventana. |
| Voz | `core/voice_engine.py` | Implementada; integración completa pendiente | Wake word, Whisper, TTS, micrófono configurable. |
| Gestos | `core/gesture_engine.py` | Implementado; requiere prueba física repetible | MediaPipe detecta palma, puño, pellizco y acciones configurables. |
| IA local | `core/ollama_bridge.py` | Implementada | Consulta Ollama, por defecto `qwen3:8b`, incluye modo streaming y visión Moondream. |
| Automatización local | `core/file_tools.py`, `core/obsidian_logger.py`, `core/system_controller.py` | Implementada parcialmente | Notas, búsqueda limitada a carpetas permitidas, capturas y aplicaciones. |
| Agente HTTP | `agent_service/`, `start_nova_agent.py` | Parcial y paralelo | FastAPI, enrutamiento LLM, registro SQLite, watcher y adaptadores de herramientas. |
| Adaptadores de herramientas | `mcp_servers/` | Implementados como llamadas internas | Escritorio, vault, Git, n8n y web. No son un servidor MCP interoperable. |
| Cliente web | `nova-command-center/` | Prototipo visual | React/Vite. Estados simulados, sin comunicación con NOVA. |
| Aplicación móvil | `novaapp/` y `my-application.zip` | Prototipo visual | Android/Compose/Room. Estados simulados, no controla PC ni OBSBOT. |
| Pruebas | `tests/` | 97 pruebas superadas | Principalmente unitarias y con mocks; no sustituyen prueba física. |
| Empaquetado | `build_exe.py`, `build/`, `dist/` | Artefactos presentes | Hay artefactos locales pesados, no deben ser fuente de verdad. |

### Tamaño y mantenimiento

- `venv/` ocupa aproximadamente 1.6 GB.
- `dist/` ocupa aproximadamente 962 MB y `build/` aproximadamente 172 MB.
- Estos directorios generados no deben versionarse ni usarse como referencia de código.
- La app móvil, el Command Center, la carpeta de estética y el ZIP móvil están actualmente **sin seguimiento Git**. Si el disco falla o se cambia de equipo, no estarán garantizados en GitHub.

---

## 4. Estado real por capacidad

| Capacidad objetivo | Código | Prueba automática | Validación real | Estado |
|---|---:|---:|---:|---|
| Abrir OBSBOT Center al iniciar NOVA | Sí | Parcial | Observada en logs | Implementada, frágil por automatización de ventana. |
| Abrir flujo de vídeo en NOVA | Sí | Parcial | Observada en logs | Implementada; depende de índice, suspensión y exclusividad USB. |
| Enviar comandos OSC | Sí | Sí | No demostrada de forma repetible | Pendiente de aceptación de hardware. |
| Seguimiento de persona | Se envía `ToggleAILock` | Sí, por mocks | Inconsistente en los reportes | Crítico: falta confirmar configuración y feedback real de OBSBOT. |
| Despertar/suspender cámara | Se envía `WakeSleep` | Sí, por mocks | Inconsistente | Pendiente de matriz física de prueba. |
| Zoom, direcciones y presets | Sí | Sí | No certificada | Pendiente de validar payloads y presets reales. |
| Voz a comando | Sí | Sí | Observada en logs | Funcional en la ruta clásica. |
| Responder por voz | Sí | Parcial | No certificada como conversación completa | Debe probarse pregunta → LLM → TTS audible. |
| Gestos a acción | Sí | Sí | Observada en logs anteriores | Requiere evitar activaciones repetidas y validar frente a cámara real. |
| Preguntas a Ollama | Sí | Sí | Observada en logs | Funcional; la velocidad depende del modelo y del equipo. |
| Notas de Obsidian | Sí | Sí | Pendiente de prueba de extremo a extremo | La ruta clásica puede escribir notas dentro de la carpeta configurada. |
| Búsqueda de archivos | Sí | Sí | Pendiente de prueba de extremo a extremo | Limitada a carpetas permitidas, lo cual es correcto. |
| API de agente con herramientas | Sí | Parcial | No conectada a la voz principal | Ruta paralela. |
| Control desde web | Solo UI | No | No | No implementado. |
| Control desde móvil | Solo UI | No | No | No implementado. |
| Funcionamiento 100 % local | Parcial | No | No | No se cumple aún por TTS Edge y dependencias Gemini/Firebase móviles. |

---

## 5. Arquitectura de escritorio: qué funciona y qué está dividido

### 5.1 Ruta que ejecuta el usuario

Al ejecutar `python main.py`, NOVA crea directamente:

- `CameraManager`
- `OSCController`
- `SystemController`
- `VoiceEngine`
- `GestureEngine`
- `CommandDispatcher`
- `OllamaBridge`
- interfaz PyQt6 (`ui/`)

La voz y los gestos llegan a `CommandDispatcher`. Este utiliza el enrutador clásico de `core/intent_router.py`.

Esta es la ruta correcta para concentrar primero la validación de cámara, voz y gestos, porque es la que se está usando realmente.

### 5.2 Ruta de agente paralela

`start_nova_agent.py` inicia un servidor FastAPI en `127.0.0.1:8000`, el watcher y después importa NOVA. El `agent_service` contiene un `AgentLoop` que elige respuestas o herramientas por LLM.

Existe `voice_service/voice_client.py`, preparado para llevar voz al agente HTTP y reproducir la respuesta, pero `main.py` ni `start_nova_agent.py` lo instancian. Por eso:

> Una frase hablada puede llegar al `CommandDispatcher` clásico, mientras que el conjunto de herramientas del agente queda sin usar por esa misma conversación.

Esta bifurcación explica por qué una función parece existir en una parte del proyecto, pero no responde desde la aplicación que el usuario está ejecutando.

### 5.3 Uso del término MCP

`mcp_servers/` no implementa el protocolo Model Context Protocol estándar: no hay dependencia MCP, transporte JSON-RPC/stdio/SSE ni servidor interoperable. Son clases Python locales con esquemas de herramientas e invocación directa.

No es malo como diseño inicial, pero debe elegirse una opción:

1. Llamarlo claramente **adaptadores internos de herramientas** y seguir simplificando el monolito local.
2. Implementar MCP estándar de verdad, si se requiere que clientes externos descubran y consuman estas herramientas.

La documentación no debe afirmar interoperabilidad MCP mientras no exista ese protocolo.

---

## 6. OBSBOT: estado, causa probable de los fallos y criterio de aceptación

### 6.1 Lo que el código hace

La configuración actual apunta a:

```yaml
camera_index: 0
device: OBSBOT Tiny 3 Lite
osc_host: 127.0.0.1
osc_port: 16284
```

`OSCController` transmite comandos de seguimiento, zoom, dirección, vista, presets y despertar/suspensión a OBSBOT Center. `SystemController` intenta abrir `D:\OBSBOT Center\bin\OBSBOT_Main.exe`, escribir una preferencia OSC y minimizar la ventana.

### 6.2 Problema central

En los registros se confirma que NOVA recibe “sígueme” y ejecuta la función de cámara. Eso demuestra intención y envío desde NOVA, **no demuestra que la cámara física haya aceptado ni ejecutado el comando**.

El estado de la interfaz se actualiza de forma optimista justo después de enviar OSC. El controlador tiene receptor de feedback, pero hoy no se usa como confirmación obligatoria antes de mostrar “seguimiento activo”. Por eso la UI puede decir que está siguiendo aunque la cámara esté quieta.

### 6.3 Hipótesis que deben probarse, no asumir

1. OBSBOT Center no tiene OSC activo de forma persistente, o sobrescribe el archivo de preferencias al iniciar.
2. El puerto o el formato de los mensajes no coincide con la versión de OBSBOT Center o el firmware.
3. El modelo de cámara expone vídeo UVC pero no acepta una orden concreta de seguimiento desde OSC.
4. La cámara está ocupada, suspendida o en un modo que bloquea la orden.
5. Las posiciones/preajustes están indexados de manera distinta. En el código hay llamadas a preset `1`, `2` y `3`, mientras la plantilla de referencia disponible habla de índices `0`, `1` y `2`.
6. El feedback del dispositivo no llega, no se interpreta o no se refleja en UI.

### 6.4 Prueba de aceptación obligatoria de cámara

No avanzar a funciones complejas hasta completar una matriz repetible, con OBSBOT Center abierto y con NOVA:

| Prueba | Acción | Evidencia válida |
|---|---|---|
| Conexión | Arrancar NOVA | Vídeo en panel y estado de dispositivo identificado. |
| Wake | “despierta la cámara” | Cambio físico y feedback/estado confirmado. |
| Sleep | “suspende la cámara” | Cambio físico y feedback/estado confirmado. |
| Seguimiento | “sígueme” | La cámara encuadra y acompaña al sujeto durante 15 s. |
| Detener | “para de seguirme” | La cámara cesa seguimiento. |
| Zoom | “acércate” / “aléjate” | Cambio visible y rango acotado. |
| Pan/Tilt | izquierda/derecha/arriba/abajo | Movimiento visible en la dirección correcta. |
| Preset | posición 1, 2 y 3 | Posición guardada correcta, sin desfase de índice. |
| Recuperación | suspender, despertar, repetir | Las órdenes vuelven a funcionar sin reiniciar NOVA. |

El resultado debe guardarse con fecha, versión de OBSBOT Center, firmware, modelo exacto, puerto y payload enviado. Hasta entonces “tracking” debe mostrarse como **orden enviada**, no como “activo”.

### 6.5 Decisión de interfaz: botón de despertar

Debe mantenerse un botón de despertar como recuperación visible y accesible. No debe ser el método obligatorio:

- La voz debe permitir despertar y suspender cuando el micrófono siga disponible.
- El botón sirve si el reconocimiento falla, si el micrófono está silenciado o al diagnosticar la conexión.
- La UI debe mostrar tres estados: `desconocido`, `orden enviada`, `confirmado por dispositivo`.

---

## 7. Voz, conversación y privacidad

### Implementado

- Wake word configurada: `hey_jarvis`.
- Whisper: modelo `small`, idioma español.
- Micrófono configurable mediante índice; los registros anteriores mostraban índice `1`.
- TTS configurado con voz `Salome`.
- Ollama por defecto: `qwen3:8b`, con `think: false`, límite de salida y `keep_alive`.

### Hallazgos

1. El mensaje de arranque muestra la ruta del modelo wake-word en vez de una frase humana. Es un defecto de UX, no una confirmación de que se escucha “NOVA”.
2. La ruta clásica puede consultar Ollama; falta una prueba explícita de conversación completa: audio → texto → respuesta LLM → audio audible → panel.
3. `edge-tts` no es un motor de síntesis completamente local. Para cumplir privacidad local, debe reemplazarse por una alternativa instalada localmente (por ejemplo Piper o una voz SAPI local de Windows), o declarar claramente el modo en línea y pedir consentimiento.
4. El usuario desea múltiples fuentes de entrada (audífonos, OBSBOT, micrófono externo). Falta un selector de dispositivos por nombre, medidor de nivel, prueba de audio y recuperación si el índice cambia tras reconectar USB. Los índices numéricos no son estables.

### Recomendación de rendimiento

Mantener `qwen3:8b` como modelo de calidad, pero ofrecer perfiles:

| Perfil | Uso | Recomendación |
|---|---|---|
| Instantáneo | órdenes y conversación corta | Enrutador determinista primero; modelo pequeño local como `qwen3:4b` si está disponible. |
| Equilibrado | preguntas normales | `qwen3:8b`, respuestas breves, streaming de TTS por frase. |
| Visión | “¿qué ves?” | Moondream solo bajo demanda, nunca en cada frame. |
| Profundo | análisis largo | Modelo grande/cola explícita; no bloquear voz, cámara ni UI. |

Los comandos conocidos (“sube volumen”, “abre Blender”, “sígueme”) no deben pasar por LLM: deben resolverse con reglas instantáneas. El LLM queda para intención abierta y respuesta conversacional.

---

## 8. Gestos y visión

### Implementado

- MediaPipe detecta mano y consolida gestos.
- Mapeos observados: palma abierta → seguimiento, puño → detener seguimiento, pellizco → zoom.
- Los registros previos demuestran detección de `palma_abierta`, `puno` y `pellizco` y envío de sus comandos asociados.

### Lo que falta

1. Estado visible del gesto detectado y de la acción ejecutada en la UI.
2. Enfriamiento por acción, para que un puño sostenido no ejecute “detener” repetidamente.
3. Modo de gestos armado/desarmado por voz y botón. Sin él, los gestos accidentales son inevitables.
4. Calibración de iluminación, distancia y mano dominante.
5. Catálogo de gestos limitado y seguro antes de asignar acciones peligrosas (cerrar apps, borrar archivos, enviar mensajes).
6. Pruebas reales que midan falsos positivos y latencia.

La propuesta segura inicial es: palma = seguimiento, puño = detener, pellizco = acercar, dos dedos = cambiar ventana, palma sostenida = pausar gestos. Cada acción debe mostrar una notificación reversible.

---

## 9. Aplicación móvil: propósito original y estado real

### 9.1 Qué es

`novaapp/` es una app Android nativa en Kotlin, Jetpack Compose y Room. Su intención visual es ser un compañero móvil de NOVA con:

- panel de estado de cámara/IA;
- botones de tracking, zoom, despertar y suspensión;
- feed de vídeo;
- misiones, actividad, notas de Obsidian y configuración;
- registro local de acciones.

Es una dirección de producto coherente: un control remoto local de NOVA puede ser útil para grabación, streaming, presentaciones y automatización.

### 9.2 Qué no hace todavía

La aplicación no se conecta al PC ni a OBSBOT:

- No usa Retrofit, OkHttp, WebSocket ni una API de NOVA.
- Sus cambios de tracking, zoom y sueño modifican `StateFlow` y registros Room; no envían OSC ni HTTP.
- El supuesto vídeo es una vista `Canvas`, no CameraX ni stream del PC.
- Las notas de Obsidian se guardan como ejemplos locales; no sincronizan con el vault.
- La actividad contiene datos semilla y mensajes simulados.
- Las dependencias de CameraX están comentadas.

Por tanto, debe presentarse como **prototipo de UX**, no como control remoto funcional.

### 9.3 Conflicto con el requisito de privacidad

El proyecto Android declara Firebase AI, App Check reCAPTCHA, una clave `GEMINI_API_KEY` en su documentación y una capacidad de Gemini del lado servidor. Esto contradice el objetivo de no enviar datos ni generar pagos.

Para que sea local y privada, la aplicación móvil debe:

1. Eliminar Firebase AI/Gemini si no es imprescindible.
2. Conectarse únicamente al agente NOVA que corre en el PC dentro de la red local.
3. Usar emparejamiento por QR y token de un solo dispositivo, no una clave compartida en APK.
4. Usar HTTPS/TLS local o una red privada confiable; como mínimo, limitar IPs y requerir token.
5. No publicar el servicio FastAPI a `0.0.0.0` sin autenticación.

### 9.4 Verificación de compilación pendiente

No hay wrapper `gradlew` en la carpeta y el entorno inspeccionado dispone de Java 8, mientras el Android Gradle Plugin declarado requiere una instalación moderna de Android Studio/JDK. No fue posible certificar una compilación Android reproducible desde este entorno.

### 9.5 Arquitectura móvil objetivo

```text
App Android ── HTTPS/WebSocket con token ──► API local de NOVA en PC
       ▲                                         │
       │ estados/eventos                         ├─► CommandDispatcher único
       │ preview opcional                         ├─► OSC / OBSBOT Center
       └─────────────────────────────────────────┴─► Ollama / Obsidian / archivos
```

La app no debe implementar su propia lógica de cámara, gestos o IA. Debe ser cliente de un único núcleo NOVA.

---

## 10. Command Center web: propósito y estado real

`nova-command-center/` es una interfaz React/Vite visualmente prometedora. Ofrece un dashboard de cámara, actividad, notas, automatizaciones y controles.

Pero actualmente:

- No hay llamadas `fetch`, cliente HTTP, WebSocket ni conexión con FastAPI.
- El estado es local y simulado.
- El script Vite inicia por defecto en el puerto `3000`, mientras `ui/tray_app.py` abre `http://localhost:5173`. El menú abre un puerto diferente al configurado por el proyecto.
- La configuración usa `--host=0.0.0.0`; en desarrollo expone el panel a la red local innecesariamente.

Debe considerarse prototipo de diseño. Antes de usarlo como interfaz operacional se necesita un contrato API compartido, autenticación, estados en tiempo real y un único puerto/configuración.

---

## 11. Seguridad, privacidad y riesgos técnicos

### Críticos (resolver antes de abrir APIs a móvil/web)

| Riesgo | Evidencia | Impacto | Acción necesaria |
|---|---|---|---|
| Escape del vault de Obsidian | `mcp_servers/vault_mcp.py` une rutas con `os.path.join` sin resolver y validar que sigan dentro del vault. | Un `../../` puede leer/escribir fuera del vault con permisos del proceso. | Resolver ruta absoluta y rechazar toda ruta fuera de `vault_path`; pruebas de traversal. |
| Watcher autoalimentado | El watcher observa el proyecto completo y no excluye `logs/`; el agente registra cada interacción en `logs/agent_audit.db`. | Guardar un evento puede provocar otro evento y más llamadas al LLM en bucle. | Excluir logs, bases SQLite, build/dist; debounce y cola; solo vigilar rutas explícitas. |
| Servicio LAN sin modelo de seguridad | FastAPI está solo en localhost hoy; para móvil habrá que exponerlo. | Abrirlo sin token permitiría controlar aplicaciones/cámara desde la red. | Emparejamiento, token, lista de clientes, permisos y auditoría. |

### Altos

| Riesgo | Evidencia | Acción necesaria |
|---|---|---|
| Estado de cámara optimista | OSC marca estados al enviar, no al confirmar feedback. | Separar `orden enviada` de `confirmado`; registrar feedback/timeout. |
| Dos núcleos de intención | `main.py` usa router clásico; `agent_service` usa otro. | Definir un solo `CommandBus` y conectar voz, gestos, API, web y móvil a él. |
| Privacidad declarada pero no efectiva | `edge-tts` y Firebase/Gemini móvil contradicen “todo local”. | Reemplazar o hacer opt-in explícito; documentar todo flujo de red. |
| Control de procesos amplio | Cierre de aplicaciones usa coincidencia parcial de nombre. | Lista permitida, vista previa y confirmación para acciones disruptivas. |
| Web reader sin política de red | Puede solicitar URLs arbitrarias. | Restringir hosts internos, dominios y requerir confirmación antes de navegar. |

### Medios

- Falta `beautifulsoup4` en `requirements.txt`, aunque `core/web_reader.py` importa `bs4`. Una instalación limpia puede fallar.
- Falta `httpx` para ejecutar `FastAPI TestClient`; no hay prueba automatizada del endpoint HTTP.
- No hay pruebas E2E reales de OBSBOT, micrófono, Ollama, Obsidian, web o móvil.
- Hay contradicciones en documentación: se declaran 79, 84 y 94 pruebas según el documento; la verificación actual obtuvo 97.
- `git diff --check` encuentra espacios finales en cambios locales de `tests/test_gesture_engine.py`. No se modificaron en esta auditoría.
- Hay advertencias conocidas de `pkg_resources` de pygame; no bloquean NOVA, pero requieren actualización de dependencias a mediano plazo.

---

## 12. Pruebas ejecutadas durante esta auditoría

| Verificación | Resultado | Alcance real |
|---|---|---|
| Compilación Python (`compileall`) | Correcta | `core`, `agent_service`, `mcp_servers`, `voice_service`, `watchers`, `ui`, lanzadores. |
| Suite Python | **97 passed**, 1 advertencia, 13.53 s | Unitarias/mocks; no prueba cámara, USB, micrófono ni OBSBOT físicamente. |
| Importación FastAPI | Correcta | El servidor puede importarse. |
| Prueba HTTP con `TestClient` | No ejecutable | Falta `httpx` en el entorno de prueba. |
| Compilación Android | No certificada | Falta wrapper y entorno Android/JDK compatible en esta estación. |
| Validación física OBSBOT | No certificada | Los logs prueban comandos de NOVA, no el movimiento físico. |

---

## 13. Estado del control de versiones y continuidad

### En Git

El repositorio remoto está configurado y la rama local está vinculada a `origin/main`. La base Python y los commits recientes relacionados con visión, gestos, agente y TTS están en el historial.

### Fuera de Git al momento de la auditoría

- `novaapp/`
- `nova-command-center/`
- `nova estetica/`
- `my-application.zip`
- `docs/Auditoria_Integral_y_Profunda_NOVA_v3.1.0.md`

Esto crea dos riesgos: pérdida de trabajo y divergencia entre lo que vive en el equipo y lo que otra IA o colaborador puede recuperar desde GitHub.

### Reglas de versionado recomendadas

1. Añadir código fuente de `novaapp/`, `nova-command-center/`, activos que se usen y documentación útil.
2. No añadir `.env`, claves Gemini, `venv/`, logs, bases SQLite generadas, `build/`, `dist/` ni cachés.
3. Elegir una sola fuente móvil: carpeta fuente versionada; el ZIP solo como exportación opcional con versión/fecha.
4. Crear un `README` raíz actualizado con una tabla de superficies y comandos de arranque.
5. Corregir documentos obsoletos antes de prometer capacidades no integradas.

---

## 14. Hoja de ruta priorizada hacia la meta

### Fase 0 — Estabilización y seguridad (bloqueante)

1. Corregir traversal del vault y agregar pruebas de seguridad.
2. Corregir watcher: exclusiones, debounce, cola y prevención de autoeventos.
3. Añadir `beautifulsoup4` y dependencias de prueba separadas (`httpx`).
4. Versionar fuentes de móvil/web y actualizar `.gitignore`.
5. Unificar y fechar la documentación de estado.

**Criterio de salida:** no hay escape de rutas, no hay bucle de watcher, instalación limpia reproducible y todas las fuentes importantes están versionadas.

### Fase 1 — Verdad física de OBSBOT (bloqueante para prometer tracking)

1. Confirmar versión de OBSBOT Center, firmware y habilitación OSC desde su UI oficial.
2. Registrar exactamente cada paquete OSC y todo feedback recibido.
3. Implementar estado confirmado/timeout, no estado optimista.
4. Corregir índice de presets si la matriz física lo confirma.
5. Ejecutar la matriz de aceptación de cámara de la sección 6.4 y guardarla en `docs/`.

**Criterio de salida:** wake/sleep, seguimiento, stop, zoom, pan/tilt y presets funcionan tres veces consecutivas sin abrir manualmente OBSBOT Center.

### Fase 2 — Un solo núcleo NOVA

1. Definir un `CommandBus`/servicio central como única entrada de comandos.
2. Conectar a él: voz, gestos, PyQt, FastAPI, móvil y web.
3. Mantener enrutamiento determinista para órdenes conocidas; LLM solo para intención abierta.
4. Devolver un evento estructurado: intención, acción, resultado, error, confirmación del dispositivo y respuesta verbal.
5. Decidir si se adopta MCP real o se renombra el adaptador interno.

**Criterio de salida:** el mismo comando produce el mismo resultado sin importar si llega por voz, botón, web o móvil.

### Fase 3 — Conversación local, rápida y audible

1. Añadir una prueba E2E para pregunta corta → Ollama → TTS → panel.
2. Reemplazar Edge TTS por motor local o añadir modo de privacidad explícito.
3. Implementar selector de micrófono por nombre, prueba de audio, VU meter y fallback.
4. Mantener perfiles Instantáneo/Equilibrado/Visión/Profundo.
5. Medir latencia p50/p95 y consumo de CPU/RAM/GPU con la GPU limitada como está.

**Criterio de salida:** una pregunta breve recibe respuesta audible en segundos, sin bloquear cámara ni UI.

### Fase 4 — Gestos seguros y utilizables

1. Añadir modo armado, cooldown y visualización de gesto/acción.
2. Definir máximo cinco gestos iniciales, todos reversibles.
3. Medir falsos positivos en diferentes condiciones de luz.
4. Guardar cada activación con fecha, confianza y acción para depurar.

**Criterio de salida:** los gestos se ejecutan una vez por intención y son comprensibles para el usuario.

### Fase 5 — API local, Command Center y aplicación móvil funcional

1. Diseñar contrato API versionado (`/status`, `/commands`, `/events`, `/preview`).
2. Añadir autenticación de emparejamiento y permisos antes de abrir LAN.
3. Conectar React y Android al contrato, retirando estados simulados.
4. Eliminar Firebase/Gemini si el requisito es local; usar solo PC + Ollama.
5. Añadir stream de preview de bajo bitrate o snapshots; no duplicar procesamiento de visión en el teléfono.
6. Preparar pruebas Android y navegador contra una API de desarrollo segura.

**Criterio de salida:** móvil y web muestran el estado real de NOVA, reciben eventos y controlan únicamente a un PC emparejado.

### Fase 6 — Consolidación como producto local

1. Instalador reproducible, configuración inicial y diagnóstico de dispositivos.
2. Modo seguro, logs rotativos, exportación de bitácora y restauración de configuración.
3. Métricas locales de recursos y límites por perfil de hardware.
4. Guía de comandos/gestos dentro de la interfaz.
5. Suites E2E para los flujos críticos y registro de compatibilidad por cámara/firmware.

---

## 15. Qué puede continuar otra IA sin reinterpretar

1. **No dar por resuelto el tracking**: primero ejecutar y documentar la prueba física OBSBOT. Los logs de “Ejecutando comando de cámara” no son confirmación de movimiento.
2. **No construir funciones nuevas sobre el watcher actual** hasta evitar el ciclo con `logs/agent_audit.db`.
3. **No exponer FastAPI a red local** antes de autenticar y confinar herramientas.
4. **No describir Android o React como aplicaciones conectadas**: son maquetas funcionales locales de UI, no clientes de NOVA.
5. **No afirmar procesamiento totalmente local** mientras se use Edge TTS o dependencias Gemini/Firebase.
6. **Unificar la ruta de intención** antes de añadir más comandos: la voz clásica y el agente HTTP deben pasar por el mismo núcleo.
7. Conservar los cambios locales existentes y revisar cada uno antes de hacer commits; el árbol ya estaba modificado antes de esta auditoría.

---

## 16. Conclusión

NOVA ya supera la fase de idea: tiene cámara, comandos, voz, gestos, LLM local, Obsidian y una UI de escritorio operando como base. El trabajo prioritario no es sumar más botones ni más modelos, sino asegurar la verdad del hardware, eliminar rutas paralelas, cerrar riesgos de seguridad y conectar las interfaces móvil/web al mismo núcleo.

La siguiente entrega técnicamente correcta debe ser una **Fase 0 + Fase 1**: seguridad y prueba física de OBSBOT con feedback verificable. Solo después conviene convertir la app móvil y el Command Center en clientes reales del asistente.
