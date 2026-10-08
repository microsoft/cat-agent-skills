# Widget Branding

Read this only when configuring website widget branding, header logos, bot avatars, entry-button icons, or when brand analysis returned weak/missing image assets.

## Field Map

- `color`: widget theme/header color. Must be a hex color such as `#0ea5e9`.
- `logo`: widget header logo URL or `false`/empty to remove it.
- `headerAlignment`: `left` or `center`.
- `botIcon`: bot avatar in messages. Use built-ins such as `robot`, `book`, `life-ring`, or an uploaded/public image URL. Save `false` for none.
- `icon`: entry button icon. Built-ins are limited; public image URLs are also accepted.
- `brandAnalysis.colors`: brand color presets from analysis.
- `brandAnalysis.logos`: candidate brand images, commonly objects with `url`, `type`, and `mode`.

Save these with `update_bot` after reading current bot settings and preserving unrelated fields.

When the bot was created from website analysis, the full analyzer result must be persisted as `brandAnalysis`. Widget settings reads saved `brandAnalysis.colors` and `brandAnalysis.logos` to render the discovered brand presets. Saving only `color` and `logo` is not enough for the user to see those presets later.

## Selection Flow

1. Start from `analyze_website_for_bot` output.
2. Select the initial color as onboarding does: first `colors[0].hex`, else non-default `buttonColor`, else the best visible preset/custom color.
3. Select the initial header logo as onboarding does: full logo matching the selected color target, then matching icon, then opaque-background full logo, then opaque-background icon, then first full logo/icon/logo, then `logoUrl`.
4. Prefer a full logo for `logo` and a compact icon/avatar for `botIcon` or `icon`.
5. Prefer logos already identified in `brandAnalysis.logos` over favicons or generic OG images.
6. Use `headerAlignment: "center"` for balanced full logos; use `"left"` when the logo is wide or paired with a compact product name.
7. After selection, do the contrast check below. Onboarding-compatible selection is a starting point, not a substitute for visual review.

Do not copy the same uploaded header logo into `icon` or `botIcon` by default. `logo` is the widget header image and is often wide, cropped, or text-heavy. `icon` is the entry-button mark and `botIcon` is the chat avatar; choose a compact square/circular mark for those, use appropriate built-ins, or leave existing values unchanged. Only set `icon` or `botIcon` to the same image as `logo` when the user explicitly asks for that and the image is visually appropriate at icon size.

## Contrast Check

Before saving a logo/color pair, visually inspect the candidate logo against the chosen widget color:

- If the widget color is dark, choose a light/white logo or an image with an opaque/light background.
- If the widget color is light, choose a dark logo or an image with an opaque/dark enough mark.
- If logo metadata has `mode`, use it as a hint: `light` usually means suited for dark backgrounds; `dark` usually means suited for light backgrounds; `has_opaque_background` can work on most colors.
- Do not rely only on metadata. Open or inspect the image when practical, especially for transparent PNG/SVG logos.
- Reject favicon-only or tiny square marks for the header when a real horizontal/full logo is available.
- If all full logos fail contrast, either choose a different brand color from presets or use an opaque-background logo.

Practical visual test: view the logo on a rectangle filled with the chosen `color`; verify the brand mark and wordmark are readable at widget-header size. If it blends in, change the logo variant or color before saving.

## Fallback Logo Discovery

If `brandAnalysis.logos` is missing, favicon-only, or low contrast:

1. Inspect the public website header/footer for logo image URLs.
2. Check common public assets such as `/logo.svg`, `/logo.png`, `/brand`, `/press`, `/media-kit`, or Open Graph metadata, but avoid using generic OG hero images as header logos.
3. Prefer SVG/PNG/WebP images with transparent or crisp backgrounds.
4. Use the selected image URL directly if it is public, stable, and hotlink-safe enough for a widget.
5. If the logo is not publicly usable as a URL, use the upload fallback below or give the user the widget design deep link.

## Upload Fallback

MCP can save a public image URL into bot settings, but the dashboard upload flow itself uploads bytes from the browser to Firebase Storage. Use this fallback when the right logo was not identified by brand analysis and cannot be used as a stable public URL.

Dashboard flow:

1. Send the user to `https://docsbot.ai/app/bots/{botId}/widget/design`.
2. Tell them to upload a PNG, JPEG, GIF, or WebP image in the Header Styles logo upload control.
3. Tell them to choose the matching widget color preset or custom hex color.
4. After they upload/save, re-read bot settings and verify `logo`, `color`, and `headerAlignment`.

Agent-assisted upload when the local file is available and the environment has dashboard auth/storage access:

1. Use `create_bot_image_upload_url` with `fileName` and optional matching `contentType`.
2. Upload bytes to the returned `uploadUrl` outside MCP using the returned `contentType`.
3. Save the returned `cdnUrl` to `logo`, `botIcon`, or `icon` with `update_bot`.
4. Re-read the bot and visually verify contrast.

Do not use `https://storage.googleapis.com/...`, `https://firebasestorage.googleapis.com/...`, `gs://...`, or raw Firebase/Appspot bucket URLs for production widget `logo`, `icon`, or `botIcon` values. Those may not be publicly authorized through the widget. Do not derive widget branding URLs from source-upload responses such as `create_source_upload_url`; that endpoint is for knowledge-source files and returns pending `user/{userId}/team/{teamId}/bot/{botId}/...` paths, not dashboard image paths or CDN URLs for widget assets.

If the image upload operation is unavailable or bytes cannot be uploaded in the current environment, provide the dashboard deep link and exact upload instructions instead of inventing or converting a storage URL. Do not print signed upload URLs, storage credentials, or temporary private paths.

## Verification

Before handoff:

- Read the saved bot and confirm `color`, `logo`, `headerAlignment`, `botIcon`, and `icon` as applicable.
- Confirm every custom uploaded `logo`, `botIcon`, or `icon` uses a public `https://cdn.docsbot.ai/...` URL in production, not `storage.googleapis.com`, `firebasestorage.googleapis.com`, Appspot bucket URLs, signed upload URLs, or source-upload pending paths.
- Confirm `icon` and `botIcon` are compact icon/avatar assets or intentional built-ins; do not reuse a wide/header-only logo for them unless explicitly requested.
- Confirm saved `brandAnalysis.colors` and `brandAnalysis.logos` are present when site analysis returned them.
- Confirm the header logo is readable against the chosen color.
- Confirm the selected image is not just a favicon unless the user explicitly chose an icon-only header.
- Include the widget design link in handoff for any remaining visual review: `https://docsbot.ai/app/bots/{botId}/widget/design`.
