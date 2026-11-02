# Hebrew-English Bidi

Create and repair mixed Hebrew-English text without reversing source text,
translating content, or flattening editable documents.

The skill is written in English and accepts English or Hebrew requests.
It treats paragraph direction, inline direction, and alignment separately.

## Format-aware workflows

- **Word and PowerPoint:** native paragraph/run properties, preserving design,
  links, lists, notes, and editability.
- **HTML and Markdown:** semantic direction markup, with explicit
  renderer/sanitizer limitations.
- **Plain text:** viewer-level settings first; approved Unicode isolates only
  when needed.
- **Excel:** per-cell reading order without reversing sheet columns or
  changing formulas.
- **CSV/TSV:** preserve data; explain that these formats cannot store RTL
  cell-formatting metadata.
- **Email, PDF, OpenDocument, and legacy formats:** tool-aware workflows,
  source-first repair, and approval before lossy conversion or OCR.

This is an instruction skill, not a universal converter or bundled editing
engine. File access, editing, conversion, and rendering depend on the tools
available in the host. Cowork and Copilot Studio are intended targets, not a
claim of completed end-to-end tests in those platforms.

## Try it

> Fix the Hebrew-English direction in this PowerPoint. Preserve the design
> and editable text. Inspect every slide and speaker notes.

> Fix mixed RTL/LTR paragraphs in this Word document without accepting tracked
> changes or changing English-only paragraphs.

> תתקן את הכיווניות של העברית והאנגלית במסמך בלי לשנות את העיצוב.

The skill preserves the original by default, reports actual checks performed,
and distinguishes structural validation from visual verification.
It includes a synthetic mixed-language regression corpus, not private documents.

Source, installation instructions, and contributions:
[OfirGavish/hebrew-english-bidi-skill](https://github.com/OfirGavish/hebrew-english-bidi-skill).

MIT licensed. Author: Ofir Gavish.
