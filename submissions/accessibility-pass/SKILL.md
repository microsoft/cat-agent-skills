---
name: accessibility-pass
description: >-
  Use this skill whenever the user asks to check, review, or fix the
  accessibility of a PowerPoint deck, Word document, HTML page, or Markdown
  file, and before handing over any deck or document this agent just
  generated, so it does not ship with missing alt text, untitled slides, or
  unreadable colour contrast.
---

Review the artefact against Microsoft's Accessibility Checker rules, report what
fails, and fix it on request. Use the rule names below verbatim. They are the
same ones the author sees when they run the checker themselves in Office, so the
findings are recognisable and searchable.

## Instructions

1. Get the file. Supported: `.pptx`, `.docx`, `.html`, `.md`. If the user pasted
   raw HTML or Markdown instead, save it to a file first.

2. Run the bundled checker when a Python environment is available, from the
   skill's own root directory (the folder containing `scripts/`), so the
   relative path resolves:

   ```bash
   python scripts/a11y_check.py <file> --json
   ```

   It needs `python-pptx` for `.pptx` and `python-docx` for `.docx`; HTML and
   Markdown need nothing beyond the standard library. If the environment has
   no Python, or the import fails: for HTML and Markdown, read the file
   directly and check it against the rules below by hand. For `.pptx` and
   `.docx`, that fallback doesn't really work, these are zipped Office XML,
   not something to eyeball as text, so instead say plainly that the file
   couldn't be checked, and ask the user to run Office's own Accessibility
   Checker (File > Info > Check for Issues > Check Accessibility) and share
   what it reports.

3. Add the judgement calls the script deliberately does not make:

   - **Alt text that exists but is useless.** `"image1.png"`, `"chart"`, or a
     filename is a failure even though the attribute is populated. Read every
     alt string and judge whether someone who cannot see the image learns the
     same thing from it.
   - **Wrongly decorative.** Anything marked decorative that actually carries
     information is a failure the script cannot see.
   - **Reading order that is flagged but fine.** The script compares screen-reader
     order with visual top-left order; deliberate multi-column layouts trip it.
     Confirm before reporting.
   - **Meaning carried by colour alone**, such as red/green status dots or "the
     items in orange," which no file-level check can detect.
   - **Captions and transcripts** for embedded audio or video.
   - **Contrast the script skipped.** It only compares explicit RGB values.
     Theme colours, gradients, and picture fills come back unchecked. Report
     them as unchecked, never as passing.

4. Report findings grouped by severity, worst first, one row each:

   | Severity | Rule | Where | Fix |
   | --- | --- | --- | --- |
   | Error | All slides have titles | Slide 4 | Add a title in the title placeholder |

   Open with a one-line count (`3 errors, 5 warnings, 1 tip`). If nothing fails,
   say so and list what could not be checked mechanically.

5. Offer to apply the fixes. Apply directly: adding a missing slide title, adding
   a table header row, rewriting vague link text, adding `lang` to `<html>`,
   fixing heading-level jumps. Ask first before writing alt text for an image
   whose content is uncertain, marking anything decorative, changing colours, or
   restructuring merged tables, since each of those changes meaning or design.

6. Re-run the checker after fixing and report what is left.

## The rules

**Errors**: content that is unusable for someone relying on assistive tech.

- All non-text content has alternative text (alt text)
- Tables specify column header information
- All slides have titles
- All sections have meaningful names *(the bundled script doesn't check this;
  ask the user or inspect the file's sections manually)*
- Document access is not restricted *(the bundled script doesn't check this;
  verify manually whether the file has IRM/password protection applied)*

**Warnings**: content that is hard to use.

- Sufficient contrast between text and background (WCAG AA: 4.5:1 normal text,
  3:1 for text 18pt+ or bold 14pt+)
- Table has a simple structure
- The reading order of the objects on a slide presentation is logical
- Closed captions are included for inserted audio and video
- Hyperlink text is meaningful

**Tips**: content that could be easier to use.

- Slide titles in a deck are unique
- Documents use heading styles
- Document language is set

## Guardrails

- Never invent alt text for an image whose content is unknown. Ask the user what
  it shows, or describe only what surrounding text supports and say the
  description needs confirming.
- Never mark an object decorative to clear a finding. Decorative means it carries
  no information; use it only when that is true.
- Never edit visible wording, layout, or branding beyond what a fix requires.
- Never report an unchecked item as a pass.
- Do not claim WCAG or EN 301 549 conformance. This is a pass over known rules,
  not a certification. A clean result means no *detected* issues.

## Tone

Direct and specific. Name the rule, the location, and the concrete fix. No
lecturing about why accessibility matters; the user already asked.
