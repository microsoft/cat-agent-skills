# AcroForm Writer

Turn an existing fillable PDF (application, intake sheet, contract, gov form)
into a completed document by writing values straight into its real AcroForm
fields — then, optionally, lock the fields read-only so it's ready to send.

Unlike overlay-based approaches that paste text at fixed coordinates (and
break the moment a layout shifts slightly), this skill works from the PDF's
actual form field definitions, so it stays accurate regardless of page
layout.


## How it works
1. `scripts/fill_form.py list <input.pdf>` — inspect every real form field
   (name, type, current value, checkbox/dropdown states) so the agent knows
   exactly what's fillable.
2. `scripts/fill_form.py fill <input.pdf> <data.json> <output.pdf> --flatten`
   — write the values in and, with `--flatten`, mark every field read-only
   so it behaves as non-editable in standard viewers. This is a best-effort
   lock (sets `/NeedAppearances` and the widget read-only flag) rather than
   true flattening — the AcroForm and field definitions remain in the file.

Built and tested against a sample fillable PDF (`assets/sample_intake_form.pdf`)
covering text fields and a checkbox, including the unmatched-field warning
path and the "no AcroForm found" error path for non-fillable PDFs.

## Bundled files
- `scripts/fill_form.py` — pure `pypdf` (already available in the agent
  sandbox), no external services. Two modes:
  - `list <input.pdf>` — dumps all AcroForm fields as JSON (name, type,
    current value, checkbox/radio states, dropdown options). Exits 1 with a
    clear message if the PDF has no fillable fields at all.
  - `fill <input.pdf> <data.json> <output.pdf> [--flatten]` — writes the
    supplied values into the matching fields and, with `--flatten`, sets
    `/NeedAppearances` and marks every field's widget read-only so the
    result behaves as non-editable in standard viewers (best-effort lock,
    not true flattening).
- `assets/sample_intake_form.pdf` — a tiny fillable sample (name, email,
  checkbox) for smoke-testing the flow end-to-end before trying it on a real
  document.

## Requirements
`pypdf` only — already present in the Copilot Studio Python
sandbox. No network calls, no external services.
