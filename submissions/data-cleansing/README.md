# Data Cleansing (Excel)

Cleans Excel files that users upload in the chat. The agent runs a bundled Python script (pandas + openpyxl) and returns a `<name>_cleaned.xlsx` for every file. Originals are never modified.

## Before you start

- Turn **code interpreter** on for the agent (Python with pandas and openpyxl, which the Copilot Studio sandbox provides - the skill does not install anything).
- Turn on **file upload** in chat.
- Supported inputs: `.xlsx`, `.xlsm`, `.xls` (`.xls` needs `xlrd` in the sandbox, otherwise the agent asks for a re-save as `.xlsx`). Not supported: CSV.

## How to use it

Upload one or more Excel files and ask, for example:

- "Clean this file."
- "Find and remove duplicates - Customer ID is the unique key."
- "Clean these files; Email and Name must never be blank; dates are DD/MM/YYYY."

The agent only asks questions that change the result (unique key, required columns, ambiguous date order).

## What you get back

A workbook with four kinds of sheet:

| Sheet | Contents |
| --- | --- |
| Summary | Rows read / kept / quarantined per sheet, plus items that need a human decision |
| *your sheet name* | The cleaned data |
| *sheet* Rejected | Quarantined rows with their original values, source row number and reason |
| Change Log | Every automatic fix with a count and an example |

**Fixed automatically:** whitespace and hidden characters, placeholders (`N/A`, `-`, `#N/A`) to empty, blank rows/columns, text to real numbers (`$1,200.50`, `(200)`, `12%`) and real dates (timezone-aware timestamps are stored as UTC without a timezone), lower-cased emails, consistent capitalisation in category columns. ID-like columns (IDs, zip, phone, SKU) and any value with 16+ digits stay as text so leading zeros and long reference numbers survive.

**Quarantined, never silently deleted:** invalid dates/numbers/emails, rows missing required fields or mostly empty, exact duplicates and repeated key values (a blank key is never counted as a duplicate). Title or note rows above the header are moved to the Rejected sheet too; if more than one row above the table holds several values (so it could be a header with empty cells), that sheet is left out and the agent asks you which row is the header, then re-runs with it. Other sheets in the file are still cleaned.

**Flagged only:** extreme outliers, columns mixing numbers and text, ambiguous dates, blanks left in place. Missing values are never guessed.

## Good to know

- Formulas become their last saved values; formatting, charts, merged cells, pivots and macros are not preserved.
- It checks that data is well-formed, consistent and complete, not that it is factually correct.
- Near-duplicates ("Jon" vs "John") are not detected.
- Very large files may time out in the sandbox; split them if so.

## Try it

Build a small workbook with a title row above the headers, a repeated ID, an invalid email, a text date like `not a date`, `N/A` placeholders and amounts like `$1,200.50`, then check each lands in the right sheet.
