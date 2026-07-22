# Knowledge Corpus Curator

Review the files used by an AI knowledge source for duplication, redundancy,
staleness, overlap, and potentially conflicting guidance. A cleaner,
better-governed knowledge corpus can improve grounded response quality, reduce
retrieval noise and response latency, and make content easier to maintain.

The skill analyzes uploaded copies without changing the source files. It
combines all uploaded batches into one corpus and returns an Excel review
backlog, an HTML summary, JSON results, and a batch manifest.

The Excel backlog and HTML report include a shared UTC creation timestamp in
their filenames, such as
`knowledge-corpus-curation-backlog-2026-07-22-142530Z.xlsx`, so repeated runs do
not overwrite earlier reports.

The Excel backlog consistently contains four tabs: `Review Backlog`, `Summary`,
`Document Inventory`, and `Curation Settings`.

## Before you start

- Download the SharePoint library or folders you want reviewed.
- Include only files you are authorized to process.
- Optionally add the corresponding SharePoint site or library as agent knowledge
  to help validate high-risk findings.

Agent knowledge is optional. The uploaded files remain the authoritative
analysis corpus. This workflow does not require SharePoint connector actions or
a SharePoint MCP server.

## What SharePoint knowledge enables

Adding the corresponding SharePoint site, library, or document location as an
agent knowledge source gives the skill an additional validation layer alongside
the uploaded files. It can:

- Check whether current SharePoint passages support or clarify high-risk
  duplicate and conflict findings.
- Identify audience, region, effective-date, or scope differences that may
  explain an apparent conflict.
- Find related or potentially authoritative documents that were not included in
  the uploaded corpus.
- Flag relevant SharePoint documents as `Not included in uploaded corpus` for a
  future review batch.

SharePoint knowledge does not replace the uploaded source files. Retrieved
knowledge passages are partial chunks, so they cannot prove whole-document
duplication, a complete-document conflict, or exhaustive library coverage. They
also do not reliably provide original owners, URLs, approval status, or modified
dates; supply the optional metadata manifest when those fields matter.

## Prepare the files

Package the export as one or more independent ZIP files while preserving the
SharePoint folder structure when possible.

- Each uploaded ZIP can be up to **50 MB**.
- The combined size of all files uploaded in one chat session can be up to
  **200 MB**.
- Target **45 MB or less per ZIP** to leave practical headroom.
- Use logical batches such as business area, policy family, document type, or
  top-level SharePoint folder.
- Keep each document in only one batch.
- Do not use split archives such as `.zip.001`; every ZIP must open independently.

If the intended corpus exceeds 200 MB, reduce the scope or analyze separate
corpora in separate chat sessions. Results from separate sessions are not
automatically combined, so cross-session duplicate, similarity, and conflict
coverage is incomplete.

## How to use it

1. Add the skill to your Copilot Studio agent.
2. Attach one or more ZIP files. Multiple ZIPs can be attached to the same
   message, and additional batches can be sent in later messages in the same
   conversation. Each ZIP can be up to 50 MB, provided the combined size of all
   files attached in the chat session remains under 200 MB.
3. If the agent asks whether more files are coming, confirm that the upload is
   complete or attach another batch. No specific confirmation phrase is
   required.
4. The agent stages all confirmed uploads together, analyzes every uploaded file, validates
   the highest-risk findings, and returns the report files.

Final-batch confirmation is the only required intake question. The skill does
not ask whether the upload is a whole library or subset, and it does not filter
drafts, archives, or historical versions. Every file in the confirmed upload is
included. Staleness uses the default 365-day threshold unless you already
requested another value.

## What it finds

- Exact and normalized-text duplicates
- Near-duplicates that may drift over time
- Related or overlapping content
- Potentially conflicting guidance with paired evidence
- Stale-content candidates
- Unsupported files and extraction gaps
- Relevant knowledge-source files missing from the uploaded corpus

Potential conflicts and duplicate findings include the related filenames,
locations, excerpts, and PDF page numbers where available. Recommendations are
review actions only; the skill never deletes, moves, renames, publishes,
archives, or overwrites source content.

Confidence values are deterministic numeric detection scores where available.
Blank confidence means the analyzer did not produce a score; it never means a
finding was human validated.

The backlog is always ordered by priority: `Critical`, `High`, `Medium`, then
`Low`, so the most urgent review items appear first in every output format.

Columns remain consistent across runs. The Excel backlog retains primary and
related paths for traceability, while the HTML report omits those path columns
for readability. The report title includes its UTC creation date and time, and
the source ZIP filename or filenames appear directly below the title.

## Example outputs

### HTML curation report

![Knowledge Corpus Curator HTML report showing summary metrics and the priority backlog](https://raw.githubusercontent.com/microsoft/cat-agent-skills/main/submissions/knowledge-corpus-curator/assets/example-outputs/knowledge-corpus-curation-report.png)

### Excel review backlog

![Knowledge Corpus Curator Excel review backlog showing prioritized findings and document evidence](https://raw.githubusercontent.com/microsoft/cat-agent-skills/main/submissions/knowledge-corpus-curator/assets/example-outputs/knowledge-corpus-curation-backlog.png)

## Good to know

- Upload all batches in one conversation so comparisons work across batch
  boundaries.
- Files from an earlier conversation should not be assumed to remain available.
- SharePoint downloads may replace original modified dates. Supply the optional
  metadata JSON described by the skill when accurate freshness dates, owners,
  URLs, or approval status matter.
- Large corpora can exceed the configured pairwise comparison threshold. Exact
  duplicate detection remains corpus-wide, but semantic comparisons may be
  limited and will be disclosed in the report.
- If the runtime does not include the Excel dependency, the skill still returns
  HTML and JSON, and the JSON file contains the complete backlog.
