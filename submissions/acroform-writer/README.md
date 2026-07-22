# AcroForm Writer

Turn an existing fillable PDF (application, intake sheet, contract, gov form)
into a completed document by writing values straight into its real AcroForm
fields — then flatten it into a normal, non-editable PDF ready to send.

Unlike overlay-based approaches that paste text at fixed coordinates (and
break the moment a layout shifts slightly), this skill works from the PDF's
actual form field definitions, so it stays accurate regardless of page
layout.


## How it works
1. `scripts/fill_form.py list <input.pdf>` — inspect every real form field
   (name, type, current value, checkbox/dropdown states) so the agent knows
   exactly what's fillable.
2. `scripts/fill_form.py fill <input.pdf> <data.json> <output.pdf> --flatten`
   — write the values in and bake them into a static, non-editable PDF.

Built and tested against a sample fillable PDF (`assets/sample_intake_form.pdf`)
covering text fields and a checkbox, including the unmatched-field warning
path and the "no AcroForm found" error path for non-fillable PDFs.

## Requirements
`pypdf` only — already present in the Copilot Studio Python
sandbox. No network calls, no external services.
