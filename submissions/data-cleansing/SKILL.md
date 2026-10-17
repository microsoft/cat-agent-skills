---
name: data-cleansing
description: Cleans Excel files that a user uploads in the chat - finds and fixes or quarantines corrupt, duplicate, incomplete, or inaccurate records so the data is reliable for analysis. Returns a cleaned .xlsx plus a list of rejected rows and a change log. Use when the user uploads .xlsx/.xlsm/.xls files and asks to clean, cleanse, scrub, dedupe, tidy, fix, validate, or prepare data, or says a spreadsheet is "messy", has duplicates, blanks, bad dates, or inconsistent values.
---

# Data Cleansing (Excel)

Runs `scripts/clean_excel.py` (Python, pandas + openpyxl, both preinstalled in the code interpreter - do not pip install) on every Excel file the user uploaded, then hands back a cleaned file for each. Always run the script rather than editing data by hand, and never invent or guess values.

## Step 1: Find the uploaded files

Uploaded files are in the code interpreter's working directory. Pass that folder (or the file paths) to the script. It processes every `.xlsx`, `.xlsm` and `.xls` it finds and skips files already named `*_cleaned.xlsx`. If no Excel file is found, ask the user to upload one. `.csv` is not supported; offer to convert it first.

## Step 2: Ask only what you cannot tell

Look at the files first (sheet names, column headers). Ask the user **before running** only when it changes the result:

- **Unique key** - "Which column(s) uniquely identify a record (e.g. Customer ID, Invoice No)?" Without one, only rows that are identical in every column count as duplicates. Skip the question if the headers make it obvious (a single `ID` column) and say which one you used.
- **Required fields** - "Which columns must never be blank?" Rows missing them are quarantined. If the user has no preference, run without `--required`.
- **Date format** - ask only if the data has dates like `03/04/2024` where day and month could swap. Default is month-first (US); use `--dayfirst` for DD/MM/YYYY.

If the user said "just clean it", don't ask - run with defaults, then report the open items from Step 4.

## Step 3: Run the script

```
python scripts/clean_excel.py <folder-or-files> [--out-dir DIR] [--key COL ...] [--required COL ...] [--min-filled 0.5] [--dayfirst] [--recursive]
```

```
# Defaults, everything in the working folder
python scripts/clean_excel.py .

# Customer list: unique by ID, email and name mandatory, UK-style dates
python scripts/clean_excel.py sales.xlsx --key "Customer ID" --required Email Name --dayfirst
```

Column names are matched case-insensitively. Each input produces `<original name>_cleaned.xlsx` next to it; if two inputs in the same run would share that name (e.g. `sales.xlsx` and `sales.xlsm`), the later one is written as `<name>_2_cleaned.xlsx`, so check the `OUTPUT:` lines for the real file names (the original is untouched; `.xlsm` macros are not carried over, output is always `.xlsx`).

### What it does

**Fixes automatically (safe, reversible, logged):**
- Trims and collapses whitespace; removes hidden characters (non-breaking spaces, zero-width, control characters).
- Turns placeholders (`N/A`, `null`, `nil`, `-`, `--`, `(blank)`) and Excel errors (`#N/A`, `#DIV/0!`, ...) into truly empty cells.
- Finds the real header row (skips title lines above the table); renames blank/duplicate headers; drops blank rows and empty unnamed columns.
- Converts text to real numbers (`$1,200.50`, `(200)`, `12%`) and real Excel dates (`yyyy-mm-dd`). Identifier-like columns (ID, zip, phone, SKU, account, code, anything with leading zeros) are kept as text so `00123` is not damaged.
- Lower-cases emails; makes inconsistent capitalisation consistent in category-style columns (`usa` / `USA`).

**Quarantines (moved to the `<sheet> Rejected` sheet with source row and reason, never silently deleted):**
- *Invalid*: unparseable or implausible dates, non-numeric values in a numeric column, malformed emails.
- *Incomplete*: missing a `--required` field, or fewer than `--min-filled` (default 50%) of the sheet's core columns filled.
- *Duplicate*: exact duplicate rows, and later repeats of a `--key` value. The first occurrence is kept.

**Flags only (kept as-is, listed in the Summary sheet and console):** extreme numeric outliers, columns mixing numbers and text, ambiguous dates, empty cells left in kept rows. It never fills blanks with guessed values.

## Step 4: Respond

1. Attach each `*_cleaned.xlsx` so the user can download it. Open sheets: **Summary**, the cleaned data, any **Rejected** sheet, **Change Log**.
2. Give a short summary per file: rows read, rows kept, rows quarantined by reason (invalid / incomplete / duplicate), and the main fixes (counts from the console output).
3. List every `REVIEW:` line from the output in plain language and ask the user to confirm or correct them (e.g. date order, mixed columns, which column is the key). Offer to re-run with different settings.
4. Be explicit about assumptions: which column was used as the key, which date order was assumed.
5. If the script prints `ERROR:` for a file (corrupt, password-protected, unsupported `.xls`), say which file and why, and ask the user to re-save it as an unprotected `.xlsx`. If the error names a single sheet, say that sheet was left out of the cleaned file while the others were cleaned. Don't try to repair anything by hand.

## Limits

- Formulas are read as their last saved (cached) value; the cleaned file contains values, not formulas. Formatting, charts, merged cells, pivot tables and macros are not preserved.
- Multi-line cells are collapsed to one line.
- It cannot verify factual accuracy (e.g. whether an address or price is *correct*), only that values are well-formed, consistent and complete. Say so if asked.
- Near-duplicates (`Jon Smith` vs `John Smith`) and fuzzy matching are not handled.
- Very large files (hundreds of thousands of rows) may be slow in the sandbox; tell the user if it times out and suggest splitting the file.
