# Capital Markets

Ten Cowork skills for analyst work in investment banking, research, and private equity.

## Skills

- **company-profile-pack** — company profiles.
- **comps-analysis** — comparable company analysis.
- **merger-model** — merger models.
- **cim-teardown** — CIM teardowns.
- **document-diligence** — document diligence.
- **dd-checklist** — diligence tracking.
- **earnings-note** — earnings notes.
- **coverage-meeting-prep-debrief** — coverage meeting prep and debriefs.
- **pitch-deck-skeleton** — pitch deck skeletons.
- **ic-memo** — investment committee memos.

## Boundaries

Every output states its source and date and marks assumptions rather than inventing them. The skills
provide analytical support, not advice, and never send or share anything without your confirmation.

## How it was tested

This plugin went through both human and AI evaluation and has a passing score for overall quality
and build.

## Extending with connectors

The plugin runs without paid data. Each skill uses a configured connector when one is available. If
none is configured, it falls back to the sources below and marks any missing figures `NEEDS FEED`.

| Skill | Connectors that improve it | Fallback without them |
|---|---|---|
| company-profile-pack | Market-data (market cap, EV, multiples); CRM (relationship section) | SEC EDGAR via web search or browser, then a 10-K upload |
| comps-analysis | Market-data provider (prices, multiples) | Uploaded and SharePoint/OneDrive files, then web search, labelled as web-sourced |
| pitch-deck-skeleton | Market-data (share price); deal database (precedent transactions) | Filed statements via web search and sec.gov |

The other seven skills have no connector-specific inputs. They read uploads first, then
SharePoint/OneDrive and Microsoft 365 mail and Teams, then public web search.
