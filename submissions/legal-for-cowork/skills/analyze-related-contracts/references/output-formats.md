# Related Contracts Report — output formats

The user's selected format and template always win. Word is the recommended
default when the user does not choose. For Word or Excel, follow an uploaded,
attached or linked template when supplied; otherwise use the standard format
below.

## Template handling

Treat a supplied template as the formatting and structure authority: match its
section or sheet order, headings, column order, labels, terminology, date style
and professional presentation, while preserving every required finding,
conflict, gap and limitation from the analysis. If the template has no place for
a conflict or gap, add a clearly labelled section rather than dropping it. If a
required template field cannot be populated from the supplied documents, leave
it blank or write `Not stated`, as the template permits, and record the gap
rather than inventing a value.

## Standardized dates and timing

Use consistent labels wherever multiple document dates appear in one field or
cell. Write each value on its own line, in this exact order:

- `Signed: [date or Not stated]`
- `Effective: [date, mechanism, or Not stated]`
- `Expires: [date, mechanism, or Not stated]`

Do not alternate between `execution date`, `signature date`, `date signed` or
unlabelled dates. Use `Signed`, `Effective` and `Expires` throughout Word, Excel
and chat unless the user's template requires different wording.

## Standard Excel format

Hand the work to Cowork's built-in Excel workbook creator once to create, populate and format the workbook,
handing it the complete dataset and the formatting requirements below; it owns creation and placement.

**Exactly four sheets — do not add more.** They answer the four questions a
reviewer opens the file for: what have I got, how do they connect, what applies
now, and what still needs a human.

**Refer to every document by its name, never by a code.** No `D1`/`D2` IDs and
no `Doc ID` or `Ref` column in any sheet. Use a short readable name derived from
the document's own title — "Deed of Variation", "Amendment No. 1 to SOW-01",
"Master Services Agreement" — in every cell of every sheet, including inside
quoted evidence and cross-references ("Deed of Variation cl 6.1", not
"D2 §6.1"). Where two documents would share a name, disambiguate by date or
number, still without a code. Filenames belong nowhere in the report; the
document's name is what the reader recognises.

**Column headers are questions a reader can answer, not internal shorthand.**
Every header must be self-explanatory to someone who has not read this skill.
Use the exact headers below.

1. **Documents** — *Document · Document type · Parties · Dates / timing · Order
   in the relationship chain · How the order was worked out · Notes*.
   Sort by `Order in the relationship chain` (1 = earliest in the chain); this
   sheet is also the chronology, so do not create a separate sequence sheet.
   `How the order was worked out` states the basis — effective dates, execution
   dates, or, where the documents are undated, the chain of cross-references
   between them; say which was used. `Dates / timing` uses the exact three-line
   `Signed` / `Effective` / `Expires` format above. The `Expires` line is
   **never left blank**: give the date, or the mechanism and why no date can be
   given ("Expires: None of its own — runs with SOW-01, which terminates with
   the master agreement, cl 2.3 and cl 17.6"). Put the family-level counts in a
   header row above the table — documents supplied, read in full, further
   documents referred to but not supplied — rather than in a separate summary
   sheet. Do **not** add a `Governing law`, `Status` or `Read status` column:
   governing law belongs in Operative terms, and anything about a document's
   standing or readability belongs in Conflicts & gaps.

2. **Relationships** — *This document… · …affects this document · What it does
   to it (amends / amends and restates / replaces / terminates / supplements /
   incorporates by reference / assigns / renews) · Clause that does it · The
   words that do it · Which provision is affected · Effect on that provision
   (added / deleted / replaced / restated / suspended / renumbered) · What it
   said before · What it says now · When the change takes effect · Stated or
   inferred?*.
   One row per individual change, not per document — a document that changes
   five clauses gets five rows. The headers are written so a row reads as a
   sentence: *[A] does [C] to [B], by [D], which says [E]*. The `What it said
   before` / `What it says now` columns carry the clause-level detail; do not
   split them into a separate effects sheet.

3. **Operative terms** — *Term · Current version or value · Governing doc +
   provision · Effective from · Previous version(s) · Superseded by ·
   Confidence (stated / inferred / unconfirmed)*.

4. **Conflicts & gaps** — *Issue · Documents · Status (Counsel decision / Needs
   review / Missing source) · Impact if unresolved*.
   **Exactly these four columns.** Where the documents can honestly be read two
   ways, both readings and the wording supporting each go **inside the `Issue`
   cell** — "Two readings are open: [first, with its wording]; or [second, with
   its wording]. This report chooses neither." Never state the conflict without
   the competing readings: an issue the reader cannot evaluate is not a finding.
   **This sheet is mandatory and is never omitted, even when empty** — when
   nothing is unresolved, say so in one row. It is the only place the report
   records what it does not know, and it absorbs coverage and limitations:
   unreadable or partially read documents, unexecuted or draft documents, terms
   searched for but not found, and externally referenced documents that were not
   supplied all appear here as `Missing source` or `Needs review` rows stating
   what each prevents. Without it, an ambiguity has nowhere to go except a
   confident-looking cell.

**Cross-references between sheets name the issue, never a code.** Because there
is no `Ref` column, a pointer from another sheet reads "see Conflicts & gaps —
the missing SOW-01", not "see C8". If the user asks for short citable handles
during review, add a numbered reference column then — not by default.

**Every sheet explains itself.** Each carries, above its header row, a one-line
title ending "(Draft — for counsel review)" and, beneath it, a plain English
subtitle giving the question that sheet answers and any term a reader would not
otherwise understand — "What applies today? … 'Unconfirmed' means the wording
exists but its value is an unfilled placeholder." The workbook must be
intelligible with the chat transcript gone.

**Presentation.** Freeze the header row on every sheet, size columns to their
content, wrap text and top-align every data cell (these are long text tables,
not number grids), and band alternate rows. Colour-code the reader's decision
columns so status is visible at a glance — `Counsel decision` red, `Missing
source` amber, `Needs review` teal, and the same amber on `Unconfirmed` in
Operative terms and `Inferred` in Relationships.

### Workbook execution safety

Instruct Cowork's built-in Excel workbook creator to build the workbook in a small number of coarse,
independently verifiable steps. Do not put workbook setup, all report data and
all formatting into one large script, and do not make one call per row.

1. **Set up the worksheets.** Create or rename the four required worksheets
   before deleting any unwanted default worksheet. Never attempt to delete the
   workbook's only remaining worksheet. The workbook must contain exactly the
   four required sheets when this phase finishes. Verify the worksheet names
   before continuing.
2. **Populate the report.** Write titles, subtitles, headers and data in
   whole-sheet or other bounded batches. Use explicit worksheet names and range
   addresses throughout. Verify that each sheet has a non-empty used range and
   that its header row has the expected number of columns.
3. **Format and validate.** Apply presentation requirements with explicit
   worksheet and range references, then inspect sheet names and used range
   dimensions once more before reporting success.

Scripts run in a non-interactive automation environment. Never use `select()`,
`activate()`, an active worksheet, an active cell or any other API that depends
on user selection or application state. Freeze panes and apply formatting
directly to the named worksheet or target range.

If a workbook call fails, treat the workbook as potentially partially changed.
Inspect its worksheet names and used ranges, identify the first incomplete
phase, and apply only the missing changes to the same workbook. Do not rerun the
entire script blindly and do not create a replacement workbook unless the
original file itself is unavailable.

## Standard Word format

When Word is selected, produce the same **complete legal analysis** as a
`.docx`, but design it for reading in Word rather than reproducing the Excel
tables literally. Compactness comes from removing repeated labels and duplicate
statements, never from removing findings or evidence. Preserve every document,
clause-level relationship, operative term, conflict, gap, limitation, unresolved
reading, provision reference and exact quotation needed for legal accuracy.

Use these four report sections:

1. **Documents** — one compact chronology table, one row per document. Combine
   closely related fields where that improves readability, but retain the
   document name, type, parties, standardized dates/timing, relationship order
   and basis, and notes.
2. **Relationships** — group rows under the document that creates the effect.
   Keep one row per individual clause-level change, but combine the eleven Excel
   fields into readable columns covering: affected document; action and
   provision; operative wording; affected provision and effect; before → now;
   and effective date plus stated/inferred status. Do not create a separate
   heading and vertical key/value table for every relationship.
3. **Operative terms** — one consolidated matrix, one row per term, combining
   governing document/provision with the current wording or value, and previous
   version with the instrument that superseded it, without losing any dates,
   amounts, carve-outs, confidence labels or source references.
4. **Conflicts & gaps** — one compact four-column table matching the Excel
   fields, with both supported readings and their evidence inside the issue
   entry.

State a fact or quotation once in the most relevant section and use a
human-readable cross-reference elsewhere instead of repeating it. Do not use
document codes or opaque finding IDs. If exact source wording is too long for a
normal table cell, use a clearly associated evidence continuation row or an
evidence appendix; never omit, paraphrase or truncate it merely to shorten the
report.

Use table-oriented Word layout: repeat header rows, compact paragraph spacing,
readable 9–10 pt table text, sensible cell padding, and landscape pages for wide
matrices where useful. Avoid forced page breaks between individual documents,
relationships, terms or issues. Do not target, cap, pad or optimize for a page
count. The report is complete when every required finding and its supporting
evidence is present once, ambiguities and gaps are explicit, and the result is
readable without unnecessary repetition.

### Single-pass dispatch

After completing the analysis, write the complete report content to
`working/report-content.md` — the finished tables and findings exactly as they
are to appear, represented as compact data rather than bespoke prose for each
finding. Do not impose a content size limit, summarize findings away, or trade
legal exactness for a shorter document.

Hand the work to Cowork's built-in Word document creator **once**, handing it `working/report-content.md` as
the sole and complete report-content authority, together with the layout
requirements above. Instruct it explicitly that it must not re-research,
reinterpret, re-order, summarize, trim or add legal content, and must not ask
for the analysis to be restated in another form. Never trim, rewrite or
duplicate the legal report merely to satisfy a generic content brief.

Plan every section up front and hand over the whole report at once rather than
creating a draft and editing it in rounds, which risks a second model pass
reinterpreting the completed analysis. Require it to:

1. generate the DOCX in a single pass from the supplied content;
2. validate the generated DOCX with its own validator;
3. render once and visually inspect up to three representative pages covering
   the opening, a dense relationship or operative terms table, and conflicts &
   gaps;
4. fix only genuine generation or presentation defects, without changing,
   omitting, approximating or adding legal content; and
5. report the exact filename and location of the finished `.docx`.

Do not repeat the render-and-inspect cycle when the first inspection finds no
defect. If a defect is found, make one focused correction and rerun only the
validation needed to confirm it. Confirm the file exists from the creator's report
before telling the user it is ready. Keep chat to a short plain language
summary — put the detail and any confidential wording in the file, not in the
chat transcript.

## Standard chat format

Start with `### Related Contracts Report` and mark it `Draft — for counsel
review`. Use concise sections for Documents, Relationships, Key operative terms,
and Conflicts & gaps. Keep the analysis complete, but avoid repeating the same
evidence in prose and tables.

The **Key operative terms** section must be a Markdown table:

| Term | Current version or value | Governing document and provision | Effective from | Previous version(s) | Superseded by | Confidence |
| --- | --- | --- | --- | --- | --- | --- |

Use `Stated`, `Inferred` or `Unconfirmed` in Confidence. Use the standardized
`Signed`, `Effective` and `Expires` wording in any chat table cell presenting
multiple document dates. End with Conflicts & gaps, including an explicit
`No unresolved conflicts or gaps identified` statement when there are none.
