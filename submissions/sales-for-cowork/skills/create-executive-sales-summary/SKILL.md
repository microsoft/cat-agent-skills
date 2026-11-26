---
name: create-executive-sales-summary
description: Create a sales results and forecast summary for senior leadership, highlighting expected outcomes, material risks and decisions requiring executive support. Use for "summarize sales results for our leaders" or "forecast summary for the VP". Do NOT use for deal-by-deal pipeline management, customer-facing business reviews, proactive pitches, or edits to an existing deck.
metadata:
  displayName: "Create an executive sales summary"
  domain: Sales
---

# Executive sales summary

## Production order
1. Host/user/brand/template authority takes precedence. Complete any required host design selection without inventing its result or bypassing hooks or permissions. A governing template or existing layout stays on the host's template-edit path; apply narrative and evidence without requiring fresh PptxGenJS creation. When the host authorizes original composition, read [design-to-production](references/custom-design-authoring.md) alone through EOF. Preserve supplied identity, palette, fonts and assets; fill only permitted choices. Write a concrete `design-language.md` in the actual active workspace, wait for successful Write, then issue a separate complete Read of that file before planning, outlining or authoring. A brand kit alone is not a governing template; its strictness and host restrictions determine the permitted choices.
2. Resolve paths from the successful Skill response's base directory, not a hardcoded harness directory. Read the host's resolved `image/SKILL.md` and `pptx/pptxgenjs-icons.md` separately, using the available skill roots for Claude or GHCP. Plan relevant image AND named semantic-icon slots in one measured permitted batch. Join results, retain actual paths; host/no-image/no-icon/no-notes limits prevail. Missing permission or unavailable guidance is a real blocker, not permission to fabricate assets or a design result.
3. For fresh PptxGenJS creation, require [production guard](scripts/production.cjs) in the ordinary build BEFORE adding slides. It validates your plan, not designs it: guard=production(pptx,{tokens:{colors:{...},fonts:{...}},slots:[{id,type:'image'|'icon',role}]},[{id,success:true,path:absoluteAssetPath}]). Use guard.place(id,slide,{x,y,w,h}) for each returned image/icon; export with guarded pptx.writeFile. Save guard.seal() to production-evidence.json. Missing/unplaced roles refuse export; fix actual assets, never dummyfiles. Explicit user/host exclusions may use exemptions:[{type,authority,reason}] and remain exceptions. Template editing follows host tools; verify equivalent placement, never replace brand layout.
4. Render every page; inspect source truth, meaningful relationships, readable lookup and actualmedia. No helper certifies aesthetic/semantic quality. Save `output.pptx` in the host's designated output directory and complete its normal delivery workflow; a local file is not delivery.

## Narrative and evidence
Establish audience, entity, source cutoff, measure definitions and leadership question. Default10slides total: cover; executive conclusion; actual/target; drivers; contribution; limits; outlook; conditions; leadership decision; actions. Adapt to complete readable questions, not filler. Single opportunity instead follows qualification, value limits, stakeholders/alternatives, authority, delivery/legal checkpoints and executive help; never invent portfolio actuals. User count/order/template wins.
Main pages carry judgment/evidence; source analysis has indexed homes. Distinguish leadership decision, attention and routine follow-up. Preserve material weakness and uncertainty. Suggestions stay proposed, benefits unproven unless sourced; lower sales is not lower demand.
Align currencies/populations/periods and authorized targets. Separate bookings, recognized revenue, cash, pipeline and forecast. Actual-plan variance needs one convention, additive signed drivers and exact total. Largest contribution is absolute, not rate. Ratios need matching populations/windows. Partial-period actuals are provisional. Costs absent means no profit claim. Forecast approval does not remove conditions; preserve expected-order/acceptance qualifiers. Each core gap reaches a sourced action or explicit open question, with authority/owner/date or gaps.

## Focal exhibit choices
Use a signed waterfall for reconciled actual-plan drivers: opening/closing bars start at zero, components float at cumulative endpoints, residual explicit. Without additive drivers use aligned variance bars, not a false bridge. Outlook uses separate actual/conditional scenario bands with target marker. Executive support may use a three-level priority pyramid only for sourced priority or a labeled proposed reading order; tier area is not amount. A single-opportunity brief uses authority ladder or evidence-to-checkpoint map, not invented portfolio data. Make one comparison dominant and put source detail at indexed homes.

Apply [final evidence and closure](references/final-evidence-check.md) to actual titles, labels, dates, edges and actions. Preserve complete readable lookup and source qualifications.

Use [executive evidence relations](references/executive-visual-contracts.md) for the applicable exhibit and [worked examples](references/worked-examples.md) for the production guard's structural contract, not as proof of presentation quality.
