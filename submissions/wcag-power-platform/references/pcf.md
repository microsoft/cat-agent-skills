# PCF (PowerApps Component Framework) — Accessibility

PCF controls are custom code (TypeScript/React or standard control) embedded in
model-driven and canvas apps. **You own the rendered DOM**, so you own WCAG
conformance — the host app cannot fix an inaccessible control for you. Apply the
full `wcag-checklist.md`, plus these PCF specifics.

## Build on accessible primitives
- Strongly prefer **Fluent UI (v9 `@fluentui/react-components`)** — its
  components ship with correct roles, keyboard handling, and focus management.
  This is the single biggest win. If hand-rolling, use **native HTML elements**
  (`<button>`, `<input>`, `<select>`, `<a href>`) before reaching for `<div>`
  + ARIA.
- Match the host theme so contrast holds in light, dark, and high-contrast
  modes — read theme tokens from `context.fluentDesignLanguage` /
  `context.theme` rather than hard-coding colours.

## Keyboard & focus (2.1.1, 2.1.2, 2.4.3, 2.4.7)
- Every interactive part is reachable and operable by keyboard. Custom widgets:
  `tabindex="0"`, handle Enter/Space (and Arrow keys for composite widgets like
  grids, listboxes, tab sets per the ARIA Authoring Practices).
- Implement a **logical focus order** and a visible focus indicator (≥3:1).
  Don't strip outlines.
- Manage focus on dynamic changes (e.g. move focus into a dialog you open, return
  it on close). No keyboard traps.

## Name, role, value (4.1.2) and labels (1.3.1, 3.3.2)
- Expose accessible names for all controls (`aria-label` / `aria-labelledby` /
  associated `<label>`). For bound inputs, surface the field label.
- Keep ARIA **state** in sync with the React state: `aria-checked`,
  `aria-expanded`, `aria-selected`, `aria-disabled`, `aria-invalid`.

## Images, icons, charts (1.1.1, 1.4.11)
- Icon-only buttons need an accessible name describing the action. Decorative
  SVGs: `aria-hidden="true"`. Data viz: provide a text summary or accessible data
  table; ensure series are distinguishable beyond colour (1.4.1) and meet 3:1
  non-text contrast.

## Dynamic updates (4.1.3)
- Announce async results, validation, and value changes with an `aria-live`
  region (`role="status"` for polite, `role="alert"` for errors). PCF re-renders
  don't automatically notify screen readers.

## Manifest & lifecycle
- Set the manifest property-set/labels meaningfully; respect
  `context.accessibility?.assignedTabIndex` and the host's high-contrast signal
  (`context.fluentDesignLanguage?.isDarkTheme`, OS high-contrast).
- Honour `context.mode.isControlDisabled` — render a proper disabled state
  (still perceivable, removed from tab order).
- Respect `prefers-reduced-motion` for any animation (2.2.2 / 2.3.3).

## Reflow & resize (1.4.4, 1.4.10, 1.4.12)
- Use relative units and flexible layout so the control reflows in narrow
  columns and survives 200% zoom and user text-spacing overrides. Avoid
  fixed pixel heights that clip text.

## Verify
- **App Checker** in the maker portal + **axe DevTools** / Accessibility Insights
  against the rendered control in a harness or test page.
- Keyboard-only pass and NVDA/VoiceOver spot-check inside an actual model-driven
  form and a canvas app (host context differs).
- Test in Windows High Contrast and dark theme.
