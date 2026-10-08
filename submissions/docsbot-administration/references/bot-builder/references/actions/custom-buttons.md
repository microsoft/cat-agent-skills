# Custom Buttons

Read this only when adding or tuning custom action buttons for a specific use case that other actions cannot satisfy.

DocsBot guide: `https://docsbot.ai/documentation/doc/how-to-use-custom-action-buttons-in-docsbot`

Developer behavior: `https://docsbot.ai/documentation/developer/chat-agent#tool_call`

## Purpose And Fit

Custom buttons are not a default public-widget requirement. Use them only when a specific workflow needs a visible link-based handoff and no better built-in action, Skill, MCP connector, source, support link, lead form, or scheduling tool covers it.

Good fits:

- Unsupported booking engines that need a button to the user's calendar URL.
- Canonical status, changelog, account portal, checkout, trial, or dashboard links when the bot should offer the link only in a specific context.
- Integration connection pages where the next step must happen in the dashboard.
- Narrow sales or support handoffs that are not handled by lead collection, scheduling, escalation, Skills, or MCP.

Avoid custom buttons for ordinary docs, pricing, contact, or support links when a normal answer, trained source citation, `supportLink`, lead form, or built-in scheduling action is enough.

Do not use custom buttons for secret-bearing actions, destructive actions, or user-specific operations that require authenticated server-side checks. Use Skills or MCP actions for those.

## Operation Workflow

1. Read the bot with `get_bot`.
2. Decide whether a custom button is necessary. If another action or normal link answer covers the need, do not add one.
3. Optionally draft metadata with `draft_custom_button`.
   - Body: `{ "input": "Send users to our pricing page when they ask about plans or cost." }`
   - The draft validates plan access and action slot availability, but does not save anything.
4. Add a reviewed `url` and save the button in `tools.customButtons` with `update_bot`.
5. Read the bot again with `get_bot` and verify every saved button.

Required fields for each saved button:

- `enabled`: boolean.
- `name`: internal descriptive name.
- `functionKey`: lowercase `a-z`, numbers, and underscores only; unique per bot.
- `instructions`: when the agent should offer the button.
- `buttonText`: visible label.
- `icon`: dashboard/widget icon name. If unsure, prefer a simple link-style icon.
- `url`: final public URL.

Stored `functionKey` values do not include `button_`; DocsBot adds that prefix internally when exposing the tool.

## Save Shape

Preserve existing `tools` entries when updating:

```json
{
  "tools": {
    "customButtons": [
      {
        "enabled": true,
        "name": "Pricing page",
        "functionKey": "pricing",
        "instructions": "Offer this when the user asks about plans, pricing, billing tiers, or trial options.",
        "buttonText": "View pricing",
        "icon": "BanknotesIcon",
        "url": "https://example.com/pricing"
      }
    ]
  }
}
```

## Verification

- Verify `enabled`, `name`, `functionKey`, `instructions`, `buttonText`, `icon`, and `url` after saving.
- Add or preserve prompt guidance so the bot knows when to offer each CTA.
- For widgets/API callers, ensure the surface enables custom buttons, such as `useCustomButtons` in widget options or `custom_buttons` in Chat Agent API requests.
