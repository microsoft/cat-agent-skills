# Upload and knowledge setup

## Copilot Studio setup

1. Optionally add the SharePoint site or document library as agent knowledge for
   validation.
2. Upload this skill to the agent.
3. Do not add SharePoint connector actions or the Work IQ SharePoint MCP server
   for this workflow.

Agent knowledge supports optional semantic validation. The files attached by the
user are the analysis corpus, and a metadata JSON export is the preferred source
for SharePoint metadata.

## Preparing a SharePoint export

The user should download the target library or folder from SharePoint and upload
it as one or more ZIP batches. Preserve the folder structure when possible and
keep every ZIP within the Copilot Studio chat file upload limit of 50 MB. The
combined size of all files uploaded in one chat session can be up to 200 MB.
Target 45 MB or less per ZIP to leave practical headroom.

For large libraries, create multiple logical ZIPs instead of one oversized
archive. Good batch boundaries include:

- Business area.
- Policy family.
- Document type.
- Top-level SharePoint folder.

Create independent `.zip` files that can each be opened on their own. Do not use
multi-volume archives such as `.zip.001`, because each uploaded batch must be
independently extractable. If a ZIP is larger than 50 MB, divide its contents
into additional logical batches.

If the intended corpus exceeds the 200 MB per-session total, reduce the scope or
analyze separate corpora in separate chat sessions. Separate-session results are
not automatically combined, so cross-session duplicate, near-duplicate,
related-content, and potential-conflict comparison is incomplete.

Keep each document in only one batch. Upload all batches in the same active
conversation and identify the final batch before analysis starts.

After each upload, the agent asks whether the complete intended corpus is now
present or whether another batch is coming. If another batch is coming, the
agent waits without extracting or analyzing files. Staging starts only after the
user explicitly confirms the final batch.

Confirmation that the corpus is complete is sufficient to start analysis. The
agent then asks three distinct setup questions, one at a time: whether the
corpus is the whole intended library or a subset; whether drafts, archives, and
historical versions are included; and which freshness threshold in days to use.
Upload completion and library coverage are different concepts, so the agent
briefly explains that distinction rather than treating the questions as
duplicates. It does not begin staging until all three answers are known.

## Cross-batch comparison

Cross-batch comparison works when every ZIP is extracted under one combined
input root and `curate_library.py` runs once over that root:

- Exact file and normalized-text hashes compare across every batch.
- Near-duplicate and related-content similarity compare across every batch.
- Potential-conflict analysis compares relevant documents across every batch.

If batches are analyzed in separate runs, their results are not automatically
merged and cross-batch comparison is incomplete. Files from a previous
conversation must not be assumed to remain available.

The configured `maximumPairwiseDocuments` limit still applies. Above that limit,
exact duplicate detection remains corpus-wide, while near-duplicate, related,
and conflict comparisons are skipped.

## Optional metadata

SharePoint downloads may not preserve the original owner, URL, approval state,
or modified date. A metadata JSON file can preserve fields supported by
`RESULT-SCHEMA.md`.

Without metadata, stale-content findings use the downloaded file's available
timestamp and must be treated as provisional.

## Runtime file handling

User uploads are available under `/app/uploads/`. Stage every ZIP and loose file
with:

```bash
python scripts/prepare_batches.py \
  --uploads /app/uploads \
  --output /app/workspace/knowledge-library \
  --manifest /app/created/knowledge-curation/batch-manifest.json
```

The script creates a unique directory per ZIP, preserves internal relative
paths, rejects traversal paths, symbolic links, encrypted entries, and excessive
compression ratios, and prevents cross-batch filename collisions.

The returned `batch-manifest.json` maps each combined-corpus path to its source
ZIP. Write all reports under `/app/created/knowledge-curation/`.

Pass the user's intake answers to `curate_library.py` using `--corpus-scope`,
`--content-scope`, and `--stale-after-days`. These values appear in the
`Curation Settings` worksheet.

## Validation model

Use complete uploaded files for:

- File hashing.
- Exact and normalized duplicate detection.
- Full-document extraction and comparison.
- Potential-conflict evidence.

Use agent knowledge for:

- Business terminology and topic discovery.
- Relevant passage retrieval.
- Audience, scope, and effective-date context.
- Finding related or authoritative documents that may be absent from the upload.

Always distinguish a complete uploaded file from a retrieved knowledge chunk.
Knowledge results cannot establish exhaustive coverage.

## Scope language

Use these labels:

- `Complete for uploaded corpus`: every supported uploaded file was processed.
- `Partial uploaded-corpus coverage`: one or more uploaded files failed,
  exceeded analysis limits, or were unsupported.
- `Not included in uploaded corpus`: knowledge identified a relevant SharePoint
  file that was not uploaded.

Do not use `Complete for SharePoint library` unless the user confirms the export
contained the entire requested library.

## Example request

> I added our HR policy library as agent knowledge and uploaded
> `HR-Policies-01.zip`, `HR-Policies-02.zip`, and `HR-Policies-03.zip`. That is
> the final batch. Combine them and review all uploaded files for duplicate,
> stale, and potentially conflicting guidance. Use knowledge to validate the
> highest-risk findings.
