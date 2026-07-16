---
name: Universal Document Converter
description: "Convert documents between Markdown, HTML, PDF, Word, PowerPoint, Excel/CSV and text — fully offline, using only the libraries already in the agent sandbox."
agentDescription: "Use this skill whenever the user asks to convert a document or file from one format to another — Markdown, HTML, PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx), CSV, or plain text (e.g. \"turn this Word doc into a PDF\", \"make slides from this markdown\", \"convert this page to markdown\"). Run the bundled scripts/convert.py instead of writing ad-hoc conversion code, BEFORE attempting any conversion yourself."
platforms: [Copilot Studio]
tags: [documents, conversion, markdown, pdf, office, scripts]
author: Andreas Adner
authorUrl: "https://github.com/adner"
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

## Instructions

1. Identify the input file and the target format the user wants. Targets:
   `md`, `html`, `pdf`, `docx`, `pptx`, `txt`. Inputs additionally include
   `xlsx` and `csv`.
2. Run the converter from the skill folder:

   ```bash
   python scripts/convert.py INPUT --to FORMAT [-o OUTPUT]
   ```

   It prints the output path on success. If `-o` is omitted, the output lands
   next to the input with the new extension.
3. For a folder of files, use batch mode and share the printed summary table
   with the user:

   ```bash
   python scripts/convert.py --batch DIR --to FORMAT [--out-dir DIR]
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
