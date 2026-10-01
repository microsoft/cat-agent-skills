# Scheduling Actions

Read this only when the bot should offer booking for meetings, demos, onboarding, or sales calls.

DocsBot guides:

- Calendly: `https://docsbot.ai/documentation/doc/how-to-set-up-calendar-actions-with-calendly-in-docsbot`
- Cal.com: `https://docsbot.ai/documentation/doc/how-to-set-up-calendar-actions-with-cal-com-in-docsbot`
- TidyCal: `https://docsbot.ai/documentation/doc/how-to-set-up-calendar-actions-with-tidycal-in-docsbot`

Developer behavior: `https://docsbot.ai/documentation/developer/chat-agent#tool_call`

## Purpose

Scheduling actions help sales and success bots turn qualified buying intent into a booked meeting without making the user hunt for the right calendar page. They are especially useful for:

- Demo requests.
- Presales qualification and discovery calls.
- Implementation or onboarding calls.
- Office hours or high-touch support sessions.

Do not enable scheduling just because the company has a calendar link; enable it when booking time is a desired outcome for the bot.

## Built-In Providers

DocsBot has built-in scheduling tools for exactly these providers:

| Provider | Tool key | Agent tool name | Widget/API enable flag |
| --- | --- | --- | --- |
| Calendly | `calendly` | `book_calendly` | `useCalendly` / `calendly` |
| Cal.com | `calcom` | `book_calcom` | `useCalCom` / `calcom` |
| TidyCal | `tidycal` | `book_tidycal` | `useTidyCal` / `tidycal` |

For unsupported booking engines, do not invent a built-in scheduling tool. Create a [custom button](custom-buttons.md) that links to the user's booking URL instead.

## Operation Workflow

1. Read the bot with `get_bot`.
2. Determine whether the booking engine is one of the built-in providers: Calendly, Cal.com, or TidyCal.
3. Verify the booking URL from site research or the user. Prefer a specific demo/sales event URL over a generic profile when the use case is clear.
4. Decide when the tool should trigger, including any pre-qualification the bot must complete first.
5. Save the provider tool with `update_bot`, preserving other `tools`.
6. Read the bot again and verify the provider tool is enabled with instructions and URL.

Use this shape under `tools`:

```json
{
  "calendly": {
    "enabled": true,
    "instructions": "Offer this when the user wants a product demo, sales call, or onboarding session.",
    "url": "https://calendly.com/example/demo"
  }
}
```

Replace `calendly` with `calcom` or `tidycal` for those providers.

For unsupported booking engines, use [custom-buttons.md](custom-buttons.md) and create a CTA such as:

```json
{
  "enabled": true,
  "name": "Book a sales call",
  "functionKey": "book_sales_call",
  "instructions": "Offer this after the user shows buying intent or asks to talk to sales.",
  "buttonText": "Book a sales call",
  "icon": "CalendarDaysIcon",
  "url": "https://example.com/book-demo"
}
```

## Trigger Instructions

The provider `instructions` field controls when the agent offers the scheduling tool. Use it to encode the sales workflow instead of adding a broad "always offer a meeting" rule.

Good trigger instructions are specific:

```text
Offer this when the user asks for a demo, wants to speak with sales, compares plans for a purchase, or asks about implementation help. Before offering it, ask for company size and use case if those details are missing.
```

```text
Offer this only after the user confirms they are evaluating the product for their team and has shared their main use case. Do not offer it for routine documentation or troubleshooting questions unless the user asks to talk to someone.
```

```text
Offer this when a qualified prospect asks about enterprise pricing, security review, procurement, or migration planning. If the user is just browsing pricing, answer from documentation first and ask whether they want to book a call.
```

The agent should not trigger booking before required qualification steps if the instructions say qualification is required.

## Prompt Guidance

Add one concise line to the agent prompt describing when to offer the booking action and what the call is for. Avoid making booking the default answer to normal documentation questions.

For sales bots, include whether the bot should qualify first:

```text
When a visitor shows sales intent, qualify their use case and company size, then offer the demo booking action if they want to speak with sales.
```

If using a custom button fallback, mention that the button is a booking link, not a built-in scheduling tool.

## Verification

- Saved bot read shows the expected provider under `tools`.
- Widget/API deployment enables the selected scheduling tool where applicable, such as `useCalendly`, `useCalCom`, `useTidyCal`, or the matching Chat Agent API boolean.
- Unsupported booking engines use a saved custom button with a verified booking URL.
- The tool or button instructions define when to suggest booking and any pre-qualification required before triggering.
- Handoff includes the booking URL and the reason scheduling was enabled.
