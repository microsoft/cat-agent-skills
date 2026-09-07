---
name: pdf-table-data-conversion
description: >-
  Use this skill whenever the user wants tabular data from a PDF document AS A
  FILE — to extract, pull out, export, convert, or "put into a
  spreadsheet/Excel/CSV" (e.g. "pull out the rebates from the Contoso contract",
  "extract this pricing table", "get this into a spreadsheet"). This INCLUDES
  follow-up requests after you have already answered or summarized the data in
  chat — e.g. "now give me that as a file/spreadsheet", "export what you just
  showed me", "download that as Excel". In those follow-ups you MUST still invoke
  this skill and extract from the source document; never hand-build a spreadsheet
  from the chat summary. Do NOT use this skill for answer-in-line questions such
  as "what are the rebates in the Contoso contract?" — those are grounded Q&A.
---

Turn tables locked inside a PDF into a clean, nicely formatted spreadsheet the
user can open in Excel or feed to another tool. The user is asking for the *data
as a file*, not a prose answer — so your job is to locate the source PDF, get its
**full** content (not just retrieved chunks), extract the relevant table(s), and
hand back a formatted workbook.

## When this applies (and when it does not)
- **Applies** — the user wants the tabular data itself as a file: "pull out /
  extract / export / convert / get me a spreadsheet of …", "put the rebate
  schedule in Excel", "give me the line items from this contract".
- **Applies to follow-ups too** — even if you already answered or summarized the
  data in the chat, a subsequent "give me that as a file / spreadsheet / Excel"
  is still an extraction request. Invoke this skill and rebuild the file from the
  **source document** — do not assemble a spreadsheet from the text already in the
  conversation, which may be partial, truncated, or reformatted.
- **Does not apply** — the user is asking a question to be answered in the
  conversation: "what are the rebates for Contoso?", "how much is the Q3
  discount?". Answer those inline from knowledge within reason; do **not** run an
  extraction or produce a file.

If a request is ambiguous (e.g. "show me the rebates"), prefer a short inline
answer and offer to export it as a file if they want the full table.

## Instructions
1. **Identify the target document.** Let the user ask naturally — they need not
   name an exact file. Use the cues in their request (customer/contract name,
   topic, document title, or a file they referenced) to search knowledge for the
   best-matching PDF. If one document is a clear match, proceed with it. Only when
   the match is genuinely ambiguous — several plausible documents, or none obvious
   — ask the user a brief question to confirm which one they mean.
2. **Get the FULL document, not chunks.** Retrieved knowledge chunks are enough
   to *answer* a question but not to *extract a whole table* — rows are routinely
   split across chunks — so work from the complete PDF in the agent's container.
   A SharePoint knowledge source handles this naturally: let it search and pull
   the full file down. If the maker collects files another way (direct upload, a
   connector, a different store), use whatever mechanism is available to get the
   full PDF locally. The rest of these steps are the same once the file is local.
3. **Extract the table(s) — script first.** Run the bundled
   `scripts/extract_tables.py` against the downloaded PDF to pull tabular data out
   deterministically (see *Bundled files*). This is the default path because it
   lifts the grid verbatim — no dropped or "tidied" rows — which matters most for
   long schedules. It writes a formatted `.xlsx` workbook by default, with one tab
   per detected table (so multiple tables and page splits stay cleanly separated).
   Narrow to the relevant table when the user named a specific one (e.g. rebates,
   pricing, line items) using the `--contains` filter; otherwise extract all
   detected tables.
4. **Fall back to reading it yourself when the script can't cope.** `pdfplumber`
   relies on a text layer and clean rules, so it under-performs on **scanned /
   image-only PDFs** (no text to extract) and **borderless or merged-cell tables**
   (misaligned output). When the script returns nothing, or the output is clearly
   garbled/misaligned versus the PDF, read the table directly from the document
   and build the workbook yourself following the cleaning rules below. Use your
   judgement to pick the right table when a keyword filter is too blunt.
5. **Clean the output.** Ensure a single header row per table, trim stray
   whitespace, drop fully empty rows (but keep empty columns — they preserve the
   table's structure and alignment), and keep numbers/currency/dates as they
   appear in the source (do not invent, reformat, or "correct" values). If cells
   were merged or a header spans multiple rows, flatten to one clear header row.
   Put each distinct table on its own sheet/tab; if one logical table is split
   across pages, you may merge the parts into a single sheet.
6. **Respond with a recap, then the file.** Open your reply with a short,
   natural summary of what the user asked for and what you pulled — restate the
   request in your own words (e.g. "Here's the full rebate schedule from the
   Contoso contract you asked for") — then attach the **full** extracted data as a
   formatted `.xlsx` workbook. The complete data lives in the file, not the chat:
   don't paste the whole table inline or truncate it. When multiple tables were
   extracted, give each its own clearly named tab and briefly say what each
   contains. Then **offer a `.csv` as an alternative** ("Let me know if this works, or if you'd prefer a CSV instead") — produce it with `--format csv` (or `both`) if they say yes, one
   CSV per table.
7. **Confirm and flag gaps.** Give a one-line summary (which document, which
   table(s)/tab(s), rows × columns) and note whether the script or a manual read
   produced it. Call out anything uncertain — a table that spanned pages, cells
   that failed to parse, or a table the tool could not detect — so the user can
   verify rather than trust silently.

## Bundled files
The attached `.zip` includes:
- `scripts/extract_tables.py` — extracts tables from a local PDF using
  `pdfplumber` (available natively in the agent container). Run it as
  `python scripts/extract_tables.py <document.pdf> --out-dir out`. By default it
  writes a formatted `.xlsx` workbook — one tab per table, with a bold frozen
  header row, an autofilter, and sized columns. Useful flags:
  - `--format xlsx|csv|both` — output format (default `xlsx`; `csv` writes one
    CSV per table; `both` writes the workbook and the CSVs),
  - `--pages 2-5` (or `--pages 3`) to limit to specific pages,
  - `--contains rebate` to keep only tables whose text contains a keyword,
  - `--out-dir out` to choose where the files are written.
  It prints a JSON summary of everything produced (workbook path, per-table sheet
  names, any CSV paths, source page, row/column counts) so you can report back
  accurately. If it produces no tables or clearly
  mangles them (scanned or borderless PDFs), fall back to reading the tables
  yourself per step 4.

## Guardrails
- Never fabricate rows, values, or headers. If a cell is unreadable, leave it
  empty and flag it rather than guessing.
- Do not answer extraction requests from retrieved chunks alone — always work
  from the full downloaded document so tables aren't truncated.
- **Never build the file from the chat.** When the user asks for a file after
  you've already answered or summarized in conversation, still run this skill and
  extract from the source document — do not hand-assemble a spreadsheet from the
  text in the chat, which may be partial or reformatted.
- Do not turn a plain question into a file dump; only produce a file when the user
  actually wants the data as a file.
- Do not expand scope beyond what was asked (don't export every table when the
  user asked only for the rebates).

## Tone
Precise and practical. Prefer surfacing uncertainty over confidently returning a
table that may be incomplete.
