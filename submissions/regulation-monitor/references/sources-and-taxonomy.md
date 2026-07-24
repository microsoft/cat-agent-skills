# Sources, taxonomy, and search-query templates

This file is loaded by the skill during setup and every sweep. It defines the
default reputable-domain allowlist, the item classification taxonomy, and how
per-topic search queries are built.

## Default reputable-domain allowlist

The sweep only accepts `web_search` results whose domain matches one of these
patterns (or an extension the user added at setup). Seed sources the user
provided are always honored regardless of domain.

### Government and inter-governmental (broad)

- `*.gov` — U.S. federal, state, local
- `*.gov.uk` — United Kingdom
- `*.gc.ca` — Canada federal
- `*.gov.au` — Australia
- `*.govt.nz` — New Zealand
- `*.europa.eu` — European Union institutions
- `*.oecd.org` — OECD
- `*.un.org` — United Nations
- `*.who.int` — WHO
- `*.bis.org` — Bank for International Settlements
- `*.imf.org` — IMF
- `*.worldbank.org` — World Bank

### Sector-specific regulators (opt-in but pre-approved)

Financial: `sec.gov`, `cftc.gov`, `federalreserve.gov`, `fdic.gov`, `occ.gov`,
`ecb.europa.eu`, `eba.europa.eu`, `esma.europa.eu`, `fca.org.uk`, `bankofengland.co.uk`.

Privacy and data: `ftc.gov`, `edpb.europa.eu`, `ico.org.uk`, `cnil.fr`,
`bfdi.bund.de`, `oaic.gov.au`, `priv.gc.ca`.

Competition: `justice.gov`, `ftc.gov`, `ec.europa.eu`, `cma.gov.uk`,
`bundeskartellamt.de`, `competitionbureau.gc.ca`.

Health: `hhs.gov`, `fda.gov`, `cms.gov`, `ema.europa.eu`, `mhra.gov.uk`.

Environment / ESG: `epa.gov`, `energy.gov`, `iso.org`, `issb.ifrs.org`,
`sec.gov` (climate disclosure), `efrag.org`.

Labor and workforce: `dol.gov`, `eeoc.gov`, `nlrb.gov`.

Tax: `irs.gov`, `treasury.gov`, `hmrc.gov.uk` (state DOR sites are already covered by `.gov`).

Standards and technical: `nist.gov`, `iso.org`, `ieee.org`, `w3.org`,
`iana.org`.

### Reputable trackers and think tanks (opt-in)

- `taxfoundation.org` — Tax Foundation
- `taxpolicycenter.org` — Tax Policy Center
- `mtc.gov` — Multistate Tax Commission
- `ncsl.org` — National Conference of State Legislatures
- `cost.org` — Council on State Taxation (public materials only)
- `iapp.org` — International Association of Privacy Professionals
- `future-of-privacy-forum.org`
- `brookings.edu`, `hoover.stanford.edu`, `aei.org`, `epic.org`

The user can extend this list via `domain_allowlist_extensions` in the config.
Add sparingly — the whole point of the allowlist is signal, not volume.

## Item taxonomy

Each item recorded by the sweep has:

| Field | Values | Notes |
|-------|--------|-------|
| `topic` | one of the profile's `watch_topics[].key` | required |
| `jurisdiction` | from profile's `jurisdictions`, or `global` / `local: <name>` | required |
| `stage` | `proposed` / `in-consultation` / `passed` / `regulatory-guidance` / `in-force` / `litigation` / `withdrawn` | required |
| `date` | ISO date the source is dated or the action took place | required |
| `title` | source's short title, verbatim | required |
| `summary` | 1-2 sentences in the model's own words | required |
| `source_name` | publisher's short name | required |
| `source_url` | canonical public URL that was actually retrieved | required |
| `relevant_to_your_team` | `true` if any function-area keyword matches | derived at Step 7 |

## Search-query templates

The sweep builds one query per watch topic. Use this shape:

```
("<keyword1>" OR "<keyword2>" OR "<keyword3>") AND (regulation OR guidance OR rule OR bill OR "final rule" OR consultation) AND (<jurisdiction1> OR <jurisdiction2>) after:<window-start>
```

Guidance:

- Prefer exact-quoted phrases for multi-word keywords ("EU AI Act", not
  EU AI Act) to reduce false positives.
- Add jurisdiction terms only if the profile's list is short and specific.
  If the profile lists 6+ jurisdictions, drop the jurisdiction clause and
  filter by domain after.
- Use `after:YYYY-MM-DD` (or the equivalent recency filter available in the
  web_search tool) to enforce the window at query time.
- Fan topics out in parallel, one query per topic. Do not run multiple
  redundant variants of one topic.

## Stage inference

Pick the stage from the source's own language:

- "introduced", "filed", "sponsors" → `proposed`
- "consultation", "call for evidence", "request for comment", "notice of proposed rulemaking" → `in-consultation`
- "passed the Senate", "royal assent", "adopted by Council" → `passed`
- "guidance", "circular", "policy statement", "notice", "FAQ" → `regulatory-guidance`
- "effective", "in force", "applies from" (past date) → `in-force`
- "court", "ruling", "opinion", "settlement", "consent decree" → `litigation`
- "withdrawn", "vacated", "rescinded" → `withdrawn`

If the source is genuinely ambiguous, pick the earliest applicable stage and
say so in the summary.
