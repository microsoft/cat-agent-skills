# Verification, review items and the report, version 3

## 1. Principles

1. **The snapshot is the only preservation authority.** Every comparison is against the unmodified
   `snapshot.docx`, hash-checked before use. The filler's intermediate state is never consulted.
2. **Every difference must correspond to one planned operation.** The verifier walks the snapshot tree
   and the output tree side by side. A deleted block is absent, a repeated row appears once per item,
   an inserted paragraph follows its anchor, a paragraph with replacements differs only inside the runs
   that own a replaced span. Anything else is a failure.
3. **Expected text is computed, never searched.** Paragraph and run texts are derived from the
   snapshot's text and the compiled values at the manifest offsets.
4. **Not performed is never passed.** Any check that did not run makes the result `failed`.
5. **Document-wide invariants are checked, not only the plan.** Matching every difference to an operation
   does not prove the plan was safe: a removal can unbalance a bookmark and a repeat can duplicate an
   identity while every individual edit looks authorised. `pkg.reference_integrity` checks the output as a
   whole, independently of what the plan intended.
6. **The output is scanned for residue.** After the structural walk, every output paragraph is run
   through the profile's field and instruction patterns. A match that lies inside an inserted value is
   data. A match inside a span the plan acknowledged (`literal`, `keep`, an optional or ineligible
   candidate) is acknowledged. Everything else is `residue`.

## 2. Checks

| Check id | Fails when |
|---|---|
| `input.plan` | Compile errors (only present when the plan could not be compiled; nothing else runs) |
| `fill.applied` | The filler refused (hash mismatch, deletion safety rule, malformed result) |
| `pkg.snapshot_readable`, `pkg.snapshot_matches_manifest` | The snapshot is unreadable or is not the manifest's template |
| `pkg.zip_readable` | The output is not a readable, structurally valid Word package within limits |
| `pkg.entry_set_identical` | Zip entries, order, compression or per-entry metadata differ |
| `pkg.untouched_parts_identical` | Any part without operations differs by one byte |
| `pkg.no_new_parts` | A part was added |
| `pkg.in_scope_parts_parse` | A modified part does not parse or has invalid namespace references |
| `pkg.no_new_relationships` | The multiset of `r:id`/`r:embed`/`r:link` references differs from what the planned deletions and repeats imply |
| `pkg.reference_integrity` | The output adds a document-wide structural problem the template did not have: an unpaired bookmark or comment range, a duplicate bookmark id or name, a duplicate drawing object id, a table with no rows, or a table cell with no paragraph. Checked against the template's own problems, so an already-odd template does not fail for being odd |
| `pkg.namespace_preserved` | A namespace declaration was removed, added, altered or moved; new elements carry declarations |
| `ops.structure_matches_plan` | A difference outside the planned operations, a missing deletion, a wrong copy count, a wrong insertion |
| `ops.paragraph_texts_expected` | A paragraph or owning-run text is not the computed expectation, or `xml:space` is missing |
| `ops.all_replacements_applied` | Fewer replacements verified than compiled |
| `delivery.document_size` | The output exceeds `limits.max_output_bytes` |
| `delivery.published` | The document verified but could not be promoted into `output/`. The previous publication is rolled back and kept |
| `input.accepted` | The run was rejected before it began, for example a `values.json` that is not readable JSON |
| `doctor` `workdir path length` | Windows only. Fails when the work directory leaves no room for a job's own file names inside the platform's path limit, because every later write would fail; a temporary file never exceeds the path it stands in for, so this is reported before a run rather than during one |

## 3. Result

| Result | Condition | Files |
|---|---|---|
| `failed` | Any check failed or did not run, or the plan did not compile | `report.json` and `attempts/<id>/report.json`; `attempts/<id>/failed-candidate.docx` when a document was produced. `output/` is left as it was, and the report's notes say so |
| `needs_review` | All checks passed and at least one review item exists | as above, plus the document in `attempts/<id>/` and published to `output/` |
| `ok` | All checks passed, no review items | same |

`needs_review` still publishes the document, because a reviewer needs the file in order to review it. A
deployment that must not hand out an unreviewed document should publish from `attempts/` on `ok` only and
treat exit code 2 as "hold", rather than reading `output/` unconditionally.

Exit codes of `execute`: 0 `ok`, 2 `needs_review`, 1 `failed` or refused (inputs invalid, stale job,
I/O error). `inspect`: 0 inspected, 1 blocked or unreadable. `--dry-run` writes nothing and exits 0
when the plan compiles, 1 otherwise.

## 4. Review items

| Code | Meaning |
|---|---|
| `residue` | Field-like or instruction-like text remains in the output and the plan did not acknowledge it |
| `unfillable` | An ineligible candidate stays in the document (reason given) |
| `kept` | A candidate the plan chose to keep |
| `literal_high_confidence` | A high-confidence field candidate declared literal text |
| `sentinel_used`, `empty_used` | A field rendered its absence text or nothing |
| `literal_value` | A field's value comes from the plan, not the data |
| `inserted_text` | A paragraph was inserted with text from the plan |
| `mixed_formatting` | A filled span crossed runs with different formatting |
| `row_removed` | A repeated row had zero items |
| `large_deletion` | More than the policy fraction of paragraphs was deleted, with `allow_large_deletion` |
| `unused_input` | Leaf paths in `values.data` no field consumed |
| `template_finding` | A `report`-severity construct in the template (comments, tracked changes, ...) |
| `review_flag` | A flag the plan raised |
| `no_operations` | The plan changes nothing; the output is a copy of the template |

## 5. Report

```json
{
  "schema": "fill-word-template/report/v3", "skill_version": "...", "contract_version": "3",
  "job_id": "...", "created_utc": "...", "template_sha256": "...", "policy_sha256": "...",
  "manifest_sha256": "...", "plan_sha256": "...", "values_sha256": "...",
  "result": "ok | needs_review | failed",
  "checks":  [{"id": "...", "outcome": "passed | failed | not_performed", "detail": "..."}],
  "review":  [{"code": "...", "detail": "...", "target": "..."}],
  "changes": [{"op": "...", "part": "...", "paragraph": "...", "before": "...", "after": "...", "detail": "..."}],
  "output":  {"filename": "...", "sha256": "...", "size_bytes": 0},
  "notes":   ["..."]
}
```

`changes` lists every operation with the paragraph text before and after (bounded by
`limits.max_report_text_chars`), so a reviewer can check the document against the plan without
opening the XML. A deletion reports how many paragraphs go, where the range starts, where it ends, and
samples between: a joined prefix would show only the beginning, which is exactly where an over-broad
deletion still looks correct. Read the far end of a deletion before committing it. Nothing else will
catch a range that reached past the content it was meant to remove, because verification confirms the
plan was carried out, never that the plan was right. The report therefore contains document text and input values: handle it like the
document. `ok` means mechanically verified; layout has not been inspected in Word.

## 6. Regression gates

`python scripts/build_fixtures.py --check` and `python scripts/run_job.py selftest --workdir <short path>`,
which runs every fixture through inspect, plan, dry run and execute and compares candidates, results,
review codes and full output paragraph texts with `assets/expected/*.json`. The unit test modules
(`run_job.py tests`: contract, component, package, namespace) live in the source tree and are not
distributed with the skill; where they are absent the command exits 1 rather than reporting a gate it
did not run.

The bundled expected-result files are fixed regression oracles. Their execution cases cover typed
values, XML escaping, split runs, missing-value policies, literal and unused-input reporting,
optional-section deletion, repeated rows, inserted paragraphs, content controls, comments, tracked
changes, field results, namespace preservation, and unsafe deletions. Successful rerun cases also
check deterministic output and preservation of the previous publication after a stale-plan failure.
The signature fixture must be refused during inspection.

When changing a fixture or its expectations, review the intended behavior against the contract and
fixture XML. Do not replace expected output with whatever the implementation currently produces;
that would hide regressions. `build_fixtures.py` regenerates the synthetic `.docx` packages only,
not the expected-result JSON files.
