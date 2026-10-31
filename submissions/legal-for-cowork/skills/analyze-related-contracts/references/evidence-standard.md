# Evidence standard and worked example

## Citation rules

- Every relationship, effect and operative term entry cites a **document name +
  provision** — "Deed of Variation cl 6.1", "Master Services Agreement schedule
  2 ¶4", "Deed of Novation recital B" — and quotes or closely tracks the
  operative wording. Name the document; never cite it by a code.
- Cite the provision that **defines** a term, date, party or amount, not merely
  a later provision that repeats it. Where an amendment changes it, cite the
  amending provision and show original → changed.
- Preserve concrete specifics: amounts, currencies, dates, notice periods,
  thresholds, carve-outs and party-specific asymmetries. Never flatten these
  into "the amendment changed the liability terms".
- Never fabricate or reconstruct a clause number, quotation, date, party name,
  figure, or document that is not in the supplied set.
- Distinguish **found in the text** from **inferred**. Anything inferred from a
  filename, folder name or plausibility is labelled `Inferred — needs review`.
- If a document is unreadable, say so by name, state what that prevents ("the
  operative fee cannot be confirmed"), and do not estimate around it.
- In a generated report, use human-readable document names and provisions. In a
  chat claim about a supplied document, quote the exact wording and attribute it
  inline to the exact filename plus its clause, schedule or page; never expose a
  filename-only or internal identifier in place of a provision.

## Scope and assumptions

- **Source set = only the documents the user supplies.** Never assume a document
  exists that was not supplied, and never reconstruct a missing amendment. Where
  the user points at a folder, enumerate it and confirm the resulting source set
  with them.
- **Read-only.** Never edit, move, rename or delete a source document.
- **No party perspective is assumed.** The report is neutral unless the user
  states which party they represent.
- **Execution and validity are out of scope.** Report signature blocks and dates
  as found; never conclude that a document was validly executed or delivered, or
  is enforceable. For whether a single document is complete enough to sign, the
  `check-execution-readiness` skill owns that question.
- If jurisdiction, governing law or a defined term is needed but absent from the
  supplied set, record it as a gap rather than supplying a plausible value.

## Worked example

*Hypothetical.* The user supplies five files: a Master Services Agreement dated
12 Jan 2022, an Amendment No. 1 dated 3 Mar 2023, an unsigned "Amendment No. 2
(draft)", an Amended and Restated Master Services Agreement dated 1 Feb 2024,
and a scanned statement of work whose text layer fails to extract.

Correct handling:

- The Documents sheet lists all five **by name** — no `Doc ID` column. The
  unsigned draft and the unreadable scan are not dropped: each carries a `Dates
  / timing` entry using `Signed`, `Effective` and `Expires`, with the expiry
  mechanism stated explicitly, and its problem is recorded in Conflicts & gaps
  (`Needs review — unsigned draft`; `Missing source — unreadable, no text
  layer`) with what that prevents.
- Amendment No. 1 cl 3 is cited as amending the Master Services Agreement cl 8.1
  (liability cap £1m → £2.5m, effective 3 Mar 2023). The Amended and Restated
  agreement is classified `amends and restates` the original, citing its recital
  and integration clause, and the report states that from 1 Feb 2024 the
  restated text governs — while noting that Amendment No. 1's cap change
  survives only if the restatement carries it forward, quoting its cl 8.1 to
  show whether it does.
- Because the scanned statement of work cannot be read, the report does not
  guess its scope or fees. It records that the operative statement of work
  cannot be confirmed and asks for a text-readable copy.
- If the unsigned draft purports to change the same cap, the report does **not**
  treat it as operative; it appears in the Documents sheet and in Conflicts &
  gaps as a `Needs review` item asking whether an executed version exists.
- The report never concludes whether the restatement validly superseded the
  original as a matter of contract law. That goes in Conflicts & gaps as a
  `Counsel decision`, with **both readings inside the Issue cell** — the
  supersession and integration wording on one side, the survival carve-out on
  the other — and no choice made between them.
- Where a party's signature block or a schedule of key personnel carries
  identifiers — a national insurance or social security number, a home address,
  a date of birth, bank details or health data — the report cites the provision
  and says the source contains the detail, and reproduces none of it in any
  cell, quotation or chat summary, even if the user asks for such a column.
