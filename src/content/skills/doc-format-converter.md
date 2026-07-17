---
name: Universal Document Converter
description: "Convert documents between Markdown, HTML, PDF, Word, PowerPoint, Excel/CSV and text — fully offline, using only the libraries already in the agent sandbox."
agentDescription: "Use this skill whenever the user asks to convert a document or file from one format to another — Markdown, HTML, PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx), CSV, or plain text (e.g. \"turn this Word doc into a PDF\", \"make slides from this markdown\", \"save this page as markdown\"). Only for producing a converted file as a deliverable. Do NOT use this skill to answer questions about a document's content — the analyzing-* skills handle that. Run the bundled scripts/convert.py instead of writing ad-hoc conversion code, BEFORE attempting any conversion yourself."
platforms: [Copilot Studio]
tags: [documents, conversion, markdown, pdf, office, scripts]
author: Andreas Adner
authorUrl: "https://github.com/adner"
authorGithub: adner
version: 1.0.0
createdAt: 2026-07-16
updatedAt: 2026-07-16
bundle: bundles/doc-format-converter.zip
---
Convert documents between formats using the bundled `scripts/convert.py`. It
works fully offline with libraries already present in the sandbox
(markitdown, mammoth, markdownify, reportlab, python-docx, python-pptx,
pdfplumber, beautifulsoup4, magika) and routes each conversion through the
highest-fidelity pipeline available.

## Division of labor with the analyzing-* skills

This skill **produces files**; the built-in `analyzing-*` skills **answer
questions**. Route accordingly:

- "What does this PDF say?", "find X in this workbook", "summarize this
  deck" → use `analyzing-pdf` / `analyzing-xlsx` / `analyzing-pptx` etc.,
  not this skill. In particular, never use `convert.py` as a substitute
  extraction path for PDF question-answering — `analyzing-pdf` owns that.
- "Give me this as a PDF/Word doc/slides/markdown file" → this skill.
- If the user asks content questions *after* a conversion, hand off to the
  matching `analyzing-*` skill on the original file rather than answering
  from this skill's intermediate output.
- **Reuse their artifacts when present.** If an `analyzing-*` preprocessor
  has already produced a `converted.md` for the source file, feed that to
  `convert.py` as Markdown input (`convert.py converted.md --to pptx`)
  instead of re-extracting the original — it is a high-quality extraction
  with page markers and pipe tables.

## Instructions

1. Identify the input file and the target format the user wants. Targets:
   `md`, `html`, `pdf`, `docx`, `pptx`, `txt`. Inputs additionally include
   `xlsx` and `csv`.
2. Run the converter by the script's path inside this skill's folder —
   typically `/app/skills/doc-format-converter/` — so it works regardless of
   the current working directory:

   ```bash
   python /app/skills/doc-format-converter/scripts/convert.py INPUT --to FORMAT [-o OUTPUT]
   ```

   It prints the output path on success. If `-o` is omitted, the output lands
   next to the input with the new extension.
3. For a folder of files, use batch mode and share the printed summary table
   with the user:

   ```bash
   python /app/skills/doc-format-converter/scripts/convert.py --batch DIR --to FORMAT [--out-dir DIR]
   ```

4. If the script reports an unsupported conversion, relay its message — it
   prints the full support matrix. Offer the nearest supported route (e.g.
   PDF → slides is unsupported; offer PDF → Markdown, let the user edit, then
   Markdown → PPTX).
5. If the script warns that a file's extension doesn't match its content
   (content sniffing via magika), tell the user; the converter proceeds using
   the detected content type.
6. Return the converted file to the user and briefly state which pipeline was
   used (e.g. "docx → HTML via mammoth").

## Conversion notes

- Markdown is the universal intermediate: Office/PDF inputs are extracted with
  markitdown, then re-rendered. Some layout (columns, images, footnotes) is
  simplified — say so when converting layout-heavy documents.
- For **scanned/image PDFs**, this skill's pdf → md route extracts little or
  nothing. Run the `analyzing-pdf` preprocessor instead (its OCR pipeline is
  the better extractor) and feed its text artifact into this skill's
  renderers.
- PDF output registers a CJK-capable font automatically (bundled Noto CJK
  fonts, falling back to reportlab's built-in CID fonts), so Chinese,
  Japanese, and Korean text renders correctly.
- PPTX output builds one slide per `#`/`##` heading with body content as
  bullets, overflowing onto continuation slides — it is an outline deck, not
  finished design.
- `pdf → pptx` and `pptx → pdf/docx` are deliberately unsupported: the
  extraction is too lossy to present as a finished conversion.

## Guardrails

- Never fabricate or "fill in" content the source file does not contain; if
  extraction returns nothing, report that instead of inventing text.
- Do not hand-write conversion code when `convert.py` supports the pair; only
  fall back to custom code if the script fails, and say that you did.
- Never claim a conversion succeeded without the script's success output.
- Verification test cases live in `references/test-cases.md` with fixtures in
  `assets/samples/` — use them when the user asks to validate the skill.
