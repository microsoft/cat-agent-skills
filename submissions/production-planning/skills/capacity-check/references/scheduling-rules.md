# Scheduling Rules (cited as scheduling-rules.md #<n>; engine constants mirror sections)
## 1. Load and utilization
1.1 Load = run hours + changeover hours; utilization measured against available hours. 1.2 Planned utilization above 95% is an overload escalation - paper feasibility at 92% run-hours ignores changeovers.
## 2. Material gate
2.1 An order must not be sequenced to start before its material availability date. A gated order is scheduled at/after the gate, never "hoped" earlier.
## 3. Campaign rule
3.1 Sequence products of the same family consecutively (campaigns) to minimize changeovers; break campaigns only to protect a committed due date.
## 4. Commitment priority
4.1 Committed customer orders are never sacrificed for changeover savings; ties break toward the committed order.
## 5. Draft-first
The optimized plan is a DRAFT the planner publishes; nothing is written to execution systems by this plugin.
## 6. Confidence floor
Missing routing, changeover, or material data for any order -> confidence < 0.75, escalate to planning data owner.
