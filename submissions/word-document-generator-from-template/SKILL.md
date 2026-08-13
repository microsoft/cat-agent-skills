---
name: word-document-generator-from-template
description: Generates a complete Word document by using an uploaded Word template plus user input, approved knowledge sources, and information retrieved from prior tool or connector calls. Use when a user asks to create, draft, or compile a document from a template.
---
# Word Document Generator from Template

## Purpose

Generate a complete Microsoft Word document using:

- a Word template supplied at runtime;
- information provided by the user;
- approved agent knowledge sources;
- files supplied with the request; and
- information retrieved from prior tool or connector calls in the same conversation (for example Dataverse, SharePoint, CRM, Azure Maps, or any Copilot Studio action).

The uploaded template controls the document structure, formatting, headings, tables, headers, footers, and branding.

## Required inputs

Before generating the document, identify:

- the Word template to use;
- the document title and purpose;
- the intended audience;
- any user-provided requirements;
- the approved knowledge sources to use;
- any relevant results from prior tool or connector calls; and
- the required output filename.

If required information is unavailable, use:

`Not specified in approved sources`

Do not invent facts, dates, owners, approvals, obligations, or organizational information.

## Instructions

1. Locate the Word template supplied at runtime.
2. Inspect the template to identify:
   - placeholders;
   - headings and sections;
   - tables;
   - repeating content areas;
   - headers and footers; and
   - required document metadata.
3. Retrieve relevant information from approved knowledge sources, user-supplied files, and prior tool or connector results already available in the conversation. Prefer connector-returned facts (records, dates, owners, IDs) over restating them from memory.
4. Generate content for each document section separately.
5. Create a structured JSON object matching the template fields.
6. Validate that:
   - required sections are present;
   - required fields have values;
   - generated statements are supported by approved knowledge, user files, or prior tool/connector results;
   - repeating items are represented as arrays; and
   - missing information is clearly identified.
7. Populate the uploaded Word template using the validated JSON.
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

- Use only information from approved knowledge sources, user-supplied files, or prior tool/connector results. Do not invent facts that those sources do not contain.
- Treat prior tool and connector outputs as approved sources. Record the tool or connector name in `source_ids` (for example `Dataverse:accounts`, `SharePoint:policy-library`).
- Generate long documents section by section rather than in one response.
- Keep the structured JSON as the intermediate source of truth.
- Use clear, professional, organization-appropriate language.
- Preserve mandatory wording found in approved sources.
- Do not treat the uploaded template as a knowledge source unless instructed.
- Do not add new sections unless required to complete the template.
- Do not remove sections from the template without an explicit instruction.
- Record the sources used for each major section when source information is available.

## Template handling

The template will be uploaded or retrieved at runtime.

Search the runtime working directory for the supplied `.docx` file. If more than one Word template is available, select the template identified in the user request.

If the required template cannot be found, stop document generation and report:

'The required Word template was not supplied or could not be accessed.'

## Structured JSON

Create JSON that reflects the uploaded template. Use:

- strings for individual fields;
- objects for document sections;
- arrays for repeating tables or content blocks; and
- source identifiers for traceability.

Example:

{
  "document": {
    "title": "Information Security Policy",
    "owner": "Information Security",
    "version": "0.1",
    "status": "Draft"
  },
  "sections": {
    "executive_summary": {
      "content": "Generated section content",
      "source_ids": ["SRC-001"]
    },
    "purpose": {
      "content": "Generated section content",
      "source_ids": ["SRC-001", "SRC-002"]
    }
  },
  "requirements": [
    {
      "id": "REQ-001",
      "requirement": "Generated requirement",
      "owner": "System owner",
      "evidence": "Approval record",
      "source_ids": ["SRC-002"]
    }
  ],
  "sources": [
    {
      "source_id": "SRC-001",
      "title": "Approved source document",
      "type": "knowledge"
    },
    {
      "source_id": "SRC-003",
      "title": "Dataverse — Account records",
      "type": "connector"
    }
  ]
}

Adapt the JSON fields to the actual placeholders and structure found in the runtime template.

## Quality and safety

The generated document is a draft until reviewed and approved. If a statement cannot be supported by approved knowledge, a user-supplied file, or a prior tool/connector result, do not present it as fact. Mark it for human review.
