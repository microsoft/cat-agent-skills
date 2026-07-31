# Accessibility Pass

Most skills in this gallery *produce* decks and documents. This one checks what
comes out the other end.

Point it at a `.pptx`, `.docx`, `.html`, or `.md` file and it reports every
accessibility failure it can find, using the same rule names Microsoft's own
Accessibility Checker uses, so the findings match what you see in the Office
ribbon, then fixes them on request.

## What it checks

| | |
| --- | --- |
| **Errors** | Missing alt text, untitled slides, tables with no header row, restricted document access |
| **Warnings** | Contrast below WCAG AA, merged/complex tables, illogical slide reading order, uncaptioned media, vague link text |
| **Tips** | Duplicate slide titles, documents with no heading styles, missing document language |

## How it works

Two passes. A bundled script (`scripts/a11y_check.py`) does the arithmetic: it
computes real WCAG contrast ratios, reads alt-text attributes straight out of the
file's XML, and compares screen-reader order against visual layout. Then the
agent does the part a script can't, judging whether alt text is *useful*, whether
something marked decorative really is, and whether meaning is being carried by
colour alone.

The script needs `python-pptx` for PowerPoint files and `python-docx` for Word
files. HTML and Markdown use the Python standard library only. Without a
Python environment, HTML and Markdown still work: the agent reads the file
directly and applies the same rules by hand, just less precisely. PowerPoint
and Word files don't have that fallback, they're zipped Office XML, not
something to read as plain text, so without Python the skill asks the user to
run Office's own Accessibility Checker and share what it finds instead.

## Known limits

Worth knowing before you trust a clean result:

- **Contrast is only checked where colours are explicit.** Theme colours,
  gradients, and text over images are reported as *unchecked*, not as passing.
  Office's built-in checker has the same blind spot.
- **Reading order is a geometry heuristic.** Intentional multi-column layouts can
  be flagged; the skill is told to confirm before reporting.
- **This is not a conformance audit.** No automated tool can certify WCAG or
  EN 301 549. A clean pass means no *detected* issues, which is not the same as
  accessible.

## Rules reference

[Rules for the Accessibility Checker](https://support.microsoft.com/office/rules-for-the-accessibility-checker-651e08f2-0fc3-4e10-aaca-74b4a67101c1)
· [WCAG 2.1 contrast minimum](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)

---

Skill by Tim Karlsson (╯°□°)╯︵ ┻━┻ Works 60% of the time, every time.
