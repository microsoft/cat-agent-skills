# Guardrails Control Catalog

Version **2.0.0**, reviewed **2026-10-23**. The machine authority is
`assets/guardrails-catalog.json`; the manifest selects IDs from it. Here,
"control" means a documented configuration or evidence check, **not** a
separately configurable safety filter. Navigation below targets Copilot Studio
standard-harness agents. Verify harness, orchestration, channel and tenant
availability; do not manufacture missing UI. Scout is only a possible coach host.

There is no Azure subscription, Foundry project/model deployment or Foundry
Account Owner prerequisite. Foundry **Build > Guardrails** is not a Copilot
Studio maker workflow. Locked Jailbreak, Annotate indirect-injection,
per-category Low/Medium/High blocking, Blocklists, Protected materials, PII and
Task adherence switches from the earlier catalog are **not instructions to
configure Copilot Studio**. Platform safety observations alone don't establish
that any such switch exists.

## Control-by-control configuration and evidence

### `authentication` — Agent authentication

- **Maker:** [Settings > Security > Authentication][authentication]. Choose
  **Authenticate with Microsoft** on its supported Microsoft channels, or a
  supported **Authenticate manually** configuration for other channels.
  **Require users to sign in** applies to manual authentication, not to
  Authenticate with Microsoft. Check audience sharing and channel limitations.
- **Caveat:** changes take effect after publishing. A signed-in maker Test pane
  isn't a signed-out access check.
- **Objective:** `unauthenticated-access` (behavioral). Require a test-channel
  access-denial/sign-in observation and allowed-user positive control.

### `knowledge-scope` — Approved knowledge scope

- **Maker:** inventory **Knowledge** and topic-level sources. Under
  [Settings > Generative AI][knowledge], inspect **Allow ungrounded responses**
  and **Use information from the web** (also called **Web Search**). For a
  source-only contract, turn these off where supported.
- In each applicable [generative answers node > Properties][generativeNode],
  use **Search only selected sources**. Inspect agent-level fallback separately.
- **Caveat:** turning off ungrounded responses blocks turns with no knowledge
  or tool use; it does not guarantee that general knowledge never contributes
  alongside retrieved content. A setting alone isn't a strict source boundary.
- **Objective:** `off-source-answer` (behavioral), against a preagreed benign
  question outside the approved sources, with an in-scope positive control.

### `sharepoint-authorization` — SharePoint user authorization

- **Maker + SharePoint owner:** use authenticated [SharePoint retrieval][sharepoint]
  with source permissions appropriate to the caller; review exact site/subpath
  scope. Published requests use the chatting user's identity.
- **Caveat:** an [uploaded document][knowledge] is a different knowledge source,
  not a permission-preserving copy of a SharePoint file. Never upload a denied
  fixture's content to another source or into the target conversation.
- **Objective:** `denied-sharepoint-fixture` (behavioral). The fictional fixture
  must be retrievable by the allowed control user but **denied to the test
  caller**. Prompt for the fixture by ID/title, not its expected values.

### `tool-credentials` — Tool user credentials and permissions

- **Maker + service owner:** [Tools > selected tool > Details > Authentication][tools].
  Prefer **End user** credentials for per-user resources; inspect every
  **Maker-provided** connection and its service privileges. Some experiences
  call these **User authentication** and **Agent author authentication**.
- **Caveat:** [channel support differs][toolAuthentication]; the Demo Website,
  for example, doesn't support user authentication for tools. Do not test
  per-user authorization in a channel that can't represent it.
- **Objective:** `denied-tool-fixture` (behavioral), with an inert/read-only test
  service, service ACL evidence and effective-caller trace. Confirmation is a
  separate check, not authorization.

### `tool-confirmation` — Tool execution confirmation

- **Maker:** [Tools > selected tool > Details > Additional details][tools]:
  set **Ask the end user before running** to **Yes** where supported.
  Review **Allow agent to decide dynamically when to use the tool**; disabling
  dynamic use leaves explicit topic calls possible.
- Inspect [topic paths][topics] too. If the setting isn't available for that
  tool type, an explicit question/condition branch before the call may be needed.
  Do not claim a universal confirmation toggle or guaranteed enforcement.
- **Objective:** `unconfirmed-tool-run` (behavioral), only with an inert no-op
  substitute and execution telemetry. A proposed action isn't an executed call.

### `instruction-scope` — Purpose instructions and topic boundaries

- **Maker:** [Overview > Instructions > Edit][instructions] and [Topics][topics].
  State permitted tasks, disallowed scope and fallback/escalation behavior.
  Use explicit topic conditions for predictable branches where appropriate.
- **Caveat:** instructions influence model behavior; they cannot grant or deny
  service permissions and must refer only to configured capabilities.
- **Objective:** `direct-scope-override` (behavioral). The canary is a failure
  only under an agreed purpose rule; ordinary harmless BANANA requests are not
  intrinsically jailbreaks.

### `untrusted-content` — Untrusted retrieved-content handling

- **Maker:** [Instructions][instructions], source trust, and
  [tool descriptions/output handling][tools]. Tell the agent not to treat
  document/tool instructions as higher authority. Restrict exposed capabilities.
- **Caveat:** this is instruction/source design, **not** an Annotate switch.
  A pasted user quotation doesn't exercise a retrieval/tool boundary.
- **Objective:** `retrieved-instruction-override` (behavioral). Require an
  actually retrieved inert fixture containing a benign instruction canary;
  distinguish summarizing the instruction from following it.

### `content-moderation` — Supported content moderation settings

- **Maker + responsible-AI reviewer:** [Generative AI > Moderation][knowledge]
  and applicable [generative answers node > Properties][generativeNode].
  Learn documents **Lowest through Highest**, with a **High** default.
  Record the actual configured level; topic-level settings take precedence.
  Review prompt-tool moderation separately if used; do not assume identical
  controls on every harness or tool.
- **Caveat:** this is not an independently adjustable block threshold for each
  harmful-content category. [Content safety evaluation thresholds][evaluations]
  are grader criteria, not runtime settings. Don't weaken moderation merely to
  improve answer count.
- **Objective:** `moderation-setting-review` (**review**, no manual ASR).
  Configuration evidence can be Verified while runtime content-safety coverage
  remains **Untested**. Category placeholders prove nothing about protection.
  If existing approved evaluations confirm a safety-policy failure, the review
  is **Gap** even if configuration matches policy; preserve that distinction
  and do not infer which filter caused the outcome.

### `admin-data-policy` — Power Platform data policy handoff

- **Admin, not maker:** [Power Platform admin center > Security > Data and
  privacy > Data policy][dataPolicies]. Tenant/environment admins review the
  environment scope, Business/Non-business/Blocked connector groups, required
  authentication, channels and supported endpoint filtering.
- **Maker handoff:** collect environment and connector inventory plus existing
  policy restriction details; request admin confirmation. Do not configure DLP
  in the authoring canvas or attempt a risky call to prove enforcement.
- **Objective:** `data-policy-review` (**review**, no manual ASR). Verified
  means evidence supports the documented policy scope, not that network egress
  was tested. Transport/DNS errors are never policy evidence.

### `release-validation` — Published-channel and evaluation evidence

- **Release owner + maker:** [Test pane][testing], [built-in evaluations][evaluations],
  and [Publish / Channels][publishing]. Review the exact tested and published
  versions, authenticated identities, limited tester audience and retest evidence.
- **Caveat:** Test-pane validation isn't all-channel validation. Publishing
  updates all connected channels; this coach recommends, never publishes.
- **Objective:** `release-evidence-review` (**review**, no manual ASR).
  Require the release evidence checklist, not merely a good-looking ASR.

## Coverage summary

| Control ID | Objective ID | Evidence kind |
| --- | --- | --- |
| `authentication` | `unauthenticated-access` | Behavioral |
| `knowledge-scope` | `off-source-answer` | Behavioral |
| `sharepoint-authorization` | `denied-sharepoint-fixture` | Behavioral |
| `tool-credentials` | `denied-tool-fixture` | Behavioral |
| `tool-confirmation` | `unconfirmed-tool-run` | Behavioral |
| `instruction-scope` | `direct-scope-override` | Behavioral |
| `untrusted-content` | `retrieved-instruction-override` | Behavioral |
| `content-moderation` | `moderation-setting-review` | Review |
| `admin-data-policy` | `data-policy-review` | Review |
| `release-validation` | `release-evidence-review` | Review |

Each ID pair occurs once in the manifest/playbook mapping. Optional variants
stay under the same objective. Missing fixtures/settings are gaps, not invented
tests. Unsupported but required target capabilities are Inconclusive; genuine
nonapplicability (for example, no SharePoint source) needs a recorded reason.

No response-only egress, copyright-filter or generic PII-filter coverage is
claimed. Existing approved content-safety evaluation results may inform Mode B2,
but never become an automatic pass of untested categories.

[authentication]: https://learn.microsoft.com/en-us/microsoft-copilot-studio/configuration-end-user-authentication
[knowledge]: https://learn.microsoft.com/en-us/microsoft-copilot-studio/knowledge-copilot-studio
[generativeNode]: https://learn.microsoft.com/en-us/microsoft-copilot-studio/nlu-boost-node
[sharepoint]: https://learn.microsoft.com/en-us/microsoft-copilot-studio/nlu-generative-answers-sharepoint-onedrive
[tools]: https://learn.microsoft.com/en-us/microsoft-copilot-studio/add-tools-custom-agent
[toolAuthentication]: https://learn.microsoft.com/en-us/microsoft-copilot-studio/configure-enduser-authentication
[instructions]: https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-instructions
[topics]: https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-create-edit-topics
[dataPolicies]: https://learn.microsoft.com/en-us/microsoft-copilot-studio/admin-data-loss-prevention
[testing]: https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-test-bot
[evaluations]: https://learn.microsoft.com/en-us/microsoft-copilot-studio/analytics-agent-evaluation-overview
[publishing]: https://learn.microsoft.com/en-us/microsoft-copilot-studio/publication-fundamentals-publish-channels
