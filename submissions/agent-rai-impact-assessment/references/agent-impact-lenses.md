# Agent impact lenses

These are original agent-focused review prompts. Select those that apply; record why a material lens is out of scope rather than mechanically raising a finding for every row.

| Lens | Architecture questions | Evidence or useful challenge |
| --- | --- | --- |
| People and benefits | Who gains time or access, and who bears errors, delay, surveillance, or extra review work? Can people avoid the agent or obtain an accessible alternative? | Compare the current process; distinguish measured benefit from a business-case hypothesis. Seek affected-user input, including people who never interact with the agent. |
| Action authority | Can the agent recommend, draft, submit, or commit? Under whose identity? Are resource, tenant, amount, recipient, and operation restrictions enforced outside the model? | Trace one tool call through authorization and downstream effects; examine direct invocation and delegated calls. |
| Effective human control | What does a reviewer see and have authority to change? Is approval tied to the exact action and parameters? Does a later change invalidate it? Can reviewers realistically detect errors at expected volume? | Challenge stale approval, bulk approval, missing context, unavailable reviewers, and action before approval. |
| Retrieval and untrusted content | Can a retrieved document, message, tool response, or delegated agent redirect actions or alter priorities? Can it cause disclosure or impersonate an approver? | Use harmless synthetic adversarial content in an authorized test environment. Verify instruction boundaries and tool-side restrictions, not only refusal wording. |
| State and retries | What happens on timeout after a side effect, duplicate events, conflicting concurrent agents, or delayed execution? Is intent still valid when an action commits? | Trace durable state, idempotency, authorization rechecks, bounded retries, cancellation, and reconciliation. A retry can repeat a harm. |
| Privacy and memory | Who can access prompts, retrieval results, logs, caches, shared memory, and delegated-agent state? Are original permissions preserved across those copies? | Test cross-user/session/tenant retrieval with synthetic data; inspect retention and deletion propagation. Source ACLs do not automatically secure derived memory. |
| Reliability and grounding | Can a fluent but wrong answer alter a consequential decision? Are stale sources, contradictions, unavailable tools, and unsupported languages handled? | Separate citation presence from citation support and source freshness. Test abstention or safe handoff when evidence is insufficient. |
| Fairness and inclusion | Could error, refusal, escalation, or correction burden differ by relevant language, accessibility need, or user context? Which groups are poorly represented in evaluation? | Use domain-appropriate, privacy-reviewed evaluation slices and representative scenarios. Report sample sizes and uncertainty. |
| Transparency and recourse | Do people know the agent's role, limits, and action status? Can an affected person contest an outcome, correct data, or reach a responsible human? | Evaluate explanations tied to observable evidence, not invented model reasoning. Test the correction route end to end, including non-users. |
| Multi-agent delegation | Can delegated agents amplify privileges, share protected context, or continue after cancellation? Who owns the overall result? | Trace identity, capability limits, provenance, cancellation, and action history across delegations. The caller's constraints do not automatically transfer. |
| Operational change | What happens after model, prompt, tool, permission, knowledge, or user-population changes? Can operations stop new actions while preserving accepted obligations? | Version the evaluation baseline, define regression cases and review triggers, and rehearse incident response and recovery. A kill switch does not undo completed actions. |

When evaluating decision influence, inspect actual use rather than labels. An agent described as "advisory" may still determine outcomes when operators routinely accept its recommendation without meaningful review.

## Consequence types

Name at least one of these in every harm chain so "adverse consequence" is specific enough to size and test:

- **Denial or degradation of service:** a person cannot complete a task, receives a worse outcome, or is routed to a slower path.
- **Loss of opportunity:** an application, request, or case is rejected, delayed, or deprioritized incorrectly.
- **Financial loss:** money, inventory, or entitlements are committed, charged, or withheld in error, including duplicate or unreversed actions.
- **Privacy exposure:** personal or confidential information is disclosed, retained, or inferred beyond its original permission.
- **Physical or psychological harm:** unsafe guidance is acted on, or interactions cause distress or coercion.
- **Reputational or dignitary harm:** a person or group is misrepresented, stereotyped, demeaned, or publicly embarrassed.
- **Erosion of autonomy or oversight:** people cannot tell what the agent did, cannot contest it, or defer to it without meaningful review.
- **Organizational and legal exposure:** obligations are breached or records falsified, with downstream effects on the people the organization serves.
