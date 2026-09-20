---
name: SharePoint File Creation
description: "Generate a requested file, enforce a safe pre-upload size gate, and upload it to SharePoint without streaming bytes through the model."
agentDescription: "Source/generate the requested file using whatever content rules apply to the use case, gate it against an evidence-based pre-upload size threshold using the filesystem API, and upload it to SharePoint via the Create file tool's confirmed /app/created/ path-reference mechanism — without ever streaming raw file bytes through the LLM. Use this skill whenever a request asks for a file to be produced and uploaded to SharePoint, whether or not the user specifies a path, filename, format, or content source."
platforms: [Copilot Studio]
tags: [sharepoint, files, upload, microsoft-365]
author: Lewis Baybutt
authorUrl: "https://github.com/lewisdoesdev"
authorGithub: lewisdoesdev
version: 1.0.1
createdAt: 2026-09-14
updatedAt: 2026-09-15
---
## Quick reference — the fixed sequence

1. Determine what content/format is being asked for and source it (Section 0).
2. Write the complete file under `/app/created/` only, with a descriptive unique name.
3. Re-measure the final file's size with the filesystem API. Proceed only if
   `0 < size_bytes < 4,000,000`; otherwise stop and offer options.
4. Call Create file with the `/app/created/<name>` path bound directly as the content input.
   Never read bytes into the model to populate it or target another directory.
5. Report: content source, destination, measured size, and upload result.

Treat steps 2–5 as fixed; only step 1 is meant to flex per use case.

## 0. Determine and source the content

Apply any configured content-generation rules first, including required templates,
knowledge sources, data sources, report structures, schemas, or style guides.

When no more specific rules are configured:
- Identify the requested file format and use the appropriate runtime library. Do not default
  to plain text unless plain text is requested.
- Ground the content in the user's request, available retrieval/knowledge tools, or prior
  conversation context.
- If a named source cannot be located, or no source can be identified, ask rather than
  fabricating content.

Produce a complete, correct file before continuing.

## 1. Generate the file in /app/created/ only

Write the complete file beneath `/app/created/` using a SharePoint-safe, sanitized
basename-only, collision-resistant filename. Retain `[A-Za-z0-9_-]` in the stem, replace
other runs with `_`, trim separators, and preserve one valid extension. Reject path
separators, `..`, and control characters; resolve the candidate path and verify it remains
under `/app/created/` before writing or uploading.

Use `/app/created/` because it is the confirmed path-reference location for Create file.
Other paths may be uploaded as literal path text instead of file content, causing silent
corruption.

Keep bytes inside the runtime: never print, preview, or return generated content through the
model. Track the validated path, filename, and byte count internally for upload, but do not
expose the sandbox path in normal user-facing responses.

## 2. Measure and gate the size — always on the final written file

After the file is fully written and closed, measure it with the runtime filesystem API
(`os.path.getsize`, `os.stat().st_size`, or equivalent). Never estimate from text length,
row counts, token counts, or a measurement taken before the final write.

Proceed only when `0 < size_bytes < 4,000,000`. This conservative gate addresses the current
inline connector/tool upload boundary; it is not a SharePoint file-size limit or a platform
guarantee.

If the file is empty, unreadable, or at least 4,000,000 bytes, do not call Create file.
Report the measured size and offer to reduce the content or split it into multiple files.
Do not truncate, regenerate, or split automatically without the user's approval.

## 3. Hand the reference to SharePoint Create file

Use the configured Create file tool's existing input schema. Site and folder come from
whatever is already fixed/configured for this tool; do not ask the user to restate config
that is pre-set, only ask if the destination is genuinely undetermined.

Bind the validated `/app/created/` path as the tool's content input directly (e.g. the file
input value is the absolute `/app/created/<name>` path). Do not wrap it in JSON, do not
base64-encode it, do not read it into the model to populate the argument — the runtime/tool
resolves that path to real bytes server-side. This is the confirmed mechanism, not a
hypothesis: verified across two connectors, two sessions, and re-verified with byte-for-byte
hash matches on 1 MB and 2 MB files.

**Authorization model:** when the user's original request already asks for both generation
and upload in one instruction, treat that as authorization to proceed through the upload
without a second blocking confirmation round-trip. Still surface the destination, filename,
measured size, and content source in the final report for transparency. Fall back to an
explicit pre-upload confirmation step only when the request is ambiguous about whether upload
was actually wanted, the destination is not already fixed/configured, or the content touches
anything sensitive.

## 4. Report

State clearly: what was generated (type and content source), the destination in SharePoint
(site/library/folder path or URL and filename), the measured size, and the upload result.
Never claim an upload succeeded without tool evidence.

**Do not surface the internal sandbox path** (e.g. `/app/created/<name>`) in a normal
user-facing report — it is a runtime implementation detail, not something a user asking to
"generate and upload a file" needs or expects to see. Refer to the file by its name only,
plus where it landed in SharePoint. Only include the raw sandbox path when the user is
explicitly debugging or testing the skill itself, and say so if asked directly.

## 5. Failure handling

- Permission/DLP/authentication/unsupported-operation errors: stop and report; these are not
  sizing issues, so do not reinterpret them as such.
- Size-boundary errors even under the 4,000,000-byte gate: stop and report the exact error
  text and byte count. Treat this as evidence that the threshold may need tightening; do not
  retry with a slightly smaller guess. Tell the user to contact the agent owner to report the
  limitation.
- Ambiguous or timeout outcomes: report the upload result as unknown. Never blindly retry a
  write whose outcome is unclear.
