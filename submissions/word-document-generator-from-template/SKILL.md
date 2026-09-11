---
name: word-document-generator-from-template
description: Generates a complete Word document from a Word template supplied at runtime (uploaded, or retrieved from SharePoint, OneDrive, or another connector) plus user input, approved knowledge sources, and prior tool or connector results. Use when a user asks to create, draft, or compile any document from a template — policy, procedure, report, paper, briefing, SOP, or similar.
---
# Word Document Generator from Template

## Purpose

Generate a complete Microsoft Word document of **any type the template defines**
(policy, procedure, report, paper, briefing, SOP, statement of work, or similar) using:

- a Word template supplied at runtime (uploaded by the user, or retrieved from SharePoint, OneDrive, or another connector);
- information provided by the user;
- approved agent knowledge sources;
- files supplied with the request; and
- information retrieved from prior tool or connector calls in the same conversation (for example Dataverse, SharePoint, CRM, or any Copilot Studio action).

The runtime template controls document type, structure, formatting, headings,
tables, headers, footers, and branding. Adapt JSON keys to **that** template —
do not assume a fixed outline. Use the bundled deterministic engine for DOCX
inspection, filling, and validation; do not implement ad-hoc run replacement.

## Required inputs

Before generating the document, identify:

- the Word template to use, and where it comes from (upload, SharePoint, OneDrive, or another location);
- the document type, title, and purpose;
- the intended audience;
- any user-provided requirements;
- the approved knowledge sources to use;
- any relevant results from prior tool or connector calls; and
- the required output filename.

If required information is unavailable, use:

`Not specified in approved sources`

Do not invent facts, dates, owners, approvals, obligations, or organizational information.

## Instructions

1. From the skill's root directory (the folder that contains `scripts/`, `assets/`, and `references/`), locate the runtime `.docx` template. Use the uploaded file, or retrieve the
   user-identified SharePoint / OneDrive / connector item into the working
   directory. Stop with the message under **Template handling** if unavailable.
2. Inspect it before writing content:

   ```bash
   python scripts/docx_template.py inspect template.docx --output manifest.json
   ```

   Read the manifest's exact scalar placeholders, repeating arrays, parts, and
   live Word fields. If inspection rejects the template, report the error; do
   not guess at its schema.
3. Retrieve relevant information from approved knowledge, user files, and prior
   tool/connector results already in the conversation. Prefer connector-returned
   records, dates, owners, and IDs over restating them from memory.
4. Generate long documents section by section. Build a JSON object whose paths
   exactly match the manifest. Use arrays for repeating table rows. Use
   `Not specified in approved sources` for unsupported facts.
5. Validate the JSON conceptually: all required template fields are represented,
   claims are grounded, and each array item supplies the expected row fields.
6. Fill a **new** file with the deterministic engine:

   ```bash
   python scripts/docx_template.py fill template.docx data.json output.docx \
     --summary fill-summary.json
   ```

   Never set `output.docx` to the template path.
7. Validate package integrity, unresolved tokens, and live Word fields:

   ```bash
   python scripts/docx_template.py validate output.docx \
     --template template.docx --output validation.json
   ```

   Do not return a DOCX unless both commands succeed.
8. Return the completed DOCX plus a short generation summary: output filename,
   document type, sources used, filled/defaulted fields, repeated-row counts,
   and validation status.

## Generation rules

- Follow the runtime template's outline. JSON keys must match the inspection
  manifest, not a hard-coded schema.
- Use only information from approved knowledge sources, user-supplied files, or prior tool/connector results. Do not invent facts that those sources do not contain.
- Treat prior tool and connector outputs as approved sources. Record the tool or connector name in `source_ids` (for example `Dataverse:accounts`, `SharePoint:policy-library`).
- Generate long documents section by section rather than in one response.
- Keep the structured JSON as the intermediate source of truth.
- Use clear, professional, organization-appropriate language for the stated audience.
- Preserve mandatory wording found in approved sources.
- Do not treat the template file as a knowledge source unless instructed.
- Do not add new sections unless required to complete the template.
- Do not remove sections from the template without an explicit instruction.
- Record the sources used for each major section when source information is available.
- Do not replace runs manually or clear footer/header paragraphs. The script
  handles split-run tokens and preserves PAGE, NUMPAGES, TOC, REF, and other
  live Word fields.

## Template handling

A Word template (`.docx`) is a **prerequisite**. It is supplied at runtime from one of:

- a file **uploaded** with the request;
- **SharePoint** (document library, folder, or site);
- **OneDrive**; or
- another connector or prior tool call that returns a Word file.

Resolve the template in this order:

1. Use the template the user named (filename, SharePoint/OneDrive path, or library item).
2. If it is already in the runtime working directory, use that `.docx`.
3. If it is not local, retrieve it from SharePoint, OneDrive, or the identified connector.
4. If more than one Word file is available, select the one identified in the user request.

Never overwrite the original template in SharePoint, OneDrive, or local storage. Always save a **new** DOCX.

If the required template cannot be found or retrieved, stop document generation and report:

'The required Word template was not supplied or could not be accessed.'

## Template contract

Use `{{path.to.value}}` for scalar text and `{{items[].field}}` in one sample
table row for repetition. Tokens may be split across Word runs; the engine
matches their visible paragraph text. It fills the main document, tables,
headers, and footers while preserving live Word fields.

Read [`references/placeholder-contract.md`](references/placeholder-contract.md)
for the exact grammar, supported scope, limits, and troubleshooting.

## Structured JSON

Create JSON that reflects the **runtime template**. Use:

- `document` — title, type, owner, version, status, audience, and any other metadata fields on the cover or control table;
- `sections` — one object per Heading 1 / Heading 2, keyed by a slug of that heading;
- `items` (or a name taken from the table, e.g. `leave_types`, `findings`, `steps`) — arrays for repeating tables or content blocks;
- `sources` — identifiers for knowledge, files, and connectors.

Example shape (field names change to match the template):

```json
{
  "document": {
    "title": "Quarterly Operations Report",
    "type": "Report",
    "owner": "Operations",
    "version": "1.0",
    "status": "Draft",
    "audience": "Leadership team"
  },
  "sections": {
    "executive_summary": "Generated section content",
    "purpose": "Generated section content"
  },
  "findings": [
    {
      "finding": "Generated finding",
      "impact": "Generated impact",
      "owner": "Action owner"
    }
  ],
  "sources": [
    {
      "source_id": "SRC-001",
      "title": "Approved source",
      "type": "knowledge | file | connector"
    }
  ]
}
```

A Leave Policy template might use `leave_types`; a procedure might use `steps`;
a report might use `findings` or connector rows. Always use the array names
reported by template inspection.

## Requirements

The engine uses Python's standard library plus `lxml`, preinstalled in the
Copilot Studio sandbox. The sample-template builder and tests additionally use
preinstalled `python-docx` and Pillow. No network service or `pip install` is
needed in Copilot Studio.

## Quality and safety

The generated document is a draft until reviewed and approved. If a statement cannot be supported by approved knowledge, a user-supplied file, or a prior tool/connector result, do not present it as fact. Mark it for human review.
