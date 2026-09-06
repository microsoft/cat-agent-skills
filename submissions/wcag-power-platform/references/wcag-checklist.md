# WCAG 2.1 Success Criteria — Checklist & Fixes

Every WCAG 2.1 success criterion, grouped by principle. Level in brackets.
For each: the testable check and the most common fix. Target **AA** by default;
AAA items are marked optional.

## Contents
- [1. Perceivable](#1-perceivable)
- [2. Operable](#2-operable)
- [3. Understandable](#3-understandable)
- [4. Robust](#4-robust)
- [Reference values](#reference-values)

---

## 1. Perceivable

### 1.1 Text Alternatives
- **1.1.1 Non-text Content (A)** — Every image, icon, chart, and media control
  has a text alternative serving the same purpose. Informative images: meaningful
  `alt`. Decorative: `alt=""` or `role="presentation"` / CSS background. Functional
  images (icon buttons): the alt/label describes the *action*, not the picture.
  Charts/infographics: provide a text description or data table. Inputs and
  controls have an accessible name (see 4.1.2). CAPTCHAs: provide a non-visual
  alternative.

### 1.2 Time-based Media
- **1.2.1 Audio/Video-only Prerecorded (A)** — Transcript for audio-only; transcript
  or audio track for video-only.
- **1.2.2 Captions Prerecorded (A)** — Synchronised captions for all prerecorded
  audio in video.
- **1.2.3 Audio Description or Media Alternative Prerecorded (A)** — Audio
  description or full transcript for prerecorded video.
- **1.2.4 Captions Live (AA)** — Live captions for live audio.
- **1.2.5 Audio Description Prerecorded (AA)** — Audio description for all
  prerecorded video.
- **1.2.6–1.2.9 (AAA, optional)** — Sign language, extended audio description,
  media alternative, live audio-only alternative.

### 1.3 Adaptable
- **1.3.1 Info and Relationships (A)** — Structure conveyed visually is also in
  the markup: real headings (`<h1>`–`<h6>` in order, no level skips), lists as
  `<ul>/<ol>/<dl>`, data tables with `<th scope="col|row">` and `<caption>`,
  form fields associated with `<label for>`, related controls in `<fieldset>` +
  `<legend>`, landmark regions (`<header><nav><main><aside><footer>` or ARIA
  landmarks). Never fake a heading with bold text.
- **1.3.2 Meaningful Sequence (A)** — DOM/reading order matches visual order;
  meaning survives CSS being off. Don't reorder with CSS in a way that breaks
  reading/tab order.
- **1.3.3 Sensory Characteristics (A)** — Instructions don't rely on shape, size,
  position, or sound alone ("click the round button on the right" → add a label).
- **1.3.4 Orientation (AA)** — Don't lock to portrait or landscape unless
  essential. Avoid CSS that traps a single orientation.
- **1.3.5 Identify Input Purpose (AA)** — Inputs collecting user info use the
  correct HTML `autocomplete` token (`name`, `email`, `tel`, `street-address`,
  etc.) so AT/browsers can autofill and adapt.
- **1.3.6 Identify Purpose (AAA, optional)** — Purpose of UI components, icons,
  and regions is programmatically determinable (ARIA landmarks + consistent
  patterns).

### 1.4 Distinguishable
- **1.4.1 Use of Color (A)** — Colour is never the sole means of conveying info
  (required-field asterisk + colour, error icon + text, link underline or other
  cue besides colour).
- **1.4.2 Audio Control (A)** — Audio that auto-plays > 3s has a pause/stop or
  independent volume control. Best: don't auto-play.
- **1.4.3 Contrast Minimum (AA)** — Text contrast ≥ **4.5:1**; large text (≥ 24px,
  or ≥ 18.66px/14pt bold) ≥ **3:1**. Exemptions: disabled controls, pure
  decoration, logos.
- **1.4.4 Resize Text (AA)** — Text scales to **200%** without loss of content or
  function. Use relative units (rem/em/%), avoid fixed-height containers that
  clip text.
- **1.4.5 Images of Text (AA)** — Use real text, not images of text (except logos
  / where presentation is essential).
- **1.4.6–1.4.9 (AAA, optional)** — Enhanced contrast 7:1 (4.5:1 large), low
  background audio, visual presentation controls, images of text no-exception.
- **1.4.10 Reflow (AA)** — No 2-D scrolling at **320 CSS px** width (≡ 400% zoom
  on 1280px). Content reflows to a single column; only data tables, maps, and
  similarly essential content may scroll in two dimensions. Use responsive
  layout, avoid fixed widths.
- **1.4.11 Non-text Contrast (AA)** — UI component boundaries/states (input
  borders, focus rings, toggle states, button edges) and meaningful graphical
  objects (chart lines, icon glyphs) ≥ **3:1** against adjacent colours.
- **1.4.12 Text Spacing (AA)** — No loss when the user overrides: line-height
  1.5×, paragraph spacing 2×, letter-spacing 0.12×, word-spacing 0.16× font size.
  Avoid fixed-height text containers and `!important` overrides on spacing.
- **1.4.13 Content on Hover or Focus (AA)** — Tooltips/popovers on hover/focus are
  **dismissible** (without moving pointer/focus, e.g. Esc), **hoverable** (can
  move pointer onto them), and **persistent** (stay until dismissed/invalid).

---

## 2. Operable

### 2.1 Keyboard Accessible
- **2.1.1 Keyboard (A)** — All functionality operable by keyboard. Use native
  interactive elements (`<button>`, `<a href>`, `<input>`); custom widgets need
  `tabindex="0"` + key handlers. Never use `tabindex` > 0.
- **2.1.2 No Keyboard Trap (A)** — Focus can always move away by standard means.
  Modals: trap focus *within* while open but allow Esc/close to exit.
- **2.1.3 Keyboard No Exception (AAA, optional).**
- **2.1.4 Character Key Shortcuts (A)** — Single-character shortcuts can be turned
  off, remapped, or are active only on focus.

### 2.2 Enough Time
- **2.2.1 Timing Adjustable (A)** — Time limits can be turned off, adjusted (≥10×),
  or extended (warn + ≥20s + ≥10 extensions). Applies to session timeouts.
- **2.2.2 Pause, Stop, Hide (A)** — Moving/blinking/scrolling/auto-updating content
  lasting > 5s and shown with other content has a pause/stop/hide control. Carousels
  need a pause button. Respect `prefers-reduced-motion`.
- **2.2.3–2.2.6 (AAA/AAA/AAA/AAA, optional)** — No timing, interruptions control,
  re-authenticating without data loss, timeout warnings.

### 2.3 Seizures and Physical Reactions
- **2.3.1 Three Flashes or Below Threshold (A)** — Nothing flashes > 3 times/second
  above the flash threshold.
- **2.3.2 Three Flashes (AAA, optional).**
- **2.3.3 Animation from Interactions (AAA, optional)** — Honour
  `prefers-reduced-motion` to disable non-essential motion (good practice at AA too).

### 2.4 Navigable
- **2.4.1 Bypass Blocks (A)** — A "skip to main content" link (or landmarks/headings)
  lets keyboard users skip repeated nav.
- **2.4.2 Page Titled (A)** — Each page/screen has a unique, descriptive `<title>`.
- **2.4.3 Focus Order (A)** — Tab order follows a logical, meaning-preserving
  sequence (usually = DOM order).
- **2.4.4 Link Purpose In Context (A)** — Link text (with its context) states where
  it goes. Avoid bare "click here" / "read more"; use `aria-label` or visually
  hidden text if needed.
- **2.4.5 Multiple Ways (AA)** — More than one way to find a page (nav + search, or
  sitemap), except steps in a process.
- **2.4.6 Headings and Labels (AA)** — Headings and labels are descriptive of topic
  or purpose.
- **2.4.7 Focus Visible (AA)** — Keyboard focus indicator is always visible. Never
  `outline: none` without a clearly visible replacement (≥ 3:1 contrast).
- **2.4.8–2.4.10 (AAA, optional)** — Location indicator, link purpose from text
  alone, section headings.
- *(WCAG 2.2: **2.4.11/2.4.12 Focus Not Obscured (AA/AAA)** — sticky headers/footers
  must not hide the focused element.)*

### 2.5 Input Modalities
- **2.5.1 Pointer Gestures (A)** — Multipoint/path gestures (pinch, swipe) have a
  single-pointer alternative (buttons), unless essential.
- **2.5.2 Pointer Cancellation (A)** — Actions fire on up-event, not down-event; or
  are abortable/undoable. Don't trigger on mousedown/touchstart.
- **2.5.3 Label in Name (A)** — A control's accessible name **contains** its visible
  text label (so voice-control "click Submit" works). Don't let `aria-label`
  contradict the visible text.
- **2.5.4 Motion Actuation (A)** — Motion-operated functions (shake, tilt) also have
  a UI control and can be disabled.
- **2.5.5 Target Size (AAA, optional)** — Targets ≥ 44×44px. *(WCAG 2.2 adds
  **2.5.8 Target Size Minimum at AA: 24×24px** — apply this for current best
  practice.)*
- **2.5.6 Concurrent Input Mechanisms (AAA, optional).**

---

## 3. Understandable

### 3.1 Readable
- **3.1.1 Language of Page (A)** — `<html lang="en">` (correct code) set.
- **3.1.2 Language of Parts (AA)** — Inline foreign-language passages marked with
  `lang`.
- **3.1.3–3.1.6 (AAA, optional)** — Unusual words, abbreviations, reading level,
  pronunciation.

### 3.2 Predictable
- **3.2.1 On Focus (A)** — Focusing an element causes no change of context (no
  auto-submit, no new window, no major content change).
- **3.2.2 On Input (A)** — Changing a control's value causes no surprise context
  change unless the user was warned first (e.g. don't auto-submit a form on select
  change without notice).
- **3.2.3 Consistent Navigation (AA)** — Repeated navigation is in the same relative
  order across pages.
- **3.2.4 Consistent Identification (AA)** — Same-function components are labelled
  consistently across the app (same icon = same name everywhere).
- **3.2.5 Change on Request (AAA, optional).**
- *(WCAG 2.2: **3.2.6 Consistent Help (A)**.)*

### 3.3 Input Assistance
- **3.3.1 Error Identification (A)** — Errors are identified in **text**, describing
  what's wrong, and the erroring field is indicated. Link the message with
  `aria-describedby`; set `aria-invalid="true"`.
- **3.3.2 Labels or Instructions (A)** — Every input has a visible label and any
  needed format instructions. Placeholder text is **not** a label.
- **3.3.3 Error Suggestion (AA)** — When the fix is known, suggest it ("Date must be
  DD/MM/YYYY").
- **3.3.4 Error Prevention Legal/Financial/Data (AA)** — For legal/financial/data
  submissions: reversible, checked, or confirmable before final commit.
- **3.3.5–3.3.6 (AAA, optional)** — Context help, error prevention for all.
- *(WCAG 2.2: **3.3.7 Redundant Entry (A)**, **3.3.8 Accessible Authentication (AA)**
  — don't require cognitive tests / re-typing previously entered info.)*

---

## 4. Robust

### 4.1 Compatible
- **4.1.1 Parsing (A)** — *(Obsolete/removed in WCAG 2.2; in 2.1 ensure valid
  markup: no duplicate IDs, properly nested/closed elements.)*
- **4.1.2 Name, Role, Value (A)** — Every UI component exposes a correct
  **name** (label), **role** (button/link/checkbox/…), and **value/state**
  (checked, expanded, selected, disabled) to assistive tech. Prefer native HTML;
  if using ARIA, use the right role and keep state attributes (`aria-expanded`,
  `aria-checked`, `aria-selected`, `aria-pressed`) in sync with the UI.
- **4.1.3 Status Messages (AA)** — Status messages that don't move focus are
  announced via `role="status"` / `role="alert"` / `aria-live` regions (form
  success, search-result counts, async loading, validation summaries).

---

## Reference values

- **Text contrast**: 4.5:1 normal, 3:1 large (≥24px or ≥18.66px bold).
- **Non-text contrast** (UI/graphics): 3:1.
- **Reflow**: 320 CSS px wide / 256 CSS px tall; ≡ 400% zoom at 1280px.
- **Resize text**: up to 200% without loss.
- **Target size**: 44×44px (AAA 2.1); 24×24px (AA in 2.2).
- **Flash**: ≤ 3 flashes per second.
- **Conformance levels**: A (floor) → **AA (legal/regulatory target)** → AAA
  (aspirational; not expected for whole sites).

## ARIA golden rule

Prefer native HTML elements with built-in semantics over ARIA. Only add ARIA
when no native element fits, and never use ARIA that contradicts the native role.
A wrong ARIA role is worse than none.
