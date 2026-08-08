# HTML / JS Web Resources (model-driven) — Accessibility

Web resources are custom **HTML/CSS/JavaScript** files you upload and surface
inside model-driven apps — on forms, dashboards, the command bar, or as
standalone pages. Because you author the markup, **you own WCAG conformance**;
the platform can't fix an inaccessible web resource. The full
`wcag-checklist.md` and `html-pages.md` apply directly. This file captures the
web-resource-specific guidance from Microsoft's developer docs.
Reference:
https://learn.microsoft.com/en-us/power-apps/developer/model-driven-apps/create-accessible-web-resources

## How AT sees your web resource
The browser turns your DOM elements into UI Automation (UIA) objects that
assistive technology reads. You have **limited control** over that conversion —
which is exactly why using the right elements matters: the browser only exposes
the expected properties/events when you use the element the way it was intended.

## Semantic HTML first, then layer ARIA (the core rule)
- **Use the correct native element for each interaction.** A `<div>` with a click
  handler can be *made* to look and behave like a button, but the browser won't
  expose button role/state/events to AT — so screen-reader and keyboard users get
  nothing. Use `<button>`, `<a href>`, `<input>`, `<select>`, real headings,
  lists, and tables (1.3.1, 2.1.1, 4.1.2).
- **Layer ARIA over semantic HTML**, don't replace it. Modern web resources often
  build custom widgets from many elements and update content dynamically with
  async JS — that's confusing to AT relying on semantic HTML alone. Add ARIA
  roles/states and live regions on top of correct native markup, never ARIA that
  contradicts the native role. Follow the WAI-ARIA Authoring Practices for widget
  keyboard patterns.

## Dynamic / async content (4.1.3)
- Content updated via JavaScript without a full reload must announce through
  `aria-live` / `role="status"` / `role="alert"`, and manage focus on meaningful
  changes — AT won't notice silent DOM mutations.

## The usual cross-cutting requirements still apply
Microsoft calls these out explicitly for web resources:
- **Text resize** — UI adjusts when the user increases text size (200%, 1.4.4);
  use relative units, no fixed-height clipping.
- **Colour** — don't require colour discrimination to complete a task (1.4.1);
  meet contrast (1.4.3 / 1.4.11).
- **Keyboard** — every action operable by keyboard, visible focus, no traps
  (2.1.1, 2.1.2, 2.4.7).

## Theming
- Match the host app theme (including modern/Fluent themes and high contrast) so
  contrast holds; see `references/theming.md`. Don't hard-code colours that break
  in dark or high-contrast mode.

## Verify
- **axe DevTools / Accessibility Insights** (FastPass + Assessment) on the
  rendered web resource — the practical first pass for HTML.
- If editing in **Visual Studio**, use **Tools → Check Accessibility** for a
  built-in report.
- Deeper UIA inspection (optional): **Inspect.exe** (view the UIA tree and an
  element's exposed name/role/value), **AccEvent.exe** (confirm focus/state-change
  events fire), **AccChecker** (MSAA/UIA correctness).
- Keyboard-only pass and a screen-reader spot-check (NVDA/JAWS/Narrator) **inside
  an actual form/dashboard**, since host context affects focus and announcement.
- Test at 200% text / 400% zoom, and in dark + Windows High Contrast.
