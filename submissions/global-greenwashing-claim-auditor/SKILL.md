---
name: global-greenwashing-claim-auditor
description: Use this skill whenever the user asks to audit, scan, review, classify, or de-risk environmental, sustainability, climate, circularity, recycling, emissions, or green marketing claims in pasted conversational content, CSV files, XLSX workbooks, DOCX documents, PPTX presentations, or website URLs. Report universal vocabulary risks separately from Canadian (CA), European Union (EU), and United Kingdom (UK) legal and guidance findings.
---

# Global Greenwashing Claim Auditor

Audit public-facing environmental claims using the bundled global vocabulary, regional taxonomy, legal research, and detection method. Treat the result as compliance triage, not legal advice.

## Required references

Read these before making final findings:

1. `references/Greenwashing-vocab.md`
2. `references/greenwashing-risk-taxonomy.md`
3. `references/greenwashing-detection.md`
4. `references/greenwashing-analysis-research.md`

Use `ANY` only for universal vocabulary and claim-construction risks. Use `CA`, `EU`, and `UK` only when the corresponding regional rule, law, regulation, or guidance supports the finding.

## Workflow

1. Determine the input type and intended markets. If markets are unknown, analyze `ANY`, `CA`, `EU`, and `UK`, but mark regional applicability as unconfirmed.
2. Extract all claim-bearing text while preserving source locations:
   - CSV: row and column.
   - XLSX: sheet and cell.
   - DOCX: paragraph or table cell.
   - PPTX: slide and shape.
   - Conversation: supplied text block.
   - URL: page URL and extracted block.
3. Run the matching script for first-pass triage.
4. Review every flagged unit against the full references. Keyword matches are leads, not verdicts.
5. Add claims missed by keywords, including implied claims, imagery, omissions, comparisons, labels, scope overreach, lifecycle issues, and unsupported future commitments.
6. Report separate findings for every applicable jurisdiction and retain the highest risk as the overall rating.
7. Suggest a bounded rewrite, but never invent evidence, percentages, certifications, methods, or environmental benefits.

## Scripts

Run scripts from the skill directory with Python 3. Use workspace-relative paths so commands remain portable across supported environments.

### CSV

```sh
python scripts/analyze_csv.py "claims.csv" --jurisdictions CA EU UK --out audit.json
```

Use `--text-column NAME` repeatedly to choose columns. Without it, the script scans text-like columns and then all string columns if necessary.

### XLSX

```sh
python scripts/analyze_xlsx.py "claims.xlsx" --sheet "Posts" --jurisdictions CA EU UK --out audit.json
```

Use `--max-items 1000` for a bounded first pass.

### DOCX

```sh
python scripts/analyze_docx.py "document.docx" --jurisdictions CA EU UK --out audit.json
```

### PPTX

```sh
python scripts/analyze_pptx.py "presentation.pptx" --jurisdictions CA EU UK --out audit.json
```

### Conversational content

For short content, analyze it directly using the references. For repeatable scripted triage:

```sh
python scripts/analyze_text.py --text "Our product is carbon neutral and eco-friendly." --jurisdictions CA EU UK --out audit.json
```

For long content:

```sh
python scripts/analyze_text.py --text-file "content.txt" --jurisdictions CA EU UK --out audit.json
```

### Website URL

```sh
python scripts/analyze_url.py "https://example.com/product" --jurisdictions CA EU UK --out audit.json
```

Only fetch public HTTP/HTTPS pages. Do not attempt to bypass authentication, paywalls, robots controls, or access restrictions.

### Markdown output

All entry scripts accept `--format markdown`:

```sh
python scripts/analyze_docx.py "document.docx" --format markdown --out audit.md
```

## Review requirements

Always manually inspect:

- Red findings.
- Generic claims such as `green`, `eco-friendly`, and `sustainable`.
- Carbon-neutral, climate-neutral, net-zero, or offset claims.
- Sustainability labels, seals, certifications, and badges.
- Recyclable, compostable, biodegradable, reusable, and circularity claims.
- Comparisons and future targets.
- Qualifications in footnotes, small print, links, notes, or other slides/pages.

Apply date-sensitive EU rules using the content's intended publication date. If no date is supplied, use the current date and state that assumption.

## Output

Return:

1. Scope, sources, assumed publication date, and applicable jurisdictions.
2. Counts by overall risk and jurisdiction tag.
3. One finding per claim and region, including exact quote, source location, finding code, risk, basis, reason, and remediation.
4. Highest-priority fixes.
5. Limitations, inaccessible evidence, and items requiring legal or technical review.

## Guardrails

- Do not describe `ANY` as a legal violation.
- Do not declare legal compliance; state that no issue was detected under the checks performed.
- Do not treat a keyword match alone as proof of greenwashing.
- Do not invent or assume substantiation.
- Do not ignore visual or contextual implications merely because extracted text appears qualified.
- Do not apply withdrawn proposed legislation as enacted law.
- Escalate high-risk claims for qualified legal review before publication.

## Tone

Be precise, evidence-led, constructive, and explicit about jurisdiction. Every Yellow or Red finding should include a practical remediation.
