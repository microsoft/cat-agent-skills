# Billing Actions

Read this only when the bot should answer account-specific billing, invoice, subscription, license, renewal, refund, or cancellation questions.

This is advisory guidance for the DocsBot dashboard. The administration plugin does not perform subscription or commerce mutations, including enabling Stripe payments, refunds, or cancellations through `update_bot`. Do not execute the configuration steps below through Admin MCP.

DocsBot Stripe Actions: `https://docsbot.ai/documentation/developer/stripe-actions`

Skills library details: [skills-library.md](skills-library.md)

External MCP details: [external-mcp.md](external-mcp.md)

## Choose The Right Mechanism

Use Stripe Actions when the customer's product billing is in Stripe and the deployment can pass signed private customer metadata.

Use a billing Skill when the vendor has a library Skill, such as Freemius or another billing provider, and the Skill declares the needed env, secret, or metadata bindings.

Use external MCP only for private/internal bots or safe non-user-scoped lookups. OAuth or owner-scoped MCP tools can expose the connected owner's data, so do not enable them for anonymous public customer chats unless the tool itself enforces customer scoping.

Do not confuse customer billing actions with DocsBot account billing operations. DocsBot account subscription and commerce mutations are outside this plugin. Customer billing bot configuration requires separate dashboard authorization.

## Stripe Bot Tool Workflow

1. Confirm the bot should provide customer billing support and that Stripe is the customer's billing system.
2. Confirm the deployment can pass signed JWT metadata from the customer's backend, including `metadata.priv_stripe_customer_id`.
3. Start bot Stripe OAuth in the DocsBot dashboard; the hosted named-tool catalog does not advertise this operation.
4. Give the returned authorization URL to the user. The user completes OAuth in Stripe; MCP cannot finish that browser step.
5. After OAuth completion, read the bot with `get_bot` and verify `tools.stripe` configuration without printing tokens or stored OAuth fields.
6. Enable only the needed subtools. Be conservative with refunds and cancellations.
7. Add prompt guidance for when to use Stripe tools and when to escalate.

Compact save shape after OAuth is connected:

```json
{
  "tools": {
    "stripe": {
      "enabled": true,
      "recent_billing": { "enabled": true },
      "billing_portal": { "enabled": true },
      "refund": { "enabled": false, "rules": "" },
      "cancellation": { "enabled": false, "require_feedback": true }
    }
  }
}
```

Use `clearOAuthConnection: true` inside `tools.stripe` only when the user explicitly asks to disconnect Stripe. Never send or expose OAuth token fields; update preserves server-only token fields.

## Required Deployment Context

Stripe customer-scoped tools require signed private metadata:

- The customer application backend identifies the logged-in user.
- The backend maps that user to a Stripe customer ID.
- The backend signs a JWT using the bot signature key.
- The JWT includes `team_id`, `bot_id`, `exp`, `iat`, and `metadata.priv_stripe_customer_id`.
- The widget or Chat Agent API sends the JWT as the bearer token.

Never ask the user to place `priv_stripe_customer_id` in client-side public metadata or `identify`. Private metadata must be signed by the backend.

## Refund And Cancellation Guardrails

Refunds and cancellations are high-risk. Enable them only when the user provides policy rules.

Good guardrails specify:

- Eligible plans or customer groups.
- Maximum amount and recency.
- Whether subscription renewals are excluded.
- Whether prior refunds block automatic refunds.
- When to deny and escalate to support.

If policy is unclear, do not enable refund or cancellation tools. Use billing portal, invoice lookup, and escalation instead.

## Vendor Skill Workflow

When billing is not Stripe:

1. Search library Skills by vendor and task with `list_library_skills`.
2. If a relevant Skill exists, load [skills-library.md](skills-library.md) and follow its import/configure/verify workflow.
3. If no Skill exists and the user has a safe API or MCP, load [external-mcp.md](external-mcp.md) and evaluate whether the action is appropriate for the deployment audience.
4. Add prompt guidance that asks for the required customer identifier before using the billing action.

## Verification

- Saved bot read confirms only intended billing tools are enabled.
- Saved bot read confirms Stripe OAuth state is connected before `tools.stripe.enabled` is true; otherwise save will fail.
- No OAuth tokens, signature keys, or secret values are shown in output.
- Prompt instructions explain when to use billing tools, what identifier is required, and when to escalate.
- Handoff includes backend JWT/private metadata work the user must complete before public widget testing.
