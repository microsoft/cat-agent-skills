# Knowledge Library Curator - Upload

Review an exported SharePoint knowledge library for duplicate, stale,
overlapping, or potentially conflicting content without changing the source
files. The skill combines all uploaded batches into one corpus and returns an
Excel review backlog, an HTML summary, JSON results, and a batch manifest.

## Before you start

- Download the SharePoint library or folders you want reviewed.
- Include only files you are authorized to process.
- Optionally add the corresponding SharePoint site or library as agent knowledge
  to help validate high-risk findings.

Agent knowledge is optional. The uploaded files remain the authoritative
analysis corpus.

## Prepare the files

Package the export as one or more independent ZIP files while preserving the
SharePoint folder structure when possible.

- Copilot Studio currently allows chat file uploads up to **200 MB per file**.
- Target **190 MB or less per ZIP** to leave practical headroom.
- Use logical batches such as business area, policy family, document type, or
  top-level SharePoint folder.
- Keep each document in only one batch.
- Do not use split archives such as `.zip.001`; every ZIP must open independently.

## How to use it

1. Add the skill to your Copilot Studio agent.
2. Upload every ZIP in the same active conversation.
3. After the final upload, say:

   > That is the final batch. Analyze these now.

4. The agent stages all batches together, analyzes the combined corpus, validates
   the highest-risk findings, and returns the report files.

Confirming the final batch starts the analysis. The agent does not ask a second,
redundant question about whether the upload represents the whole SharePoint
library. Unless you explicitly confirm whole-library coverage, the report
conservatively states that it is **Complete for uploaded corpus**.

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
