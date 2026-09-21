---
name: word-document-generator-from-template
description: Fills a pre-authored Word template that already uses {{placeholder}} tokens (uploaded, or retrieved from SharePoint, OneDrive, or another connector) using a deterministic fill engine plus user input, approved knowledge sources, and prior tool or connector results. Use when a user asks to fill, complete, or compile a document from such a template. Do not use when the user supplies a blank or finished Word file without this engine's placeholders, or when they want the agent to invent layout or fill scripts.
---
# Fill a Word Template

## Purpose

Fill a complete Microsoft Word document of **any type the template defines**
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

## Positioning

Copilot Studio skills run in the GitHub Copilot harness. This skill is still a
**deterministic fill**: a pre-authored Word template plus the bundled
inspect/fill/validate engine. The model's job is to gather approved facts and
map them onto that template's contract — not to design layout, author the
template, or write new OOXML or python-docx scripts.

The harness sandbox and reasoning loop are not the main value during artifact
creation. Do not treat loading this skill as a license to improvise document
generation. If the supplied file is not a skill template, stop — see
**Template handling**.

## Required inputs

Before generating the document, identify:

- the placeholder Word template to use (a `.docx` already authored with this engine's `{{placeholder}}` grammar), and where it comes from (upload, SharePoint, OneDrive, or another location);
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

1. Derive a **safe stem** (filename without extension) from the requested output
   filename: keep only `[A-Za-z0-9_-]` in the stem, replace any other character
   runs with `_`, and reject `..` and path separators.  Use this stem throughout
   as `<stem>` — append `.docx` only when forming Word filenames and `.json` for
   data files.

   Intermediate working files go under `/app/workspace/` to avoid exposing
   source data as Copilot Studio attachments.  Only the final deliverable is
   written to `/app/created/`:

   ```text
   /app/workspace/<stem>-template.docx    ← local copy of the runtime template
   /app/workspace/<stem>-manifest.json    ← inspection manifest
   /app/workspace/<stem>-data.json        ← serialised fill data
   /app/workspace/<stem>-fill-summary.json
   /app/workspace/<stem>-validation.json
   /app/created/<stem>.docx               ← completed document (the deliverable)
   ```

2. Locate the runtime `.docx` template and **copy it to
   `/app/workspace/<stem>-template.docx`** before any other step:
   - **Uploaded file**: use the file API (for example, Python
     `shutil.copy2(upload_path, "/app/workspace/<stem>-template.docx")`); do
     not interpolate the user-supplied filename into a shell command.
   - **SharePoint / OneDrive / connector**: retrieve the item directly to that path.

   Pass only `/app/workspace/<stem>-template.docx` to the engine; never use the
   upload path directly.  Stop with the message under **Template handling** if
   the template cannot be located or copied.

3. Inspect the local copy before writing content:

   ```bash
   python scripts/docx_template.py inspect /app/workspace/<stem>-template.docx \
     --output /app/workspace/<stem>-manifest.json
   ```

   Read the manifest's exact scalar placeholders, repeating arrays, parts, and
   live Word fields. If inspection rejects the template (including Strict
   OOXML), report the error; do not guess at its schema and do not write
   replacement scripts.

   If `scalar_placeholders`, `repeating_arrays`, and `conditional_paths` are
   all empty, the file is not a skill template. Stop using the message under
   **Template handling**.

4. Retrieve relevant information from approved knowledge, user files, and prior
   tool/connector results already in the conversation. Prefer connector-returned
   records, dates, owners, and IDs over restating them from memory.

5. Generate long documents section by section. Build a JSON object whose paths
   exactly match the manifest. Use arrays for repeating table rows. Use
   `Not specified in approved sources` for unsupported facts.

6. Validate the JSON conceptually: all required template fields are represented,
   claims are grounded, and each array item supplies the expected row fields.
   Then **write it to disk** so the fill command can read it:

   ```python
   from pathlib import Path
   import json
   Path("/app/workspace/<stem>-data.json").write_text(
       json.dumps(data, indent=2, ensure_ascii=False) + "\n",
       encoding="utf-8",
   )
   ```

7. Fill a **new** file with the deterministic engine:

   ```bash
   python scripts/docx_template.py fill \
     /app/workspace/<stem>-template.docx \
     /app/workspace/<stem>-data.json \
     /app/created/<stem>.docx \
     --summary /app/workspace/<stem>-fill-summary.json
   ```

   Never set the output path to the template path.

8. Validate package integrity, unresolved tokens, and live Word fields:

   ```bash
   python scripts/docx_template.py validate \
     /app/created/<stem>.docx \
     --template /app/workspace/<stem>-template.docx \
     --output /app/workspace/<stem>-validation.json
   ```

   Do not return a DOCX unless both commands succeed.

9. Return `/app/created/<stem>.docx` as the completed document plus a short
   generation summary: output filename, document type, sources used,
   filled/defaulted fields, repeated-row counts, and validation status.

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

A Word template (`.docx`) **already authored with this engine's
`{{placeholder}}` grammar** is a **prerequisite**. A blank Word file, a
finished prose document, or any `.docx` without inspectable placeholders is
not a valid input. The expected input style is
[`assets/sample-template.docx`](assets/sample-template.docx); the grammar is
in [`references/placeholder-contract.md`](references/placeholder-contract.md).

The template is supplied at runtime from one of:

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

Stop document generation — and **do not** generate replacement scripts,
`python-docx` writers, or ad-hoc run replacement — when any of the following
is true:

- the required template cannot be found or retrieved;
- inspect, fill, or validate raises (including Strict OOXML);
- inspect succeeds but `scalar_placeholders`, `repeating_arrays`, and
  `conditional_paths` are all empty.

Report one of:

'The required Word template was not supplied or could not be accessed.'

'The attached Word file is not a skill template. Supply a .docx already authored with {{placeholder}} tokens in this engine's grammar (see assets/sample-template.docx). Do not use a blank or finished document.'

## Template contract

Before generating fill JSON, always run `inspect` and read the returned
manifest. Every key in your JSON must match a path reported by the manifest —
do not invent key names. Conditional branches (`{{#if}}` / `{{#switch}}`) and
repeating arrays (`{{items[].field}}`) are also surfaced by `inspect`.

For the full grammar, supported scope, and limits see
[`references/placeholder-contract.md`](references/placeholder-contract.md).

## Structured JSON

Build the fill JSON exclusively from the inspection manifest:

- Use every `scalar_placeholders` path as a top-level or nested key.
- Use every `repeating_arrays` key as a JSON array of objects, each containing the listed field names.
- Use every `conditional_paths` key as a boolean or comparable scalar that drives the `{{#if}}` / `{{#switch}}` logic in the template.
- Do **not** add keys that are absent from the manifest; the engine will ignore them and the discrepancy will confuse downstream reviewers.

Example — given this manifest excerpt:

```json
{
  "scalar_placeholders": ["document.title", "document.owner"],
  "repeating_arrays": { "findings": ["finding", "impact"] },
  "conditional_paths": ["employee.type"]
}
```

Produce:

```json
{
  "document": { "title": "...", "owner": "..." },
  "findings": [
    { "finding": "...", "impact": "..." }
  ],
  "employee": { "type": "permanent" }
}
```

Field names and nesting depth come entirely from the manifest, not from
assumptions about the document structure.

## Requirements

The engine uses Python's standard library plus `lxml`, preinstalled in the
Copilot Studio sandbox. No network service or `pip install` is needed in
Copilot Studio.

## Quality and safety

The generated document is a draft until reviewed and approved. If a statement cannot be supported by approved knowledge, a user-supplied file, or a prior tool/connector result, do not present it as fact. Mark it for human review.
