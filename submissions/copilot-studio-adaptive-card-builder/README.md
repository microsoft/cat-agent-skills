# Copilot Studio Adaptive Card Builder

Turn a plain-language interaction requirement into a maker-ready Adaptive Card package for Microsoft Copilot Studio. The skill produces the card, sample data when useful, input and action mappings, node wiring guidance, validation results, accessibility notes, and a plain-text fallback.

## Important boundary

**Agent instructions cannot dynamically render an Adaptive Card.** The skill creates artifacts for a maker to paste or configure in a Copilot Studio **Ask with Adaptive Card**, **Message**, or **Question** node. If card JSON is emitted into chat by a model, it normally appears as text or a code block rather than as a native card.

This is a maker-assistance skill. It is not a runtime UX engine, an authorization control, a complete Power Fx framework, or a guarantee that every channel renders a card identically.

## What makes it useful

The package goes beyond generating JSON:

* Eight conservative templates cover welcome prompts, information summaries, data collection, confirmation, approvals, disambiguation, status, and escalation.
* A dependency-free Python semantic linter checks the high-confidence failures that commonly break Copilot Studio cards.
* Explicit input, output, and action contracts make downstream conditions and tools easier to wire.
* Host profiles prevent a card built for the test pane from silently depending on features unavailable in Teams or live chat.
* Accessibility and mobile-safe defaults are built into the workflow.
* Every result includes a plain-text fallback.

The linter is intentionally bounded. It is not a replacement for the official Adaptive Cards schema, the Copilot Studio designer, or testing in each target channel.

## Before you start

You need:

* Microsoft Copilot Studio access to edit an agent topic.
* Python 3.10 or later only if you want to run the bundled linter locally. The linter uses the Python standard library and installs no packages.
* A clear target channel. If none is supplied, the skill defaults to the portable Copilot Studio 1.5 profile.

Do not provide secrets, tokens, credentials, sensitive identifiers, or raw production records as example content.

## How to use it

Ask in plain language:

* "Build a Teams-safe approval card for a purchase request."
* "Create an accessible intake form with category, due date, and details."
* "Make a status summary card for a Message node, plus a text fallback."
* "Review this Adaptive Card JSON for Copilot Studio and explain how to wire its outputs."
* "Turn this confirmation step into a card package, but require explicit confirmation before the destructive action."

The response should contain:

1. `card.json`, a paste-ready static card or static representative for a dynamic card.
2. `card.powerfx`, only when dynamic values genuinely require a Power Fx formula.
3. Sample or test data when the card is dynamic or data-driven.
4. Input, output, and action mapping.
5. Copilot Studio node and downstream wiring guidance.
6. Linter results with the selected host profile.
7. Accessibility and mobile notes.
8. A plain-text fallback.

## Validate a card

From the skill directory:

```powershell
python scripts\validate_cards.py assets\templates --profile portable-1.5
```

Validate a generated card and require a specific node mode:

```powershell
python scripts\validate_cards.py card.json --profile teams-1.5 --mode interactive
```

Machine-readable output is available with `--format json`. Add `--warnings-as-errors` for a stricter quality gate.

## Host profiles

| Profile | Maximum card version | Intended use |
|---|---:|---|
| `portable-1.5` | 1.5 | Default across Teams, live chat, Web Chat, and test chat |
| `teams-1.5` | 1.5 | Microsoft Teams |
| `omnichannel-1.5` | 1.5 | Omnichannel live chat widget |
| `web-chat-1.6` | 1.6 | Bot Framework Web Chat, excluding `Action.Execute` |
| `test-chat-1.6` | 1.6 | Copilot Studio test chat only |

The bundled templates stay at version 1.5. `Action.Execute` is outside every bundled profile. The safe action subset is `Action.Submit` and HTTPS `Action.OpenUrl`.

## Product facts and sources

Microsoft documents that Copilot Studio supports Adaptive Cards schema 1.6 and earlier, with Teams and the Omnichannel live chat widget limited to 1.5. Bot Framework Web Chat supports 1.6 but not `Action.Execute`. Version 1.6 cards render in test chat rather than on the authoring canvas. See [Adaptive Cards overview](https://learn.microsoft.com/en-us/microsoft-copilot-studio/adaptive-cards-overview).

Interactive cards belong in an **Ask with Adaptive Card** node and require at least one submit button. Copilot Studio creates output variables from card inputs, and Microsoft recommends unique submit data when multiple cards can remain active. See [Ask with Adaptive Cards](https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-ask-with-adaptive-card).

Informational cards belong in a **Message** or **Question** node. See [Send a message](https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-send-message#add-an-adaptive-card).

Dynamic values can be authored with Power Fx in the card node. Power Fx variable references use scope prefixes such as `Topic.`, `Global.`, and `System.`. See [Create expressions using Power Fx](https://learn.microsoft.com/en-us/microsoft-copilot-studio/advanced-power-fx).

For accessibility, Microsoft recommends input `label` properties, `isRequired` and `errorMessage`, logical JSON order, descriptive action titles, heading styles, and channel testing with screen readers. See [Accessibility tips for Adaptive Cards](https://learn.microsoft.com/en-us/microsoft-copilot-studio/adaptive-card-accessibility-tips) and [Input validation](https://learn.microsoft.com/en-us/adaptive-cards/authoring-cards/input-validation).

## Good to know

* Validation proves only that a card satisfies this package's bounded policy. It does not prove channel rendering.
* Test the final card in the Copilot Studio test chat and every intended published channel.
* Keep cards concise. Prefer a single-column layout for forms and mobile use.
* Cards collect and present data. They do not authorize a user or enforce a business transaction.
* Validate permissions and business rules again in the downstream topic, flow, connector, or API.
* External images are excluded from the bundled profile by default.
* Never use card data as a place to hide credentials or authorization decisions.
