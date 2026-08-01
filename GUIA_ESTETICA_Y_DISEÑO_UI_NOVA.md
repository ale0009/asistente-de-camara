# ESPECIFICACIÓN ESTÉTICA Y GUÍA DE DISEÑO DE UI DE NOVA

> **Documento de Referencia de Diseño Gráfico y Componentes de Interfaz**  
> **Estilo:** Glassmorphic HUD / Dark Mode Midnight / Cyan Eléctrico (`#00e5ff`)  
> **Fecha:** 31 de Julio de 2026  
> **Propósito:** Documentar con máximo lujo de detalle el sistema de diseño visual, paleta de colores, tipografías, geometría de componentes, sombras con resplandor y patrones de animación para guiar el desarrollo de nuevas interfaces.

---

## 1. SISTEMA DE DISEÑO VISUAL Y FILOSOFÍA

El diseño de NOVA se basa en la estética **HUD Glassmorphism (Cyberpunk/Sci-Fi Elegante)**:
- **Translucidez y Capas:** Fondos azul noche profundo con transparencia alpha (`rgba(4, 10, 24, 0.87)`), permitiendo ver sutilmente el escritorio debajo.
- **Bordes Neon Cian Eléctrico:** Bordes ultra-finos (1px) con opacidades variables de cian (`#00e5ff`) que delimitan las áreas interactivas.
- **Luces y Resplandor (Glow Shadows):** Efectos de sombra flotantes de gran radio (Blur 48px) con tintes cian para simular iluminación propia de pantalla retroiluminada.
- **Jerarquía Tipográfica Dual:** Combinación de la fuente humanista **Inter** para títulos/botones y la tipografía monoespaciada **JetBrains Mono** para datos técnicos, terminales y lecturas de cámara.

---

## 2. PALETA DE COLORES OFICIAL (TOKENS DE COLOR)

### 2.1. Colores Primarios y Acentos

```css
/* Color Primario de Acento */
--acc-primary:       #00e5ff;               /* Cyan Eléctrico Neón */
--acc-08:            rgba(0, 229, 255, 0.08); /* Fondo botones/badges sutiles */
--acc-15:            rgba(0, 229, 255, 0.15); /* Botón primario / Hover suave */
--acc-25:            rgba(0, 229, 255, 0.25); /* Bordes activos / Selección */
--acc-50:            rgba(0, 229, 255, 0.50); /* Resplandor intermedio */
--acc-90:            rgba(0, 229, 255, 0.90); /* Texto de acento / Títulos vivos */

/* Fondos y Vidrio (Glassmorphic Surfaces) */
--bg-panel:          rgba(4, 10, 24, 0.87);   /* Fondo principal del Card */
--bg-dialog:         rgba(4, 10, 24, 0.95);   /* Fondo para diálogos modales */
--bg-canvas:         #060f1e;                 /* Azul medianoche absoluto */
--bg-video-frame:    #0d162e;                 /* Contenedor del feed de video */
--bg-log-list:       rgba(0, 0, 0, 0.42);     /* Fondo del terminal/log */
--bg-chip-overlay:   rgba(0, 0, 0, 0.76);     /* Fondo oscuro para chips de video */

/* Textos y Estados */
--text-white:        #ffffff;                 /* Blanco puro para títulos principales */
--text-dim:          rgba(190, 210, 255, 0.58);/* Azul hielo tenue para leyendas */
--text-acc:          rgba(0, 229, 255, 0.90); /* Texto de acento activo */
--color-danger-bg:   rgba(255, 55, 55, 0.06);  /* Fondo botón de parada/error */
--color-danger-border: rgba(255, 55, 55, 0.16);/* Borde botón de peligro */
--color-danger-text: rgba(255, 90, 90, 0.82); /* Icono de peligro */
--color-obsidian-bg: rgba(100, 70, 200, 0.07);/* Fondo especial Obsidian */
--color-obsidian-border: rgba(100, 70, 200, 0.18);/* Borde especial Obsidian */
--color-obsidian-text: rgba(148, 110, 240, 0.85);/* Púrpura brillante */
```

---

## 3. TIPOGRAFÍA Y REGLAS DE TEXTO

| Rol | Familia Tipográfica | Peso | Tamaño | Espaciado de Letras | Ejemplo de Uso |
|---|---|---|---|---|---|
| **Marca / Título Header** | `'Inter'` | 700 Bold | 12px | `letter-spacing: 2px` | Título "NOVA" en el cabezal |
| **Título Modal / Sección** | `'Inter'` | 700 Bold | 11px | `letter-spacing: 1px` | "CONFIGURACIÓN DE NOVA" |
| **Icono de Botón** | `'Inter'` | 600 SemiBold | 14px | Normal | Iconos vectoriales/unicode (☀, ⊙, ■, ◉) |
| **Etiqueta de Botón** | `'Inter'` | 500 Medium | 8px | Normal | "Despertar", "Trackear", "Captura" |
| **Leyendas de Input** | `'Inter'` | 600 SemiBold | 9px | Normal | "Micrófono de entrada:" |
| **Textos en Dropdown** | `'Inter'` | 500 Medium | 10px | Normal | Elementos del `QComboBox` |
| **Chips de Estado Video** | `'JetBrains Mono'` | 500 Medium | 9px | Normal | `▶ Tracking: Humano` \| `⊕ Zoom: 1.0x` |
| **Terminal / Log List** | `'JetBrains Mono'` | 400 Regular | 9px | Normal | `[11:30] CMD: despierta la cámara` |

---

## 4. ANATOMÍA Y GEOMETRÍA DE COMPONENTES EXISTENTES

```
┌─────────────────────────────────────────────────────────────┐  (340px)
│ [N] NOVA                              [● Escuchando]  [×]   │  Header (52px)
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                                                         │ │  Video Feed Container
│ │                   [FEED CÁMARA 16:9]                    │ │  (316px × 178px)
│ │                                                         │ │  Corner Radius: 8px
│ │ [▶ Tracking: Humano] [⊕ Zoom: 1.0x]                     │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │  Log Terminal
│ │ [11:30] Sistema: NOVA iniciada                          │ │  (316px × 76px)
│ │ [11:31] CMD: despierta la cámara → Cámara despierta     │ │  Background: rgba(0,0,0,0.42)
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ ┌────────────┐  ┌────────────┐  ┌────────────┐              │
│ │ ☀ Despert. │  │ ⊙ Trackear │  │ ■  Parar   │              │  Grid de Acciones
│ └────────────┘  └────────────┘  └────────────┘              │  10 Botones (3 columnas)
│ ┌────────────┐  ┌────────────┐  ┌────────────┐              │  Tamaño Botón: 98px × 52px
│ │ ◉ Captura  │  │ ⊘ Silencio │  │ ♪+ Vol+    │              │  Border Radius: 8px
│ └────────────┘  └────────────┘  └────────────┘              │
│ ┌────────────┐  ┌────────────┐  ┌────────────┐              │
│ │ ♪− Vol−    │  │ ✦ Config   │  │ ◈ Obsidian │              │
│ └────────────┘  └────────────┘  └────────────┘              │
│                 ┌────────────┐                              │
│                 │ ?  Ayuda   │                              │
│                 └────────────┘                              │
└─────────────────────────────────────────────────────────────┘  (524px)
```

### 4.1. Panel Principal Flotante (`FloatingPanel`)
- **Dimensiones:** `340px` (ancho) × `524px` (alto).
- **Esquinas:** `border-radius: 16px`.
- **Fondo:** `background: rgba(4, 10, 24, 0.87);`.
- **Borde:** `border: 1px solid rgba(0, 229, 255, 0.26);`.
- **Sombra Flotante:** `QGraphicsDropShadowEffect`, Blur Radius `48px`, offset `(0, 16)`, color `rgba(0, 0, 0, 200)`.

### 4.2. Header y Marca (`_build_header`)
- **Alto:** `52px`, borde inferior `1px solid rgba(0, 229, 255, 0.10)`.
- **Badge Logo "N":** `28px × 28px`, `border-radius: 7px`, fondo `rgba(0, 229, 255, 0.08)`, borde `1px solid rgba(0, 229, 255, 0.28)`, texto `#00e5ff` Inter Bold 12px.
- **Badge de Estado ("Escuchando"):** Alto `24px`, `border-radius: 12px`, `background: rgba(0, 229, 255, 0.08)`, `border: 1px solid rgba(0, 229, 255, 0.18)`.
  - **PulsingDot:** Indicador circular `8px × 8px` con parpadeo suave de opacidad (0.35 ↔ 1.0) cada 600ms.

### 4.3. Feed de Video y Overlay Chips (`_build_video`)
- **Contenedor:** `316px × 178px`, `border-radius: 8px`, fondo `#0d162e`.
- **Chips Overlay:** Flotando sobre el borde inferior izquierdo del video (offset Y 152px).
  - Fondo: `rgba(0, 0, 0, 0.76)`.
  - Borde: `1px solid rgba(0, 229, 255, 0.28)` (Tracking) / `rgba(0, 229, 255, 0.15)` (Zoom).
  - Tipografía: JetBrains Mono 9px Medium, padding `3px 7px`.

### 4.4. Terminal de Registro de Acciones (`_build_log`)
- **Contenedor:** `316px × 76px`, `border-radius: 8px`, fondo `rgba(0, 0, 0, 0.42)`, borde `1px solid rgba(255, 255, 255, 0.05)`.
- **Items de Lista:** JetBrains Mono 9px Regular, padding `2px 0`, separador `border-bottom: 1px solid rgba(255,255,255,0.03)`.
- **Color de Texto:** `#00e5ff` para comandos y voz; `rgba(190, 210, 255, 0.58)` para logs del sistema.

### 4.5. Cuadrícula de Botones (`_make_button`)
- **Dimensiones de Botón:** `98px` (ancho) × `52px` (alto), `border-radius: 8px`.
- **Variante Primario (Trackear):**
  - Fondo: `rgba(0, 229, 255, 0.15)`.
  - Borde: `1px solid rgba(0, 229, 255, 0.28)` (Hover: `rgba(0, 229, 255, 0.55)`).
- **Variante Peligro/Parada (Parar):**
  - Fondo: `rgba(255, 55, 55, 0.06)`, Borde: `rgba(255, 55, 55, 0.16)`.
  - Texto Icono: `rgba(255, 90, 90, 0.82)`.
- **Variante Especial Obsidian:**
  - Fondo: `rgba(100, 70, 200, 0.07)`, Borde: `rgba(100, 70, 200, 0.18)`.
  - Texto Icono: `rgba(148, 110, 240, 0.85)`.
- **Variante Neutra Standard:**
  - Fondo: `rgba(255, 255, 255, 0.03)`, Borde: `1px solid rgba(255, 255, 255, 0.07)`.
  - Hover: Fondo `rgba(0, 229, 255, 0.07)`, Borde `rgba(0, 229, 255, 0.18)`.

### 4.6. Notificaciones Flotantes Toast (`show_toast`)
- **Dimensiones:** `320px` × `42px`, `border-radius: 10px`.
- **Fondo:** `rgba(4, 10, 24, 0.94)`.
- **Borde Éxito:** `1px solid rgba(0, 229, 255, 0.35)` (Resplandor Cyan Blur 16px).
- **Borde Error:** `1px solid rgba(255, 80, 80, 0.45)` (Resplandor Rojo Blur 16px).
- **Animación:** Entrada desvanecida y deslizamiento vertical suave (Duración 220ms, curve `OutCubic`).

---

## 5. GUÍA PASO A PASO PARA CONSTRUIR NUEVAS INTERFACES FALTANTES

Para mantener 100% la consistencia estética al desarrollar nuevos paneles o ventanas modales en NOVA:

### 5.1. Reglas de Ventana y Translucidez en PyQt6
```python
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor

class NuevaVentanaNova(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 1. Quitar bordes de Windows y hacer translúcido
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 2. Definir tamaño fijo
        self.setFixedSize(400, 300)
        self._build_ui()

    def _build_ui(self):
        # 3. Contenedor principal con la hoja de estilo Glassmorphic
        container = QWidget(self)
        container.setFixedSize(400, 300)
        container.setStyleSheet("""
            QWidget {
                background: rgba(4, 10, 24, 0.92);
                border: 1px solid rgba(0, 229, 255, 0.28);
                border-radius: 14px;
            }
        """)

        # 4. Sombra exterior con resplandor Cian
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 229, 255, 50)) # Alpha 50 = Resplandor sutil
        container.setGraphicsEffect(shadow)
```

### 5.2. Estilo para Formularios e Inputs Nuevos (`QLineEdit`, `QTextEdit`, `QComboBox`)
```css
/* Entradas de Texto / Buscadores */
QLineEdit, QTextEdit {
    background: rgba(0, 0, 0, 0.45);
    border: 1px solid rgba(0, 229, 255, 0.20);
    border-radius: 6px;
    color: #ffffff;
    padding: 6px 10px;
    font: 400 10px 'Inter';
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid rgba(0, 229, 255, 0.60);
    background: rgba(0, 229, 255, 0.04);
}
```

### 5.3. Estilo para Tablas o Listas de Resultados (`QTableWidget`, `QListWidget`)
```css
QTableWidget, QListWidget {
    background: rgba(0, 0, 0, 0.35);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    gridline-color: rgba(0, 229, 255, 0.10);
}

QHeaderView::section {
    background: rgba(0, 229, 255, 0.10);
    color: rgba(0, 229, 255, 0.90);
    font: 700 9px 'Inter';
    border: none;
    padding: 4px;
}
```

---

## 6. RESUMEN DE CHECKLIST DE DISEÑO

Al crear cualquier nueva vista para NOVA, verifica que cumpla los 6 puntos clave:
- [ ] **Fondo:** Transparente con container `rgba(4, 10, 24, 0.87-0.95)`.
- [ ] **Borde:** `1px solid rgba(0, 229, 255, 0.20-0.35)` con radio entre 8px y 16px.
- [ ] **Resplandor:** `QGraphicsDropShadowEffect` con tinte Cyan (`rgba(0, 229, 255, 50)`).
- [ ] **Títulos:** Inter Bold en mayúsculas sostenidas con `letter-spacing` (1px o 2px).
- [ ] **Datos Técnicos:** JetBrains Mono 9px para valores, timestamps o código.
- [ ] **Botones:** Fondos semitransparentes de 28px o 52px de alto con hover reactivo cyan.
