# Staffing & Bench Match

For resource managers and engagement partners staffing a newly signed engagement.

It extracts the roles from the SOW, loads the bench, availability, rates and conflicts register, scores each candidate's fit, refuses conflicted or unavailable candidates with the rule cited and drafts a partner-ready staffing recommendation.

The design bet is that the best match on paper is worthless if they cannot be staffed: independence, conflicts and availability are checked before anyone reaches the slate, and every refusal says why.

## What's included

1. **role-intake** reads the signed engagement, SOW role extract or staffing request into the roles to be filled, each field cited.
2. **bench-query** loads the bench, availability, rate and conflicts-register data for those roles.
3. **fit-score** scores candidate-role fit, adds utilisation context and produces a provisional ranking.
4. **constraint-check** applies independence, conflict, prior-role, ethical-wall and availability rules and refuses ineligible candidates.
5. **slate-draft** drafts the partner staffing recommendation, including refused top matches and any staffing gaps.

## Before you start

The SOW or staffing request, a bench roster with skills and grades, availability, rates and the conflicts and independence register. No connectors are required; supply the files directly or point to them in SharePoint or OneDrive.

The independence and eligibility rules bundled in each skill's `references/` folder are illustrative summaries, not a real firm's policy. Replace them with your firm's own rules before relying on the output.

The proposed slate this plugin produces can feed the **Engagement Mobilization Pack** plugin.

## Try it

- **Staff a new engagement:** "We just signed [client] for [engagement]. Extract the roles from the SOW in [folder] and build me a staffing slate."
- **Check eligibility:** "Is anyone on the shortlist for [engagement] conflicted with [client]? Why can't we use the top match?"
- **Draft the recommendation:** "Draft the partner approval note for the [engagement] staffing slate."

## Limitations

Draft staffing recommendations for partner review. It never approves, allocates or assigns staff, changes rates or overrides an independence decision.

Outputs are drafts that support, not replace, professional judgement. Use synthetic or anonymised staff data when trying it out.

## Contributors

- Copilot Acceleration Team (CAT)
