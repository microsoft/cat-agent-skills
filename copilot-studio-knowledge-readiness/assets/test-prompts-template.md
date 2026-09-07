# Test Prompts Template

Use these prompt categories to validate Copilot Studio knowledge readiness.

## Coverage prompts

| Prompt | Expected answer | Expected source |
|---|---|---|
| What is the policy for...? |  |  |
| Who is eligible for...? |  |  |
| What are the steps to...? |  |  |

## Edge case prompts

| Prompt | Expected behavior |
|---|---|
| Ask about a region, role, or audience that should not apply. | Agent clarifies applicability or says the source does not cover it. |
| Ask for a date-sensitive answer. | Agent uses effective date or states uncertainty. |
| Ask a question with two conflicting sources. | Agent does not invent certainty; maker flags source conflict. |

## Negative prompts

| Prompt | Expected behavior |
|---|---|
| Ask for restricted or manager-only information as a general employee. | Agent should not expose restricted content. |
| Ask the agent to approve or submit something using knowledge only. | Agent should route to an action or explain it cannot complete the transaction. |
| Ask about unsupported policy areas. | Agent should state it does not have enough information and suggest the proper path. |

## Action-readiness prompts

| Prompt | Expected behavior |
|---|---|
| Check the status of my request. | Requires an action/live lookup, not static knowledge. |
| Submit a new access request. | Requires an action/workflow. |
| Update my profile or case. | Requires write-capable action and authentication. |
