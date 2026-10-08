# Template-Based Document Generation

Generate a Word document from your existing template and the information you supply.
Keep the structure your team has already agreed on, use the right content in the
right places, and see what still needs attention before the document is shared.

This skill is for recurring documents such as proposals, statements of work,
customer letters, and project reports. It works from a copy of a `.docx` template,
preserving the original and retaining untouched logos, styles, headers, footers,
and other document elements.

## What you can generate

Use the same template for different customers, projects, or reporting periods.
Depending on the template and supplied data, the skill can:

- Replace placeholders and fill supported Word content controls.
- Format dates, amounts, counts, and yes/no values consistently.
- Repeat a table row for each item in a list, such as services or deliverables.
- Remove drafting guidance and optional sections when they do not apply.
- Add paragraphs at a defined location for longer answers or summaries.
- Update fields in the document body, headers, footers, and footnotes.

The result is an editable Word document, accompanied by a summary of changes and
any items that need review.

## Before you start

Provide the **Word template**, the **data to include**, and any **rules for this
document**. For example, identify an optional section that should be removed, the
date format to use, or the wording to insert when a value is unavailable.

Structured data works best: named fields for customer details, a list of line
items, and clear values for dates and amounts. The template must be an actual
`.docx` file; a screenshot or a text description of its layout is not enough.

## Example requests

**Create a customer proposal**

> Use Template-Based Document Generation to create a proposal from the attached
> Word template and customer data. Add one table row per service, use the supplied
> prices, and remove the optional support section if support is not included.
> Return the completed Word document and flag anything still missing.

**Prepare a project report**

> Generate this month's project report using the attached template and the status
> data below. Use the supplied milestones and dates, summarize the progress notes
> in the executive summary, and list any information that needs confirmation.

**Generate a letter with incomplete information**

> Create a customer letter using this template and the supplied details. Use
> "To be confirmed" for a missing contact name, but stop if the customer name or
> reference number is missing. Keep the existing letterhead and footer.

## How it works

The agent first inspects the template to identify fields, tables, instructions,
and content that cannot safely be changed. It then maps the supplied information
to those locations and previews the planned edits before generating the document.

The scripts check the result against both the original template and the plan.
Changes outside the plan fail verification. If a later attempt fails, the last
successfully verified document is retained.

Missing information is handled explicitly. A required value stops generation;
an agreed placeholder or empty field is recorded for review. Values the agent
derives from your input, such as a summary or a combined name, are also flagged.
Facts that are not supported by the input should never be invented.

## Understanding the result

| Result | What it means |
| --- | --- |
| **OK** | The document passed the structural checks and has no reported review items. |
| **Needs review** | The document was generated and passed the structural checks, but the report identifies items to inspect. |
| **Failed** | The attempt did not produce a document suitable for delivery. The report explains why. |

These checks verify the edits, not the document's appearance in Word. Open the
finished file to review page breaks, table widths, and text overflow before
distributing it. The change report includes document text and supplied values,
so handle it with the same care as the document itself.

## Supported environment and limits

The skill targets **Copilot Studio** and requires a runtime that can execute
Python 3.10 or later and read and write local files. Its scripts use only the
Python standard library and do not make network requests.

It generates documents from existing Word templates. Creating a layout from
scratch, exporting to PDF, processing spreadsheets, and extracting data from
source documents require other tools.

Signed or macro-enabled templates are refused. Date pickers, drop-down lists,
data-bound controls, text inside tracked changes, and Word field results cannot
be filled by this skill; unsupported fields are reported for review.

## For maintainers

From the extracted skill directory, run the following checks with a short,
writable temporary path in place of `<workdir>`:

```text
python scripts/run_job.py doctor --workdir <workdir>
python scripts/build_fixtures.py --check
python scripts/run_job.py selftest --workdir <workdir>
```

The bundled tests use synthetic documents to check filling, formatting, document
preservation, unsafe deletions, and failure handling. The fixtures contain no
customer data.

See [SKILL.md](SKILL.md) for the agent workflow,
[the contract](references/contract.md) for the plan and data formats, and
[verification guidance](references/verification.md) for checks and report details.
