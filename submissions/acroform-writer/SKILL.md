---
name: acroform-writer
description: >-
  Use this skill whenever the user wants values written INTO an existing PDF
  form that lives in the connected SharePoint knowledge source — filling out,
  completing, populating, or submitting a fillable PDF (application, intake
  sheet, contract, government form) from data they supply, a spreadsheet row,
  or the conversation. Triggers include "fill out the job application form",
  "complete the intake form for [person]", "populate our standard NDA
  template", and "make this ready to send / non-editable" (flatten). The
  source form is found via knowledge search — never ask the user to upload it.
  Do NOT use this for extracting or reading data OUT of a PDF (that's a
  different task), and do NOT use it on scanned/image-only PDFs that have no
  real fillable fields — those need OCR or manual overlay instead, which this
  skill explicitly detects and reports rather than silently failing.
---

Fill an existing PDF's real AcroForm fields with supplied data, and
optionally lock the result read-only so it's ready to send or file without
further edits. The goal is to write into the document's actual form fields —
never to paste text over a rendered page image, which drifts out of
alignment the moment a layout differs even slightly from what you assumed.

## Instructions
1. **Find the source PDF via knowledge search — do not ask the user to upload it.**
   The blank fillable form (e.g. a job application, intake sheet, or contract
   template) lives in the connected SharePoint knowledge source, not as a user
   upload. Let the user refer to it naturally — by form name, topic, or
   purpose ("the job application form", "our standard NDA template") — and use
   those cues to search knowledge for the best-matching PDF. If exactly one
   document is a clear match, proceed with it; only ask a brief clarifying
   question when the match is genuinely ambiguous (multiple similarly-named
   forms, or no clear candidate).
2. **Pull the FULL document, not retrieved chunks.** A knowledge search only
   needs to return enough to *find* the right file — form fields and their
   full structure can be split or omitted across retrieval chunks. Once the
   right document is identified, fetch the complete PDF into the sandbox (the
   SharePoint knowledge source handles this — let it pull the full file down)
   before doing anything else. Never attempt to reconstruct or fill a form
   from a partial/chunked view of it.
3. **Collect the values to fill.** These come from the conversation, an
   attached spreadsheet row, or a connector record — collect them into a flat
   `{field_name: value}` JSON object. Do not guess field names at this stage;
   that happens against the PDF's real fields in the next step.
4. **Always list fields first.** Run:
   ```
   python scripts/fill_form.py list <downloaded_form.pdf>
   ```
   This prints every real form field (name, type, current value, and — for
   checkboxes/radios/dropdowns — the valid states or options). Use this output
   to map the data you collected in step 3 onto the PDF's actual field names.
   **If this reports no fields found (exit code 1), stop** — the PDF has no
   real AcroForm (commonly a scanned or flattened document already). Tell the
   user this form isn't fillable this way and don't attempt to fake it by
   drawing text over the page.
5. **Match data to fields carefully.**
   - Checkboxes/radio buttons must be set to one of the exact `states` values
     reported in step 4 (typically `/Yes` and `/Off`), not `true`/`false`.
   - Dropdown/choice fields must use one of the reported `options` values
     verbatim.
   - If a value you were given doesn't obviously map to any listed field, do
     not force it into the closest-sounding one — leave it out and flag it to
     the user rather than guessing.
6. **Fill (and lock read-only, if the result should be final):**
   ```
   python scripts/fill_form.py fill <downloaded_form.pdf> <data.json> <output.pdf> [--flatten]
   ```
   Add `--flatten` whenever the output is meant to be a finished, submission-
   ready document (the common case) so the fields are marked read-only and
   most viewers treat it as no longer editable. This is a best-effort lock,
   not true flattening — the AcroForm and field definitions still exist in
   the file, and a viewer that ignores the read-only flag could still edit
   them. Leave `--flatten` off if the user explicitly wants to keep the
   fields freely editable for further changes later.
7. **Check the JSON result the script prints.** It reports `fields_filled` and
   any `unmatched_fields` — data keys that didn't correspond to a real field.
   Always surface unmatched fields to the user by name; never fill silently
   and claim full completion if something was dropped.
8. **Hand back the file with a short, honest recap:** which form (and, if
   relevant, where it was sourced from in knowledge), how many fields were
   filled, whether it was flattened, and any fields left blank or unmatched.
   Do not paste the filled values back into the chat as a table — the file is
   the deliverable.

## Guardrails
- Never ask the user to upload the blank form — find it via knowledge search
  first. Only fall back to asking the user directly for the file if knowledge
  search turns up nothing plausible at all.
- Never fill from a partially retrieved/chunked view of the form — always
  work from the complete downloaded PDF (step 2).
- Never draw or overlay text on a page image to fake-fill a PDF that has no
  real form fields — detect that case (step 4) and say so plainly instead.
- Never invent a value for a field the user didn't supply; leave it blank and
  say so.
- Never force a supplied value into a checkbox/radio/dropdown field using
  anything other than that field's own reported states/options.
- Don't silently drop unmatched data — always report it.
- `--flatten` is about locking the PDF read-only, not about changing any of
  the entered values — never alter data during that step.

## Tone
Precise and matter-of-fact. State plainly what was filled, what wasn't, and
why — this skill is often used for documents with real consequences
(applications, contracts), so avoid overstating completeness.