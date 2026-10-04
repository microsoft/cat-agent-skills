---
name: wcag-power-platform
description: >-
  Ensure web apps, HTML pages, and Power Platform components meet WCAG 2.1
  accessibility guidelines. Use this skill WHENEVER building, reviewing, or
  refactoring any web UI or Power Platform artifact — standalone HTML/CSS/JS
  pages, websites and single-page apps, React/web artifacts, PCF (PowerApps
  Component Framework) controls, HTML/JS web resources, model-driven apps and
  forms, canvas apps, or
  Power Pages — even if the user does not say "accessibility". Trigger on
  requests to create pages or components, build forms, style UI, add
  buttons/inputs/grids/charts, theme an app, apply a Power Apps modern theme /
  CustomTheme, implement dark mode / high-contrast / design tokens, fix a
  control, write HTML/CSS/React, or audit a page against WCAG/ADA/Section
  508/EN 301 549. Also trigger on "make this accessible", "a11y", "screen
  reader", "keyboard navigation", "colour contrast", "dark mode", "theme",
  "ARIA", or "WCAG". Apply the checks proactively so output conforms to WCAG
  2.1 AA by default, across every theme variant.
---

# WCAG 2.1 for Web Apps & Power Platform

This skill makes anything you build or review conform to **WCAG 2.1 Level AA**
(the legal default for most public-sector and EU/UK accessibility law), while
flagging the AAA criteria worth reaching for. It covers generic web content,
full HTML pages/sites and SPAs, and modern theming (dark mode, high contrast,
design tokens), **and** the four Power Platform component types: PCF controls,
model-driven apps/forms, canvas apps, and Power Pages.

## Default target

Unless the user states otherwise, conform to **Level AA**. Level A is the floor
and AA is what regulations (ADA, Section 508, EN 301 549 / UK Public Sector
Bodies Accessibility Regulations) actually require. Mention AAA only as an
optional enhancement.

## How to use this skill

1. **Identify the component type** (web/PCF/model-driven/canvas/Power Pages).
   The platform changes *how* you satisfy a criterion — see the routing table
   below and read the matching reference file.
2. **Author or review against the four principles.** Read
   `references/wcag-checklist.md` — it lists every WCAG 2.1 success criterion
   grouped under Perceivable, Operable, Understandable, Robust, with the
   concrete, testable thing to check for each. This is the heart of the skill.
3. **Apply the platform-specific guidance** from the relevant reference file.
4. **Self-verify** using the verification section below before declaring done.

When *building* something new, bake the checks in as you write — don't bolt
them on afterwards. When *auditing*, report findings as a table: criterion,
level (A/AA/AAA), pass/fail, location, and the fix.

## Component routing

| If the work involves…                          | Read this reference                    |
|------------------------------------------------|----------------------------------------|
| Generic HTML/CSS/JS or React web artifacts     | `references/wcag-checklist.md`         |
| A full HTML page, website, or single-page app  | `references/html-pages.md`             |
| Theming: Power Apps modern themes, dark mode, high contrast, design tokens | `references/theming.md`           |
| PCF (PowerApps Component Framework) controls   | `references/pcf.md`                    |
| HTML/JS web resources (model-driven)           | `references/web-resources.md`          |
| Model-driven apps, forms, views, dashboards    | `references/model-driven.md`           |
| Canvas apps                                    | `references/canvas.md`                 |
| Power Pages (portals)                          | `references/power-pages.md`            |

Always read `references/wcag-checklist.md` — every other file assumes it and only
adds deltas. Read `references/html-pages.md` for any standalone page/site/SPA, and
`references/theming.md` whenever colour schemes, dark mode, high-contrast, or a
design-token/theme system is in play (these stack with the platform files — e.g.
a themed Power Pages site reads the checklist + power-pages + theming).

## The four principles (POUR) — quick orientation

- **Perceivable** — users can perceive the information: text alternatives,
  captions, colour not used alone, 4.5:1 text contrast / 3:1 large text & UI,
  reflow to 320px, resizable text, programmatic structure.
- **Operable** — users can operate it: full keyboard access, no keyboard traps,
  visible focus, logical focus order, enough time, no seizure-inducing flashing,
  target size, skip links, descriptive link text.
- **Understandable** — readable and predictable: page language set, labels and
  instructions on inputs, clear error identification + suggestions, consistent
  navigation, no surprise context changes on focus/input.
- **Robust** — works with assistive tech: valid markup, correct name/role/value
  for every control, status messages announced via live regions.

## The highest-leverage AA checks (apply to everything)

These catch the majority of real failures. Verify every one before finishing:

1. **Every interactive element is keyboard reachable and operable** (Tab/Shift+Tab,
   Enter/Space), with a **visible focus indicator** (2.4.7) and **no keyboard
   trap** (2.1.2).
2. **Every form control has a programmatic label** (`<label for>`, `aria-label`,
   or `aria-labelledby`) — not just a visual placeholder (1.3.1, 3.3.2, 4.1.2).
3. **Every meaningful image has alt text; decorative images have empty alt**
   (`alt=""`) or are hidden from AT (1.1.1).
4. **Text contrast ≥ 4.5:1** (≥ 3:1 for large text ≥ 18.66px bold / 24px), and
   **UI components & graphical objects ≥ 3:1** (1.4.3, 1.4.11).
5. **Colour is never the only way** information is conveyed (1.4.1) — pair it
   with text, icon, or pattern.
6. **Semantic structure**: real headings in order (h1→h2→h3, no skips), lists as
   lists, one `<main>`, landmark regions, tables with `<th scope>` (1.3.1).
7. **Page/screen has a descriptive title** and `lang` is set (2.4.2, 3.1.1).
8. **Dynamic updates are announced** to screen readers via `aria-live` /
   status roles (4.1.3).
9. **Content reflows** with no horizontal scroll at 320 CSS px / 400% zoom and
   text resizes to 200% without loss (1.4.10, 1.4.4).
10. **Errors are identified in text, near the field, with a suggested fix**, and
    the field is linked via `aria-describedby` (3.3.1, 3.3.3).

## Verification before "done"

Run through these — automated tools catch ~30–40%, the rest needs the manual
checks:

- **Automated**: axe-core / Accessibility Insights / Lighthouse / WAVE. For
  Power Platform, also the built-in **App Checker** (model-driven & canvas) and
  the **Accessibility checker** in the canvas studio. Treat these as a first
  pass, not proof of conformance.
- **Keyboard-only pass**: unplug the mouse. Tab through the whole UI. Can you
  reach and operate everything? Is focus always visible? Does order make sense?
  Can you always Tab back out (no trap)?
- **Screen reader spot-check**: NVDA or JAWS (Windows) / VoiceOver (Mac). Is
  every control announced with a sensible name, role, and state? Are errors and
  dynamic changes announced?
- **Zoom/reflow**: 400% browser zoom (≈320px). No two-dimensional scrolling for
  non-data content; nothing clipped or overlapping.
- **Contrast**: spot-check text and UI against the 4.5:1 / 3:1 thresholds with a
  contrast checker; verify in any dark/high-contrast theme too.
- **Themes**: re-run the contrast, focus-visibility, and colour-only checks in
  *every* theme variant you ship — light, dark, and OS high-contrast /
  forced-colors (see `references/theming.md`). Conformance is not inherited from
  the default theme.
- **Colour-only**: would the meaning survive in greyscale?

If a criterion genuinely can't be met (e.g. essential complex data viz), say so
explicitly and propose the closest accessible alternative rather than silently
skipping it.

## Note on standards version

This skill targets WCAG 2.1. **WCAG 2.2** (a superset) adds nine more criteria —
notably Focus Not Obscured (2.4.11/2.4.12), Dragging Movements (2.5.7),
Target Size Minimum 24×24px at AA (2.5.8), Consistent Help (3.2.6), Redundant
Entry (3.3.7), and Accessible Authentication (3.3.8). If the user asks for 2.2
or you're targeting current best practice, also apply those; the checklist notes
where they extend 2.1.
