# Model-driven Apps — Accessibility

Model-driven apps render through Microsoft's Unified Interface, which is built to
be WCAG 2.1 AA / EN 301 549 conformant **out of the box**. Your job is mostly to
**configure metadata correctly** so the platform can do its work — most failures
come from missing labels, colour-only choices, and inaccessible custom code.

## What the platform gives you (don't break it)
- Keyboard navigation, focus management, ARIA roles, and screen-reader support
  are built into Unified Interface forms, grids, and command bar. Stick to
  standard components and you inherit conformance.

## Where you must act

### Labels & descriptions (1.1.1, 1.3.1, 3.3.2, 4.1.2)
- Give every **column** a clear, human-readable **Display Name** — it becomes the
  field's accessible label. Avoid schema-only names leaking to the UI.
- Fill **Description** / tooltip text on fields where format or purpose isn't
  obvious (3.3.2). Set **alt text on image columns** and web resource images.
- Tab/section/field display names must be meaningful (2.4.6, 1.3.1) — they form
  the form's heading/landmark structure.

### Colour & contrast (1.4.1, 1.4.3, 1.4.11)
- **Business rules / form logic must not convey meaning by colour alone.** If you
  use formatting or icons to flag status, also convey it in text.
- Custom **themes**: verify brand colours meet 4.5:1 text / 3:1 UI contrast in
  the theme editor before publishing. Test the high-contrast theme.
- Choice/Option-set colours and view "edit" formatting: never colour-only.

### Modern themes (New look / Fluent 2) — see `references/theming.md`
- If the app uses the **New look**, classic theming is ignored; branding comes
  from a `CustomTheme` XML web resource. Accessibility traps to avoid: prefer
  `LockPrimary="false"` (accessibility-optimised palette); `LockPrimary="true"`,
  manual slot overrides, and `AppHeaderColors` overrides all bypass the
  protection — validate 4.5:1 / 3:1 on every foreground/background pair and on
  **every app-header button state** (rest, hover, pressed, selected). Note the
  theme doesn't restyle Timeline, lookup dropdowns, legacy grids, audit history,
  or BPF — verify those separately. Full detail in `references/theming.md` Part 1.

### Forms & views
- Keep a **logical field order** on the form (drives tab order, 2.4.3).
- Use sections and tabs to give structure rather than cramming everything in one
  block.
- For views/grids, sensible column headers (read by screen readers) and avoid
  relying on icon-only columns without a text/tooltip equivalent.

### Charts & dashboards (1.1.1, 1.4.1, 1.4.11)
- Charts are visual; ensure the underlying view/data is reachable as a table.
  Distinguish series by more than colour; check non-text contrast.

### Custom code (PCF, web resources, embedded canvas) — your responsibility
- **PCF controls**: see `pcf.md`. The platform won't fix a custom control.
- **HTML/JS web resources**: see `references/web-resources.md` — semantic HTML +
  layered ARIA, keyboard, focus, live regions; the platform won't fix custom
  markup.
- **Embedded canvas apps**: see `canvas.md`.

### Error handling (3.3.1, 3.3.3, 4.1.3)
- Use platform field validation / business rules so errors surface in the
  standard accessible way. For custom validation, announce via the form
  notification API (which the platform exposes accessibly) rather than a silent
  colour change.

## Verify
- **App Checker** (Solution / app designer) — fix flagged issues.
- **Accessibility Insights / axe** on a published form and view.
- Keyboard-only navigation of a record form, grid, and command bar.
- Screen reader (NVDA/JAWS) pass on create/edit/save flows, confirming labels,
  required-field state, and error announcements.
- Custom theme contrast check; Windows High Contrast mode.
