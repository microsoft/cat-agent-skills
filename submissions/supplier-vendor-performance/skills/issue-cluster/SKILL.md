---
name: issue-cluster
description: Clusters recurring issues by type and lane with record evidence, and maps scorecard breaches to governing trading terms, deterministically. Use on "what keeps going wrong", "cluster the issues", after scorecard-roll.
license: MIT
metadata: {version: "1.0", author: Microsoft Retail & CPG Skills, category: Merchandising & Supply}
---
# Issue Cluster
## Purpose
Deterministic clustering (>= 3 occurrences, #2.1) and breach-to-clause mapping (#3.1) with remedies stated, not invoked (#3.2).
## When to use
After scorecard-roll in every review.
## Inputs
scored.json + issues.json + config/trading-terms.json.
## Steps
1. Run scripts/issue_cluster.py --scored scored.json --issues issues.json --terms trading-terms.json --out clustered.json
2. Quote clusters with their record ids and the term text verbatim. Remedies (rebates, CAR rights) are stated with the clause quoted - invoking them is the buyer's decision.
## Output
clustered.json - the {issue_clusters, governing_terms} hop.
## Grounding requirements
Clusters cite record ids; terms cite the agreement clause.
## Constraints
- No cluster below threshold; no breach talking point without its clause (#3.1).
## Escalation / uncertainty
Breach without a retrievable clause -> open item for the buyer and legal.
