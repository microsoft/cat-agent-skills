# Power Pages (Portals) — Accessibility

Power Pages produces public-facing websites, so it is the component type most
likely to be **legally** required to meet accessibility standards (ADA, Section
508, EU/UK public-sector regulations). The platform itself conforms to **WCAG
2.2**, **US Section 508**, and **ETSI EN 301 549** out of the box — but Microsoft
is explicit that **when you customise the site, you own conformance**. You
control markup, CSS, and Liquid/JS, so the full `wcag-checklist.md` applies
directly. Because the platform targets 2.2, prefer the WCAG 2.2 superset here
(the checklist notes the extra 2.2 criteria). Follow the **WAI-ARIA Authoring
Practices** for page layout and any custom widgets. Below are the Power Pages
specifics.

## Templates, themes & Bootstrap
- Power Pages ships on Bootstrap; starter templates are reasonably accessible but
  **customisation is where conformance is lost**. Re-check after any theme,
  CSS, or web-template edit.
- **Theme contrast**: verify your brand palette gives 4.5:1 text / 3:1 UI
  contrast for buttons, links, form borders, and focus states. Check link colour
  against background *and* that links aren't distinguished by colour alone
  (1.4.1) — keep underlines or another cue.
- Don't remove Bootstrap's focus outlines without an equally visible replacement
  (2.4.7).

## Page structure (1.3.1, 2.4.1, 2.4.2, 2.4.6)
- One `<h1>` per page; headings in order via the editor's heading styles, not
  bold text. Use landmark structure (`<header><nav><main><footer>`).
- Provide a **skip-to-content** link (2.4.1).
- Set a unique, descriptive **page title** for every web page (2.4.2) and the
  correct site `lang` (3.1.1).
- Maintain consistent navigation across pages (3.2.3).

## Images & media (1.1.1, 1.2.x)
- Set **alt text** on every content image (web file / image component);
  decorative images get empty alt. Provide captions/transcripts for embedded
  video/audio; don't auto-play audio (1.4.2).

## Forms — basic, advanced, multistep (1.3.1, 3.3.1–3.3.4, 4.1.2)
Basic-form controls are built to WCAG 2.2; two built-in settings improve them —
turn them on:
- **ToolTips Enabled** — renders the target column's *Description* as the field's
  `title` attribute, giving screen readers extra context. Off by default; enable
  it and write useful field descriptions in Dataverse.
- **Enable Validation Summary Links** — renders anchor links in the validation
  summary that jump focus to the field in error. On by default; keep it on (it
  directly supports 3.3.1 error identification and focus management).

- Entity/basic forms and multistep forms: ensure each field has a **visible,
  associated label** (the column display name) — check the rendered `<label
  for>`. Mark required fields with text/icon, not colour alone.
- Configure validation so errors render as **text** near the field with a
  suggested fix; verify the error is associated (`aria-describedby`,
  `aria-invalid`) and announced. Provide a confirmation/review step for
  legal/financial/data submissions (3.3.4).
- **CAPTCHA**: the default may be a barrier — provide an accessible alternative or
  use an accessible CAPTCHA (1.1.1).
- Group radio/checkbox sets in `<fieldset>`/`<legend>`.

## Lists & tables (1.3.1)
- Entity lists rendered as tables need proper `<th scope>` headers and a caption;
  avoid layout tables. Ensure list filtering/sorting controls are keyboard
  operable and labelled.

## Embedded Power BI (1.1.1, 1.4.1, 1.4.11)
- Power BI reports/dashboards embed as a first-party component, but their
  accessibility is the **report author's** responsibility — the embed doesn't fix
  an inaccessible report. Build the report per Microsoft's Power BI accessibility
  guide: set alt text on visuals, tab order, distinguish series beyond colour,
  meet contrast, and provide the accessible "Show as table" data view.

## Liquid / custom JS / web templates
- Any custom markup must be semantic and keyboard-operable; dynamic AJAX updates
  (entity list paging, lookups) must announce via `aria-live` (4.1.3) and manage
  focus. Custom modals must trap focus while open and restore it on close, with
  Esc to dismiss (2.1.2, 2.4.3).

## Reflow, resize, motion (1.4.4, 1.4.10, 1.4.12, 2.2.2)
- Confirm responsive reflow to 320px / 400% zoom with no horizontal scroll;
  text resizes to 200%; user text-spacing overrides don't clip content.
- Carousels/banners that move > 5s need pause/stop; respect
  `prefers-reduced-motion`.

## Verify
- **Accessibility Insights** is Microsoft's recommended tool — run both
  **FastPass** (automated checks) and an **Assessment** (measures WCAG 2.2 AA).
  axe DevTools / WAVE / Lighthouse also work. Test as anonymous *and*
  authenticated, since forms differ.
- Keyboard-only navigation of nav, a form, and an entity list.
- Screen reader pass on a key journey (e.g. sign-in → submit a form →
  confirmation) confirming labels, errors, and live updates — Microsoft suggests
  **Windows Narrator**; NVDA/JAWS also fine.
- Use **Immersive Reader** in Edge to confirm the page renders and reads
  sensibly.
- Test at **400% zoom** (1.4.10): text readable, controls still function.
- Contrast audit of the live theme; mobile/responsive and 200% zoom checks.
- Produce/maintain an **accessibility statement** if legally required.
