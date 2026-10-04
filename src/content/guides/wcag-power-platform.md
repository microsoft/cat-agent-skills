# WCAG 2.1 for Web Apps & Power Platform

A skill that makes anything the agent builds or reviews conform to **WCAG 2.1
Level AA** — across generic web UI, full HTML pages and single-page apps, modern
theming (dark mode, high contrast, design tokens), and the four Power Platform
component types: **PCF** controls, **model-driven** apps/forms, **canvas** apps,
and **Power Pages**.

Level AA is the target by default because it's what most accessibility law
actually requires (ADA, Section 508, EN 301 549, and the UK Public Sector Bodies
Accessibility Regulations). AAA criteria are flagged as optional enhancements.

## What it does

When the agent is building, reviewing, or refactoring any web or Power Platform
UI, this skill triggers automatically — even when "accessibility" isn't
mentioned — and:

- Bakes WCAG 2.1 AA checks into anything it authors, rather than bolting them on
  afterwards.
- Audits existing components against every WCAG 2.1 success criterion, reporting
  criterion, level, pass/fail, location, and the fix.
- Applies platform-specific guidance so a check is satisfied the right way for
  the component type (e.g. `AccessibleLabel`/`TabIndex` in canvas, Fluent UI +
  `aria-live` in PCF, column display names in model-driven, semantic markup and
  skip links in Power Pages).

## The four principles (POUR)

| Principle | Covers |
|-----------|--------|
| **Perceivable** | Text alternatives, captions, colour not used alone, 4.5:1 text / 3:1 UI contrast, reflow to 320px, resizable text, programmatic structure |
| **Operable** | Full keyboard access, no keyboard traps, visible focus, logical focus order, enough time, no seizure-inducing flashing, target size, skip links, descriptive links |
| **Understandable** | Page language, labels & instructions, clear error identification + suggestions, consistent navigation, no surprise context changes |
| **Robust** | Valid markup, correct name/role/value for every control, status messages announced via live regions |

## Skill structure

```
wcag-power-platform/
├── SKILL.md                        # Workflow, routing, POUR overview, top-10 AA checks, verification
└── references/
    ├── wcag-checklist.md           # Every WCAG 2.1 success criterion + testable check + fix
    ├── html-pages.md               # Standalone HTML pages, websites, single-page apps
    ├── theming.md                  # Power Apps modern themes, dark mode, high contrast, forced-colors, tokens
    ├── pcf.md                      # PowerApps Component Framework controls
    ├── web-resources.md            # HTML/JS web resources in model-driven apps
    ├── model-driven.md             # Model-driven apps, forms, views, dashboards
    ├── canvas.md                   # Canvas apps
    └── power-pages.md              # Power Pages (portals)
```

The skill uses progressive disclosure: the platform reference files are only
loaded when relevant, so the agent reads the core checklist plus the one file
that matches the component being worked on.

## Verifying conformance

Automated tools catch roughly 30–40% of issues; the rest needs manual checks.
The skill directs the agent to verify with:

- **Automated**: axe-core / Accessibility Insights / Lighthouse / WAVE, plus the
  built-in **App Checker** (model-driven & canvas) and the canvas studio
  **Accessibility checker**.
- **Keyboard-only pass**: reach and operate everything, focus always visible,
  sensible order, no traps.
- **Screen reader spot-check**: NVDA/JAWS (Windows) or VoiceOver (Mac).
- **Zoom/reflow** to 400% (≈320px) and **text resize** to 200%.
- **Contrast** spot-checks and a **colour-only** (greyscale) review.

## Standards version

Targets WCAG 2.1. The skill also notes where **WCAG 2.2** extends it — e.g. Focus
Not Obscured, Dragging Movements, Target Size Minimum (24×24px at AA), Consistent
Help, Redundant Entry, and Accessible Authentication — so you can opt into 2.2
for current best practice.

## Source

WCAG 2.1 success criteria are based on the
[W3C Web Content Accessibility Guidelines (WCAG) 2.1](https://www.w3.org/TR/WCAG21/).
