# Fill a Word Template

Fill a Microsoft Word template you already have — **uploaded**, or retrieved
from **SharePoint**, **OneDrive**, or another connector — using **user input**,
approved agent **knowledge sources**, and **results from prior tool or connector
calls**. Works for any document the template defines: **policy, procedure,
report, paper, briefing, SOP, statement of work**, or similar.

This is a **deterministic fill**, not a blank-page author. You bring a prepared
template with placeholders; a fill engine writes the values in and keeps your
structure, branding, styles, tables, headers, and footers. It handles split
Word runs, repeating table rows, conditional blocks, and validation while
preserving live PAGE / NUMPAGES fields. The skill writes a **new** Word file —
it never overwrites the original.

**You do not need this skill** if you do not already have a pre-processed Word
template — a `.docx` with this engine's `{{placeholder}}` tokens, matching
[`assets/sample-template.docx`](assets/sample-template.docx). Open that sample
in Word first. If your file does not look like it (blank page, finished prose,
or no `{{...}}` tokens), skip this skill and use another document flow.

## Where this fits

Copilot Studio skills load in the **GitHub Copilot harness**. This skill does
**not** use that harness as an open-ended document author. The Word template
(placeholders, styles, branding) is the contract; the bundled engine inspects,
fills, and validates it. The model's job is to gather approved facts and map
them onto that contract.

Most of the sandbox and reasoning-loop benefit is unused during artifact
creation. Use this skill when you already have that pre-processed template
and the value is **high-fidelity fill without building Power Automate +
prompts**. If you do not have a placeholder template, **do not use this
skill** — prefer a workflow, standard-harness path, or another document
skill instead.

## When to use it

| Document kind | Typical template |
| --- | --- |
| Policy | Corporate policy shell (purpose, scope, rules, related docs) |
| Procedure / SOP | Numbered steps, roles, inputs/outputs |
| Report / briefing | Summary, findings table, recommendations |
| Paper | Title, abstract, body headings, references |
| Status pack | Narrative plus rows from Dataverse, SharePoint, or another connector |

Ask the agent to fill that template — not to invent a Word file from a blank page.

## Before you start

**Look at the sample first.** Open
[`assets/sample-template.docx`](assets/sample-template.docx) in Word. That
file is the expected input style: Heading styles, branding, and
`{{placeholders}}` in the body, tables, header, and footer. Your template
must follow the same pattern. The full grammar is in
[`references/placeholder-contract.md`](references/placeholder-contract.md).

If you do not have a pre-processed template like that sample, **you do not
need this skill** — and the agent should not invent one or write fill
scripts for a blank document.

| Input | Why it matters |
| --- | --- |
| Placeholder Word template (`.docx`) — **required** | Controls layout, placeholders, and branding. Must contain inspectable `{{...}}` tokens. May be **uploaded**, or retrieved from **SharePoint**, **OneDrive**, or another connector |
| Document type, title, and purpose | Sets what is being drafted |
| Intended audience | Tones the language |
| Requirements | Anything the template must cover |
| Approved knowledge sources | Grounded content |
| Prior tool / connector results | Records, lists, and fields already retrieved this conversation |
| Output filename | Name of the new DOCX |

Approved sources include knowledge, uploaded files, **and** data returned by
upstream tools or connectors. If a required fact is not in those sources, the
agent writes `Not specified in approved sources` instead of inventing it.

**Not a valid template** — compare your file with
[`assets/sample-template.docx`](assets/sample-template.docx) before you start:

- a blank or nearly empty Word file
- a finished document with no `{{...}}` tokens
- a file whose placeholders do not match
  [`references/placeholder-contract.md`](references/placeholder-contract.md)

If the agent is given one of those, it stops and asks for a real skill
template. It does not invent fill scripts or rebuild the document from
scratch. You do not need this skill until your template looks like the
sample.

## Ideal Word template structure

The same pattern works for every document type. Use **Word styles** (Heading 1,
Heading 2, Normal) and deterministic `{{placeholders}}` — not finished body
text. The engine supports:

- scalar paths: `{{document.title}}`, `{{sections.purpose}}`;
- repeating rows: `{{findings[].finding}}`, `{{findings[].owner}}`;
- conditional blocks: `{{#if employee.type == "permanent"}}` … `{{/if}}` and `{{#switch}}` / `{{#case}}`;
- `&&` (AND) and `||` (OR) in conditions: `{{#if a.b == "x" && c.d}}`;
- placeholders that Word splits across multiple formatting runs;
- body, table, header, and footer text.

**Do**

- Put branding, page numbers, and classification in the **header / footer**.
- Use **Heading 1** for every major section the finished document must keep.
- Use a **one-row sample table** for anything that repeats (steps, findings, leave types, owners), with the array name followed by `[]`.
- Name placeholders after the field: `{{document.title}}`, `{{sections.section_name}}`.
- Keep body cells short: `{{sections.purpose}}` or `[Insert from approved sources]`.
- Use `{{#if path == "value"}}` … `{{/if}}` (each marker in its own paragraph) to include sections only for certain employee types, statuses, or any other data-driven condition.
- Use `{{#if a && b}}` / `{{#if a || b}}` for compound conditions; `{{#switch path}}` / `{{#case "value"}}` … `{{/switch}}` for multi-branch logic.

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
2. Runs deterministic inspection to discover exact placeholders, repeating arrays, conditional paths, and Word fields.
3. Pulls facts from approved knowledge, user-supplied files, and prior tool or connector results.
4. Builds JSON that matches **this** template's fields.
5. Evaluates conditional blocks, fills a new DOCX with split-run and repeating-row support.
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

`scripts/build_sample_template.py` and `scripts/test_docx_template.py` additionally require `python-docx` and Pillow (preinstalled in the dev environment); no extra installs are needed to run the tests.

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
- **Do not use this skill** unless you already have a pre-processed
  `.docx` like [`assets/sample-template.docx`](assets/sample-template.docx).
  Open that sample and compare before you attach anything. A blank or
  finished Word document is not enough; attach a real placeholder template,
  or point the agent at SharePoint, OneDrive, or another connector that can
  fetch that file.
- The template is not treated as a knowledge source unless you say so.
- Sections are not added or removed unless you explicitly ask.
- The original template in SharePoint, OneDrive, or the upload is never overwritten.
- Supported replacement content is plain text (including line breaks). Rich
  HTML/Markdown conversion and placeholders spanning multiple paragraphs are
  intentionally rejected or out of scope.
- Conditional block markers (`{{#if}}`, `{{#else}}`, `{{/if}}`, `{{#switch}}`,
  `{{#case}}`, `{{/switch}}`) must each occupy their own paragraph or table row
  with no other text. Nesting one block inside another is not supported.
- Filling fails loudly on malformed tokens, invalid JSON shapes, remaining
  placeholders, corrupt DOCX packages, or changed Word field instructions.
- If no `.docx` template is available, generation stops with:
  `The required Word template was not supplied or could not be accessed.`
