---
name: Zenith
colors:
  surface: '#fcf8ff'
  surface-dim: '#dcd8e4'
  surface-bright: '#fcf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f2fe'
  surface-container: '#f0ecf8'
  surface-container-high: '#ebe6f2'
  surface-container-highest: '#e5e0ed'
  on-surface: '#1c1b23'
  on-surface-variant: '#474554'
  inverse-surface: '#312f38'
  inverse-on-surface: '#f3effb'
  outline: '#787586'
  outline-variant: '#c8c4d7'
  surface-tint: '#5847d2'
  primary: '#5341cd'
  on-primary: '#ffffff'
  primary-container: '#6c5ce7'
  on-primary-container: '#faf6ff'
  inverse-primary: '#c6bfff'
  secondary: '#5c4fb5'
  on-secondary: '#ffffff'
  secondary-container: '#9f93fe'
  on-secondary-container: '#34248c'
  tertiary: '#884800'
  on-tertiary: '#ffffff'
  tertiary-container: '#ac5d00'
  on-tertiary-container: '#fff5f1'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e4dfff'
  primary-fixed-dim: '#c6bfff'
  on-primary-fixed: '#160066'
  on-primary-fixed-variant: '#4029ba'
  secondary-fixed: '#e4dfff'
  secondary-fixed-dim: '#c7bfff'
  on-secondary-fixed: '#180065'
  on-secondary-fixed-variant: '#44369c'
  tertiary-fixed: '#ffdcc3'
  tertiary-fixed-dim: '#ffb77d'
  on-tertiary-fixed: '#2f1500'
  on-tertiary-fixed-variant: '#6e3900'
  background: '#fcf8ff'
  on-background: '#1c1b23'
  surface-variant: '#e5e0ed'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '800'
    lineHeight: 56px
    letterSpacing: 0.1em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: 0.05em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: 0.05em
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-mono:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 8px
  container-padding: 24px
  gutter: 16px
  card-gap: 20px
  section-margin: 48px
---

## Brand & Style

This design system embodies a "Minimalist Samurai" aesthetic—a fusion of traditional discipline and futuristic precision. It is designed for premium SaaS platforms that prioritize focus, high performance, and mental clarity. The interface utilizes high-contrast typography and expansive whitespace to create a sense of "digital breathing room," mirroring the meditative state of a modern warrior.

The visual style is characterized by:
- **Minimalist Modernism:** Large, airy layouts with a focus on essential data.
- **Futuristic Accents:** Subtle technical nods via monospaced fonts and ethereal lavender gradients.
- **Ethereal Depth:** Soft, glowing surfaces that appear to float above a clean, cool-toned background, avoiding harsh borders in favor of light-based separation.
- **Discerning Imagery:** High-fidelity 3D renders of characters and artifacts in a cohesive palette of white, lavender, and slate blue.

## Colors

The palette is centered around a "Lavender Twilight" theme. The primary lavender (`#6C5CE7`) acts as the focal point for action and progress, while the background maintains a cool, surgical cleanliness.

- **Primary & Secondary:** Used for active states, progress indicators, and primary call-to-actions. Secondary shades are often used in linear gradients (Primary to Secondary) to suggest movement and energy.
- **Neutrals:** The background uses a subtle grey-white (`#F5F5F8`) to allow pure white cards (`#FFFFFF`) to pop through elevation rather than borders.
- **Typography:** Deep charcoal is reserved for headers to maintain a commanding presence, while medium gray is used for body text to reduce visual fatigue and create hierarchy.

## Typography

The typography strategy relies on the contrast between high-impact, all-caps headlines and functional, monospaced metadata.

- **Headlines:** Set in **Inter** with bold weights and wide tracking. This creates a rhythmic, architectural feel reminiscent of Japanese minimalist posters.
- **Body:** **Inter** is used for its exceptional legibility at small scales, maintaining a clean and neutral tone.
- **Accents/Data:** **JetBrains Mono** is utilized for technical subtext, timestamps, and data points. This adds a "warrior-tech" layer to the system, suggesting precision and calculation.

## Layout & Spacing

This design system utilizes a **Fluid Grid** with generous internal safe areas. The layout philosophy is "Centric," where the most critical information occupies the core of the screen, surrounded by ample negative space.

- **Grid:** A 12-column system for desktop and a 4-column system for mobile.
- **Rhythm:** An 8px base unit drives all spacing. Consistent 24px margins are applied to all primary containers to maintain the "framed" look visible in the reference.
- **Reflow:** On mobile, side-by-side card components stack vertically, and horizontal scrolling is used exclusively for "Quick Action" chips or secondary navigation bars.

## Elevation & Depth

Hierarchy is established through **Tonal Layering** and soft, diffused shadows rather than lines.

- **Base Layer:** The background (`#F5F5F8`).
- **Surface Layer:** Pure white cards (`#FFFFFF`) featuring a `0px 10px 30px rgba(108, 92, 231, 0.08)` shadow. The tint of the primary lavender in the shadow creates a "glow" effect rather than a traditional gray shadow.
- **Interactive States:** Upon hover or focus, the shadow expands and increases in opacity slightly (e.g., `rgba(108, 92, 231, 0.15)`) to simulate the element lifting toward the user.
- **Overlays:** Modals and menus use a high-blur backdrop filter (glassmorphism) to maintain the ethereal atmosphere.

## Shapes

The geometry is dominated by large radii and "pill" shapes, creating a soft but disciplined profile.

- **Cards:** Strictly defined with a **24px (rounded-xl)** corner radius.
- **Interactive Elements:** Buttons and tags utilize a **Pill (fully rounded)** style to differentiate them from the structural containers of the UI.
- **Icons:** Encapsulated in circular backgrounds or soft-edged squares to maintain consistency with the component shapes.

## Components

### Buttons
- **Primary:** Full-width or auto-width capsule (pill) buttons. Use a gradient background from Primary to Secondary. Typography is white, bold Inter, all-caps.
- **Secondary/Ghost:** Transparent background with a 1px border using the accent pastel color.

### Cards
- **Structure:** 24px rounded corners, pure white background, soft lavender-tinted shadow. No borders.
- **Content:** Headlines inside cards should be followed by JetBrains Mono labels for a technical touch.

### Input Fields & Controls
- **Inputs:** Soft-gray background (`#F5F5F8`) with 12px rounded corners. On focus, the background remains, but a 1px primary lavender border appears.
- **Checkboxes/Radios:** Circular (pill-style) even for checkboxes to maintain the "Zenith" geometry.

### Navigation
- **Bottom Bar (Mobile):** A floating white dock with a central "Action" button that is larger and features a vibrant gradient glow.
- **Dashboard Sidebar (Desktop):** Minimalist icons with text labels appearing only on hover or in expanded states.

### Progress Indicators
- **Circular Gauges:** Use thick strokes with rounded caps. The active path is a lavender gradient; the inactive path is a light lilac or gray.