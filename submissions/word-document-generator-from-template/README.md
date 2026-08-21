# Word Document Generator from Template

Fill a Microsoft Word template supplied at runtime — **uploaded**, or retrieved
from **SharePoint**, **OneDrive**, or another connector — using **user input**,
approved agent **knowledge sources**, and **results from prior tool or connector
calls**. Works for any document the template defines: **policy, procedure,
report, paper, briefing, SOP, statement of work**, or similar.

The template keeps control of structure, branding, styles, tables, headers, and
footers. A deterministic OOXML engine handles split Word runs, repeating table
rows, and validation while preserving live PAGE / NUMPAGES fields. The skill
writes a **new** DOCX — it never overwrites the original.

## When to use it

| Document kind | Typical template |
| --- | --- |
| Policy | Corporate policy shell (purpose, scope, rules, related docs) |
| Procedure / SOP | Numbered steps, roles, inputs/outputs |
| Report / briefing | Summary, findings table, recommendations |
| Paper | Title, abstract, body headings, references |
| Status pack | Narrative plus rows from Dataverse, SharePoint, or another connector |

Ask the agent to create, draft, or compile the document from that template.

## Before you start

| Input | Why it matters |
| --- | --- |
| Word template (`.docx`) — **required** | Controls layout, placeholders, and branding. May be **uploaded**, or retrieved from **SharePoint**, **OneDrive**, or another connector |
| Document type, title, and purpose | Sets what is being drafted |
| Intended audience | Tones the language |
| Requirements | Anything the template must cover |
| Approved knowledge sources | Grounded content |
| Prior tool / connector results | Records, lists, and fields already retrieved this conversation |
| Output filename | Name of the new DOCX |

Approved sources include knowledge, uploaded files, **and** data returned by
upstream tools or connectors. If a required fact is not in those sources, the
agent writes `Not specified in approved sources` instead of inventing it.

## Ideal Word template structure

The same pattern works for every document type. Use **Word styles** (Heading 1,
Heading 2, Normal) and deterministic `{{placeholders}}` — not finished body
text. The engine supports:

- scalar paths: `{{document.title}}`, `{{sections.purpose}}`;
- repeating rows: `{{findings[].finding}}`, `{{findings[].owner}}`;
- placeholders that Word splits across multiple formatting runs;
- body, table, header, and footer text.

**Do**

- Put branding, page numbers, and classification in the **header / footer**.
- Use **Heading 1** for every major section the finished document must keep.
- Use a **one-row sample table** for anything that repeats (steps, findings, leave types, owners), with the array name followed by `[]`.
- Name placeholders after the field: `{{document.title}}`, `{{sections.<heading>}}`.
- Keep body cells short: `{{sections.purpose}}` or `[Insert from approved sources]`.

**Don’t**

- Bury finished wording in the template (it is not a knowledge source).
- Use floating text boxes or images that hide placeholders.
- Skip headings and rely on bold paragraphs — the agent may miss sections.

### Generic skeleton

**Header:** `Organisation | Classification | {{document.title}}`

**Title (Heading 1):** `{{document.title}}`

**Document control (Heading 2)**

| Field | Placeholder |
| --- | --- |
| Type | `{{document.type}}` |
| Owner | `{{document.owner}}` |
| Version | `{{document.version}}` |
| Status | `{{document.status}}` |
| Audience | `{{document.audience}}` |

**Body** — one Heading 1 per section, placeholder underneath. Name sections
after the template, for example:

| Kind | Typical Heading 1s |
| --- | --- |
| Policy | Purpose, Scope, Policy statements, Responsibilities, Related documents |
| Procedure | Purpose, Scope, Roles, Procedure steps, Exceptions |
| Report | Executive summary, Findings, Analysis, Recommendations |
| Paper | Abstract, Introduction, Discussion, Conclusion, References |

`{{sections.purpose}}`, `{{sections.scope}}`, `{{sections.findings}}`, and so on.

**Repeating table** — keep the header row; leave **one sample data row** to clone:

| Column A | Column B | Column C |
| --- | --- | --- |
| `{{items[].col_a}}` | `{{items[].col_b}}` | `{{items[].col_c}}` |

Rename columns to match the document (`Step` / `Owner` / `System`, or
`Finding` / `Impact` / `Action`, or `Leave type` / `Entitlement` / `Owner`).
Use one array per sample row.

**Footer:** `{{document.version}} | Page X of Y | {{document.status}}`

Insert Page X of Y with Word's live PAGE and NUMPAGES fields, not typed numbers.
The engine changes only the placeholders and verifies those field instructions
remain intact.

The agent fills placeholders from approved sources, **repeats the sample row**
for each JSON array item, and leaves gaps as `Not specified in approved
sources`. Styles, header, footer, and table formatting stay as in the template.

### Example mapping — Leave Policy

A leave policy is only one use of the same skeleton: Heading 1s become Purpose,
Scope, Leave types, Responsibilities; the repeating table columns become
`{{leave_types[].leave_type}}`, `{{leave_types[].entitlement}}`,
`{{leave_types[].owner}}`, `{{leave_types[].evidence}}`.

## How it works

1. Finds the Word template at runtime — from the upload, SharePoint, OneDrive, or the named connector.
2. Runs deterministic inspection to discover exact placeholders, repeating arrays, and Word fields.
3. Pulls facts from approved knowledge, user-supplied files, and prior tool or connector results.
4. Builds JSON that matches **this** template's fields.
5. Fills a new DOCX with split-run and repeating-row support.
6. Validates package integrity, unresolved placeholders, and live Word fields.
7. Returns the new DOCX and a machine-generated summary.

## Quick test

The bundled report template intentionally contains split-run placeholders, a
repeating findings row, branding, two sections, and live PAGE / NUMPAGES fields.

```bash
# 1. Discover the template contract
python scripts/docx_template.py inspect assets/sample-template.docx \
  --output sample-manifest.json

# 2. Fill a new file
python scripts/docx_template.py fill \
  assets/sample-template.docx assets/sample-data.json sample-output.docx \
  --summary sample-summary.json

# 3. Verify there are no raw tokens and live fields survived
python scripts/docx_template.py validate sample-output.docx \
  --template assets/sample-template.docx --output sample-validation.json
```

Expected: each command exits `0`, the findings table has three data rows, no
`{{...}}` remains, and validation reports
`"field_signature_preserved": true`.

For the full grammar and limits, see
[`references/placeholder-contract.md`](references/placeholder-contract.md).

### Bundled files

| File | Purpose |
| --- | --- |
| `scripts/docx_template.py` | Production inspect / fill / validate engine |
| `assets/sample-template.docx` | Realistic report template with split runs and live fields |
| `assets/sample-data.json` | Template-shaped example data |
| `assets/sample-template.manifest.json` | Expected inspection result |
| `references/placeholder-contract.md` | Exact grammar, supported scope, and limits |
| `scripts/test_docx_template.py` | Automated regression suite |
| `scripts/build_sample_template.py` | Rebuild the sample template |

## Example requests

> Use the Leave Policy template in SharePoint (`Policies/Templates/Leave-Policy.docx`).
> Draft version 0.1 for internal staff from approved HR knowledge.
> Save as `Leave-Policy-v0.1.docx`.

> Fill the incident-response **procedure** template in OneDrive.
> Use the approved ops playbook for the steps. Save as `IR-Procedure-v2.docx`.

> Get this quarter's accounts from Dataverse, then fill the **status report**
> template. Connector rows go in the findings table; knowledge base for the narrative.
> Save as `Q3-Account-Status.docx`.

The agent returns the completed Word file plus a summary of what was filled,
what was missing, and which sources were used — including connector names.

## Good to know

- Output is a **draft** until a human reviews and approves it.
- Connector and tool results from earlier in the conversation are valid sources; the agent should not re-fetch them unless they are missing.
- Unsupported statements are marked for review, not presented as fact.
- The template is a prerequisite. Attach it, or point the agent at SharePoint, OneDrive, or another connector that can fetch the `.docx`.
- The template is not treated as a knowledge source unless you say so.
- Sections are not added or removed unless you explicitly ask.
- The original template in SharePoint, OneDrive, or the upload is never overwritten.
- Supported replacement content is plain text (including line breaks). Rich
  HTML/Markdown, nested repeating arrays, and placeholders spanning paragraphs
  are intentionally rejected or out of scope.
- Filling fails loudly on malformed tokens, invalid JSON shapes, remaining
  placeholders, corrupt DOCX packages, or changed Word field instructions.
- If no `.docx` template is available, generation stops with:
  `The required Word template was not supplied or could not be accessed.`
