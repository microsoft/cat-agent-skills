# Worked example: Contoso Customer Service (fictional)

Contoso is a fictional company. All facts below are invented for this example and must never be reused as real data.

## 1. Intake (as captured)

| Item | Answer |
|---|---|
| Scope | Customer Service function, about 1,200 representatives in three regions |
| Audience | VP of Customer Service (sponsor), service operations leads, CISO delegate |
| Outcomes | Cut average handle time 15 percent; raise first-contact resolution 10 points; one to three year vision: half of routine order inquiries resolved without a representative |
| Initiatives | (A) reply-drafting assistant for representatives, live pilot; (B) warranty policy advisor, in build; (C) customer-facing order status agent on the website, proposed |
| Evidence | AI policy (2026), DLP configuration notes, pilot feedback survey, knowledge base inventory spreadsheet |
| Format | Word report |
| Unknown | No agent inventory beyond the pilots; no training plan; no baselines for handle time by queue |

## 2. Pattern map

| Initiative | Pattern | Serves | Assist or execute | Risk tier | Rationale |
|---|---|---|---|---|---|
| A. Reply drafting | Employee AI enablement | Individual representative | Assist | Tier 1 | Representative reviews and sends; no system action |
| B. Warranty advisor | Business expert empowerment | Representatives who need the warranty lead's guidance | Assist | Tier 2 | Answers on behalf of an expert; wrong answers mislead customers indirectly |
| C. Order status agent | External engagement | Customers outside Contoso | Execute | Tier 3 | Crosses the trust boundary and represents the brand |

Straddle flag: if (C) also processes returns, it adds Core business process transformation behavior. Recommend keeping returns out of scope for the first release.

## 3. Maturity diagnostic

| Pillar | Level | Confidence | Evidence | Unknowns |
|---|---|---|---|---|
| AI strategy and experience | 200 | Medium | Draft vision slide; no named executive sponsor for agents | Whether the vision is approved |
| Business strategy | 200 | Medium | Pilots improve single steps; no baselines | Handle time baselines by queue |
| Governance and security | 300 | High | Documented AI policy, DLP, dev/test/prod separation | Agent registry, incident plan |
| Technology and data | 200 | Medium | One platform chosen; knowledge split across three sites | Ownership of knowledge sources |
| Organization and culture | 200 | Low | Ad hoc training; no champions | Leader usage, sentiment data |

No overall score is shown.

## 4. Gap analysis (scripts)

```bash
python scripts/gap_calc.py --input assets/example-input-contoso.json --markdown gaps.md
python scripts/radar_chart.py --input assets/example-input-contoso.json --output radar.png
```

Result summary (summary target table):

| Pattern | Learn-named scale-breaker | Computed scale-breaker | Verdict |
|---|---|---|---|
| Employee AI enablement | Organization and culture | Organization and culture (1 level) | One pillar short: close it or pilot while closing |
| Business expert empowerment | Technology and data | Technology and data (1 level), tied with Organization and culture | Two pillars short: clear scale-breaker |
| External engagement | Governance and security | Governance and security (2 levels), tied with three others | Several pillars short: ambition outruns readiness |

Weakest pillar (ceiling): four pillars at 200.

Interpretation: (A) and (B) are close to ready. (C) is a stepping-stone case. Learn's guidance is to build capability on the assist side first and treat (C) as a bounded pilot only after governance and technology move up.

## 5. Roadmap (priority pillars: Organization and culture, Technology and data)

| Horizon | Actions | Pillar | Learn source |
|---|---|---|---|
| 90 days | Name a business owner per pattern; publish risk tiers; start an intake form and weekly CoE check-in; take (A) to production with monitoring | Organization and culture, Governance | next-steps-action-plan, govern-agents-risk |
| 90 days | Name the warranty lead as owner of (B); consolidate warranty knowledge into one authoritative source | Technology and data | pattern-business-expert-empowerment |
| 6 months | Role-based training cohort and champions network; capture handle time baselines | Organization and culture, Business strategy | enablement-community, measure-report-value |
| 12 months | Reassess maturity; decide whether (C) moves to a bounded pilot with disclosure and real-time monitoring | All | maturity-model-how-to-use, pattern-external-engagement |

## 6. CoE blueprint (summary)

- Structure: centralized for (A) and (C); federated delivery for (B) with the warranty lead owning content and the CoE owning evaluation standards.
- Governs: Tier 1 self-service checklist; Tier 2 release gate with expert validation; Tier 3 not yet released.
- Enables: one golden path for reply-drafting agents; office hours.
- Optimizes: weekly health review; evaluation test set for (B).
- Scales: catalog entry for (A) to reuse in other regions.
- Failure-mode check: Tier 1 self-service avoids gatekeeper; monthly sponsor review avoids ghost; shipping (A) now avoids perfectionist.

## 7. Leader decisions for the VP of Customer Service

1. Fund Employee AI enablement and Business expert empowerment now; defer External engagement to a gated pilot.
2. Name the warranty lead as accountable owner of (B).
3. Set autonomy limits for any future customer-facing agent (no refunds or account changes without a person).
4. Choose the CoE model: central CoE inside service operations, linked to the enterprise security function.
5. Approve baselines and targets for handle time and first-contact resolution before scaling.

## 8. What the report would say first (executive summary excerpt)

Contoso Customer Service is ready to scale assistive agents and is not yet ready for a customer-facing agent. The scale-breakers are organization and culture for the reply assistant and knowledge quality for the warranty advisor. Governance is the strongest pillar but is two levels short for external engagement. The VP needs five decisions, starting with named owners and baselines.
