# Submission Authoring Rules
Companion to the consistency_check engine (`base/scripts/consistency_check.py`). The engine's RULE_* constants
mirror the numbered rules below line for line, and every engine finding cites its rule number verbatim.
Grounding is swappable: a sponsor may replace this file with its own numbered SOP, keeping the numbering.

## #1 Cross-section numeric consistency
Every N, date and population definition asserted in a drafted section must equal the value in `source_facts`
(extracted from the protocol, SAP and TLF set by source-ingest). A mismatch is never auto-corrected by the model -
it is reported as an open item for the medical writer / biostatistician to resolve against the source.
A value that differs only in type (e.g. "248" vs 248, or 248.0 vs 248) is still a mismatch, reported as a type
mismatch, and the finding must name both types so the reviewer can see why two identical-looking values were flagged.

## #2 Population definition discipline
"Enrolled", "randomized", "completed" and "safety population" are distinct counts. A section must not substitute
one for another even when the numbers happen to coincide in a given source. When
`config/style-guide.json.population_terms_must_match_sap` is true, an asserted population count that does not match
its own source field but does match a different population field is reported as a population substitution.
`config/style-guide.json.numeric_format` governs precision: an asserted number that is a rounded form of the
source value is reported as a rounding violation, never accepted as equal.

## #3 Draft-first, never filed
`submission-assemble` never sets a submission to filed/submitted state. Assembly status is one of
`draft_clean` (0 open items) or `draft_open_items` (>=1 open item) - never `submitted`. The contract constrains
`assembly_status` to that enum, so a filed state is unrepresentable rather than merely discouraged. An input that
already carries any other status (e.g. `submitted`) is never silently overwritten: the computed draft state replaces
it and the replacement is escalated.
Action levels: L0 (read/analyse) for source-ingest, section-plan and consistency-check; L1 (draft for human
approval) for section-draft and submission-assemble. The plugin never operates above L1.

## #4 No unsourced assertion
An asserted field with no corresponding entry in `source_facts` is an unsourced assertion. It is reported as an
open item, never skipped and never counted as checked-and-clean. This is the machine-checkable form of
section-draft's "never assert a number that does not appear in source_facts".

## #5 Every fact cites its grounding
Every `source_facts` entry carries a `citation` naming the source document and table/section (TLF table, SAP
section, protocol section). Every asserted value carries the citation it was drafted from, and that citation must
match the citation on the source fact. A missing or mismatched citation is an open item; citations ride the
contract so provenance survives every hand-off.

## #6 Required-section coverage gates assembly
The required sections for the target submission type come from `config/submission-templates.json`
(`required_sections`), never from the model. Every required section must appear in `draft_sections` before
assembly. A missing required section - including the degenerate case of no drafted sections at all - is an open
item, so an empty or partial draft can never assemble as `draft_clean`. This is the mechanical form of
submission-assemble's dependency on consistency-check. A payload with no `submission` block or no
`submission.submission_type` cannot be gated at all; it is rejected (no report), never reported as an unknown type.
