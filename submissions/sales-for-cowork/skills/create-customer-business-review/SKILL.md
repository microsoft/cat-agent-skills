---
name: create-customer-business-review
description: Create a recurring customer-facing business review or QBR of agreed goals, results, adoption, value evidence, risks, commitments and next-period priorities. Use for "prepare our customer QBR" or "review outcomes and commitments with the customer". Do NOT use for internal account-health assessment or account planning, pipeline management, a new sales pitch, or edits to an existing deck.
metadata:
  displayName: "Create a customer business review"
  domain: Sales
---

# Customer business review

## Production order
1. Host/user/brand/template authority takes precedence. Complete any required host design selection without inventing its result or bypassing hooks or permissions. A governing template or existing layout stays on the host's template-edit path; apply narrative and evidence without requiring fresh PptxGenJS creation. When the host authorizes original composition, read [design-to-production](references/custom-design-authoring.md) alone through EOF. Preserve supplied identity, palette, fonts and assets; fill only permitted choices. Write a concrete `design-language.md` in the actual active workspace, wait for successful Write, then issue a separate complete Read of that file before planning, outlining or authoring. A brand kit alone is not a governing template; its strictness and host restrictions determine the permitted choices.
2. Resolve paths from the successful Skill response's base directory, not a hardcoded harness directory. Read the host's resolved `image/SKILL.md` and `pptx/pptxgenjs-icons.md` separately, using the available skill roots for Claude or GHCP. Plan relevant image AND named semantic-icon slots in one measured permitted batch. Join results, retain actual paths; host/no-image/no-icon/no-notes limits prevail. Missing permission or unavailable guidance is a real blocker, not permission to fabricate assets or a design result.
3. For fresh PptxGenJS creation, require [production guard](scripts/production.cjs) in the ordinary build BEFORE adding slides. It validates your plan, not designs it: guard=production(pptx,{tokens:{colors:{...},fonts:{...}},slots:[{id,type:'image'|'icon',role}]},[{id,success:true,path:absoluteAssetPath}]). Use guard.place(id,slide,{x,y,w,h}) for each returned image/icon; export with guarded pptx.writeFile. Save guard.seal() to production-evidence.json. Missing/unplaced roles refuse export; fix actual assets, never dummyfiles. Explicit user/host exclusions may use exemptions:[{type,authority,reason}] and remain exceptions. Template editing follows host tools; verify equivalent placement, never replace brand layout.
4. Render every page; inspect source truth, meaningful relationships, readable lookup and actualmedia. No helper certifies aesthetic/semantic quality. Save `output.pptx` in the host's designated output directory and complete its normal delivery workflow; a local file is not delivery.

## Narrative and evidence
Establish customer audience, goals/cutoff/meeting date and commitments. Default11slides total: cover; voice/goals; results; adoption; service; value/limits; issues; commitments; next options/authority; joint actions; confirmation. Combine/expand for real questions; user structure wins. Narrow quality scope uses [quality](references/quality-review.md). Main pages serve customer dialogue, not CRM audit; no agenda delay without useful navigation.
Preserve all commitments with IDs, full promise, owner/date, delivered evidence and customer confirmation separately. Link customer concerns to specific next action or open question; no repeated complete action inventories. Preserve proposed versus agreed goals/pilots; prior targets need period authority at close. Unknown responsibility is a question, not blame.
Keep exact statistic(mean/median), event, population, denominator, units, threshold operators and comparison windows. Response is not closure, vendorclosed is not customerconfirmed. Judge overdue at source cutoff, not meeting date. Delivery/adoption/attribution is not realized value; ROI needs baseline/cost/attribution. Preserve modeled/unapproved status. Hypotheses are not causes. Monitoring needs no invented upsell/approval.

## Focal exhibit choices
Use an open result rail above a dominant trend/threshold comparison, keeping population and authorized period visible. Show evidence->validation->customer confirmation as editable lanes when the links are supported, with supplied owner/date or gaps. A schedule with start/end evidence can use a Gantt; isolated deadlines need a milestone ribbon instead. Paired current/target bars or small multiples support comparisons; no invented ROI, causal arrow or pyramid of customer value. Let the joint decision occupy the closing focal area, with routine actions in one linked lookup.

Apply [final evidence and closure](references/final-evidence-check.md) to actual titles, labels, dates, edges and actions. Preserve complete readable lookup and source qualifications.

Use [QBR evidence relations](references/qbr-visual-contracts.md) for the applicable customer question and [worked examples](references/worked-examples.md) for the production guard's structural contract, not as proof of presentation quality.
