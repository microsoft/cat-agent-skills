# PDF Form Extractor — Script Bundle

Helper scripts used by the **PDF Form Extractor** Copilot Studio skill.

## Contents
- `extract_fields.py` — normalizes extracted fields (dates, phones, checkboxes)
  and validates them against a JSON Schema, flagging low-confidence values.
- `schema.example.json` — a sample expected-field schema to adapt.

## Requirements
- Python 3.9+ (standard library only).

## Usage
```bash
python extract_fields.py fields.json schema.example.json
```

`fields.json` is the raw extraction the skill produces from a PDF form. The
script prints normalized fields plus any validation problems.
