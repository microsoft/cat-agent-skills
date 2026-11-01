# WORK-ORDER WRITE-UP — {{work_order_id}} · {{asset_id}}

> **DRAFT — PENDING PLANNER / SUPERVISOR REVIEW** · Act steps are draft-first; no CMMS write-back,
> no scheduling, and no stock commitment until a human approves.

Produced by wo-intake → knowledge-retrieve → similar-work-rank → parts-readiness → work-order-writeup
under contract `mfg.work-order-assist.v1`. Every determination carries engine provenance, confidence,
and a citation.

## 1. Work order & asset context

| Field | Value |
|---|---|
| Work order | {{work_order_id}} — {{wo_type}} |
| Asset / tag | {{asset_id}} — {{asset_name}} |
| Location | {{location}} |
| Criticality class | {{asset_criticality}} ({{redundancy}}) |
| Reported by / when | {{reported_by}} · {{reported_at}} |
| Problem | {{problem_description}} |

## 2. Issue summary & applicable SOP

- Issue keywords: {{issue_keywords_joined}}
- Applicable SOP: **{{sop_doc}}** — {{sop_title}} ({{sop_section}})
- SOP default remedy: {{sop_default_remedy}}
- History window: {{history_window_days}} days · prior work orders: {{prior_wo_count}}

{{if escalations}}## ⚠ Open escalations — read before scheduling
{{for each escalation}}- {{escalation}}
{{end}}{{end}}

## 3. Most similar past work (ranked)

| Rank | Prior WO | Similarity | Shared signals | Outcome | Repeat? | Confidence | Citation |
|---|---|---|---|---|---|---|---|
{{for each similar_work}}| {{rank}} | {{wo_id}} | {{similarity_score}} | {{shared_signals_short}} | {{outcome}} | {{repeat_failure}} | {{confidence}} | {{citation}} |
{{end}}

*Ranking source: `engine:similar_work`. Where the SOP-default fix recurred with the fault returning,
the match is flagged `repeat_failure` per `references/similar-work-rules.md` #3.1.*

{{if superseding_fix.active}}### Superseding fix found
Fix note **{{superseding_fix.from_fix_note}}** supersedes part **{{superseding_fix.supersedes_part}}**
with **{{superseding_fix.recommended_part}}** — {{superseding_fix.rationale}}
*(`engine:similar_work` · similar-work-rules.md #3.3).*{{end}}

## 4. Parts readiness

**Status: {{parts_readiness.status}}**  ·  source `engine:parts_readiness`
(`references/parts-readiness-rules.md` #1–#4)

| Part | Required | On hand | Line status | Order this | Note |
|---|---|---|---|---|---|
{{for each parts_readiness.line}}| {{part_no}} | {{required_qty}} | {{on_hand}} | {{line_status}} | {{effective_part}} | {{note}} |
{{end}}

{{if parts_readiness.blockers}}Blockers: {{parts_readiness_blockers_joined}}{{end}}

## 5. Recommended next-best action (draft)

**{{next_best_action}}**

- Follow {{sop_doc}} except where a superseding fix or a parts redirect above changes it.
- Confirm parts are reserved/expedited before the job is scheduled.
- On a recurring-failure escalation, open a root-cause analysis (RCM) alongside the repair.

*All actions are drafts pending planner/supervisor review — no CMMS/EAM write-back in v1.*

## 6. Draft {{writeup_audience}} note

{{writeup_summary}}

## 7. Scope boundary & handoff

This write-up completes the plugin's scope. **Auto-scheduling, stock commitment, and CMMS
write-back (Wave 3)** are out of scope; this plugin assembles and drafts the work order in front of
you, a planner schedules and executes it.

## Appendix A — contract payload

```json
{{contract_payload}}
```
