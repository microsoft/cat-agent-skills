# Product Content & Catalog Enrichment

For merchandisers and PIM stewards turning supplier spreadsheets, spec sheets and manuals into
channel-ready records that satisfy a taxonomy, a brand voice and a regulated-claim boundary.

It ingests supplier sources, normalises attributes against the taxonomy with GTIN validation,
scores completeness per channel, validates claims and regulated terms against the approved
claim library, and drafts the descriptions and review packet.

This is the one plugin both sides of the trading relationship use, from opposite ends of the
same feed.

## How it works

1. Reads supplier sheets, specs and portal exports.
2. Normalises to the taxonomy, validates GTIN check digits (deterministic).
3. Scores completeness per channel and names the missing fields per SKU.
4. Validates claims against the approved library — the Govern step.
5. Drafts descriptions, comparison copy and the review packet.

## Example scenario

*"Use the copy as written, launch Friday, their legal reviewed it."*

- One GTIN **fails the GS1 check digit** — the record is blocked before anything else runs.
- *"Kills 99.9%"*, *"antibacterial"* and *"biodegradable"* are regulated terms with **no
  substantiation in the claim library** for these products. The supplier's own legal review is
  not your substantiation.
- The draft ships with approved attributes only. Blocked claims never appear in the output.

## What you bring

PIM and GDSN records, supplier spreadsheets and portals, product manuals and specifications,
your approved claim library, brand and taxonomy guidelines, channel templates, and
regulated-term lists.

## Boundaries

Ends at an approval-ready draft record. It does not publish to channel, approve a regulated
claim or change the taxonomy.
