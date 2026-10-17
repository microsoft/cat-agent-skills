# Contract, version 3

Normative for `template-based-document-generation` 3.x. The scripts implement it, the fixtures test it, the verifier
judges output against it. If a script and this document disagree, the document wins and the script has a bug.

Persisted JSON schemas retain the `fill-word-template/` prefix for compatibility with existing jobs.

## 1. Promise

> One `.docx` template plus one plan (data) plus one values file (any JSON) produces one `.docx` whose
> every difference from the template corresponds to one operation in the plan, plus a report that lists
> every change and everything a person should look at.

No template-specific logic lives in the scripts. What counts as a field, an instruction or a part in
scope comes from a profile (section 8). What the document must become comes from the plan. The scripts
only know Word's file format.

## 2. Job directory

`inspect` creates `<workdir>/<job_id>/` with:

| File | Written by | Content |
|---|---|---|
| `snapshot.docx` | inspect | Exact copy of the template; the only preservation authority |
| `manifest.json` | inspect | Section 3 |
| `plan.draft.json` | inspect | A plan skeleton to complete. Written without keys still at their default, so it carries the decisions to make rather than a screenful of defaults. Omitting them changes nothing: reading it back restores every default and produces the same hash |
| `plan.json` | you | Section 4 |
| `values.json` | you | Section 5 |
| `report.json` | execute | The latest attempt's report. See verification.md |
| `attempts/<attempt_id>/` | execute | One directory per attempt: its own `report.json`, plus the document it produced or `failed-candidate.docx` |
| `output/<stem>__<job_id>.docx` | execute | The document of the most recent attempt that passed verification, with a copy of its report |

`execute` is rerunnable and every attempt leaves a durable record, including one rejected before it began:
a malformed `values.json` writes `attempts/<id>/refused.json` and sets `report.json` to `failed`, rather than
leaving the previous run's success standing next to a job that no longer works. Publication is ordered so that a
failed attempt can never destroy a document an earlier attempt verified: the new document is written to
its attempt directory first, `output/` is replaced only once verification has passed, and the previous
publication is moved aside rather than deleted, so a promotion that fails is rolled back and the report records
`delivery.published` as failed instead of asserting a delivery that did not happen. When an attempt
fails, `output/` keeps the earlier document and the report says so in its notes. `execute` never reads the
original template path again; `snapshot.docx` is hashed and re-inspected on every run and the manifest
must match. Two `execute` runs on one job at the same time are not supported.

## 3. Manifest

### 3.1 Paragraphs

Every `w:p` in every part in scope, in document order, nested paragraphs (text boxes) included:

| Key | Meaning |
|---|---|
| `id` | `<part>#p<index>`, the handle plans use |
| `break_count` | Line and page breaks in the whole paragraph, so an operation can address one past the stored preview |
| `text`, `truncated`, `text_sha256` | Paragraph text: `w:t` text, `w:tab` as `\t`, `w:br`/`w:cr` as `\n`, nested paragraphs excluded. Text is stored up to `limits.max_paragraph_text_chars`; the hash covers the full text |
| `style` | `w:pStyle` value |
| `container`, `container_id` | The nearest *real* container: `body`, `cell`, `textbox`, `footnote`, `endnote`, `header`, `footer`, `other`. Content controls, custom XML and tracked-change wrappers are transparent |
| `block_first`, `block_last` | Paragraph index range of the top-level block (paragraph or table) that holds this paragraph inside its container |
| `row_id` | `<part>#tbl<n>/tr<m>` when the paragraph is inside a table row |
| `flags` | `section_break`, `tracked_change`, `field_code`, `bookmark`, `comment_marker`, `drawing`, `in_control`, `empty`, `hidden`, `highlighted` |

`rows[]` lists every table row with its paragraph range, ordinal and the row count of its table.

### 3.2 Candidates

Text the profile's patterns or the document's structure suggest is not final content:

| `kind` | Source | `decision_required` |
|---|---|---|
| `field` | A field pattern match (`{{ x }}`, `[x]`, `<x>`, `____`, ...) | high and medium confidence |
| `instruction` | An instruction pattern match, or a hidden or highlighted text run | high and medium confidence |
| `control` | A plain-text or rich-text content control; the span is its displayed text | yes, unless a field candidate lies inside it |
| `blank` | An empty paragraph in a table cell | no |

Every candidate carries `id` (`<kind letter>:<part>#p<n>#<start>-<end>`), the span in paragraph-text
offsets, `text`, `label` (the inner text for fields), `name_guess`, `pattern`, `confidence`,
`context_before`/`context_after`, `mixed_formatting`, and for controls the `tag`, `alias`, `type`,
`data_bound` and `placeholder` attributes.

Overlap rules: instruction matches suppress overlapping field matches; among matches of the same kind,
the earlier pattern in the profile wins. Matches are not re-scanned inside inserted values.

**Eligibility.** A candidate is `eligible` unless its span covers a tab or break, lies outside a run,
sits under `w:ins`, `w:del`, `w:moveFrom`, `w:moveTo`, `w:fldSimple` or `w:customXml`, inside a
complex field (tracked by `w:fldChar` depth across runs), in a paragraph with a tracked paragraph mark, or
in a run where any text element declares a namespace (the run is rebuilt when it is filled).

Content controls decide fillability for *every* candidate kind, and the whole ancestry counts, not just the
nearest control: every token the span covers is examined, and one protected control anywhere under the span
makes the whole replacement ineligible. A candidate inside a control whose type is not `text` or `richText` is
ineligible, because a date picker or a drop-down holds a typed value rather than free text. A candidate under a
data-bound control is ineligible however deep it sits, including a plain control nested inside a bound one,
because Word repopulates a bound control from its custom XML part when the document opens and anything written
there is discarded in silence. Only the binding is inherited this way: a text control legitimately nests inside
a repeating section or a group. Each candidate records its enclosing control in `control`, and filling any candidate inside a
control clears that control's placeholder state. An ineligible candidate needs no decision; it stays in the
document and is reported as `unfillable`.

### 3.3 Findings

`repeated_text` is the safety net for a convention the profile does not know. A short paragraph text that
repeats and that no pattern claimed is reported, naming the string and its count, because that is the one way
a wrong document could otherwise be handed over quietly: such a marker is not a candidate, so nobody decides
it, and the residue scan cannot recognise it. Repetition is convention-independent evidence, since a template
author writes the same prompt into every slot. It reports rather than blocks, because no rule can tell whether
"Not provided" is a marker or an answer. Declaring a pattern for it in the profile turns it into a candidate
and the finding clears itself. Thresholds live in the profile's `repeated_text` block.

Constructs the policy classifies. `block` (signatures, macros, unreadable parts, too many candidates or
paragraphs, and a part whose byte-level and parsed views disagree) sets `blocked: true`; no plan draft is
written and execute refuses. `unsupported_part_markup` is the last of those: eligibility is decided on the
parsed tree while the filler edits bytes, so a part that only one of them understands (a non-UTF-8 encoding,
several aliases for the WordprocessingML namespace) is refused at inspection rather than at apply time. `report` (comments,
tracked changes, embedded objects, field codes, non-hyperlink external relationships, field-like text in
a part outside the scope) becomes a `template_finding` review item.

A zip entry that is not a valid OPC part name, carries no content type and is targeted by no relationship is
archive debris, not a part. Real documents contain it: some implementations delete a part by moving its entry
to `[trash]/0000.dat`. It is preserved byte-for-byte and noted, and it never makes a template unreadable. An
entry whose name could be folded onto a real part, such as a trailing dot, is still refused.

## 4. Plan

```json
{
  "template_sha256": "...", "manifest_sha256": "...",
  "decisions": [], "fields": [], "operations": [],
  "locale": {}, "review_flags": [], "instructions_used": [], "allow_large_deletion": false
}
```

Only `template_sha256` and `manifest_sha256` are required; everything else defaults. A `schema` and a
`contract_version` are stamped automatically and never have to be written. They exist so that a file left
over from an older package is refused with a clear message rather than half-understood, so supplying a
wrong one is still an error.

`manifest_sha256` is the canonical-JSON SHA-256 of `manifest.json` (sorted keys, compact separators,
defaults materialised). The draft carries the right value; a plan bound to another manifest fails.

### 4.1 Decisions

`{"candidate_id", "decision", "field", "reason"}` with `decision` one of:

| Decision | Effect | Review |
|---|---|---|
| `field` | Replace the span with the named field's rendered value (controls: also drop `showingPlcHdr` and the PlaceholderText style) | `mixed_formatting` when runs differ |
| `literal` | Ordinary text; nothing happens | `literal_high_confidence` for a high-confidence field candidate |
| `remove_text` | Delete the span; one adjacent space is absorbed | |
| `remove_paragraph` | Delete the whole paragraph (section 7) | |
| `keep` | Leave it in place deliberately | `kept` |

Every eligible candidate with `decision_required` must have a decision unless its paragraph is deleted
by an operation. Candidates inside a repeated row may be `field`, `literal`, `remove_text` or `keep`.

### 4.2 Fields

| Key | Meaning |
|---|---|
| `name` | `^[A-Za-z_][A-Za-z0-9_]*$`, unique |
| `type` | `string`, `integer`, `decimal`, `date`, `boolean` |
| `format` | string: `max_length`, `trim` (default true), `case` (`none`/`upper`/`lower`/`title`), `join` (for list values, default newline). integer: `thousands_separator`, `min`, `max`. decimal: `precision` (0 to 12, default 2), `decimal_separator`, `thousands_separator`, `rounding` (`half_even`/`half_up`), `min`, `max` as strings. date: `pattern` with tokens `YYYY`, `YY`, `MMMM`, `MMM`, `MM`, `M`, `DD`, `D`. boolean: `true_text`, `false_text`. Separators, month names, true and false text and the date pattern default to the locale |
| `absence_policy` | `required` (default; a missing, null or blank value fails the job), `sentinel` (insert `absence_text`, review `sentinel_used`), `empty` (insert nothing, review `empty_used`) |
| `source` | Path into `values.data`: dotted with `[n]` indexes (`client.name`, `items[2].qty`), or RFC 6901 (`/client/name`). Empty path is the whole data (or the whole item for repeat fields) |
| `literal` | A constant instead of a source; review `literal_value` |
| `repeat` | The `id` of a `repeat_row` operation; `source` is then relative to each item |

A `source` must be a well-formed path: dotted with `[n]` indexes, or an RFC 6901 pointer. An empty segment
(`client..name`) is a typo and is rejected rather than resolved.

Accepted JSON values: string types take any scalar or a list of scalars; integers take ints, integral
floats and ASCII digit strings without leading zeros; decimals take numbers and numeric strings;
dates take `YYYY-MM-DD`, optionally followed by a real time (`T10:30`, `T10:30:00Z`, ` 10:30:00+01:00`);
booleans take `true`/`false` and the strings true, false, yes, no, y, n, 1, 0. Nothing else is coerced. `\r\n` becomes `\n`. A value that
renders to the empty string is an absence. Rendered text may contain printable characters, `\n` and
`\t` only, and at most `limits.max_value_chars` characters.

### 4.3 Operations

| `op` | Keys | Effect |
|---|---|---|
| `delete_paragraph` | `paragraph` | Remove the paragraph. The sole paragraph of a table cell is emptied instead (its `pPr` kept) |
| `delete_range` | `from_paragraph`, `to_paragraph` | Remove every top-level block from the first paragraph's block to the last paragraph's block, both in the same container. A table between them goes too |
| `delete_row` | `paragraph` (any in the row) | Remove the table row. Removals are judged against what would survive, not against the template, so several operations that each look safe cannot together leave a table with no rows; an empty `repeat_row` counts the same way |
| `delete_break` | `paragraph`, `occurrence` (1-based, default 1) | Remove one line or page break, keeping the rest of the paragraph. Deleting a cover page leaves the next paragraph starting with a page break, which would render a blank first page; this removes it. Refused on a paragraph that is also deleted or also filled |
| `repeat_row` | `id`, `paragraph`, `source` | Replace the row by one copy per item of the list at `source`; field candidates in the row whose field has `"repeat": id` render from each item, other fields render once. Zero items removes the row (review `row_removed`) and counts as a deletion. Refused when the row contains a construct carrying a document-wide identity (a bookmark, a comment marker, a content control, a drawing, a footnote reference), because copying the row would duplicate that identity and there is no safe automatic remapping |
| `insert_paragraph_after` | `paragraph`, `text` or `field` | Add a paragraph after the anchor with the anchor's `pPr` (minus any section break) and its first run's `rPr`. Literal text is reviewed as `inserted_text` |

Conflicts are errors: a replacement or insertion in a deleted paragraph, overlapping replacements,
overlapping repeated rows, a direct replacement inside a repeated row (use repeat-scoped fields).

### 4.4 Locale, flags, notes

`locale` overrides the profile's locale for this plan. `review_flags[]` (`target`, `reason`) become
`review_flag` items. `instructions_used[]` is free text for the record. `notes` is optional free text
for the record, at most 2000 characters; the draft carries a reminder in it that may be removed or
replaced. `allow_large_deletion` is required when more than `limits.max_deleted_fraction` of the
paragraphs would be deleted.

Validation precedes transformation. A field whose type, format or locale does not validate is never
rendered, so an invalid setting produces a named error rather than a formatted value or a crash. Errors are
collected across the whole plan, so one bad field does not hide the rest.

## 5. Values

`{"data": <any JSON>}`, with an optional `provenance` string. The shape of `data` is yours; the plan's
`source` paths map it onto fields.
Every leaf path of `data` that no field or repeat consumed is listed once in an `unused_input` review
item, so silently dropped data is visible. A leaf counts as consumed when a field read it or read an
object containing it. Paths are compared segment by segment, never as rendered strings, so a literal key
`"client.name"` is different data from a nested `client` then `name`. What is displayed is capped; what is
counted is not.

## 6. How text is written

- The paragraph text model is the same for the inspector, filler and verifier, so offsets agree.
- A span split across runs is consolidated into its first owning run; later runs lose the covered
  characters and keep their elements. The first run's formatting applies to the whole value.
- The value is written as `w:t` elements with `w:br` for `\n` and `w:tab` for `\t`, all inside the
  first owning run, escaped exactly once, with `xml:space="preserve"` wherever whitespace matters.
- An empty paragraph (blank cell, empty control) gains one run carrying the paragraph mark's `rPr`.
- Untouched parts are byte-identical; touched parts are edited in place at byte level so every root
  namespace declaration, `mc:Ignorable` list, rsid and paraId survives.

## 7. Deletion safety

Every operation that makes content disappear goes through the same checks, whichever one it is: a deleted
paragraph, a deleted range, a deleted row, the content of a cleared cell paragraph, and a repeated row whose
input list is empty. Refused: a region containing a `w:sectPr`; a region whose bookmark or comment markers
are not all inside it, taking every removal in the run together; a deletion that would leave a table cell,
body, header, footer, footnote or text box without a paragraph; deleting the only paragraph of a content
control (delete the range covering the control instead); a range whose endpoints lie in different containers.

Deleting more than `limits.max_deleted_fraction` of the paragraphs needs `allow_large_deletion`, and rows
removed by an empty repeat count toward that fraction.

## 8. Profiles: templates as configuration

A candidate's `name_guess` is a proposal, never authoritative. When several field candidates guess the same
name, which happens whenever a template repeats one prompt such as `<insert here>` down a column of labelled
rows, each is renamed from the label that precedes it, so a plan built from the draft cannot write one value
into every row. A genuinely repeated placeholder such as `{{ client_name }}` keeps its single shared name.

`references/profile.default.json` declares `parts_in_scope` (globs), `field_patterns` and
`instruction_patterns` (name, Python regex, confidence; group 1 is the field label), `instruction_formatting`
(confidence for hidden and highlighted text), `blank_cells`, `repeated_text` (`min_occurrences`,
`max_chars`; omit the block to disable the check), and `locale`. A per-job profile passed to
`inspect --profile` is merged over it: its patterns take precedence and come first, `disable_patterns`
removes defaults by name, `parts_in_scope` replaces, `locale` merges. The effective profile is recorded in
the manifest, so execute re-inspects with exactly the same rules. A pattern is rejected when it is longer
than 1000 characters, uses back-references, or applies a quantifier to a group that already contains one
(`(a+)+` and the like), because that shape backtracks exponentially on a near miss and one paragraph would
hang the inspection. Introducing a template family with new conventions means writing a
profile, not changing code.

## 9. Identity and hashing

Document hashes (`manifest_sha256`, `plan_sha256`, `values_sha256`) are SHA-256 over canonical JSON.
File hashes (`template_sha256`, `policy_sha256`, the output) are SHA-256 over bytes. The filler checks
the text hash of every paragraph it touches; the verifier derives every expectation from the snapshot.
`SKILL_VERSION` and `CONTRACT_VERSION` live in `scripts/models.py`; a job from another version must be
re-inspected.
