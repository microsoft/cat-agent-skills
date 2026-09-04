# Host Profiles, Templates, and Contracts

Read this reference when selecting a host profile, choosing a template, or producing mappings and wiring guidance.

## Capability boundary

This package builds and reviews maker artifacts. It does not attach cards to runtime messages and does not edit Copilot Studio topics.

Copilot Studio supports Adaptive Cards 1.6 and earlier, but target hosts differ:

| Profile | Maximum version | Scope | Bounded policy |
|---|---:|---|---|
| `portable-1.5` | 1.5 | Teams, Omnichannel live chat, Web Chat, and test chat | Default and recommended |
| `teams-1.5` | 1.5 | Microsoft Teams | Test Teams separately |
| `omnichannel-1.5` | 1.5 | Omnichannel live chat widget | Test live chat separately |
| `web-chat-1.6` | 1.6 | Bot Framework Web Chat | `Action.Execute` remains unsupported |
| `test-chat-1.6` | 1.6 | Copilot Studio test chat | Test-only evidence, not deployment evidence |

The linter supports a deliberately conservative subset:

### Elements

* `TextBlock`
* `FactSet`
* `Container`
* `ColumnSet`
* `Column`
* `ActionSet`
* `Input.Text`
* `Input.Number`
* `Input.Date`
* `Input.Time`
* `Input.Toggle`
* `Input.ChoiceSet`

### Actions

* `Action.Submit`
* `Action.OpenUrl` with HTTPS

This subset is not the full Adaptive Cards schema. A type outside it can be valid Adaptive Cards JSON and still fail this linter because it is outside the package's portability and safety policy.

## Template catalog

| Template | Node mode | Use | Primary outputs |
|---|---|---|---|
| `welcome-starter-prompts.json` | Interactive | Start a conversation with three stable intents | `actionSubmitId`, `intent` |
| `information-summary.json` | Informational | Present a concise record or decision summary | None |
| `data-collection-form.json` | Interactive | Collect text, category, and due date | `requestTitle`, `requestCategory`, `requestedDate` |
| `confirmation.json` | Interactive | Confirm or go back before a consequential step | `confirmed`, action identity |
| `approval-decision.json` | Interactive | Approve, reject, or request changes; comment is optional for approval and downstream-required for rejection or changes | `reviewComment`, action identity |
| `choice-disambiguation.json` | Interactive | Resolve one ambiguous request from a controlled list | `selectedOption`, action identity |
| `status-progress.json` | Informational | Show current state, owner, and next step | None |
| `escalation-handoff.json` | Interactive | Capture a safe handoff summary and urgency | `handoffSummary`, `urgency`, action identity |

Use the smallest card that supports the interaction. A card should not become a miniature application.

## Card package contract

Return this directory shape when file output is appropriate:

```text
adaptive-card-package/
  card.json
  card.powerfx             optional, dynamic cards only
  sample-data.json         optional, data-driven cards only
  mapping.md
  wiring.md
  validation.json
  accessibility.md
  fallback.txt
```

`card.json` is always present. For a dynamic card it is a static representative that can be linted and used to inspect structure.

## Input mapping contract

```yaml
inputs:
  - id: requestTitle
    card_type: Input.Text
    output_type: String
    copilot_output: requestTitle
    downstream_variable: Topic.requestTitle
    required: true
    sample: Replace a damaged item
    validation:
      client: isRequired and maxLength
      downstream: trim, length, policy, authorization
```

Input IDs are the stable contract. Changing an ID is a breaking change to downstream mappings.

Suggested Copilot Studio output types:

| Input type | Typical output type |
|---|---|
| `Input.Text` | String |
| `Input.ChoiceSet` | String, or a documented delimited string for multiselect |
| `Input.Number` | Number |
| `Input.Date` | String or Date after explicit conversion |
| `Input.Time` | String or Time after explicit conversion |
| `Input.Toggle` | String or Boolean after explicit conversion and schema review |

Copilot Studio creates output variables based on card inputs. Makers must inspect the generated output schema and correct types where needed.

## Action mapping contract

Every submit action includes:

```yaml
action:
  title: Approve
  data:
    cardId: approval_decision_v1
    actionId: approve
    actionSubmitId: approval_decision_v1_approve
    intent: approval.approve
    riskLevel: consequential
  downstream_branch:
    condition: actionSubmitId equals approval_decision_v1_approve
    authorization_check: required
    stale_submission_check: required
    duplicate_submission_check: required
    business_rule_check: required
```

`actionSubmitId` identifies one button on one card version. `actionId` is a short stable branch key. `intent` gives a readable machine contract.

`riskLevel` is required and must be `none`, `consequential`, or `destructive`. A destructive action also requires `confirmationInputId`, `requiresExplicitConfirmation: true`, and a matching initially-off required confirmation toggle with distinct on and off values. Escape actions can use `associatedInputs: "none"` when they must bypass incomplete form validation, but they must declare `riskLevel: "none"` and `isEscapeAction: true`. Consequential and destructive actions cannot bypass associated inputs.

### Conditional downstream input validation

Adaptive Card native validation applies to the card submission, not selectively
to individual submit actions. Do not set `reviewComment` as card-required in the
approval template, because that would also block Approve.

After matching the submitted action against the trusted expected
`actionSubmitId`:

* **Approve:** `reviewComment` can be blank.
* **Reject:** trim `reviewComment`; if blank, reprompt and do not record or invoke the decision.
* **Request changes:** trim `reviewComment`; if blank, reprompt and do not record or invoke the decision.

Treat action data as untrusted input. Configure these branch rules in the topic
or downstream service rather than trusting a client-provided requirement flag.

Do not put authorization claims, secrets, or trusted server state into action data. Users and clients can submit payloads independently of the intended visual flow.

## Dynamic card contract

Use Power Fx only when the card needs values from the conversation or another node.

Produce:

1. A static representative JSON card with synthetic values.
2. A Power Fx formula derived from that structure.
3. A variable table naming every reference and scope.
4. Sample values for testing.
5. A statement that the linter validates only the static JSON.

Example variable table:

| Display purpose | Power Fx reference | Type | Sample |
|---|---|---|---|
| Request title | `Topic.RequestTitle` | String | Replace a damaged item |
| Due date | `Topic.RequestedDateText` | String | 2026-09-18 |

Do not use `${Topic.RequestTitle}` inside JSON. That is a template expression, not a Copilot Studio JSON binding contract.

## Plain-text fallback contract

An informational fallback preserves all decision-relevant facts:

```text
Request REQ-1042
Status: Waiting for review
Owner: Service desk
Next step: A reviewer will respond by 18 September 2026.
```

An interactive fallback preserves a parseable choice:

```text
Reply with one option:
1. Approve
2. Reject
3. Request changes

Include a comment after the number if needed.
```

Do not pretend `fallbackText` creates a full alternate form. It is a graceful rendering fallback. Topic-level plain-text handling must be designed separately when the interaction is business-critical.

## Security and privacy checks

Reject or redesign a card that:

* asks for a password, secret, token, API key, private key, or credential;
* embeds raw production records without minimization;
* puts trusted state or authorization assertions in action data;
* invokes an irreversible operation without confirmation;
* uses an external image without a documented need, trusted host, and privacy review;
* includes an HTTP rather than HTTPS link;
* treats a hidden field as tamper-proof.

Cards are untrusted presentation and input surfaces. Enforce permissions, validation, idempotency, and business rules downstream.

## Accessibility and mobile checklist

* Use `label` on every input.
* Use `isRequired` and a useful `errorMessage` for required inputs.
* Put elements in the intended keyboard order.
* Start with a `TextBlock` using `style: "heading"`.
* Set `wrap: true` on all `TextBlock` elements.
* Keep instructions next to the relevant fields in JSON order.
* Use descriptive action titles.
* Reinforce color with text.
* Avoid hidden validated inputs.
* Prefer one column and short labels.
* Keep primary actions to three or fewer.
* Test with keyboard navigation and a screen reader in every target channel.

## Validation result contract

```yaml
validation:
  validator: copilot-studio-adaptive-card-linter
  validator_version: 1.0.0
  scope: bounded semantic lint, not official schema validation
  profile: portable-1.5
  mode: interactive
  working_directory: skill root
  command: python scripts/validate_cards.py card.json --profile portable-1.5 --mode interactive
  errors: 0
  warnings: 0
  host_rendering_tested: false
  remaining_tests:
    - Copilot Studio test chat
    - Microsoft Teams desktop
    - Microsoft Teams mobile
    - Keyboard and screen reader
```

## Official sources

* [Adaptive Cards overview in Copilot Studio](https://learn.microsoft.com/en-us/microsoft-copilot-studio/adaptive-cards-overview)
* [Ask with Adaptive Cards](https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-ask-with-adaptive-card)
* [Send a message](https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-send-message)
* [Power Fx expressions](https://learn.microsoft.com/en-us/microsoft-copilot-studio/advanced-power-fx)
* [Accessibility tips for Adaptive Cards](https://learn.microsoft.com/en-us/microsoft-copilot-studio/adaptive-card-accessibility-tips)
* [Adaptive Cards input validation](https://learn.microsoft.com/en-us/adaptive-cards/authoring-cards/input-validation)
* [Adaptive Cards schema](https://adaptivecards.io/schemas/adaptive-card.json)
