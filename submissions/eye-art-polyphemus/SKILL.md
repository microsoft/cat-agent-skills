---
name: eye-art-polyphemus
description: Use Eye.Art Polyphemus when the user wants to create or refine an image, edit a reference image, match a visual to webpage code, create editable SVG, or explore supported artist-guided and motion workflows.
---

# Eye.Art Polyphemus

Use Eye.Art when the user asks for an image or editable vector. Polyphemus is a hosted workflow router, not a downloadable model. Its model and workflow choices stay behind one remote MCP endpoint.

## Choose the right request

- For a new image, use `eye_art_make_image` with `mode: "image"`.
- For a visual muse, pass `artist`: `polyphemus`, `dali`, `goya`, `matisse`, `leonardo`, `van_gogh`, `rothko`, or `ross`. Preserve the user's subject and composition. Treat artist names as visual direction, not endorsement or exact imitation.
- For icons and compact illustrations, use `mode: "small_art"`; specify size, silhouette, contrast, and background.
- For a website-matched image, use `mode: "site_match"`; describe the target section, crop, palette, and clear space for copy. Before sending any HTML, CSS, JavaScript, or TypeScript to Eye.Art, tell the user that the selected source will be uploaded to the external service and ask for confirmation. Send only the minimum relevant snippet, and remove credentials, personal data, proprietary code, and unrelated page content. Do not populate `pageReferences` until the user confirms.
- For an edit, use `eye_art_edit_image` with the source image as `imageDataUrl`. Say exactly what to change and what to preserve. Keep the source attached for follow-up edits when needed.
- For an editable vector, use `eye_art_make_svg` and save the returned `svg` field as an `.svg` file. This creates vector geometry; it does not trace raster references or animate SVG.
- Use `eye_art_prompt_ideas` to explore directions before rendering. Use `mode: "motion"` only for supported motion requests.

## Preserve conversation context and retrieve results

1. For related turns, pass the returned `conversationId` into the next make/edit call so the service can use its retained conversation and reference context. Start a fresh conversation or set `clearReferences: true` for an unrelated concept.
2. If a make/edit call returns a `jobId`, poll `eye_art_image_status` at reasonable intervals for up to 15 minutes total. Show an image only after a completed result is returned. If the job is still queued or running at the time limit, report that status and the `jobId` so it can be checked later; do not keep polling indefinitely or claim completion.
3. When an edit drifts, send the original image again and ask for a narrower change. State both the requested change and the parts that must remain fixed.
4. Report the actual tool status and errors. Do not claim an image was created if the tool only queued a job or failed.

## Limits and privacy

- No Eye.Art key is needed. Anonymous image generation is currently limited to 20 generations per hour per caller network identity; free to try does not mean unlimited.
- Longer staged workflows can take several minutes. Relay the actual queued/running state; do not promise a fixed completion time.
- Image references are sent to Eye.Art. Do not upload private or sensitive images without the user's direction. Images, prompts, and conversations may be retained for up to 30 days for service history and debugging.
- Do not claim guaranteed speed, provider, workflow, or quality. Artist names describe visual guidance only; Eye.Art is not affiliated with or endorsed by the named artists or their estates.

## Tool reference

The endpoint currently exposes `eye_art_make_image`, `eye_art_make_svg`, `eye_art_edit_image`, `eye_art_prompt_ideas`, `eye_art_image_status`, and conversation list/get/delete tools. Check the live endpoint's schemas for exact argument details:

`https://eye.art/api/eye-mcp`
