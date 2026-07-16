# Verification test cases

Twelve test cases to verify the Universal Document Converter end-to-end. Run
them from the skill's root folder (the one containing `scripts/` and
`assets/`). Each case gives the prompt you can ask the agent, the exact
command behind it, and an observable pass criterion.

The fixtures in `assets/samples/` (`sample.md`, `sample.html`, `sample.csv`,
`sample.docx`) all describe the same small "Quarterly Product Update"
document, so conversions can be cross-checked against each other.

Quick automated check of the core pipelines (cases 1, 3, 5–9):

```bash
mkdir -p /tmp/dfc && cd /tmp/dfc
for t in md pdf docx pptx html txt; do python <skill>/scripts/convert.py <skill>/assets/samples/sample.$([ $t = md ] && echo docx || echo md) --to $t -o out.$t; done
```

---

## 1. DOCX → Markdown

- **Prompt:** "Convert `assets/samples/sample.docx` to Markdown."
- **Command:** `python scripts/convert.py assets/samples/sample.docx --to md -o /tmp/t1.md`
- **Pass:** exit code 0; `/tmp/t1.md` contains `# Quarterly Product Update`
  (heading preserved) and a Markdown table row containing `Americas`.

## 2. DOCX → HTML

- **Prompt:** "Turn the sample Word doc into an HTML page."
- **Command:** `python scripts/convert.py assets/samples/sample.docx --to html -o /tmp/t2.html`
- **Pass:** output contains `<h1>` and a `<table>` element (direct mammoth
  route, not a lossy detour through plain text).

## 3. Markdown → PDF

- **Prompt:** "Make a PDF of `assets/samples/sample.md`."
- **Command:** `python scripts/convert.py assets/samples/sample.md --to pdf -o /tmp/t3.pdf`
- **Pass:** PDF is created; extracting its text (e.g. with pdfplumber)
  finds the title `Quarterly Product Update` **and** the table cell `12,400`.

## 4. CJK text in PDF output

- **Prompt:** same as case 3 — the fixture's last section is Japanese.
- **Pass:** text extracted from `/tmp/t3.pdf` contains `日本語` (proves a
  CJK-capable font was registered; without it the characters drop out or
  render as boxes). In the Copilot Studio sandbox this uses the bundled Noto
  CJK fonts; elsewhere the reportlab CID fallback is acceptable.

## 5. Markdown → DOCX

- **Prompt:** "Convert the sample markdown to a Word document."
- **Command:** `python scripts/convert.py assets/samples/sample.md --to docx -o /tmp/t5.docx`
- **Pass:** opening `/tmp/t5.docx` with python-docx shows paragraphs styled
  `Heading 1`/`Heading 2` (including `Quarterly Product Update` and
  `Highlights`) and one table with 4 rows × 3 columns.

## 6. Markdown → PPTX

- **Prompt:** "Turn `sample.md` into slides."
- **Command:** `python scripts/convert.py assets/samples/sample.md --to pptx -o /tmp/t6.pptx`
- **Pass:** opening with python-pptx shows ≥5 slides; the first slide's title
  is `Quarterly Product Update` and one slide is titled `Highlights`.

## 7. HTML → Markdown

- **Prompt:** "Convert `assets/samples/sample.html` to Markdown."
- **Command:** `python scripts/convert.py assets/samples/sample.html --to md -o /tmp/t7.md`
- **Pass:** output contains `# Quarterly Product Update` and `**Falcon**`
  (bold survives).

## 8. CSV → Markdown table

- **Prompt:** "Show `sample.csv` as a Markdown table."
- **Command:** `python scripts/convert.py assets/samples/sample.csv --to md -o /tmp/t8.md`
- **Pass:** output starts with `| Region | Active Users | Growth |` and
  includes a row for `APAC`.

## 9. PDF → Markdown (round trip)

- **Prompt:** "Convert the PDF from case 3 back to Markdown."
- **Command:** `python scripts/convert.py /tmp/t3.pdf --to md -o /tmp/t9.md`
- **Pass:** exit code 0 and `/tmp/t9.md` contains `Quarterly Product Update`.
  (Formatting fidelity may degrade — the pass bar is content survival.)

## 10. Unsupported pair fails gracefully

- **Prompt:** "Turn `/tmp/t3.pdf` into a PowerPoint."
- **Command:** `python scripts/convert.py /tmp/t3.pdf --to pptx`
- **Pass:** non-zero exit; stderr says the pair is `not supported` and prints
  the `Supported conversions` matrix; **no Python traceback**. The agent
  should relay the matrix and suggest PDF → md → pptx instead.

## 11. Extension mismatch is detected

- **Setup:** `cp assets/samples/sample.html /tmp/fake.docx`
- **Command:** `python scripts/convert.py /tmp/fake.docx --to md -o /tmp/t11.md`
- **Pass:** exit code 0; a warning on stderr says the content
  `looks like html`; the output was converted as HTML (contains
  `# Quarterly Product Update`); no crash.

## 12. Batch mode

- **Prompt:** "Convert everything in `assets/samples/` to Markdown."
- **Command:** `python scripts/convert.py --batch assets/samples --to md --out-dir /tmp/t12`
- **Pass:** exit code 0; the printed summary table shows `sample.csv`,
  `sample.docx`, and `sample.html` as `converted`, `sample.md` as `skipped`
  (`already md`), and same-stem outputs get disambiguated names
  (`sample.docx.md`, `sample.html.md`) instead of overwriting each other.
