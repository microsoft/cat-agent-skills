# Worked Example — Supplier Invoice Approval

A compressed end-to-end run showing the expected shape of each phase's output. Use it as a
pattern, not a script — adapt to the user's actual process.

## Phase 0 — Frame
- **Process:** Supplier invoice approval
- **Desired outcome:** Correct invoices paid on time; exceptions caught early
- **Customer:** Internal (Finance) + external (suppliers awaiting payment)
- **Success looks like:** <3-day cycle time, <1% payment errors, zero missed early-pay discounts
- **Constraints:** SOX controls, 3-way match required, ERP is system of record

## Phase 1 — Expand (5 guiding outcomes)
1. Invoices are understood the moment they arrive — no manual keying.
2. Only genuine exceptions ever reach a human.
3. Every approval decision has an instant, auditable rationale.
4. Suppliers get a status answer without emailing anyone.
5. The process learns from each exception and prevents the next one.

## Phase 2 — Current-State Task Map (excerpt) + baseline
| # | Task | Stage | Systems | Freq/Vol | Pain | Hotspot? |
|---|------|-------|---------|----------|------|----------|
| 1 | Receive & sort invoice email | Intake | Outlook | 400/wk | Manual, misfiled | ✅ |
| 2 | Key invoice into ERP | Intake | ERP | 400/wk | Slow, typos | ✅ |
| 3 | 3-way match vs PO + GRN | Triage | ERP | 400/wk | Copy-paste, errors | ✅ |
| 4 | Chase missing PO/GRN | Triage | Email | 90/wk | Waiting, rework | ✅ |
| 5 | Approve within threshold | Approve | ERP | 400/wk | Bottleneck at month-end | ✅ |
| 6 | Answer supplier "where's my payment?" | Deliver | Email | 120/wk | Interrupt-driven | ✅ |

**Baseline:** cycle time 6 days · 400 invoices/wk · ~4% error/rework · ~2.5 FTE.

## Phase 3 — Redesign principles & must-keep controls
- **Principles:** exception-only human effort; capture-once at intake; status is self-serve.
- **Must-keep controls:** 3-way match, SOX segregation of duties, audit trail on every approval.

## Phase 4 — Future-State Blueprint (swimlane excerpt)
```
STAGE Intake
  AI      │ Intake agent extracts fields from invoice, posts to ERP   [AI-owned]
  Systems │ ERP creates draft record
STAGE Triage
  AI      │ Matching agent runs 3-way match, auto-clears clean ones   [AI-owned]
  Human   │ AP clerk reviews only mismatches queued by the agent      [Hybrid]
STAGE Approve
  AI      │ Auto-approve within threshold + policy; log rationale     [AI-owned]
  Human   │ Approver signs off above-threshold exceptions             [Human-led]
STAGE Deliver
  AI      │ Status agent answers supplier queries from ERP state      [AI-owned]
  Govern. │ Validator samples 5% of auto-approvals weekly             [Human-led]
```

## Phase 5 — Summary table (excerpt)
| Category | Task / role | Ownership | Rationale | N/C/R | Building block |
|----------|-------------|-----------|-----------|-------|----------------|
| Automate | Field extraction & keying | [AI-owned] | rules-based, high volume | Changed | tool + extraction skill |
| Automate | 3-way match (clean cases) | [AI-owned] | deterministic | Changed | tool (ERP action) |
| AI Agents & Skills | Supplier status answers | [AI-owned] | retrieval over ERP state | New | skill (retrieval) |
| Simplify | Exception review queue | [Hybrid] | humans see only mismatches | Changed | process change |
| Human | Above-threshold approval | [Human-led] | accountability / SOX | Changed | — |
| Human | Auto-approval sampling (5%) | [Human-led] | governance | New | — |
| Remove | Manual email sorting | — | intake tool replaces | Removed | — |

**AI-capability backlog (top 3):** (1) Invoice extraction — *block:* tool + reusable skill —
*risk:* OCR errors → *metric:* keying time ↓90%. (2) 3-way matching — *block:* tool (ERP action),
no agent needed — *risk:* false clears → *metric:* error rate <1%, 5% sampling. (3) Supplier
status answers — *block:* reusable retrieval skill (promote to a connected agent only if supplier
comms grows into its own domain) — *risk:* stale data → *metric:* inbound "where's my payment" ↓80%.

**Roadmap:** *Next 2 weeks* — pilot invoice extraction on one supplier group; stand up sampling.
*Next 6–12 weeks* — roll matching + auto-approve with thresholds; add the status skill; embed the
weekly validation ritual and an AI Workflow Owner.

## Wrap-up (spoken close — example)
*"Great session — you've reimagined invoice approval end to end. You now have a one-page summary,
a current-state map, a future-state blueprint, a what-changed list, the five-bucket table, a
prioritised capability backlog, and adoption notes. The headline shift: AI owns intake, matching,
and supplier status; people keep only above-threshold approvals and 5% sampling; manual email
sorting disappears — targeting cycle time from 6 days to under 3, and errors under 1%. Notably,
most of this is tools and reusable skills, not new agents. In the next two weeks we'd pilot
extraction on one supplier group and stand up sampling. Do you want to go further — which process
should we remodel first: the highest-volume, the highest-pain, or the fastest to show value?"*
