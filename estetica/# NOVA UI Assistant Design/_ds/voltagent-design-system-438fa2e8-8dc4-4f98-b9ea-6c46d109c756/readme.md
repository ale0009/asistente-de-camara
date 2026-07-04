# VoltAgent Design System

A developer-first design system for **VoltAgent** — an open-source AI agent engineering framework built for developers who want to compose, orchestrate, and ship production-grade AI agents.

**Source:** [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md/blob/main/design-md/voltagent/DESIGN.md) — the canonical DESIGN.md for VoltAgent's brand. Explore this repo further for additional context and cross-brand comparisons.

---

## Product Context

VoltAgent is a TypeScript-first AI agent framework. Its public surface is the **marketing website** (voltagent.dev) — a dark, developer-centric single-page scroll that reads like polished documentation that decided to also sell something. The brand speaks to engineers: no gradients, no illustrations, no photography — instead, inline code snippets, terminal-style mockups, and a precise grid of feature cards.

The sole product is the framework itself (open-source). The design system reflects the marketing site and, by extension, how in-product UI (agent consoles, dashboards) should feel.

---

## CONTENT FUNDAMENTALS

### Tone & Voice
- **Developer-first, respect assumed.** Copy speaks to an engineer who already knows what agents are. No hand-holding, no oversimplification.
- **Sentence-case everywhere.** Headlines, CTAs, card titles, nav links — all sentence-case. The only uppercase text is the signature eyebrow labels (`EVERYTHING YOU NEED`, `WHY VOLTAGENT`).
- **Terse and precise.** Headlines are declarative statements, not marketing slogans: *"AI Agent Engineering Platform"*, not *"Build the Future of AI!"*
- **First-person plural ("we") is rare.** Copy is product-centric, not company-centric. "VoltAgent lets you…" not "We built…"
- **No emoji.** None in any surface. Unicode characters used rarely (→ arrows, lightning ⚡ glyph in the logo mark only).
- **Inline code is a content element.** `npx create-voltagent-app`, `@voltagent/core` — technical strings appear inline in body copy and are styled as code chips, never paraphrased.
- **Metric copy is terse:** "12+ integrations", "100% TypeScript", "MIT licensed" — no filler words around numbers.

### Specific Examples
- Hero headline: *"AI Agent Engineering Platform"*
- Eyebrow: *"EVERYTHING YOU NEED"*
- Body: *"Build, orchestrate, and deploy production-ready AI agents with a framework designed by developers, for developers."*
- CTA primary: *"Get started"*
- CTA secondary: *"View on GitHub"*

---

## VISUAL FOUNDATIONS

### Color
Single-accent, dark-canvas system. No light mode exists.

| Role | Token | Hex |
|---|---|---|
| Page background | `--color-canvas` | `#101010` |
| Elevated surface | `--color-canvas-soft` | `#1a1a1a` |
| Brand accent / CTA | `--color-primary` | `#00d992` |
| Accent soft | `--color-primary-soft` | `#2fd6a1` |
| Accent deep (links) | `--color-primary-deep` | `#10b981` |
| On-accent text | `--color-on-primary` | `#101010` |
| Default text | `--color-ink` | `#f2f2f2` |
| Hero headline | `--color-ink-strong` | `#ffffff` |
| Body / supporting | `--color-body` | `#bdbdbd` |
| Captions / muted | `--color-mute` | `#8b949e` |
| Card / button border | `--color-hairline` | `#3d3a39` |
| Dashed section divider | `--color-hairline-dashed` | `rgba(79,93,117,0.4)` |

The electric green `#00d992` is used **only** for: primary buttons, status indicators, the lightning logo glyph, active nav indicators, and the occasional green hairline divider band. Never as body text fill.

### Typography
Two typefaces. No exceptions.
- **Inter** (sans): display, body, buttons, nav, eyebrows. Weights 400/500/600/700.
- **JetBrains Mono** (mono, substituting SF Mono): code blocks, inline command chips, terminal mockups, numeric counters.

> ⚠️ **Font substitution:** The brand uses SF Mono (Apple system). This design system substitutes **JetBrains Mono** from Google Fonts as the nearest free equivalent. For production use, supply the original SF Mono files.

Display type sits at weight 400 — intentionally calm, not a bold marketing shout. Eyebrow labels use Inter at 600 weight with `2.52px` letter-spacing (not a mono face).

### Backgrounds & Surfaces
- Single dark surface (`#101010`) runs edge-to-edge with no light-mode counterpart.
- `#1a1a1a` marks inset areas: code blocks, form inputs, pricing card backgrounds.
- No gradients. No textures. No photography. No illustrations.
- A 1px dashed `rgba(79,93,117,0.4)` line occasionally divides section bands.
- A 2px solid `#00d992` green hairline marks featured/active card states and occasional section dividers.

### Cards
The brand's primary chrome: **hairline-bordered rectangles on near-black canvas**.
- Default: `border: 1px solid #3d3a39`, `border-radius: 8px`, `padding: 24px`, background `#101010`
- Emphasized: same but `border-width: 3px`
- Active/featured: `border: 2px solid #00d992`
- No drop shadows on cards. Ever.
- Hover state: subtle `box-shadow: 0 0 15px rgba(92,88,85,0.2)` outer glow.

### Buttons
- **Primary**: green fill (`#00d992`), near-black text, `border-radius: 6px`, `padding: 12px 16px`
- **Outline**: canvas bg, ink text, `1px solid #3d3a39` border — same radius/padding
- **Ghost green**: no border, green text (`#2fd6a1`)
- **Pill tag**: `border-radius: 9999px`, hairline border, small padding — inline category labels only
- No pill-shaped primary CTAs. `border-radius: 6px` is the CTA shape.

### Spacing
Base unit 4px. Scale: 2/4/8/12/16/20/24/32/40/48/64px.

### Animation
Minimal. No entrance animations, no decorative loops. Hover transitions use `transition: all 150ms ease` or similar — color and glow changes only. No bounce, no spring, no slide-in.

### Borders & Radius
- `6px` for buttons, inputs
- `8px` for cards, code blocks
- `9999px` for status pills and category tags only
- `0px` for full-bleed section bands

### Icons & Imagery
- No photography on the marketing surface
- Code mockups (dark card + SF Mono text) replace screenshots
- The lightning bolt `⚡` glyph is the only brand mark referenced in source — see ICONOGRAPHY section

### Hover / Press States
- Buttons: slight brightness increase or opacity change (no color shift on primary)
- Cards: `box-shadow: 0 0 15px rgba(92,88,85,0.2)` glow appears on hover
- Nav links: color shifts from `#bdbdbd` to `#f2f2f2`
- No scale transforms on hover/press

---

## ICONOGRAPHY

- **No icon font or sprite system** is present in the source DESIGN.md or repo.
- The brand's only signature mark is the **lightning bolt glyph** (`⚡` / SVG), used in the logo. No icon set is standardized.
- Inline indicators use small colored dots or the primary green for "live" status.
- If an icon system is needed for in-product UI, **Lucide Icons** (CDN: `https://unpkg.com/lucide@latest`) is the recommended companion — it matches the brand's stroke-weight and minimal style. Flag this as an intentional addition: the DESIGN.md does not specify an icon set.

**Intentional additions:**
- Lucide Icons suggested as companion icon set (brand source does not define one)

---

## COMPONENTS

| Component | Location |
|---|---|
| Button | `components/core/Button.jsx` |
| Card | `components/core/Card.jsx` |
| Badge | `components/core/Badge.jsx` |
| CodeBlock | `components/core/CodeBlock.jsx` |
| CodeChip | `components/core/CodeChip.jsx` |
| Input | `components/core/Input.jsx` |
| NavBar | `components/core/NavBar.jsx` |

Component card: `components/core/components.card.html`

---

## UI KITS

| Product | Location |
|---|---|
| VoltAgent Marketing Site | `ui_kits/marketing/index.html` |

---

## GUIDELINES

| Card | Location |
|---|---|
| Primary & accent colors | `guidelines/colors-primary.card.html` |
| Neutral colors | `guidelines/colors-neutral.card.html` |
| Semantic / text colors | `guidelines/colors-text.card.html` |
| Display type | `guidelines/type-display.card.html` |
| Body type | `guidelines/type-body.card.html` |
| Code / mono type | `guidelines/type-code.card.html` |
| Eyebrow labels | `guidelines/type-eyebrow.card.html` |
| Spacing scale | `guidelines/spacing.card.html` |
| Border radius | `guidelines/radii.card.html` |
| Elevation / borders | `guidelines/elevation.card.html` |
| Buttons | `guidelines/buttons.card.html` |
| Cards | `guidelines/cards.card.html` |

---

## ASSETS

| Asset | Location |
|---|---|
| *(No logo file in source)* | — |

> ⚠️ **No logo file was available** in the source repository. The brand name "VoltAgent" is rendered in plain Inter type wherever a mark is needed. Supply the real SVG logo to complete the system.

---

## File Index

```
styles.css              ← global CSS entry (import this one file)
tokens/
  colors.css
  typography.css
  spacing.css
  radii.css
  shadows.css
components/core/        ← reusable primitives
guidelines/             ← specimen cards (Design System tab)
ui_kits/marketing/      ← VoltAgent marketing site kit
assets/                 ← logos, icons, imagery
readme.md               ← this file
SKILL.md                ← agent skill definition
```
