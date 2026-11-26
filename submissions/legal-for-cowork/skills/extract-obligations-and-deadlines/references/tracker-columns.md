# Tracker columns, evidence standard, and the chat citation protocol

Loaded on demand by `extract-obligations-and-deadlines`. Nothing here overrides the guardrails in
SKILL.md.

## The default nine columns

| Column | What goes in it |
| --- | --- |
| **Party** | The specific party owing the obligation or holding the right, by name or defined role. Never `Party`, `Parties` or `All parties`. Where the provision applies to several, list each. Where the document does not identify the party clearly, use `Unclear` and explain in Notes. |
| **Category** | The principal legal or commercial topic — Assignment, Confidentiality, Data Protection, Disputes, Indemnity, Intellectual Property, Payment, Reporting, Term. Use a concise document-specific category where none fits, and apply labels consistently. |
| **Action** | A plain language summary beginning `Must`, `Must not` or `May`, so the mandatory, prohibited or optional character is preserved. No separate type labels. Do not copy the provision verbatim unless simplification would change its meaning. Retain material qualifications and defined terms; timing, triggers and consequences go in their own columns. |
| **Deadline** | The fixed date or contractual timing rule and, where reliably calculable, the calculated date plus its basis. |
| **Condition / trigger** | The event, condition, dependency or circumstance that activates or qualifies the action. |
| **Consequence** | The stated result of compliance, non-compliance, delay, failure or exercise; otherwise `Not stated`. |
| **Document** | The source document only, named exactly as supplied and written identically on every row from that document so the column filters cleanly. Add a short date or version where two documents share a name (`Amendment No. 1 (3 Feb 2026)`). Never put a clause reference here. |
| **Clause** | The human-readable locator within that document — clause, section, schedule, annex, exhibit or amendment provision. Give the locator alone (`cl. 5.1`, `Sch. 2, para. 4`), not the document name again. |
| **Notes** | Ambiguity, missing source material, unresolved tracked changes, calculation basis, apparent duplication or conflict, and the supersession markers. Put the supersession marker first in the cell so it is visible without expanding the row. |

Where the user's template carries the document reference in a single column rather than two, use
their single column and put the document name and clause together in it. Where the user has an
existing populated tracker, instruct Cowork's built-in Excel workbook creator to add new rows in their format rather than
restructuring their sheet, and never to overwrite or delete rows they already have. Do not add,
rename or reorder their columns; append an extra column only if the user agrees and no existing
column can carry a captured field.

## Evidence standard

- Every row must be traceable: the Document and Clause cells together must let a reader open the
  named document and find the provision without searching.
- Cite the provision that **defines** a party, date, amount or threshold, not merely a later
  provision that repeats it.
- Preserve concrete specifics — amounts, notice periods, thresholds, exceptions and party-specific
  carve-outs — rather than flattening them into a general description.
- Never fabricate or reconstruct clause numbers, dates, figures, defined terms or quotations.
- Separate mechanical extraction from judgement. Facts drawn from the text go in the columns;
  anything requiring interpretation is marked `Unclear` in the field and explained in Notes for the
  user or counsel to decide.

## Chat citation protocol

Where the user selected **In chat**, preserve citation discipline for every tracker row and every
substantive document claim in the accompanying summary.

1. Finish inspection and extraction first, then plan the complete set of exact supporting citations
   before writing the reply. Do not assemble citations incrementally.
2. Quote the operative wording inline and cite it by exact document name plus the precise locator —
   clause, section, schedule, page, or sheet and cell. Use the most specific location containing the
   support, including a paragraph inside a table cell, and quote the exact verbatim source text.
   Every tracker row needs at least one citation; use additional citations where its fields depend on
   more than one source location.
3. Verify each citation against the source text before delivering. If one cannot be verified, correct
   only that citation; never restate ones already verified.
4. Write the complete tracker as the normal final reply. In each row's Clause cell give the
   human-readable locator, and put the document name and its locator immediately after the
   punctuation of any grounded sentence in the summary. Never expose internal identifiers, file paths
   or tool mechanics in the prose.

## Further worked examples

**Optional right.** *"The Customer may terminate on 30 days' written notice following a material
breach."* Action reads `May terminate on 30 days' written notice` so the optional right stays
distinct from a duty; trigger is `Material breach by the Supplier`; consequence is `Not stated` if
none is given.

**Supersession.** The MSA sets a 30-day payment term at cl. 5.1 and Amendment No. 1 cl. 3 replaces it
with 45 days. Keep both rows. The MSA row reads `Superseded — replaced by Amendment No. 1, cl. 3` in
Notes; the amendment row reads `Supersedes Supplier MSA, cl. 5.1` and records the current obligation.
If instead a later order form simply states a different term with no amending language, mark both
rows `Unclear — possible conflict` and leave which one governs to counsel.

**User template.** The user asks to use the matter tracker they attached. Read it and adopt its
headings exactly. If it has `Owner`, `Obligation`, `Due`, `Ref` and `Comments` but no consequence
column, map the consequence into `Comments` and say so. Leave `Owner` blank if it means the internal
responsible person, which the contract does not state.
