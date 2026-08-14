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

The runtime template controls document type, structure, formatting, headings, tables, headers, footers, and branding. Adapt sections, tables, and JSON keys to **that** template — do not assume a fixed outline.

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

1. Locate the Word template supplied at runtime. Obtain it from whichever source the user identified:
   - a file uploaded with the request;
   - SharePoint (library, folder, or site);
   - OneDrive; or
   - another connector or prior tool result that returns a `.docx` file.
   If the template is not already in the working directory, retrieve it with the matching connector or tool before continuing.
2. Inspect the template to identify:
   - document type (policy, procedure, report, paper, or other);
   - placeholders;
   - headings and sections;
   - tables;
   - repeating content areas;
   - headers and footers; and
   - required document metadata.
3. Retrieve relevant information from approved knowledge sources, user-supplied files, and prior tool or connector results already available in the conversation. Prefer connector-returned facts (records, dates, owners, IDs) over restating them from memory.
4. Generate content for each document section separately, matching the template's headings.
5. Create a structured JSON object matching the template fields (not a fixed schema).
6. Validate that:
   - required sections from the template are present;
   - required fields have values;
   - generated statements are supported by approved knowledge, user files, or prior tool/connector results;
   - repeating items are represented as arrays; and
   - missing information is clearly identified.
7. Populate the runtime Word template using the validated JSON.
8. Preserve the template's:
   - styles;
   - layout;
   - branding;
   - section breaks;
   - headers and footers; and
   - table formatting.
9. Save the completed document as a new DOCX file.
10. Never overwrite the original template.
11. Check the completed document for:
    - unresolved placeholders;
    - missing sections;
    - broken tables;
    - duplicated content;
    - unsupported statements; and
    - formatting or pagination problems.
12. Return the completed Word document and a short generation summary.

## Generation rules

- Follow the uploaded template's outline. Rename JSON keys to match its headings and placeholders.
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
    "title": "{{document.title}}",
    "type": "policy | procedure | report | paper | other",
    "owner": "{{document.owner}}",
    "version": "{{document.version}}",
    "status": "{{document.status}}",
    "audience": "{{document.audience}}"
  },
  "sections": {
    "<heading_slug>": {
      "content": "Generated section content",
      "source_ids": ["SRC-001"]
    }
  },
  "items": [
    {
      "col_1": "Value for first repeating-table column",
      "col_2": "Value for second column",
      "source_ids": ["SRC-002"]
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

A Leave Policy template would map `items` to `leave_types`; a procedure would map it to `steps`; a report would map it to `findings` or connector rows. Always adapt to the actual placeholders.

## Quality and safety

The generated document is a draft until reviewed and approved. If a statement cannot be supported by approved knowledge, a user-supplied file, or a prior tool/connector result, do not present it as fact. Mark it for human review.
