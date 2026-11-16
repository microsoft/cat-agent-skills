# Research Brief Outline — default

Used when no house template is supplied. A customer template replaces the section order and field list; the identity, citation, and search-limit rules still apply.

Target one to two pages. Every fact carries its source and date.

## 1. Entity identification

State this first — everything below depends on it.

| Field | Content |
|---|---|
| Exact legal name | Including suffix, as registered |
| Jurisdiction | State or country of formation |
| Identifier | Entity or file number |
| Status | As stated by the registry, with retrieval date |
| Formation date | As filed |
| Trade names / former names / d/b/a | Each with its registration, or `NOT FOUND` |
| Registered agent | As filed |
| Addresses | Principal and registered office |

Where identity could not be confirmed, say so here and mark every downstream finding `GAP — possible match, identity not confirmed`.

## 2. Corporate structure

Parent, subsidiaries, and affiliates **as evidenced**. Name the source for each relationship.

Where no connector supplies a corporate family tree, say so:
`NEEDS FEED — corporate hierarchy source (e.g. D&B, S&P Capital IQ)`. Do not assemble a tree from inference or from similar names.

## 3. Business overview

What the company does, its markets, locations, and approximate size — attributed to the company's own statements, filings, or trade press, each with a date. Distinguish what the company says about itself from what an independent source reports.

## 4. Leadership

Named officers and directors with role and tenure, from registry filings, the company site, or filings. Business-relevant detail only. No protected characteristics, and no personal financial or legal history.

## 5. Public-record findings

One subsection per search type. **Every subsection states the index, jurisdiction, exact name searched, and date run** — including when the result is clean.

| Search | Report |
|---|---|
| UCC filings | Each filing: secured party, file number, date, collateral description as stated. Or a clean-result statement naming the index and its limits |
| Real property / recorder | Recorded instruments per county searched |
| Litigation / judgments | Filed cases from public indexes, attributed, with no characterisation of posture or merit |
| Regulatory / licensing | Where a public register exists for the industry |

Clean results use this form:

```
NOT FOUND — no UCC filings of record for "<exact name>" (<jurisdiction>, <identifier>) in the
<index>, searched <date>. Exact-name index; a search under variant or former names, or in
other jurisdictions, may return different results.
```

Never write "no liens", "unencumbered", or "clean".

## 6. Financial information

Only where a public source supplies it.

- **Registrant** → EDGAR figures with form type, period end, accession number, and the caption as printed. This is a public record, not borrower-supplied; never merge the two.
- **Not a registrant** → `NOT FOUND — no SEC filings; company is not a registrant`. This is a normal result for a private borrower.
- Business credit scores and peer benchmarks → `NEEDS FEED — business credit source (e.g. D&B, Experian commercial)`.

No ratios, trends, or commentary are computed here. Statement spreading belongs to `financial-statement-spread`, which requires borrower-supplied statements.

## 7. Recent developments

Material events from the last 6–12 months, each with publisher, headline, and date. Attributed, never asserted. Allegations remain allegations.

## 8. Relationship history

What M365 shows about prior contact: earlier briefs, prior files, past correspondence, with dates. Where the search ran and found nothing, say so — a cold name is a useful finding.

## 9. Open items

What could not be established, using the right marker and naming what would resolve it.

## Marker legend

| Marker | Meaning |
|---|---|
| `NOT FOUND` | The source answered and has no record. Names the source and what was searched. |
| `NOT RETRIEVED` | The source could not be reached this session. |
| `NEEDS FEED` | No source available for this field — names the connector that would supply it. |
| `GAP` | A record was returned but does not match on identity or date. |
| `AS OF <date>` | Found, but stale. |
| `UNVERIFIED — secondary source` | From something reproducing the record rather than the record itself. |

## Footer

```
Entity: <exact legal name, jurisdiction, identifier, status, as of date>
Searches run: <each: source, jurisdiction, exact name searched, date, result>
Sources: <count> — <each with publisher/registry and date>
Retrieval coverage: <complete | partial — name what was partial | sources not reached>
Template: <bundled default | house template name>
Artifact handoff: <docx built-in>
Connectors used: <names, or "none">
Other sources used: <public registry | supplied documents | M365 | secondary, marked>
Output: inline draft | file created <identifier> | creation failed
Persistence: not attempted | saved <verified location> | failed
Save detail: <what was produced; where written; where not written; incomplete items>
Gaps: <NOT FOUND / NOT RETRIEVED / NEEDS FEED / GAP items, or "none">
Generated: <date> — public-record research only. Not a credit bureau report, formal lien
search, or sanctions/PEP/adverse-media screen. No credit assessment or recommendation.
```

Each field reports what actually happened. Do not claim a registry was searched when it could not be reached, and do not describe coverage as complete when a jurisdiction was skipped.
