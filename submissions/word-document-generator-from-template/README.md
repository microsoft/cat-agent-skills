# Word Document Generator from Template

Fill a Microsoft Word template supplied at runtime — **uploaded**, or retrieved
from **SharePoint**, **OneDrive**, or another connector — using **user input**,
approved agent **knowledge sources**, and **results from prior tool or connector
calls**. Works for any document the template defines: **policy, procedure,
report, paper, briefing, SOP, statement of work**, or similar.

The template keeps control of structure, branding, styles, tables, headers, and
footers. The skill writes a **new** DOCX — it never overwrites the original.

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
Heading 2, Normal) and `{{placeholders}}` — not finished body text.

**Do**

- Put branding, page numbers, and classification in the **header / footer**.
- Use **Heading 1** for every major section the finished document must keep.
- Use a **one-row sample table** for anything that repeats (steps, findings, leave types, owners).
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
| `{{item.col_a}}` | `{{item.col_b}}` | `{{item.col_c}}` |

Rename columns to match the document (`Step` / `Owner` / `System`, or
`Finding` / `Impact` / `Action`, or `Leave type` / `Entitlement` / `Owner`).

**Footer:** `{{document.version}} | Page X of Y | {{document.status}}`

The agent fills placeholders from approved sources, **repeats the sample row**
for each JSON array item, and leaves gaps as `Not specified in approved
sources`. Styles, header, footer, and table formatting stay as in the template.

### Example mapping — Leave Policy

A leave policy is only one use of the same skeleton: Heading 1s become Purpose,
Scope, Leave types, Responsibilities; the repeating table columns become
`{{leave_type}}`, `{{leave_entitlement}}`, `{{leave_owner}}`, `{{leave_evidence}}`.

## How it works

1. Finds the Word template at runtime — from the upload, SharePoint, OneDrive, or the named connector.
2. Inspects document type, placeholders, sections, tables, headers, and footers.
3. Pulls facts from approved knowledge, user-supplied files, and prior tool or connector results.
4. Builds JSON that matches **this** template's fields.
5. Validates required sections, source-backed statements, and repeating rows.
6. Populates the template while preserving styles and layout.
7. Saves a new DOCX and returns a short generation summary.

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
- If no `.docx` template is available, generation stops with:
  `The required Word template was not supplied or could not be accessed.`
