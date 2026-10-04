# HTML Pages & Websites — Accessibility

For standalone HTML/CSS/JS pages, static sites, and single-page apps (SPAs). The
full `wcag-checklist.md` applies criterion-by-criterion; this file covers the
**page- and site-level** concerns that the checklist treats per-criterion but
that matter most when you own a whole document.

## Document skeleton (1.3.1, 3.1.1, 2.4.2, 4.1.1)
- Valid `<!DOCTYPE html>`, `<html lang="en">` (correct language code; set
  `dir="rtl"` where needed).
- `<head>`: a unique, descriptive `<title>` per page (2.4.2);
  `<meta charset="utf-8">`; `<meta name="viewport" content="width=device-width,
  initial-scale=1">` **without** `maximum-scale`/`user-scalable=no` (blocking zoom
  fails 1.4.4).
- No duplicate `id` attributes; properly nested/closed elements.

## Landmarks & structure (1.3.1, 2.4.1)
- One `<main>`, plus `<header>`, `<nav>`, `<aside>`, `<footer>` as appropriate.
  Give multiple same-type landmarks distinct names (`<nav aria-label="Primary">`,
  `<nav aria-label="Footer">`).
- Exactly one `<h1>` describing the page; headings nest in order (no skipped
  levels). Don't fake headings with styled text.
- A **skip-to-main-content** link as the first focusable element (2.4.1):
  ```html
  <a class="skip-link" href="#main">Skip to main content</a>
  ...
  <main id="main" tabindex="-1">…</main>
  ```
  Keep `.skip-link` visually hidden until focused (don't `display:none` it — that
  removes it from the tab order).

## Navigation & links (2.4.4, 2.4.5, 3.2.3)
- Descriptive link text; avoid bare "click here"/"read more" (add visually
  hidden context or `aria-label`).
- Indicate the current page in nav (`aria-current="page"`).
- Provide more than one way to find pages (nav + search or sitemap) — 2.4.5.
- Repeated navigation appears in the same relative order across pages (3.2.3).
- Links that open new tabs/downloads should say so in text.

## Forms (1.3.1, 3.3.1–3.3.3, 4.1.2)
- Every control has a programmatic `<label for>` (or `aria-label`/
  `aria-labelledby`); placeholders are not labels. Group with `<fieldset>` +
  `<legend>`. Use correct `type` and `autocomplete` tokens (1.3.5).
- Errors: text near the field, `aria-invalid="true"`, message linked via
  `aria-describedby`; on submit, move focus to a summary or the first error.
- Required fields marked with text/icon (`aria-required`), not colour alone.

## Images, icons, media (1.1.1, 1.2.x)
- Informative `alt`; decorative `alt=""`; functional (icon buttons) describe the
  action. Inline SVG: `role="img"` + `<title>`, or `aria-hidden="true"` if
  decorative. Video/audio: captions + transcript; never auto-play audio.

## Single-page apps / dynamic content (4.1.3, 2.4.3, 3.2.1)
- On client-side route change, update `document.title` and **move focus** to the
  new view's `<h1>` (or a focusable container) so screen-reader and keyboard
  users aren't stranded.
- Announce async updates, validation, and loading via `aria-live`
  (`role="status"` polite, `role="alert"` assertive) / live regions.
- Custom widgets (menus, tabs, dialogs, comboboxes, accordions): follow the
  **ARIA Authoring Practices Guide** patterns — correct role, keyboard
  interaction (arrows/Home/End/Esc), and synced state
  (`aria-expanded`/`-selected`/`-checked`). Prefer native elements first.
- Modals: trap focus while open, restore focus to the trigger on close, Esc to
  dismiss, `aria-modal="true"` + a label.

## CSS & layout (1.4.4, 1.4.10, 1.4.12, 1.3.2)
- Use relative units (rem/em/%/`ch`); avoid fixed heights that clip scaled text.
- Responsive layout reflows to 320 CSS px / 400% zoom with no 2-D scrolling
  (except data tables, maps, etc.). Don't reorder content with CSS (flex/grid
  `order`, absolute positioning) in a way that breaks DOM reading/tab order.
- Survive user text-spacing overrides (1.4.12) — no `!important` on line-height
  or letter-spacing, no fixed-height text boxes.
- Respect `@media (prefers-reduced-motion: reduce)` for animation/transitions.
- Theme/contrast concerns (dark mode, high contrast, design tokens): see
  `references/theming.md`.

## Focus (2.4.7)
- Always keep a visible focus indicator with ≥3:1 contrast. Prefer
  `:focus-visible`; never `outline:none` without a clearly visible replacement.

## Verify
- axe DevTools / WAVE / Lighthouse / Accessibility Insights, plus an HTML
  validator for parsing/duplicate-id issues.
- Keyboard-only walkthrough (skip link, nav, a form, any widget); screen-reader
  pass (NVDA/VoiceOver) on a key journey; 400% zoom / 200% text; contrast and
  greyscale (colour-only) checks; reduced-motion and (see theming) dark/forced
  colours.
