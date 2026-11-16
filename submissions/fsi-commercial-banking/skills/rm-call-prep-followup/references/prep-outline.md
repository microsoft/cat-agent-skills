# Pre-Call Brief Outline — default

Used when no house template is supplied. A customer template replaces section order and headings; the provenance, marker, and no-commitment rules still apply.

**Workflow boundary:** a named external commercial borrower/prospect relationship call with contact history and commitments. Not internal operating/forecast review prep or a standalone stakeholder Q&A pack. Missing relationship history stays a gap; a template cannot substitute a generic business review.

One page where possible. This is read in the ten minutes before a meeting.

## 1. Meeting

| Field | Content |
|---|---|
| Client | Name as used; legal name and identifier where established |
| Date and time | From the calendar item, or `as supplied by user` |
| Attendees | From the calendar item — bank side and client side separately |
| Purpose | As stated in the invite or by the user |
| Location / channel | As stated |

Where the calendar item was not found, say so. Do not reconstruct attendees from a mail thread and present them as the invitee list.

## 2. Relationship snapshot

Facilities, balances, products in use, and fee relationship — **from a connector or from supplied files only.**

Where no CRM, core, or treasury connector is configured:

```
NEEDS FEED — relationship exposure source (e.g. CRM, core banking, treasury connector).
The items below are reconstructed from M365 and supplied files, not from the system of record.
```

Never estimate a balance, utilisation, or fee figure.

## 3. Recent contact

Last five to ten interactions, most recent first.

| Column | Content |
|---|---|
| Date | As recorded |
| Channel | Mail · Teams · meeting · call note |
| Participants | As recorded |
| Subject | One line |
| Source | Where it was found |

## 4. Open items

| Column | Content |
|---|---|
| Item | What it is |
| Owner | As stated, else `TBC` |
| Due | As stated, else `TBC` |
| Status | As documented |
| Source | Document, thread, or task list, with date |

Never assign an owner by inference from who sent the message.

## 5. Public refresh

News, filings, and announcements since the last recorded contact. Per item: headline, publisher, date, and one line of substance. Secondary coverage marked `UNVERIFIED — secondary source`.

Where nothing was found, use the clean-search form: the sources searched, the exact name searched, and the date — not "no news".

## 6. Talking points

Each point is an observation with its source. Permitted forms:

- A change in the public record and its date.
- An open item and its documented status.
- A date documented in a file — maturity, renewal, reporting deadline.
- A question the record does not answer.

Not permitted: recommended products with terms, pricing, indications of appetite or approval likelihood, or anything phrased as what the bank will do.

## 7. Coverage statement

Explicit, not implied:

```
Searched: <each location> — <reachable | NOT RETRIEVED>
Not searched: <locations outside this session's access>
```

An unsearched mailbox, channel, or site is never presented as an empty one.

## Marker legend

| Marker | Meaning |
|---|---|
| `NOT FOUND` | The source answered and has no record. |
| `NOT RETRIEVED` | A location could not be reached this session. |
| `NEEDS FEED` | No source available for this field — names the connector that would supply it. |
| `TBC` | The record does not state it. |
| `UNVERIFIED — secondary source` | From something reproducing the record rather than the record itself. |

## Footer

```
Mode: prep
Client: <name as used; legal name and identifier where established>
Meeting: <date, attendees, purpose — source named, or "as supplied by user">
Searched: <each location searched and whether it was reachable>
Coverage: <complete | partial — name what was not reachable>
Connectors used: <names, or "none — relationship reconstructed from M365">
Other sources used: <M365 | public primary | secondary, marked>
Open items: <count> — <owners stated <n>, TBC <n>>
Template: <bundled default | house template name>
Artifact handoff: <docx built-in>
Output: inline draft | file created <identifier> | creation failed
Persistence: not attempted | saved <verified location> | failed
Sent: nothing sent
Gaps: <NOT FOUND / NOT RETRIEVED / NEEDS FEED items, or "none">
Generated: <date> — brief for RM review. No pricing, terms, commitments, or credit signals.
```
