# Source Types And Add Flows

Use this reference before creating sources. Inspect the advertised `create_source` schema before the first create in a session because source types, plan gates, and connector fields can change.

For bot-level field names such as `retrieverTags`, `labels`, `tools`, and `mcpServers`, see the Compact Field Map in [operations.md](operations.md).

## Coverage Strategy

For production support, presales, docs, or product bots, import the full relevant knowledge base, help center, developer docs, and product detail pages. A few manually chosen top-level URLs are only enough for a smoke test or a tightly scoped bot.

Preferred order:

1. Sitemaps first. Use full sitemaps for the target docs/KB/product sections. Prefer sub-sitemaps when they cleanly include the right section and exclude noisy areas such as full blogs, legal archives, jobs, unrelated marketing pages, or stale translated copies.
2. Website mapping second. If no sitemap exists, use `map_website_urls` against the best root URL, then create a `website` source from the returned applicable URLs. Treat this as a quick site-structure discovery pass, not a complete crawl. It commonly finds quickly accessible top-level or obvious linked URLs and can miss deeper KB/docs/product pages. Observed on 2026-07-03: `website` creation accepts `type: "website"`, a root `url`, selected `urls`, `tags`, and `scheduleInterval`.
3. Manual crawl fallback. If MCP website mapping cannot discover the structure, briefly crawl or fetch public pages yourself, extract all applicable internal links for the target docs/KB/product sections, filter noise, then create a URL-list source through MCP.
4. URL lists only for explicit URLs. `type: "urls"` does not crawl linked pages. It indexes only the URLs in the `urls` array. Do not pass one docs root as a URL list and expect linked pages to be imported.

Sitemaps are preferred because they are intended to enumerate a site or section. Website mapping is useful when sitemaps are unavailable or too noisy, but the returned URL set must be reviewed for missing subsections before claiming final-product coverage. For broad bots, compare mapped URLs against navigation, docs indexes, search pages, or a manual crawl and add missing URLs before handoff.

When the bot covers multiple distinct products, product lines, editions, or major versions, define source tags before creating sources. Create `retrieverTags` on the bot first, then pass the matching `tags` array on each source create. If sources already exist, apply or repair tags later with `set_source_tags`.

## Common Create Body

Stable fields:

- `type`: required.
- `title`: required for source types whose UI requires it, especially document sources. For URL lists, websites, and sitemaps it is a dashboard label; indexed page titles still come from the pages.
- `url`: required for `url`, `sitemap`, `youtube`, and `rss`; also required as the root URL for mapped `website` sources.
- `urls`: explicit URL list for `urls` and mapped `website` sources. For URL-list sources, these are the only pages indexed; linked pages are not crawled.
- `file`: pending upload path from `create_source_upload_url`.
- `fileDir`: pending batch upload directory ending in `/`.
- `faqs`: required for `qa`, as `[{ "question": "...", "answer": "..." }]`.
- `scheduleInterval`: `daily`, `weekly`, `monthly`, or `none` depending on plan and source type.
- `tags`: source tag keys matching bot `retrieverTags`.
- `processImages`: only for source types that support image extraction.
- `crawlerJS`: restricted; do not rely on it unless advertised schema/readback shows access.

For important website, docs, support, pricing, changelog, and product sources, use monthly auto-refresh when the source type supports scheduling unless the user requests another cadence.

## Source Type Matrix

| Source kind | Types | Add flow |
| --- | --- | --- |
| Single public page | `url` | Create with `type`, `title`, `url`, optional `tags`, and monthly `scheduleInterval` for important pages. |
| Curated URL list | `urls` | Create with `type: "urls"`, `urls: [...]`, optional dashboard `title`, `tags`, and monthly refresh when supported. Use only after enumerating every applicable URL yourself; URL lists do not crawl linked pages. |
| Mapped website section | `website` | Use `map_website_urls` to discover candidate URLs, select all applicable scoped URLs, then create with `type: "website"`, root `url`, selected `urls`, tags, and monthly refresh. The map result is usually incomplete for deep docs/KB/product pages; validate it against site navigation or manual crawl output before treating it as final coverage. If the named tool rejects `website`, fall back to `type: "urls"` only after preserving the full selected URL set and record the catalog mismatch. |
| Sitemap crawl | `sitemap` | Create with `type`, sitemap `url`, optional `title`, `tags`, and monthly refresh. Prefer full sitemaps or targeted sub-sitemaps for final-product coverage; never claim final readiness while a critical sitemap is indexing or zero-chunk. |
| RSS/changelog | `rss` | Create with `type`, `url`, `title`, tags, and monthly refresh when supported. Good for changelogs, release notes, and feature announcements. Verify nonzero chunks. |
| WordPress | `wp` | Search live schema. Treat as file-backed or connector-backed depending on the current catalog; when auth/site selection is required, load [sources/connectors.md](sources/connectors.md). |
| YouTube | `youtube` | Create with `type`, watch/live/playlist `url`, optional `title`, tags, and schedule only for playlists where supported. Channel URLs are rejected. |
| Documents/media/spreadsheets | `document`, `media`, `csv` | For `document`, load [sources/document-uploads.md](sources/document-uploads.md) before requesting upload URLs or creating file/fileDir sources. For other file-backed types, inspect the advertised schema first. MCP cannot upload bytes. |
| Manual Q&A | `qa` | Create with `type: "qa"`, `title`, and `faqs`. A later create may merge into the existing Q&A source and queue reingest. |
| Truto cloud connectors | `notion`, `confluence`, `zendesk`, `google_docs`, `sharepoint`, `github`, `slack`, `s3`, `gcs`, and similar connector types | Usually require dashboard OAuth and item selection. Load [sources/connectors.md](sources/connectors.md) before configuring or handing off. |
| Helpdesk importers | `freescout`, `teamworkdesk`, and similar support-history types | Use connector-specific fields from the advertised tool schema, such as FreeScout URL/key/mailbox/months or Teamwork Desk host/key/inbox/months. Treat secrets as out-of-band and do not print them. Prefer native Help Scout integration for Help Scout workflows. |

## Conditional Detail References

Load these only when that source category is actually in scope:

- [sources/document-uploads.md](sources/document-uploads.md): Single-file and multi-file document upload details, supported file types, limits, and upload verification.
- [sources/connectors.md](sources/connectors.md): Truto/cloud connector OAuth, dashboard selection handoff, and connector verification.

## Verification

After adding any source:

- List sources and read each important source detail.
- Verify queued status, expected URL/file fields, warnings, tags, and refresh schedule.
- Verify source tag counts.
- For website sources, verify that the selected `urls` are broad enough for the promised scope. Mapping output that contains only top-level pages is smoke-test coverage unless the bot is intentionally narrow.
- For URL-list sources, verify `indexedUrls` matches the full intended URL set; a one-URL list is one page, not a crawl.
- Retry or replace failed/zero-content critical sources.
- Do not poll waiting for indexing. Configure the rest of the bot, then do one final source status check before handoff.
- Do not use broad indexing sources as ready evidence. If they are still indexing at handoff, tell the user answers for those areas may be incomplete until indexing finishes.
- For uploaded or connector sources, note any dashboard-only step that remains.
