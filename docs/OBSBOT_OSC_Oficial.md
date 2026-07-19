# OBSBOT — Comandos OSC oficiales (extraídos de la propia instalación)

> Fuente: `D:\OBSBOT Center\data\ctrl\touchosc\OBSBOT Sample-UDP.tosc` y `OBSBOT Sample-TCP.tosc`
> Estos archivos `.tosc` son plantillas oficiales de TouchOSC que **OBSBOT Center incluye en su propia instalación** — no son reconstrucciones de terceros para otro modelo. Ambos archivos (UDP y TCP) coinciden exactamente en direcciones y argumentos.
>
> Formato del archivo: zlib comprimido (`zlib.decompress`) conteniendo un XML propietario de TouchOSC 3, con cada control definido como `<node>` con propiedades (`name`, `tag`) y mensajes OSC bajo `<messages><osc><path>` (compuesto de `<partial>` tipo `CONSTANT` o `PROPERTY`).
>
> Extraído y verificado: 2026-07-05.

## Tabla completa de comandos (envío)

| Control (nombre interno) | Dirección OSC | Argumento |
|---|---|---|
| Wake/Sleep | `/OBSBOT/WebCam/General/WakeSleep` | 0-1 |
| Seleccionar dispositivo 1-4 | `/OBSBOT/WebCam/General/SelectDevice` | 0 / 1 / 2 / 3 |
| Ir a posición preestablecida 1-3 | `/OBSBOT/WebCam/Tiny/TriggerPreset` | 0 / 1 / 2 |
| **Activar/desactivar seguimiento (AI Lock)** | `/OBSBOT/WebCam/Tiny/ToggleAILock` | 0-1 |
| Fondo virtual: ninguno | `/OBSBOT/WebCam/Meet/SetVirtualBackground` | 0 |
| Fondo virtual: blur | `/OBSBOT/WebCam/Meet/SetVirtualBackground` | 1 |
| Fondo virtual: verde | `/OBSBOT/WebCam/Meet/SetVirtualBackground` | 2 |
| Fondo virtual: reemplazo | `/OBSBOT/WebCam/Meet/SetVirtualBackground` | 3 |
| Auto-encuadre: apagado | `/OBSBOT/WebCam/Meet/SetAutoFraming` | 0 |
| Auto-encuadre: individual | `/OBSBOT/WebCam/Meet/SetAutoFraming` | 1 |
| Auto-encuadre: grupo | `/OBSBOT/WebCam/Meet/SetAutoFraming` | 2 |
| Zoom (control continuo) | `/OBSBOT/WebCam/General/SetZoom` | 0-100 |
| Zoom máximo | `/OBSBOT/WebCam/General/SetZoomMax` | 0-1 |
| Zoom mínimo | `/OBSBOT/WebCam/General/SetZoomMin` | 0-1 |
| Campo de visión 86° | `/OBSBOT/WebCam/General/SetView` | 0 |
| Campo de visión 78° | `/OBSBOT/WebCam/General/SetView` | 1 |
| Campo de visión 65° | `/OBSBOT/WebCam/General/SetView` | 2 |
| Resetear gimbal | `/OBSBOT/WebCam/General/ResetGimbal` | 1 |
| Gimbal arriba | `/OBSBOT/WebCam/General/SetGimbalUp` | 0-100 |
| Gimbal izquierda | `/OBSBOT/WebCam/General/SetGimbalLeft` | 0-100 |
| Gimbal abajo | `/OBSBOT/WebCam/General/SetGimbalDown` | 0-100 |
| Gimbal derecha | `/OBSBOT/WebCam/General/SetGimbalRight` | 0-100 |

## Mensajes de solo recepción (feedback de la cámara, no se envían)

- `/OBSBOT/WebCam/General/ConnectedResp`
- `/OBSBOT/WebCam/General/DeviceInfo`
- `/OBSBOT/WebCam/Tiny/PresetPositionInfo`
- `/OBSBOT/WebCam/Tiny/AiTrackingInfo`
- `/OBSBOT/WebCam/Meet/VirtualBackgroundInfo`
- `/OBSBOT/WebCam/Meet/AutoFramingInfo`
- `/OBSBOT/WebCam/General/ZoomInfo`

Estos son mensajes que OBSBOT Center **envía de vuelta** para que un panel de control (TouchOSC) refleje el estado actual — NOVA podría escucharlos en el futuro para saber si el tracking está realmente activo, en vez de solo asumir que el comando de envío funcionó.

## Diferencias importantes vs lo que NOVA tenía antes de esta corrección (2026-07-05)

| Antes (incorrecto / no oficial) | Ahora (oficial, verificado) |
|---|---|
| `SetTrackingMode` (0/1) — no existe en el protocolo real | `ToggleAILock` (0/1) |
| `SetAiMode` con enteros 0/1/2 (Headroom/Standard/Motion, doc. de Tiny 2 Lite) | No confirmado que exista para Tiny 3 Lite bajo ese nombre — no se encontró en la plantilla oficial. Pendiente de investigar si hay equivalente. |
| `GimbalReset` (nombre invertido) | `ResetGimbal`, argumento `1` (no `0`) |
| `SetGimMotorDegree` con `[speed, pan, tilt]` | Cuatro comandos separados: `SetGimbalUp/Down/Left/Right`, cada uno con un valor 0-100 |

## Cómo se extrajeron estos datos (para repetir el proceso con otras plantillas)

```python
import zlib, xml.etree.ElementTree as ET

with open("OBSBOT Sample-UDP.tosc", "rb") as f:
    xml_bytes = zlib.decompress(f.read())

root = ET.fromstring(xml_bytes)
# Cada <node> tiene <properties><property><key>name/tag</key><value>...</value></property></properties>
# y <messages><osc><send>1</send><path><partial><type>CONSTANT|PROPERTY</type><value>...</value></partial>...</path>
# <arguments><partial>...</partial></arguments></osc></messages>
# PROPERTY con value "tag" o "parent.tag" se resuelve con el "tag" del propio nodo o su padre.
```

Hay más plantillas en la misma carpeta que valdría la pena revisar si se necesitan más funciones (ej. si existen `.tosc` para otros modelos OBSBOT o para el modo "Meet"/streaming): `D:\OBSBOT Center\data\ctrl\touchosc\`.
