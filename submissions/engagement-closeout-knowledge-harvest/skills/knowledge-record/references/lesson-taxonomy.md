# Lesson Clustering Taxonomy - Engagement Closeout
Deterministic clustering rules consumed by `lesson_cluster.py` (rules in `closeout_core.py`). The model drafts prose from these clusters but does not invent the grouping or priority.

## 1. Cluster taxonomy
### 1.1 Delivery governance
Decision cadence, escalation paths, sign-off ownership, scope control and governance forums.
### 1.2 Adoption and change
Training, communications, champion networks, role readiness and behaviour change.
### 1.3 Data and integration
Data quality, migration, integration sequencing, environments and technical dependencies.
### 1.4 Commercial and staffing
Staffing model, budget, resourcing, margin, contracting and partner dependencies.
### 1.5 Unclassified evidence
Evidence with no taxonomy keyword match remains `unclassified` and is a review candidate. It must
not default to delivery governance. Evidence whose keyword hits tie between two or more categories
is also `unclassified`: conflicting signals never pick a category by order. Evidence withheld for
embedded-instruction review (confidentiality-sanitisation-rules.md #8.1) is never read; it is
`unclassified` with an `embedded_instruction` signal.

## 2. Priority scoring
### 2.1 High-impact signals
Issues described as blocker, critical, delayed, rework, executive escalation or go-live impact receive a priority lift.
### 2.2 Evidence count
Clusters with multiple independent evidence items receive a priority lift because the lesson is less likely to be anecdotal.

## 3. Confidence
### 3.1 Confidence floor
Clusters below 0.70 confidence are included as review candidates, not polished lessons.

## 4. Drafting boundary
### 4.1 Model role
The model may draft lesson prose from the cluster, but it must preserve citations and may not override sanitisation findings.
