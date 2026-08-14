# Word Document Generator from Template

Fill a Microsoft Word template supplied at runtime — **uploaded**, or retrieved
from **SharePoint**, **OneDrive**, or another connector — using **user input**,
approved agent **knowledge sources**, and **results from prior tool or connector
calls**. The template keeps control of structure, branding, styles, tables,
headers, and footers. The skill writes a **new** DOCX — it never overwrites the
original template.

## When to use it

Ask the agent to create, draft, or compile a document from a template, for
example:

- a leave policy from the corporate policy template;
- a statement of work from a standard SOW template;
- a report, briefing, or paper from a branded Word file;
- a procedure or SOP that must keep the official heading structure;
- a status report whose tables come from Dataverse, SharePoint, or another connector called earlier in the conversation.

## Before you start

Provide:

| Input | Why it matters |
| --- | --- |
| Word template (`.docx`) — **required** | Controls layout, placeholders, and branding. May be **uploaded**, or retrieved from **SharePoint**, **OneDrive**, or another connector |
| Document title and purpose | Sets the draft intent |
| Intended audience | Tones the language |
| Requirements | Anything the template must cover |
| Approved knowledge sources | Policies, manuals, and other grounded content |
| Prior tool / connector results | Records, lists, and fields already retrieved this conversation |
| Output filename | Name of the new DOCX |

Approved sources include knowledge, uploaded files, **and** data returned by
upstream tools or connectors. If a required fact is not in those sources, the
agent writes `Not specified in approved sources` instead of inventing it.

## Ideal Word template structure

Design the `.docx` so the agent can map sections and placeholders to JSON
without guessing. Use **Word styles** (Heading 1, Heading 2, Normal) and
clear `{{placeholders}}` — not dummy paragraphs of finished policy text.

**Do**

- Put branding, page numbers, and classification in the **header / footer**.
- Use **Heading 1** for every major section the finished document must keep.
- Use a **one-row sample table** for repeating items (leave types, owners, dates).
- Name placeholders to match fields: `{{document.title}}`, `{{sections.purpose}}`.
- Leave body cells short: `{{sections.purpose}}` or `[Insert purpose — from approved sources]`.

**Don’t**

- Bury real policy wording in the template (it is not a knowledge source).
- Use floating text boxes or images that hide placeholders.
- Skip headings and rely on bold paragraphs — the agent may miss sections.

### Example — Leave Policy template

What the Word file should look like before generation:

**Header:** `Contoso | Internal | {{document.title}}`

**Title (Heading 1):** `{{document.title}}`

**Document control (Heading 2)** — one metadata table:

| Field | Placeholder |
| --- | --- |
| Owner | `{{document.owner}}` |
| Version | `{{document.version}}` |
| Status | `{{document.status}}` |
| Audience | `{{document.audience}}` |

**Body sections** — each is Heading 1 with a single placeholder underneath:

| Heading 1 | Body |
| --- | --- |
| 1. Executive summary | `{{sections.executive_summary}}` |
| 2. Purpose | `{{sections.purpose}}` |
| 3. Scope | `{{sections.scope}}` |
| 4. Leave types | Repeating table (below) |
| 5. Responsibilities | `{{sections.responsibilities}}` |
| 6. Related documents | `{{sections.related_documents}}` |

**Leave types table** — keep the header row; leave **one sample data row** for the agent to clone:

| Leave type | Entitlement | Owner | Evidence |
| --- | --- | --- | --- |
| `{{leave_type}}` | `{{leave_entitlement}}` | `{{leave_owner}}` | `{{leave_evidence}}` |

**Footer:** `{{document.version}} | Page X of Y | Draft`

The agent fills those placeholders from approved sources, **repeats the
leave-types row** for each item in the JSON array, and leaves unused
fields as `Not specified in approved sources`. Styles, header, footer,
and table formatting stay as they are in the template.

## How it works

1. Finds the Word template at runtime — from the upload, SharePoint, OneDrive, or the named connector.
2. Inspects placeholders, sections, tables, headers, and footers.
3. Pulls facts from approved knowledge, user-supplied files, and prior tool or connector results.
4. Builds a structured JSON object that matches the template fields.
5. Validates required sections, source-backed statements, and repeating rows.
6. Populates the template while preserving styles and layout.
7. Saves a new DOCX and returns a short generation summary.

## Example requests

> Use the Leave Policy template in SharePoint
> (`Policies/Templates/Leave-Policy.docx`). Draft version 0.1 for internal
> staff. Pull content from our approved HR knowledge. Save as
> `Leave-Policy-v0.1.docx`.

> Get the open accounts from Dataverse, then fill the status-report template
> in my OneDrive (`Templates/Q3-Status-Report.docx`). Use those records for
> the table and our knowledge base for the narrative. Save as
> `Q3-Account-Status.docx`.

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
