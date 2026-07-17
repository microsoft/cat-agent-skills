---
name: Commenting Content
description: Comments Word or PowerPoint files with Comments.
agentDescription: "Analyzes a .docx or .pptx file, researches the topic using internal documents, emails, Microsoft Teams messages, and web sources, then adds native comments throughout the file authored by \"Copilot Studio AI\" — without modifying the original content."
platforms: [Cowork, Copilot Studio]
tags: [documents, productivity]
author: AndrewHessMSFT
authorUrl: "https://github.com/AndrewHessMSFT"
authorGithub: AndrewHessMSFT
version: 1.0.0
createdAt: 2026-07-08
updatedAt: 2026-07-08
bundle: bundles/commenting-content.zip
---
# Comment Content

When this skill is activated:

1. Check the file extension of the attached document.
   - If `.docx` → follow the instructions in `REFERENCE-DOCX.md`
   - If `.pptx` → follow the instructions in `REFERENCE-PPTX.md`
   - If any other format → ask the user to convert to `.docx` or `.pptx` first.
2. Execute the full commenting workflow defined in the appropriate reference file.
3. Return the updated file with native comments embedded and a short chat summary of findings.

## Guidelines

- Never modify the original document content — add comments only.
- Set the comment author to `Copilot Studio AI` on every comment added.
- Research using any available sources: internal documents, emails, Microsoft Teams messages, approved knowledge sources, and web research tools.
- Only comment where it genuinely helps — do not comment on every sentence.
- The chat summary must include: comment count, main research findings, and top 1–3 priority issues for the author to review.

## Reference Files

- [`REFERENCE-DOCX.md`](./REFERENCE-DOCX.md) — Word document commenting instructions
- [`REFERENCE-PPTX.md`](./REFERENCE-PPTX.md) — PowerPoint presentation commenting instructions

## Examples

**Example 1: Word document**
- User request: "Add research comments to this report." (attaches report.docx)
- Expected behavior: Detect .docx, follow REFERENCE-DOCX.md, return commented .docx with summary.

**Example 2: PowerPoint presentation**
- User request: "Review this deck and add comments." (attaches deck.pptx)
- Expected behavior: Detect .pptx, follow REFERENCE-PPTX.md, return commented .pptx with summary.

## Notes

- If multiple files are attached, process them one at a time and produce a separate summary for each.
- If the file type is ambiguous, ask the user to confirm before proceeding.
