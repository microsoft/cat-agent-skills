# Global Greenwashing Claim Auditor

A portable agent skill for first-pass analysis of environmental marketing
claims. It identifies potentially misleading or insufficiently substantiated
claims and reports universal claim-construction risks separately from findings
specific to Canada, the European Union, and the United Kingdom.

Use it to review product descriptions, advertising copy, sustainability
reports, presentations, websites, social content, packaging text, and other
public-facing communications before publication or legal review.

## Supported inputs

- Pasted conversational text or a text file
- CSV datasets
- XLSX workbooks
- DOCX documents
- PPTX presentations
- Public HTTP or HTTPS website URLs

The bundled scripts use only Python's standard library. XLSX, DOCX, and PPTX
content is extracted directly from their Open XML files, so no additional
Python packages are required.

## Add the skill to an agent

1. Download and unpack the skill bundle.
2. Add the unpacked skill to the agent.
3. Ensure the uploaded skill retains its `SKILL.md`, `scripts/`, and
   `references/` directories.
4. Ask the agent to audit content, specifying the intended markets and
   publication date when known.

The scripts use Python 3 and workspace-relative paths so they can run across
supported agent environments.

## Example requests

- "Audit this product description for greenwashing risks in Canada, the EU, and
  the UK."
- "Review the attached sustainability claims spreadsheet and prioritize the
  highest-risk rows."
- "Scan this presentation for environmental claims that need qualification or
  substantiation."
- "Check this public product page for vague, absolute, carbon-neutral, and
  recyclability claims."
- "Assess these claims for an EU campaign scheduled to publish on
  September 1, 2026."
- "Rewrite the flagged claims conservatively without inventing evidence."

If the target markets are not provided, the skill evaluates all four available
scopes and marks regional applicability as unconfirmed:

- `ANY`: universal vocabulary and claim-construction risks
- `CA`: Canadian laws and guidance
- `EU`: European Union laws and guidance
- `UK`: United Kingdom laws and guidance

## How an audit works

1. The skill determines the input type, intended markets, and assumed
   publication date.
2. It extracts claim-bearing text while preserving locations such as CSV row
   and column, workbook sheet and cell, document paragraph, or presentation
   slide and shape.
3. A bundled Python script performs keyword and pattern triage.
4. The agent reviews each match against the bundled vocabulary, risk taxonomy,
   detection method, and regional research.
5. It adds contextual risks that keyword matching can miss, including implied
   claims, imagery, omissions, comparisons, labels, lifecycle scope, and future
   commitments.
6. It reports findings separately for each applicable jurisdiction and assigns
   the highest applicable risk as the overall rating.

## What the report contains

The resulting audit includes:

- Scope, sources, assumed publication date, and applicable jurisdictions
- Counts by risk level and jurisdiction
- The exact claim and its source location
- Finding code, risk rating, legal or methodological basis, and reasoning
- Practical remediation and a bounded rewrite where appropriate
- Highest-priority fixes
- Limitations and issues requiring legal or technical review

The skill does not invent evidence, percentages, certifications, methods, or
environmental benefits. A keyword match is treated as a lead for review, not
proof of greenwashing.

## Quick test

From the unpacked skill directory, run:

```sh
python scripts/analyze_text.py --text "Our eco-friendly product is carbon neutral." --jurisdictions CA EU UK
```

To audit a file and save Markdown output:

```sh
python scripts/analyze_docx.py "document.docx" --jurisdictions CA EU UK --format markdown --out audit.md
```

Each analyzer supports JSON output by default and Markdown output with
`--format markdown`. See `SKILL.md` for the full command reference.

## Important limitations

- This skill provides compliance triage, not legal advice or a declaration of
  legal compliance.
- Automated extraction may not capture the full effect of imagery, layout,
  footnotes, linked evidence, or other visual context.
- Public website analysis does not bypass authentication, paywalls, robots
  controls, or access restrictions.
- Laws and regulatory guidance can change. Date-sensitive rules should be
  assessed using the content's intended publication date.
- Yellow and Red findings should be reviewed with the relevant evidence and
  escalated to qualified legal counsel when necessary.

See `SKILL.md` for the agent's operating instructions and `references/` for the
governing research, vocabulary, taxonomy, and detection methodology.
