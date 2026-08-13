# Word Document Generator from Template

Fill an uploaded Microsoft Word template using information from the user and
approved agent knowledge sources. The template keeps control of structure,
branding, styles, tables, headers, and footers. The skill writes a **new**
DOCX — it never overwrites the original template.

Instruction-only — no scripts or extra packages.

## When to use it

Ask the agent to create, draft, or compile a document from a template, for
example:

- an information security policy from the corporate policy template;
- a statement of work from a standard SOW template;
- a board paper, briefing, or status report from a branded Word file;
- a procedure or SOP that must keep the official heading structure.

## Before you start

Provide:

| Input | Why it matters |
| --- | --- |
| Word template (`.docx`) | Controls layout, placeholders, and branding |
| Document title and purpose | Sets the draft intent |
| Intended audience | Tones the language |
| Requirements | Anything the template must cover |
| Approved knowledge sources | The only facts the agent may use |
| Output filename | Name of the new DOCX |

If a required fact is not in approved sources, the agent writes
`Not specified in approved sources` instead of inventing it.

## How it works

1. Finds the uploaded Word template at runtime.
2. Inspects placeholders, sections, tables, headers, and footers.
3. Pulls facts from approved knowledge and user-supplied files.
4. Builds a structured JSON object that matches the template fields.
5. Validates required sections, source-backed statements, and repeating rows.
6. Populates the template while preserving styles and layout.
7. Saves a new DOCX and returns a short generation summary.

## Example request

> Use the attached Information Security Policy template. Draft version 0.1 for
> internal staff. Pull content only from our approved security knowledge.
> Save as `Information-Security-Policy-v0.1.docx`.

The agent returns the completed Word file plus a summary of what was filled,
what was missing, and which sources were used.

## Good to know

- Output is a **draft** until a human reviews and approves it.
- Unsupported statements are marked for review, not presented as fact.
- The template is not treated as a knowledge source unless you say so.
- Sections are not added or removed unless you explicitly ask.
- If no `.docx` template is available, generation stops with:
  `The required Word template was not supplied or could not be accessed.`
