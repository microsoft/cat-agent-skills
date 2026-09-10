# NONCONFORMANCE REPORT — {{ncr_id}}

> **DRAFT — PENDING QUALITY ENGINEER APPROVAL** · draft-first: no containment executed,
> nothing filed or sent.

Produced by spec-ingest → tolerance-check → defect-grade → ncr-draft under contract
`mfg.quality-inspection.v1`. Every determination carries engine provenance, confidence
and a citation.

{{if escalations}}## ⚠ Open escalations (resolve before closing)
{{for each escalation}}- {{escalation}}
{{end}}{{end}}

## 1. Lot identification
| Field | Value |
|---|---|
| Part / revision | {{part_number}} rev {{part_revision}} |
| Lot / quantity / sample | {{lot_id}} · {{lot_quantity}} · n={{sample_size}} |
| Certificate | {{coc.doc_id}} ({{coc.supplier}}) |
| Governing documents | {{governing_documents}} |

## 2. Nonconformance description
{{for each graded_defect}}
- **{{characteristic}}** — {{severity}}: worst {{actual}} against {{lower_tolerance}}–{{upper_tolerance}}
  ({{n_out_of_tolerance}}/{{stats.n}} parts, {{incidence_pct}}%, band consumed {{stats.band_consumed_pct}}%).
  {{if doc_conflict}}**Certificate conflict:** CoC claims conformity; measurements govern (rules #4.3, ISO 9001 8.4.3).{{end}}
  *{{source}} · confidence {{confidence}} · {{citation}}*
{{end}}

## 3. Inspection summary — all characteristics
| Characteristic | Nominal | Tolerance | Worst | n OOT / n | Band % | Status | Citation |
|---|---|---|---|---|---|---|---|
{{for each characteristic}}| {{name}} | {{nominal}} | {{lower}}–{{upper}} | {{actual}} | {{n_out_of_tolerance}}/{{stats.n}} | {{stats.band_consumed_pct}} | {{status}} | {{citation}} |
{{end}}

## 4. Grading & recommended disposition
| Characteristic | Severity | Disposition | Rule cited | Deviation auth? | Rationale |
|---|---|---|---|---|---|
{{for each graded_defect}}| {{characteristic}} | {{severity}} | {{disposition}} | {{citation}} | {{requires_deviation_authorization}} | {{rationale}} |
{{end}}

**Lot recommendation: {{recommended_disposition}}** (ISO 9001:2015 §8.7)

{{if watch_list}}## Watch list (not defects)
{{for each watch item}}- {{characteristic}}: {{note}}
{{end}}{{end}}

## 5. Containment & recommended actions (draft-first)
- Quarantine {{lot_id}}; block stock movement.
- 100% screen of unsampled parts for the nonconforming characteristic(s).
- Supplier notification referencing this NCR{{if any doc_conflict}}; SCAR candidate — certificate contradicted by measurement{{end}}.
- Schedule MRB review{{if any critical}} with design authority{{end}}.

*All actions are drafts pending QE approval.*

## 6. Scope boundary & handoff
This NCR completes the plugin's scope. **Quality Incident & CAPA (Wave 2)** consumes this
contract payload as its input.

## Appendix A — contract payload
```json
{{contract_payload}}
```
