# Document Upload Sources

Read this only when creating or validating `type: "document"` sources.

Document sources require `title` and either `file` for a single uploaded file or `fileDir` for a multi-file batch. Document sources do not auto-refresh; when the files change, reupload or reingest as applicable. `processImages` is optional only when the team plan and source type allow image extraction.

## Supported File Types

Supported document extensions:

```text
txt, docx, doc, pptx, ppt, pptm, eml, html, pdf, zip, md, csv, tsv,
xlsx, xls, xlsb, xlsm, xml, png, jpeg, jpg, gif, webp, heic, heif, srt
```

Current limits and safety rules:

- Max files per document source: 10,000.
- Max size per uploaded file: 2 GB.
- Temporary uploads live under `user/{userId}/team/{teamId}/bot/{botId}/` and are purged after 24 hours.
- `create_source_upload_url` returns a 30-minute write-only Google Cloud Storage signed URL plus the pending `file` path.
- Upload bytes outside Admin MCP with HTTP `PUT` to the signed `url` and `Content-Type: application/octet-stream`; never print signed URLs in final user-facing output.
- The source create route verifies pending upload path ownership, extension, file count, file size, and existence before moving files into the source.
- `.zip` support is plan-gated. Verify the current plan behavior and source readback before promising zip ingestion.

## Single-File Source

1. Call `create_source_upload_url` with `fileName`, for example `installation-guide.pdf`.
2. Upload the bytes to the returned signed `url` outside MCP.
3. Create the source with the returned `file` path:

```json
{
  "type": "document",
  "title": "Installation Guide",
  "file": "user/user_123/team/team_123/bot/bot_123/installation-guide.pdf",
  "tags": ["product"]
}
```

Single-file document sources store the exact file path. Dashboard title patching may be rejected for single-file document sources, so choose the final title during create or replace the source if the label must change.

## Multi-File Source

1. Use one shared batch folder under the pending upload prefix. Dashboard-generated folders use this shape:
   `user/{userId}/team/{teamId}/bot/{botId}/upload_{timestamp}_{id}/`
2. For each file, request an upload URL with a `fileName` that lands inside that same `upload_{timestamp}_{id}/` folder, preserving any desired relative paths.
3. Upload each file's bytes to its returned signed `url` outside MCP.
4. Derive `fileDir` from a returned `file` by keeping the full prefix through `upload_{timestamp}_{id}/`. The server normalizes a missing trailing slash, but always send the slash.
5. Optionally draft a batch title from filenames with `draft_source_title`; review before using it.
6. Create the source with `fileDir`:

```json
{
  "type": "document",
  "title": "Policy Documents",
  "fileDir": "user/user_123/team/team_123/bot/bot_123/upload_1700000000_abc12/",
  "tags": ["policy"]
}
```

Multi-file `fileDir` must be an allowed pending upload batch directory and end in `/`. The route lists every pending file under that prefix and moves the whole batch into the source. Multi-file document sources can expose a `files` manifest and usually support dashboard label patching.

## Verification

- Read the source after create and confirm `type`, `title`, `status`, `file` or `files`, tags, page/file counts, chunks, and warnings.
- For batches, verify every expected file appears in the manifest or normalized source details.
- Confirm no unsupported extensions, zero-byte/missing files, over-limit files, or stale temporary paths were rejected.
- For image-heavy documents, verify whether `processImages` was accepted and whether extracted text/chunks exist.
- If the upload was dashboard-assisted, record the remaining dashboard-only step and re-read source status after the user completes it.
