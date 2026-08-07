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

### 1. Ingest — `scripts/b64_to_pptx.py`

Decodes the connector's base64 (ASCII, corruption-proof in transit) to bytes,
writes them with a **binary** handle, and proves the result is a readable OOXML
package before anything else runs.


### 2. Merge — `scripts/pptx_merge.py`

- writes `[Content_Types].xml` and all `.rels` in the **default (unprefixed)**
  OPC namespace (the prefixed form is the classic "can't read this file" cause);
- gives every `<p:sldMasterId>` its required `id`, drawing master and layout IDs
  from one shared counter so they are globally unique together;
- normalizes absolute OPC targets (e.g. `/ppt/charts/chart1.xml`) to relative
  paths;
- copies media, charts, and embeddings with a source-index prefix so identical
  filenames across decks can't collide;
- re-points slide → layout → master → theme chains and carries speaker notes;
- rebuilds `[Content_Types].xml` from what is actually on disk.

### 3. Validate — `scripts/verify_pptx.py`

The "does it actually open" gate. Structural checks **plus** a real LibreOffice
render — a structural pass alone can still leave a file PowerPoint won't open.

Checks ZIP integrity, default-namespace `[Content_Types].xml`, no absolute
internal `.rels` targets, present `sldMasterId` IDs, globally-unique master/layout
IDs, and a successful render. Exit `0` only when every enabled check passes. If
LibreOffice is absent, the render check is skipped and clearly flagged rather than
claimed as a pass.

### 4. Export — `scripts/pptx_to_b64.py`

Encodes the verified file back to base64 for the return trip, refusing to export
anything that isn't a valid PPTX and verifying a decode round-trip.

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
