# PPTX Merger

A four-stage, corruption-safe pipeline that merges two or more base64-delivered
PowerPoint decks into a single `.pptx` that PowerPoint opens with no repair or
"can't read" error. Built for the Copilot Studio sandbox flow where decks arrive
as base64 from a SharePoint connector, are merged inside the sandbox, and handed
back out.

## The pipeline

```
base64 in ──▶ 1. ingest ──▶ 2. merge ──▶ 3. validate ──▶ 4. export ──▶ base64 out
              (verify)       (build)       (render gate)     (encode)
```

## Requirements

- **`lxml`** — merge and validate steps
  (`pip install lxml --break-system-packages` if not already in the sandbox).
- **LibreOffice (`soffice`)** — the render gate in step 3. If unavailable,
  validation runs structural-only and says so.
- Ingest and export use the Python standard library only.
- No network calls; the skill never uploads or downloads anything itself.

## Files

```
SKILL.md                    # agent-facing skill definition (frontmatter + instructions)
scripts/b64_to_pptx.py      # 1. ingest — base64 → verified .pptx
scripts/pptx_merge.py       # 2. merge  → single .pptx
scripts/verify_pptx.py      # 3. validate — structural + real render
scripts/pptx_to_b64.py      # 4. export — verified .pptx → base64
```

## Testing

Verified end to end on two multi-master sample decks: the full ingest → merge →
validate → export chain passes, the delivered file renders (6 pages), and the
exported base64 begins with `UEsD`. The ingest gate was tested against the exact
`U+FFFD` corruption pattern and rejects it rather than producing a broken deck.

## License

Shared under the CAT Agent Skills repository's MIT license.
