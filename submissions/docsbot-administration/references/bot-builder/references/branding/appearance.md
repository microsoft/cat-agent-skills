# Branding And Appearance

Read this when applying brand analysis, widget appearance, first message, starter questions, support URL, logos, icons, or visual polish.

For detailed widget color/logo selection, contrast checks, and logo upload fallback, load [widget.md](widget.md).

## Brand Analysis Flow

1. If a public website exists, run `analyze_website_for_bot` with `siteURL`.
2. Use returned colors, logos, screenshot, language, and support/widget hints as a first pass.
3. Prefer full logos for header/logo fields and compact icons or avatars for bot icons.
4. Choose a main widget color that has good contrast against the site background and common white/dark widget surfaces. For widget deployments, follow [widget.md](widget.md) before saving.
5. Persist the full analyzer result into the bot's `brandAnalysis` field during bot create or the next bot update.

Do not treat analyzer output as transient setup context. The dashboard uses saved `brandAnalysis.colors` and `brandAnalysis.logos` for widget color/image presets, and bot list displays can use saved `brandAnalysis.logos` plus `color` for discovered brand icons. If only `color` and `logo` are saved, those presets and discovered icons can be missing.

On create with `create_bot`, include the selected branding fields directly when the schema accepts them. If the bot already exists, save them with `update_bot` after reading current settings and preserving unrelated fields.

Onboarding-compatible payload shape:

```json
{
  "color": "#0ea5e9",
  "logo": "https://example.com/logo.svg",
  "widgetType": "other",
  "supportLink": "https://example.com/support",
  "brandAnalysis": {
    "domain": "example.com",
    "url": "https://example.com",
    "...": "include the remaining analyzer response fields such as colors, logos, screenshotUrl, language, supportUrl, and widgetType"
  }
}
```

Build `brandAnalysis` as `{ domain, url, ...analysisResult }`, using the analyzer's returned `domain`/`url` when present and the scanned site URL as fallback. Preserve arrays such as `colors` and `logos` exactly unless the live API schema requires normalization.

Initial color selection should match onboarding behavior when practical:

1. Use `analysis.colors[0].hex` when present.
2. Else use `analysis.buttonColor` when it is present and not the default blue.
3. Else choose the best visible brand preset/custom hex after contrast review.

Initial logo selection should match onboarding behavior before applying the visual contrast check:

1. Determine whether the selected color is light by luminance: `(0.299*r + 0.587*g + 0.114*b) / 255 > 0.5`.
2. Prefer a full logo whose `mode` matches the selected color target used by onboarding.
3. Then prefer a matching icon, then full logos with `has_opaque_background`, then icons with `has_opaque_background`.
4. Fall back to the first full logo/icon/logo candidate, then `analysis.logoUrl`.

If MCP create/update rejects `brandAnalysis`, report an API/catalog mismatch instead of silently omitting it. Use the dashboard/onboarding flow or propose an API helper only after confirming the normal bot write operation cannot persist the field.

## Appearance Decisions

- Use a clean production bot name and description. Do not save test/disposable/timestamp language in final-product bots.
- Write and save `labels.firstMessage` specific to the business, user journey, audience, and deployment surface. Do not leave the default first-message label in place for production bots.
- Do not edit other labels during normal appearance setup. `labels.floatingButton` or another label may change when the user asks or when the specific assigned task requires it; otherwise preserve it. If a full `labels` object is required, carry all out-of-scope values through unchanged.
- Add starter questions that match high-frequency questions discovered during research.
- Set a support/contact URL that matches the bot's use case: support route for support bots, demo/contact route for presales, internal route for staff bots.
- If the analyzer returns weak favicon-only assets, research the public site for better logo/icon candidates before settling.
- For website widgets, visually verify that the chosen header logo contrasts with the chosen widget color. If the best logo is not in `brandAnalysis.logos`, follow the upload fallback in [widget.md](widget.md).

## Verification

Before handoff, read the saved bot and verify:

- Bot name and description.
- Widget/main color.
- Header/logo/icon/avatar fields where available.
- `brandAnalysis.colors` and `brandAnalysis.logos` are persisted when the analyzer returned them.
- `labels.firstMessage`, starter questions, and unchanged values for every label outside the assigned task.
- Support/contact URL.
- Language/locale if inferred from brand analysis.

If brand fields did not save, `brandAnalysis` is missing after analysis, or assets are missing, report that as a remaining polish task rather than claiming final-product readiness.
