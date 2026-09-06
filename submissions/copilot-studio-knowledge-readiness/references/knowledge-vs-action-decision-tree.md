# Knowledge vs Instructions vs Workflows vs Actions vs Skills

Use this decision tree when assessing content for the modern Copilot Studio experience.

## Decision tree

1. **Is the guidance true for every conversation with this agent?**
   - Yes: put it in **agent instructions**.
   - No: continue.

2. **Is the content factual reference material that users may ask about?**
   - Yes: use **knowledge**, if permissions and quality are acceptable.
   - No: continue.

3. **Does the user need a deterministic guided path with required questions or handoffs?**
   - Yes: use a **workflow**.
   - No: continue.

4. **Does the task need live data, writes, approvals, tickets, status checks, notifications, or transactions?**
   - Yes: use an **action**, Power Automate flow, connector, API, or MCP tool.
   - No: continue.

5. **Is this a repeatable procedure that applies only to a specific scenario?**
   - Yes: use a **skill**.
   - No: leave it as general maker guidance or improve the source content.

## Common classifications

| Content or requirement | Recommended surface | Reason |
|---|---|---|
| HR policy PDF | Knowledge | Factual reference content. |
| "Always be concise and cite sources" | Agent instructions | Applies to every conversation. |
| Employee onboarding checklist with required branching | Workflow | Needs controlled data collection and branching. |
| Submit laptop request | Action | Creates or updates a ticket/workflow. |
| Evaluate whether a source is ready for knowledge grounding | Skill | Situational procedure with a repeatable rubric. |
| Check order status | Action | Requires live lookup. |
| Explain return policy | Knowledge | Static factual answer, if current and authorized. |
| Refund approval rules | Workflow plus action | Requires guided checks and transaction/approval. |

## Red flags about the content or the surface

Wrong surface (knowledge is not the right answer):

- The answer changes per user, region, entitlement, case, order, subscription, or date.
- The user expects the agent to submit, approve, update, notify, or create something.
- The source includes steps that must be followed exactly and audited.
- The content is really a troubleshooting flow with required diagnostics.

Unsafe source (restructure before using as knowledge):

- The source mixes public and restricted content in the same location.
