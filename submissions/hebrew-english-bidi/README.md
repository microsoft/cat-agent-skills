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
guarantee that every advertised format or feature has been tested.

## Verified scope and limitations

On 2026-11-17, synthetic Word and PowerPoint documents were repaired in Cowork
and an unpublished Copilot Studio agent, then processed a second time.
Independent checks verified editable outputs, exact text and whitespace,
formatting, links, lists, table/shape geometry, and byte-identical repeat files
within each run. Native Office renders were inspected externally:

| Fixture | Cowork | Copilot Studio |
| --- | --- | --- |
| Word: two pages, 18 direction/alignment cases and seven terminal-period cases | Passed the scoped checks | Passed the scoped checks |
| PowerPoint: four slides and a visible speaker note, 17 paragraph cases | Passed the scoped checks | Passed the scoped checks |

These are **repair-and-repeat tests with external native Office verification**,
not a claim that the cloud hosts ran desktop Office. Copilot Studio had no
usable renderer; it correctly disclosed the limitation. Cowork's LibreOffice
renderer reported minus-sign and mention artifacts absent from native Office.
Built-in document preprocessing may supplement the explicitly loaded custom
skill. Reported reference hashes matched the tested payload; this is not an
independently captured low-level execution trace.

The tests found and corrected Word physical-alignment and neutral-punctuation
guidance, plus PowerPoint mixed-run language/direction context. Other formats,
tracked changes, comments, inherited RTL styles, grouped objects, charts, and
SmartArt remain unverified. Successful upload in Copilot in PowerPoint is
recorded separately; that host's document-repair workflow was not tested.

Read the [source repository's validation report and evidence](https://github.com/OfirGavish/hebrew-english-bidi-skill/blob/main/VALIDATION.md)
for exact payload/output fingerprints, reproducible inputs, native-render
images, and the difference between host checks and external verification.

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
