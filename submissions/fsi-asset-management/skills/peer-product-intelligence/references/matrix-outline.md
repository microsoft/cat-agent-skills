# Default Comparison Matrix

Layout for `peer-product-intelligence`. A house template in
`Cowork Templates/Asset Management/peer-product-intelligence/` may replace this layout, subject to the guardrails below.

A house template governs **layout and section structure only**. It never removes citations, gap markers, source tiers, approval states, information-barrier rules, no-send restrictions, or the output footer — those apply to every output regardless of template. Output length never waives attribution or the footer; a one-line answer, single table cell, inline reply, or short excerpt still carries both. If a save, export, or write fails, report what was produced, where it was and was not written, and what remains incomplete.

Built as `.xlsx`. **One column per fund, one row per field.** Every value cell pairs with a
source cell naming the document and its date. A single filled cell still needs that source cell;
there is no brief-output exemption from attribution or the footer.

---

## Sheet 1 — Comparison

| Row | Notes |
|---|---|
| Fund name | |
| Ticker | |
| **Share class** | Label explicitly — classes differ in fee |
| Structure | Mutual fund / ETF / CIT / SMA |
| Inception date | |
| Investment objective | Verbatim from the 497K, not summarized |
| Principal strategy | Condensed, but in the fund's own framing |
| Benchmark | As the fund states it |
| **Gross expense ratio** | Competitors: from the 497K fee table. **Our fund: current-figure rule** |
| **Net expense ratio** | After waivers. Competitors: 497K. **Our fund: current-figure rule** |
| **Waiver expiry** | Flag if within 12 months. **Our fund: current-figure rule** |
| Management fee | **Our fund: current-figure rule** |
| 12b-1 fee | **Our fund: current-figure rule** |
| Minimum investment | From the 497K as a filed product term, with its prospectus date — same for our fund as for competitors |
| Top 10 holdings | From the fund company's public fact sheet (issuer-authored), with as-of date — same for our fund as for competitors |
| Full holdings | Any source that supplies a matching record — a holdings connector, or a complete public holdings filing where one can be retrieved. Otherwise the outcome markers below |
| Peer percentile rank | Peer-universe connector, or any authoritative source with a matching record. Otherwise the outcome markers below |
| Star / analyst rating | Ratings connector, or any authoritative source publishing the rating, reported as published. Otherwise the outcome markers below |
| Net flows | Flows connector, or any authoritative source with a matching record. Otherwise the outcome markers below |
| Past performance (1/5/10yr) | Competitors: from the 497K table, cited with the prospectus date. **Our fund: current-figure rule** |
| Principal risks | Listed as the prospectus lists them |
| Prospectus date | **Flag materially different dates across the set** |

**Outcome markers for the four source-dependent rows above.** The workflow in `SKILL.md`
distinguishes five outcomes; the template must too. **Never collapse them into `NEEDS FEED`** —
each tells the reader a different thing about what to do next.

| Outcome | Cell |
|---|---|
| A matching record was obtained | The value, with source, product and share class, as-of date, basis |
| No source available for this field | `NEEDS FEED — <source that would supply it>` |
| Source exists but access was denied | `NOT RETRIEVED — <source> access denied` |
| Source exists, retrieval failed | `NOT RETRIEVED — <source> did not return` |
| **Source searched successfully, no record exists** | **`NOT FOUND — <source> has no record for <fund / share class / period>`** |
| Record returned but does not match identity, date, or basis | `GAP — <source> record does not match <what>` |

`NOT FOUND` means the source answered and the record genuinely does not exist — a fund too new
to carry a rating, for example. `NOT RETRIEVED` means no answer was obtained. Never substitute
one for the other.

**Own-fund current-figure rule — applies to the marked rows only.** Current performance, AUM,
expense ratios, management and 12b-1 fees, waivers, and attribution for **our own** fund come
from the system of record for that field, or the cell is left value-less carrying
`[VERIFY vs. system of record]`. Our own filed 497K records what we stated on its filing date; it
is not a source of our current fee or return.

**Everything else follows the normal provenance tiers**, with no own-fund exception. A filed
product term or an issuer-authored fact-sheet figure is cited as-of its date — for our fund
exactly as for a competitor's. Do not blank our own column for fields a competitor's column is
allowed to carry; an asymmetric matrix is a broken matrix.

Highlight your own fund's column.

## Sheet 2 — Sources

One block per fund:
- Document type, filing date, and URL for each value taken
- Fact sheet as-of date for holdings
- Which fields came from approved internal sources (our fund only)
- Any field marked `NOT RETRIEVED`, with which page failed

## Sheet 3 — Differences

Factual, field-by-field description of where the funds differ. Written as observations:

> "Fund A's net expense ratio is 0.45% versus Fund B's 0.62%; Fund A's waiver expires
> 2027-04-30, after which its gross ratio is 0.71%."

**Not** as conclusions:

> ~~"Fund A is the cheaper option."~~

The waiver example above is exactly why — a fund that looks cheaper today may not be next year,
and stating the fact lets the specialist see that while stating the conclusion hides it.

---

## Traps

- **Gross vs. net expense ratio.** The most common substantive error. Record both, always.
- **Share class mismatch.** Comparing an institutional class to a retail class is not a comparison.
- **Stale prospectus.** Check filing dates across the set before building.
- **Top-10 ≠ full holdings.** Always label which you have.
- **Performance periods that don't align.** Funds with different inception dates show different trailing periods; note it rather than presenting them as equivalent.
