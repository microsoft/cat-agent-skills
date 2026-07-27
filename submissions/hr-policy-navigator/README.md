# HR Policy Navigator

Answers "how much parental leave do I get" or "what's the expense limit for
client dinners" by searching your organization's actual HR policy sources,
not general knowledge, and citing exactly where the answer came from.

## How it's grounded

This skill doesn't bring its own HR content. It searches whatever knowledge
source is already connected to the agent: a SharePoint HR site, uploaded
policy documents, or a connected knowledge base. Copilot Studio's SharePoint
knowledge source already respects your organization's existing permissions
and sensitivity labels and checks the user's access before answering, so this
skill relies on that rather than adding its own access logic. See
[Add SharePoint as a knowledge source](https://learn.microsoft.com/microsoft-copilot-studio/knowledge-add-sharepoint)
and
[Optimizing SharePoint content for Employee Self-Service agents](https://learn.microsoft.com/microsoft-365/copilot/employee-self-service/optimization-sharepoint)
for how to set that up well.

## What it won't do

Answer questions about a specific colleague's situation, give legal or medical
advice dressed up as a policy answer, or guess at a policy detail that isn't
in the retrieved content. Anything sensitive (harassment, discipline, an
active case) gets routed to a human HR contact instead of an answer.

## Pairs well with

[`grounded-citation-guardrail`](../grounded-citation-guardrail) for the general
citation discipline this skill applies to HR content specifically, and
[`knowledge-source-router`](../knowledge-source-router) if your organization
has multiple regional HR knowledge sources to pick between.

---

Skill by Tim Karlsson (╯°□°)╯︵ ┻━┻ Works 60% of the time, every time.
