# States, evidence standard, and the XLSX register

Loaded on demand by `identify-regulatory-gaps`. Nothing here overrides the guardrails in SKILL.md.

## The eight states

| State | Meaning |
| --- | --- |
| `Addressed` | The document contains wording that meets the requirement, quoted and cited. |
| `Partial` | The document addresses the requirement but not fully — a shorter period, a narrower scope, a missing limb. Record each delta separately. |
| `Gap` | The document is silent on the requirement. This is a location fact, never a verdict. |
| `Conflict` | The document expressly fixes a term inconsistent with the requirement. |
| `Superseded reference` | The document cites a provision the pinned change renumbered, replaced or repealed, and the before-to-after mapping is established from retrieved text. |
| `Not applicable` | Disapplication is established by a basis quoted from the standard's own scoping provision, or given by the user. |
| `Cannot determine` | The standard, or the relevant document text, could not be retrieved or read. Takes precedence over every other state where the standard is not supplied. |
| `Counsel decision` | The answer depends on applicability, an exemption, a transitional or grandfathering provision, materiality, or construction. |

A governing law, entity, product, exemption, transition or grandfathering question is `Counsel
decision` unless the factual trigger and the disapplication are mechanically established by quoted
wording on both sides. Raise applicability questions in Counsel decisions rather than changing the
state.

## Evidence standard

- Every finding carries **both** citations:
  - **standard side** — instrument or policy name, version or consolidation date, and article,
    regulation, rule, section or paragraph;
  - **document side** — document name and clause, schedule, annex, page, or sheet and cell.
- Quote enough exact operative wording on both sides to expose the difference.
- Cite the provision that defines the requirement, term, threshold or date, not a later
  cross-reference. Where an amendment changes a provision, cite the amending instrument and
  distinguish pre-amendment from post-amendment wording.
- Label commentary, law firm briefings, regulator press releases, trade summaries and news
  `Secondary source — verify against primary text`. Never present them as the rule itself. Where no
  primary text is available, inventory only operative text the secondary source purports to quote,
  mark every affected row `Cannot determine`, and record in Limitations that the requirement side
  rests on characterisation.
- Preserve amounts, percentages, deadlines, thresholds, exceptions, entity scope and obligation
  owners exactly. Never fabricate a provision number, effective date, quotation, instrument title,
  citation or URL.
- Preserve official URLs, instrument citations, versions and retrieval dates in the created report.

## The XLSX register

For a group of documents, or any change impact run, hand the work to Cowork's built-in Excel workbook creator exactly once to create
and populate `identify-regulatory-gaps.xlsx`, instructing it to read representative ranges and formulas
back before delivery and never to substitute a Markdown table. Create these sheets:

- **Findings** — one row per document and requirement:
  `Document | Requirement and citation | Document wording and citation | State | Delta | Note`
- **Coverage** — requirements inventoried versus requirements traced, and state counts per document.
- **Sources** — source role, version or date, jurisdiction, in force status and read status.
- **Change log** — for every change impact run: old wording, new wording, amending instrument,
  effective date and transitional provision.
- **Scope and basis**
- **Summary**
- **Counsel decisions**
- **Limitations**

Where the user requests a format conflicting with this routing, produce both the required register
and the requested deliverable from one dataset so they cannot diverge, and state this in Scope. Never
silently substitute a format and never drop the register. Where a supplied template has no place for
a required field, place that field in an appendix or an additional sheet rather than dropping it.

Confirm the created file is present before telling the user it exists. Where the user attached a
OneDrive folder, also upload the deliverable there —
never a source.
