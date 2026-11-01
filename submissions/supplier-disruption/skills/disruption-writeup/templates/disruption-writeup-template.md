# SUPPLY DISRUPTION WRITE-UP — {{disruption_id}} · {{supplier_or_po}}

> **DRAFT — PENDING BUYER / PLANNER REVIEW & SIGN-OFF** · Act steps are draft-first; no PO is placed
> or expedited, no ERP or schedule change is written, and no email is sent to the supplier until a
> human owner approves.

Produced by disruption-intake → supply-knowledge-retrieve → shortage-impact-map → mitigation-recommend
→ disruption-writeup under contract `mfg.supplier-disruption.v1`. Every determination carries engine
provenance, confidence, and a citation.

## 1. Disruption context

| Field | Value |
|---|---|
| Disruption | {{disruption_id}} — {{disruption_type}} |
| Supplier / PO | {{supplier}} · {{po_number}} |
| Part | {{part_no}} — {{part_description}} |
| Promised → revised | {{promised_date}} → **{{revised_date}}** |
| Short quantity | {{short_qty}} |
| Trigger / reported | {{trigger_channel}} · {{reported_at}} |
| Reason | {{reason}} |
| What happened | {{description}} |

## 2. Impact summary (engine determination)

| Determination | Value | Citation |
|---|---|---|
| Worst severity | **{{impact_worst_severity}}** | impact-mapping-rules.md #6 |
| First-impact date | **{{impact_first_impact_date}}** | impact-mapping-rules.md #5 |
| Affected products / orders | {{impact_affected_products}} / {{impact_affected_orders}} | impact-mapping-rules.md #6 |
| Affected sales orders | {{impact_affected_sales_orders}} | impact-mapping-rules.md #6 |
| Total qty at risk | {{impact_total_qty_at_risk}} | impact-mapping-rules.md #3 |
| Below safety stock | {{impact_below_safety_stock}} | impact-mapping-rules.md #2 |
| Confidence | {{impact_confidence}} | source `engine:shortage_impact_map` |

### Impact map (per order)

| Order | Type | Product | Line | Need-by | Qty at risk | Status |
|---|---|---|---|---|---|---|
{{for each impact_map}}| {{order_id}} | {{order_type}} | {{product}} | {{line}} | {{need_by}} | {{qty_at_risk}} | **{{status}}** |
{{end}}

## 3. Recommended mitigation (engine determination)

- **Option:** **{{mitigation_option}}** ({{mitigation_urgency}}) — {{mitigation_rationale}}
  (`engine:mitigation_recommend` · mitigation-escalation-rules.md #1)

{{for each mitigation.actions}}- {{action}}
{{end}}

| Notify | Role | Reason | Citation |
|---|---|---|---|
{{for each notifications}}| {{name}} | {{role}} | {{reason}} | {{citation}} |
{{end}}

{{if escalations}}## ⚠ Open items / escalations — read before you act
{{for each escalation}}- {{escalation}}
{{end}}{{end}}

## 4. Recommended next-best action (draft)

**{{next_best_action}}**

- Follow standard MRP/planner practice and supplier-management policy, except where a control gap above changes it.
- Any expedite / substitute / reschedule and any supplier email is executed by a buyer/planner after review — nothing is auto-sent in v1.
- A single-source critical part or a chronic-supplier pattern opens a second-source / SQM review before the risk recurs.

*All actions are drafts pending buyer/planner review — no PO, ERP, schedule change or email is auto-sent in v1.*

## 5. Supplier follow-up (draft)

*Draft per `references/supplier-comms-standards.md` #1-#2 — review and send from your own mailbox.*

> **To:** {{supplier}}
> **Subject:** {{po_number}} — {{part_no}} delivery ({{promised_date}} → {{revised_date}})
>
> {{writeup_supplier_followup}}

## 6. Internal escalation brief (draft)

*Draft per `references/supplier-comms-standards.md` #3 — lead with the impact and the decision needed.*

{{writeup_escalation_brief}}

## 7. Scope boundary & handoff

This write-up completes the plugin's scope. **Placing/expediting POs, writing to the ERP/MRP, changing
the schedule, and sending the supplier email (live monitoring, Wave 3)** are out of scope; this plugin
maps, recommends and drafts — a buyer/planner reviews, decides and executes.

## Appendix A — contract payload

```json
{{contract_payload}}
```
