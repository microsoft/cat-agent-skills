# Modern Themes & Theming — Accessibility

Two things hide under "themes", and both can quietly break a component that
passed in its default colours. Conformance is **not inherited** from the default
theme — every theme and every variant must independently meet WCAG (1.4.1,
1.4.3, 1.4.6 AAA, 1.4.11, 2.4.7, 1.4.12).

1. **Power Apps modern themes** — the Fluent 2-based theming feature for
   model-driven apps (and modern controls), configured via a `CustomTheme` XML
   web resource. Covered first below.
2. **General web theming** — dark mode, OS high contrast / forced-colors, and
   design-token systems. Covered second.

---

## Part 1 — Power Apps modern themes (model-driven)

Modern themes apply when the model-driven app uses the **New look** (Fluent 2).
Classic theming is **not honoured** under the New look. A maker supplies a
`CustomTheme` XML web resource that reseeds the palette and/or overrides the app
header. Reference:
https://learn.microsoft.com/en-us/power-apps/maker/model-driven-apps/modern-theme-overrides

### The core accessibility risk
The theming system *can* generate an accessible palette, but several options
**bypass that protection** and put contrast entirely on you:

- **`LockPrimary="false"` (default)** — the palette is optimised for
  accessibility from your `basePaletteColor` seed. Preferred for conformance.
  The seed colour itself may not appear in the palette; that's the trade-off for
  accessible slots.
- **`LockPrimary="true"`** — forces your seed into the primary slot and generates
  the rest by lightening/darkening. Microsoft warns this **may not meet contrast
  ratio requirements**. If you use it, you must validate every slot pairing
  yourself (and `vibrancy`/`hueTorsion` only apply in this mode, shifting the
  lighter colours — re-check after tuning).
- **Manual slot overrides** (`darker70`…`primary`…`lighter80`) — setting slots by
  hand overrides the generator completely. Any pair used as foreground/background
  (e.g. primary button text on `primary`) must hit **4.5:1** text / **3:1**
  large-text and UI (1.4.3, 1.4.11). Check against the Fluent control usage of
  each slot.

### App header overrides (`AppHeaderColors`)
The header has eight colour attributes across rest + hover + pressed + selected
states. If you set `Background`, the system only auto-calculates the others when
you omit them — once you start specifying them, you own the contrast. Per
Microsoft's own guidance, verify **≥ 4.5:1 between foreground and background for
the rest state and every button interaction state** (hover, pressed, selected).
Don't let a "selected" or "hover" state drop below 4.5:1 just because the rest
state passes.

### Fonts
The `Font` attribute renders only if the browser/OS has it. Choose a legible
font and ensure a sensible fallback in the font stack; decorative display fonts
(the docs' `'GreatVibes', cursive` example) can harm readability — avoid them for
body/UI text (supports 1.4.8 AAA and general readability).

### What modern themes do NOT restyle (still verify these separately)
The theme doesn't cover everything: **Timeline control, lookup dropdowns, legacy
grids, audit history, and business process flow** retain their own styling. Don't
assume a passing theme makes these compliant — check them in context.

### Workflow for an accessible modern theme
1. Prefer `LockPrimary="false"` and seed from your brand colour.
2. Preview the generated 16-slot palette in the **Fluent theme designer**
   (https://react.fluentui.dev/?path=/docs/theme-theme-designer--docs) before
   shipping.
3. If you lock primary or override slots/header, run a contrast check on every
   foreground/background pair and every header interaction state (4.5:1 / 3:1).
4. Confirm colour is never the only signal (selection, active tab, hover) — 1.4.1
   — since the theme changes those indicators.
5. Publish, then verify in the running app across the unstyled areas listed above.

---

## Part 2 — General web theming (dark mode, high contrast, tokens)

Applies to HTML/CSS/Power Pages/PCF/canvas wherever you control colours.

### Test every theme variant
Run contrast, focus-visibility, and colour-only checks **separately** for each
mode: light, dark, brand sub-themes, and OS high-contrast / forced-colors.

### Contrast holds in all modes (1.4.3, 1.4.11)
- Text ≥ 4.5:1 (large ≥ 3:1) against its actual background in that theme;
  re-check dark mode, where mid-greys often fall below 4.5:1.
- UI borders, input outlines, control states, and **focus indicators** ≥ 3:1 in
  every theme — a focus ring visible on white can vanish on a dark surface, so
  define it per theme.

### Design tokens
- Use **semantic** tokens (`--color-text`, `--color-bg`, `--color-border`,
  `--color-focus`, `--color-error`) and validate each text token against its
  paired background token; redefining the set per theme keeps contrast correct.
- Never convey state by a colour token alone — error/success/warning also need
  icon or text (1.4.1).
- Overriding a library's tokens (Fluent, Material, Bootstrap vars, Tailwind
  theme) can break its built-in contrast — re-verify the customised values.

### prefers-color-scheme
```css
:root { --color-bg:#fff; --color-text:#1a1a1a; --color-focus:#0b5fff; }
@media (prefers-color-scheme: dark) {
  :root { --color-bg:#121212; --color-text:#e6e6e6; --color-focus:#7aa2ff; }
}
```
Honour the OS preference; if you add a manual toggle, persist it and meet
contrast in whichever mode is active. Avoid harsh pure `#000`/`#fff` and avoid
low-contrast "soft" dark palettes that fail 4.5:1.

### Windows High Contrast / forced-colors (1.4.1, 1.4.11, 1.4.3)
Test in Windows High Contrast and `@media (forced-colors: active)`:
- Don't rely on `background-color` alone for meaning — it may be replaced. Add
  borders, text, underlines, or icons.
- Use system colour keywords (`Canvas`, `CanvasText`, `LinkText`, `ButtonText`,
  `Highlight`) and `forced-color-adjust` deliberately.
- Keep focus indicators via `outline` (preserved in forced-colors) rather than
  box-shadow only.
- `currentColor` SVG/icon fonts stay visible; background-image-only icons can
  disappear — provide a text fallback.

### Text spacing & zoom under themes (1.4.4, 1.4.10, 1.4.12)
Theme-set spacing must still allow user overrides without clipping (no
`!important` on line-height/letter-spacing, no fixed-height text boxes); use
relative units so 200% resize and 320px reflow still work.

### Platform notes
- **PCF / canvas / model-driven**: read theme from the host
  (`context.fluentDesignLanguage`, `isDarkTheme`, OS high-contrast) instead of
  hard-coding colours. See the platform reference files; for model-driven also
  see Part 1 above.
- **Power Pages / web**: validate the published theme's CSS variables, not the
  mockup.

---

## Verify (any theme)
- Contrast checker on text, UI borders, and focus rings — once per mode/variant
  (and per header interaction state for modern themes).
- Toggle OS dark mode and Windows High Contrast; confirm nothing depends on a
  replaced colour and all focus/state cues remain.
- Greyscale (colour-only) check in each theme.
- 200% text / 400% zoom with the theme applied.
- For Power Apps modern themes: preview in the Fluent theme designer first, then
  validate in the running app including Timeline, lookups, legacy grids, and BPF.
