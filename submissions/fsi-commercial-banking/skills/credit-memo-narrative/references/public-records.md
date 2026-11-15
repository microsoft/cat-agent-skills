# Public Records and Company Research

Shared reference for skills that research an entity from public sources. Read with `house-rules.md`, which governs source tiers, the credit-decision gate, and the markers.

## Routes

**A route is how you reach a source. It is not the same as which source to prefer.** Source order is defined once in `house-rules.md` ("Source resolution order") and governs everywhere. This section only covers how to *reach* a public record once that order points you at it.

Check what this session supports rather than assuming a route.

1. **Configured connector** covering the fact you need — business credit, firmographics, entity hierarchy, aggregated liens. Use it and record it as a connector source with its as-of date.
2. **The issuing authority's own site**, reached by whatever direct or browser retrieval this session supports.
3. **A document the user holds** — a certificate of good standing, a lien search report, a prior brief.
4. **Secondary source**, only when the above are unreachable and only when marked `UNVERIFIED — secondary source`.

A retrieval failure is an access failure for that source in this session — never evidence that no route exists and never evidence that the record is absent. Retry once, then record `NOT RETRIEVED` naming the source. Use `NEEDS FEED` only when no source exists in this session, and `NOT FOUND` only when the source answered with no record; never collapse the three markers.

Some government and registry sites block automated access or are form-driven. When that happens, say which source could not be reached and what it would have told you. Do not silently substitute a data aggregator for the registry.

**Decide the browser per item, not once for the session.** Where a configured connector supplies the item in front of you — the registration, the firmographic record, the aggregated lien index — use it and do not open the browser for that item. Browse only for the items no connector covers. Treat a fetch that fails as an access failure *for that source in this session*, **not a universal platform contract** — it is never proof that the browser is the only route, and it must never be reported that way. **If a direct route works, use it and do not ask the user to enable a browser unnecessarily.**

**Connector data is a vendor's rendering of the underlying record, not the record itself.** That changes what you may claim: cite the connector and its as-of date, and where the point turns on the filing rather than the vendor's summary of it, say so — do not let the rendering stand in for the record.

**A connector being configured does not mean it holds the item.** If it returns nothing for the item you need, that is a connector miss — continue to the next route. It is never a dead end, and it is never reported as the record not existing; a connector that does not carry a filing tells you nothing about whether the filing exists.

**A partial or stale connector answer is a miss for whatever it does not cover.** An aggregated lien
or judgment index that returns some records has not established the rest, and a registry status older
than the date you are relying on has not established current standing. Where the claim is a count, a
complete set, or an absence — no liens, no judgments, good standing — a non-empty connector answer
does not end the search: confirm against the issuing authority, or mark that coverage `partial` and
name what was not covered.

**Some items still call for the browser even with a connector configured.** Where the authoritative filing *is* the evidence — UCC lien position, judgment records, entity good-standing — go to the issuing authority; a vendor summary is a different authority tier and cannot settle lien priority or standing. Borrower narrative and covenant language live in the credit agreement, not a data feed — read them there, not from an aggregated profile.

## Entity identity — resolve this first

**Every public-record finding is worthless if it is attached to the wrong entity.** Commercial borrowers routinely share names with unrelated companies, operate under trade names, and hold assets in affiliates.

Before searching, establish and record:

- **Exact legal name**, including suffix — `LLC`, `Inc.`, `L.P.` — as registered.
- **Jurisdiction and registry identifier** — state of formation, entity/file number.
- **Formation date** and current status.
- Any **trade names, former names, and d/b/a** registrations.
- **Affiliates and parent** where the request concerns a group.

Take these from the borrower's own documents or the registry, not from a search result. Where the user supplied only a trading name, say so and resolve it before reporting findings.

Every finding carries the entity name and identifier it was found under. Where a record is a plausible but unconfirmed match — similar name, same city, no identifier — mark it `GAP — possible match, identity not confirmed` and say what would confirm it. Never merge a possible match into the profile as fact.

## What each source establishes

| Source | Establishes | Does not establish |
|---|---|---|
| Secretary of State / companies registry | Legal name, status, formation date, registered agent, officers where filed | Ownership, financial condition, anything outside that state |
| UCC filing search | Secured filings **of record under the name searched, in that jurisdiction** | That no liens exist — see below |
| County recorder / land records | Recorded mortgages, deeds, some judgments and tax liens by county | Anything in a county you did not search |
| Court dockets | Filed cases where the index is public and searchable | Outcome, merit, or completeness across jurisdictions |
| SEC EDGAR | Filings of SEC registrants | Anything about a private company — absence here is normal |
| FDIC BankFind / FFIEC | Institution identity, charter, call-report data — for **bank** counterparties | Non-bank borrowers |
| Census, BLS, BEA, FRED | Industry and macro context by sector and geography | Anything specific to this borrower |
| Company site, press releases | What the company states about itself, on its stated date | Independent verification of those statements |
| Trade press, news | Reported events, with a publisher and date | Fact — attribute it, and never repeat an allegation as a finding |

## Lien and litigation searches — state the limits

A public-record search result is only as good as the name, jurisdiction, and date it was run under. Report all three with every finding **and** with every clean result.

**A clean search is not proof of absence.** UCC financing statements are indexed by the debtor's exact legal name; a search under a variant, a trade name, or a former name can return nothing while filings exist. Searches are also per-jurisdiction and lag filing by days or weeks.

So the correct output for a clean search is:

```
NOT FOUND — no UCC filings of record for "Ridgeline Fabrication, Inc." (DE file 1234567)
in the Delaware Secretary of State index, searched 2026-09-27. Exact-name index; a search
under variant or former names, or in other jurisdictions, may return different results.
```

Never write "no liens" or "the borrower is unencumbered." That is a conclusion the search does not support, and in credit work it is the kind of statement that gets relied on.

The same applies to litigation and judgment searches: report the index, the jurisdiction, the name searched, and the date, and never characterise the borrower's litigation posture.

Where a formal search is required for the credit file, say that a registry search report ordered through the bank's normal process is the authoritative record and this research does not replace it.

## SEC EDGAR

Most commercial borrowers are private and will not appear. `NOT FOUND` on EDGAR is a normal, reportable result — not a failure, and not a reason to keep searching.

Where the borrower, its parent, or a public competitor **is** a registrant:

- Company and filing lists are reachable from EDGAR's company browse endpoint, which accepts a ticker directly and returns the CIK alongside the filing list — so a separate CIK lookup is usually unnecessary.
- Within a filing, the rendered financial-statement pages typically carry a full statement across three fiscal years in a single page, which is far cheaper than assembling figures line by line. Confirm which page holds which statement from the filing's own summary before relying on a page number.
- Cite form type, period end, and accession number, plus the caption as printed.

Public-filer figures are a **public record**, not borrower-supplied, and the two are never interchangeable in a spread. Say which you used.

## Freshness

Every public-record finding carries the date it was retrieved, and, where the record shows one, the date the record itself was filed or last updated. These are different dates and both matter.

Registry data lags reality. State the retrieval date rather than implying currency, and use `AS OF <date>` where a record is known to be stale.

## Scope

This research is **input to** credit analysis, never a substitute for it and never a screen.

- It is not a sanctions, PEP, adverse-media, or watchlist screen. Where a name-screening obligation applies, it is met through the bank's own screening process.
- It is not a credit bureau report, a business credit score, or a formal lien search.
- It does not support a creditworthiness characterisation, a pre-qualification, or a statement of credit appetite. See the credit-decision gate in `house-rules.md`.

Personal information about principals is limited to what is necessary and business-relevant — role, tenure, and business affiliations from public sources. Never collect, infer, or repeat a protected characteristic, and never report a principal's personal financial or legal history into a credit-related deliverable unless the user supplies it from the bank's own file.
