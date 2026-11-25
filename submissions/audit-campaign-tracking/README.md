Check a sanitized ad URL before using campaign results to make a spending decision.

Give the agent a sample URL, the originating channel, and the report in which you expect to see the visit. The skill identifies missing tracking fields and suggests the earliest follow-up test. It needs no ad account, scripts, or keys.

For a fictional hotel campaign, `https://example.com/rooms?utm_source=google&utm_medium=cpc` is missing `utm_campaign`. Add a campaign name, then verify the redirect destination and resulting visit or conversion separately.

In Copilot Studio, add the downloaded skill under **Build → Skills → Upload a skill**. [Microsoft upload instructions](https://learn.microsoft.com/microsoft-copilot-studio/agents-experience/skills-add-existing)

[Source skill](https://github.com/Qonvert-Marketing-AI/qonvert-marketing-skills/tree/main/skills/audit-campaign-tracking) · [Optional Qonvert Connect example](https://qonvert.ai/connect/google-ads?utm_source=cat_agent_skills&utm_medium=directory&utm_campaign=google_ads_mcp)
