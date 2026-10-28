# Regulatory Sources — Access Guide

How to reach US regulatory instruments, and what you may claim once you have them.

---

## 1. Choosing a retrieval route

**A route is how you reach a source. It is not the same as which source to prefer.** Authority
order is defined once in `house-rules.md` (§ 3, "Authority tiers") and governs everywhere. This
section covers only how to *reach* the instrument once that order points you at it.

**Check what this session actually has, then reach the source by:**

1. **A configured connector**, if one carries the instrument or obligation library
   (reg-intelligence, GRC obligation register, DMS). Say you used it — curated obligation text
   is a vendor's rendering of the rule, and that changes what you may claim versus the
   instrument itself.
2. **A direct retrieval route**, where the session supports one. The eCFR and Federal Register
   JSON APIs are designed for this and are the preferred direct route.
3. **The browser route.** In Cowork environments observed to date, direct URL fetches have failed
   with DNS resolution errors and the browser has been the working route to government sites.
   The user must permit browser use for the session.

Treat step 3's observation as **what to expect, not a universal platform contract.** A fetch that
fails is an access failure *for that source in this session* — it is not evidence that no HTTP or
API access exists, and it must never be reported that way. **If a direct route works, use it and
do not ask the user to enable a browser unnecessarily.**

> **If no retrieval route is available**, say so plainly and offer two paths, in this order:
> 1. Ask the user to upload the instrument by name (the rule PDF, the consent order, the bulletin).
> 2. If they decline, you may search the web. What you get back is classified by **what it is**,
>    not by the fact that you searched — see § 2.
>
> **Never state a requirement from memory.** If it was requested and could not be retrieved, it is
> `NOT RETRIEVED - <source> (Gn)`; if no request was made, it is
> `GAP - <source> retrieval not attempted (Gn)`.

### Sources observed to block automated access

These are not failures to work around. They are facts to route around.

| Source | Observed | Route |
|---|---|---|
| FFIEC BSA/AML Examination Manual | Blocks automated fetch (403) | Reference by name; ask the user to upload it, or work from FinCEN and agency material |
| `regulations.gov` API v4 | 403 without an `api.data.gov` key | Not available out of the box. If the customer has added a key, use it |

Do not present either as an out-of-the-box source, and do not silently substitute a secondary
summary of them.

---

## 2. Discovery method is not authority

**How you found an instrument and what the instrument is are separate properties.** A web search
that leads you to a final rule on `federalregister.gov`, which you then open and read, gives you
a **final rule** — cite it as the rule, with document number, agency, type, and publication date.
The search was navigation.

What makes a source secondary is that it **reproduces** the instrument instead of being it. A
law-firm alert describing a rule is tier 6 no matter how accurate it is.

**Record coverage separately from identity.** Every citation carries both:

| Coverage | Means |
|---|---|
| `complete` | You read the whole relevant section or instrument |
| `partial` | You read part of it — say which part |
| `snippet only` | You saw a search result or excerpt, **not** the instrument |
| `unavailable` | You could not open it |

**A search snippet is never sufficient evidence for a claim about an instrument.** If a snippet
is all you have, open the instrument or report the gap. Never cite a section number, effective
date, or docket number you reached only through a snippet.

---

## 3. eCFR — codified text

**What it is:** the Code of Federal Regulations as currently compiled. Tier 1.

**What it is not:** a complete statement of the law in force today.

### The codification gap — check it every time

Each eCFR title carries two different dates, and they mean different things:

| Field | Means |
|---|---|
| `up_to_date_as_of` | How current the **compilation** claims to be |
| `latest_issue_date` | The last amendment actually **incorporated** into the text |

These diverge. Observed on Title 12 (Banks and Banking): `up_to_date_as_of` 2026-09-24 against
`latest_issue_date` 2026-09-14. **A final rule published in that gap is in force and is not in
the text you just read.**

This matters most on exactly the rules a compliance team is asking about — the new ones.

**Required check, every time codified text is used as a current requirement:**

1. Read the title's `latest_issue_date` from `versioner/v1/titles.json`.
2. Query the Federal Register for **final rules** from the same agency affecting the same CFR
   part, published after that date.
3. If one exists with an effective date on or before today → marker
   `PENDING CODIFICATION — <FR document number>, effective <date>`, and **the final rule text
   governs**, not the codified text.
4. If one exists with a future effective date → report it as a **forthcoming change** with its
   date ladder. It is not yet the requirement.
5. If the check could not be performed → say so in the footer. Never report codified text as
   current while silently skipping the check.

### Useful endpoints

| Purpose | Endpoint |
|---|---|
| Title list with both dates | `/api/versioner/v1/titles.json` |
| Full-text search | `/api/search/v1/results?query=<terms>` |
| Section text | `/api/versioner/v1/full/<date>/title-<n>.xml?part=<part>&section=<section>` |

Full-text search works and is the right entry point when you have a concept rather than a
citation — "customer due diligence" returns hits led by 31 CFR § 1010.610. Confirm the section
by opening it; a search hit is `snippet only` until you do.

Titles most used here: **12** (Banks and Banking) · **17** (Commodity and Securities Exchanges) ·
**31** (Money and Finance: Treasury, including the BSA regulations at parts 1010–1030), plus the
agency-specific parts of 12 CFR for OCC, Fed, FDIC, CFPB, and NCUA.

---

## 4. Federal Register — rules and proposed rules

**What it is:** the daily journal of record. Final rules here are law (tier 2); proposed rules
are **not law** (tier 3).

### Precision over recall — this is a correctness rule, not an efficiency one

A bare term search over-returns badly. Measured:

| Query | Documents | What the newest results actually were |
|---|---|---|
| term = "anti-money laundering" | **1,141** | An SRO filing notice, an exemptive order, "Merger Transactions" |
| agency = `financial-crimes-enforcement-network`, type = `RULE` + `PRORULE` | **141** | GTO recordkeeping order, a § 311 special measure, BOI reporting revisions |

The keyword result is not a smaller version of the right answer — its newest entries are simply
not AML rules. **Always constrain the query:**

- `conditions[agencies][]=<agency-slug>` — the single most effective filter.
- `conditions[type][]=RULE` and/or `PRORULE`, `NOTICE`, `PRESDOCU`. Keep rules and proposed rules
  in **separate** result sets wherever the output distinguishes them.
- `conditions[publication_date][gte]` / `[lte]`, or `conditions[effective_date]`.
- `conditions[docket_id]` or `conditions[regulation_id_number]` where known — the most precise.
- `conditions[cfr][title]` and `[part]` to tie results to the part you are analysing.

**Never present a search-result count as coverage.** "1,141 documents mention AML" is not a
finding about the firm's obligations. State what you filtered on and that the result is scoped,
not exhaustive.

### Fields that matter

`document_number` · `type` (Rule / Proposed Rule / Notice) · `agencies` · `publication_date` ·
`effective_on` · `comments_close_on` · `cfr_references` · `regulation_id_number` · `docket_ids` ·
`html_url`.

**`type` is load-bearing.** A `Proposed Rule` carries `PROPOSED — not in force` on every
obligation derived from it, and that marker travels into every downstream table and tracker row.

### The four dates

Published · effective · compliance date · **mandatory compliance date**. The API gives the first
two reliably; the compliance dates usually appear only in the preamble text, so **open the rule**
to find them. Where the instrument does not state one, say so — never infer a compliance date
from the effective date.

---

## 5. Agency sources

| Agency | Instruments | Notes |
|---|---|---|
| **FinCEN** | Advisories, bulletins, fact sheets, GTOs, § 311 measures, SAR Stats | Advisories are tier 4 — typologies and red flags, not rules. Excellent for structuring a review |
| **OCC** | Bulletins, Comptroller's Handbook | Bulletin 2023-17 is the interagency third-party lifecycle and rescinds 2013-29 and 2020-10 |
| **Federal Reserve** | SR and CA letters | Supervisory expectation, tier 4. Check for supersession — SR 11-7 and SR 21-8 were superseded by interagency SR 26-2 in April 2026 |
| **FDIC** | FILs | Tier 4 |
| **CFPB** | Regulations, bulletins, circulars, **enforcement actions** | Consent orders are the primary source for `enforcement-action-review` |
| **SEC / FINRA / NCUA** | Rules, notices, enforcement | FINRA rules are SRO rules — say so; they are not CFR |

**Always check for supersession.** Guidance turns over, and a rescinded bulletin cited as current
is a substantive error. Where an instrument states what it rescinds or supersedes, record that.
Where you cannot establish currency → `GAP — currency of guidance not established`.

**Guidance is not law.** Write "supervisory expectation under <instrument>", never "required by".

---

## 6. Retrieving an instrument the user uploaded

When the route is an upload, `document-extraction.md` governs reading it. Additionally:

- Confirm the uploaded document **is** the instrument it is said to be — agency, document number,
  publication date, and type on its face. A printed summary of a rule is tier 6, not tier 2, even
  when the user calls it "the rule."
- A rule reprint from a commercial service is the rule only if it reproduces the instrument's own
  text and identifiers. If it is annotated or abridged, say so and treat annotations as tier 6.
- An undated printout cannot support an as-of claim → `GAP — as-of date not established`.

---

## 7. What to record for every retrieved instrument

Every citation in every output carries:

| Field | Example |
|---|---|
| Instrument | "FinCEN, Anti-Money Laundering/Countering the Financing of Terrorism Program Requirements" |
| Identifier | FR document number, docket, RIN, CFR citation, bulletin number |
| Authority tier | 1–6 per `house-rules.md` § 3 |
| Type | Final rule / proposed rule / guidance / FAQ / order |
| Dates | Published · effective · compliance · mandatory compliance, or `NOT FOUND` for each absent one |
| Coverage | `complete` / `partial` / `snippet only` / `unavailable` |
| Retrieval date | The date you actually read it |
| Route | Connector / direct / browser / upload |

While the rule's definitions section is not retrieved, the Instrument field is the FR Doc
number and short name, for example "FR Doc. 2026-18842 (CDD amendments)", never a full title
that names the regulated parties (`house-rules.md` § 2).

An assertion without these is not usable in a regulator-facing artifact. In that destination,
**a missing sentence is a better outcome than an uncited one.**
