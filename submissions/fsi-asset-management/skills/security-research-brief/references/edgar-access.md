# SEC EDGAR — Access Guide

## Choosing a retrieval route

**A route is how you reach a source. It is not the same as which source to prefer.** Source
order is defined once in `house-rules.md` ("Source resolution order") and governs everywhere.
This section only covers how to *reach* a source once that order points you at it.

**Check what this session actually has, then reach the source by:**

1. **A configured data connector**, if one carries the item you need. Fund-data providers and
   `Morningstar` supply fund facts — expense ratios, holdings, returns, and category
   classifications; `FactSet` and `S&P Capital IQ` supply issuer fundamentals as standardized
   figures. Say you used the connector, because standardization changes
   comparability versus as-reported filing figures.
2. **A direct retrieval route**, where the session supports one.
3. **The browser route documented below.** In Cowork environments observed to date, direct URL
   fetches fail with DNS resolution errors and the browser is the working route to `sec.gov`.
   The user must permit browser use for the session.

Whichever route you use, the approach is **"open a few pages and read them,"** not "call an API
per metric."

**Decide the route per item, not once for the request.** If a configured connector supplies the
item in front of you, use it and do not open the browser for that item. Browse only for items no
connector covers.

**A connector being present does not mean it holds the item.** If it returns nothing for the item
you asked for, that is a connector miss — continue to the next rung. A miss is never a dead end,
and it is never reported as the item not existing.

**A partial or stale connector answer is a miss for whatever it does not cover.** A connector that
returns some of the periods, some of the share classes, or a value older than the filing you are
citing has not answered the item — take the remainder from the filing and say which part came from
where. Where the claim is a count, a complete set, or an absence, a non-empty connector answer does
not end the search.

**Some items stay on the browser route even when a connector is configured:**

- **Narrative text** — MD&A, risk factors, strategy/objective language, and principal risks. Check whether the actual connector supplies complete, attributable passages; do not assume a standardized financial-data feed includes them. Retrieve the filing for whatever it does not cover.
- **As-reported figures where the accounting basis matters.** Connectors return standardized
  values; when the claim depends on the figure as the issuer reported it,
  read the filing.
- **Citations that require a primary identifier** such as an accession number.
  `security-research-brief` requires these, and a standardized connector record does not carry
  them.

Treat step 3's observation as what to expect, **not as a universal platform contract**. A fetch
that fails is an access failure *for that source in this session* — it is not evidence that no
HTTP or API access exists, and it must never be reported that way. If a direct route works, use
it and do not ask the user to enable a browser unnecessarily.

## Discovery method is not source authority

**How you found a document and what the document is are separate properties.** A web search that
leads you to a filing on `sec.gov`, which you then open and read, gives you a **filed record** —
cite it as the filing. The search was navigation, not the source.

What makes something secondary is that it *reproduces* the record rather than being it.

**Record coverage separately from identity.** Every citation carries both:

| Coverage | Means |
|---|---|
| `complete` | You read the whole relevant section or document |
| `partial` | You read part of it — say which part |
| `snippet only` | You saw a search result or excerpt, **not** the document |
| `unavailable` | You could not open it |

**A search snippet is never sufficient evidence for a claim about a filing's contents.** If all
you have is a snippet, open the filing or report the gap. Never let a snippet stand in for the
document it quotes.

> **If no retrieval route is available**, say so plainly and offer two paths, in this order:
> 1. Ask the user to upload the document (filing, prospectus, fact sheet) by name.
> 2. If they decline, you may search the web — but anything **reproducing** the document is a
>    **secondary source**, even when it reproduces it verbatim, and must be labelled
>    `UNVERIFIED — secondary source`.
>
> Never answer from memory.

---

## Route A — Operating companies (issuers)

### 1. Find the company and its filings

```
https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&ticker=<TICKER>&type=<FORM>&dateb=&owner=include&count=10
```

~16 KB. Accepts a **ticker directly** — no CIK lookup needed. Returns CIK plus a filing table.

Set `type` to `10-K`, `10-Q`, `8-K`, or `DEF 14A`.

If you only have a name, use `&company=<NAME>` instead. If several issuers match, **list the
candidates with ticker and CIK and ask.** Never guess between similar names.

### 2. Read the numbers from R-pages

Every XBRL filing has generated per-statement tables, far smaller than the full document:

| Page | Contains |
|---|---|
| `R3.htm` (approx.) | Statements of operations — revenue, margins, operating income, net income, EPS |
| `R5.htm` (approx.) | Balance sheets — cash, debt, equity |
| `R8.htm` (approx.) | Cash flows — D&A, capex, operating cash flow |

```
https://www.sec.gov/Archives/edgar/data/<cik>/<accession-no-dashes>/R3.htm
```

**R-numbers are not fixed.** Confirm via `FilingSummary.xml` in the same folder (it lists each
report's `ShortName`) or by checking the page heading before reading figures off it.

One R-page carries **three fiscal years** (~90 KB), so period-over-period comparison comes free.

### 3. Read narrative from the primary document

Risk factors, MD&A, and segment discussion come from the 10-K/10-Q itself. **A large 10-K is
~1.5 MB of HTML.** Navigate to the section you need rather than reading linearly, and **say so
if you could only retrieve part of it.** Never report a section as absent when you did not
reach it.

---

## Route B — Funds

### 1. Find the fund by its ticker

```
https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=<FUND_TICKER>&type=497K&dateb=&owner=include&count=10
```

~14 KB. **A fund share-class ticker works directly here** (verified with VFIAX and FXAIX) —
EDGAR resolves it to the class and returns the trust's filings. No series/class lookup needed.

### 2. Read the 497K summary prospectus — the workhorse document

The summary prospectus is **13–18 KB of text** and carries nearly everything needed for a
product comparison:

- Investment objective
- **Fee table** — management fee, 12b-1, total and net expense ratio, waivers
- Principal investment strategy
- Principal risks
- Past performance table (annual returns, 1/5/10-year averages)

This is the right source for competitor product facts. Cite it as:
`(497K summary prospectus, filed <date>, <fund name>)`

### 3. Large documents — size is a constraint, not a prohibition

**Portfolio holdings.** N-PORT is the public holdings filing. Measured for one large fund at
**488 KB of raw XML**, with EDGAR's rendered view (`xslFormNPORT-P_X01/`) at **9.5 MB** — far
past what a browser read handles. **Expect that scale**, and do not plan a workflow around it.

That is a measurement, not a universal rule. If a session has a retrieval capability that can
handle a document that large, use it and **state the coverage you achieved**. Never refuse a
filing solely because of an assumed size, and never promise that a large filing is retrievable.

Without such a capability, get top holdings from the **fund company's public fact sheet** —
usually the top ten, current, and one page. Say that it is the top ten and give its as-of date.

For full holdings, resolve the outcome rather than assuming a connector-only gap. N-PORT and
N-CSR filings are public EDGAR sources, but they are periodic, lagged, and can be too large or
granular for a browser read. If a complete holdings filing is retrieved, cite the filed record
with its period, as-of date, coverage, and any lag. If no workable source exists in the session,
mark `NEEDS FEED — Morningstar Direct, eVestment, or another holdings source`. If EDGAR, a
connector, or a fund site exists but access was denied or retrieval failed, mark
`NOT RETRIEVED — <source> <failure>`. If the source answered and has no holdings record for the
requested fund/share class/period, mark `NOT FOUND — <source> has no record for <what>`.

**ADV** is reachable at `https://reports.adviserinfo.sec.gov/reports/ADV/<CRD>/PDF/<CRD>.pdf`
but measured **7.8 MB** for a large firm. Use it for a specific lookup, not as a routine source,
and report the coverage you actually achieved.

---

## When the browser fails

Page loads through the browser time out. Observed on the platform: a first attempt returned
nothing for all three companies in a request; the identical request succeeded on retry.
**Retry once before concluding anything.**

**A failed page load is not evidence of absence:**

| Situation | Marker |
|---|---|
| Page loaded; the item is genuinely not disclosed | `NOT FOUND — not disclosed in <form>` |
| Page would not load, after a retry | `NOT RETRIEVED — <page> did not load` |

Reporting `NOT FOUND` for a page you never opened states that a company failed to disclose
something it may well have disclosed. That is a false statement about a filing.

If pages fail repeatedly, **stop and say so** rather than returning an empty deliverable.

Expect multi-entity requests to be slow — each fund or company costs two or three page loads.
Keep comparison sets to **3–5 names** per pass and offer to extend.

---

## Four gotchas that will corrupt your numbers

**1. Check the column you are reading.** Statements show three fiscal years side by side, most
recent first. Confirm the period heading (e.g. "12 Months Ended Sep. 27, 2025") before taking a
figure.

**2. Check the units.** Headers declare scale — `shares in Thousands, $ in Millions`. The
figure `416,161` means **$416.161 billion**. Misreading scale produces 1000× errors.

**3. Fiscal year ≠ calendar year.** Apple's FY2025 ended 2025-09-27; Microsoft's FY2026 ended
2026-06-30. **Never compare on fiscal-year label.** Always show the period end date.

**4. Fee tables have gross and net.** Expense ratios often show a gross figure and a net figure
after contractual waivers, with an expiry date. Report **which one** you used and note the
waiver expiry — comparing one fund's gross to another's net is a real and common error.

---

## Reading line items

Use the company's own labels rather than guessing at tag names. Expect wording to vary:

| Item | Labels you will see |
|---|---|
| Revenue | Net sales · Total revenue · Total revenues · Total net sales · Revenues |
| Operating income | Operating income · Income from operations · Operating profit |
| Net income | Net income · Net income attributable to <company> |
| Expense ratio | Total annual fund operating expenses · Net expenses after waiver |

**Record the exact label you used.** When entities use different labels they may mean different
things — flag it rather than silently treating them as equivalent.
