---
name: pptx-merger
description: >
  Use this skill whenever the task is to combine, concatenate, or merge two or
  more PowerPoint decks into one .pptx that opens with no repair or "can't read"
  error — especially when the source files arrive as base64 from a SharePoint
  connector or HTTP response. Triggers: "merge decks", "combine presentations",
  "append slides from", "join pptx files", "merge these QBR decks". It runs four
  ordered steps — ingest base64 to a verified file, merge, validate by real
  render, and export back to base64 for return/upload. Do NOT use it to build
  slides from scratch.
---

# PPTX Merger — corruption-safe deck merge for agent sandboxes

Combine PowerPoint decks into a single file that opens cleanly in PowerPoint.
The skill is built for the case where decks arrive as **base64** (e.g. from the
SharePoint *Get file content using path* connector) and must be merged inside a
sandbox and handed back out. It exists because the naive path corrupts files in
two places: binary bytes get destroyed when pushed through a text/UTF-8 codec,
and careless merging produces packages PowerPoint refuses to open. Each of the
four scripts does one job, verifies its own output, and fails loudly rather than
passing bad data forward.

## The pipeline

```
base64 in ──▶ 1. ingest ──▶ 2. merge ──▶ 3. validate ──▶ 4. export ──▶ base64 out
              (verify)       (build)       (render gate)     (encode)
```

Run the four scripts in order, in a shared working directory. Treat any non-zero
exit as a hard stop and report the reason — never deliver an unvalidated file.

### 1. Ingest — base64 → verified .pptx on disk

The connector's base64 is ASCII and survives any text pipeline. Corruption only
happens when the *binary* is decoded through a UTF-8 codec (every byte ≥ 0x80
becomes U+FFFD, inflating and destroying the ZIP). This step decodes the base64
to bytes and writes them with a **binary** handle, then proves the result is a
readable OOXML package before anything else runs.

```bash
python scripts/b64_to_pptx.py <base64_input> <output.pptx> [--expected-bytes N] [--json]
```

`<base64_input>` is a path to a file containing the base64 text **or** the literal
base64 string. Pass `--expected-bytes` with the connector-reported size for an
exact-size assertion. Run once per source deck:

```bash
python scripts/b64_to_pptx.py deck1.b64 in1.pptx --json
python scripts/b64_to_pptx.py deck2.b64 in2.pptx --json
```

Gates (any failure → non-zero exit): input must be clean ASCII base64 (rejects if
it already contains U+FFFD — meaning corruption happened upstream), strict base64
decode, binary write, optional exact-size check, and a final "is this a valid
PPTX ZIP" check. A correct base64 PPTX always begins with `UEsD` (the ZIP magic);
if the string starts with anything else the source is not clean base64.

### 2. Merge — combine verified decks

```bash
python scripts/pptx_merge.py output.pptx input1.pptx input2.pptx [input3.pptx ...]
```

First argument is the output path; the rest are inputs merged in order. It fixes
every defect that makes merged decks unopenable: `[Content_Types].xml` and all
`.rels` are written in the **default (unprefixed) OPC namespace** (a prefixed
`<ns0:Types>` is the classic "PowerPoint can't read this file" cause); every
`<p:sldMasterId>` gets its required `id`, with master and layout IDs drawn from
one shared counter so they are globally unique together; absolute OPC targets are
normalised to relative paths; media, charts, and embeddings are copied with a
source-index prefix so identical filenames across decks cannot collide; slide →
layout → master → theme chains are re-pointed; speaker notes are carried across;
and `[Content_Types].xml` is rebuilt from what is actually on disk.

### 3. Validate — the "does it actually open" gate

A structural check alone is not enough — it can pass a file PowerPoint still
won't open. This step runs the structural checks **and** performs a real
LibreOffice render. Nothing is delivered unless this passes.

```bash
python scripts/verify_pptx.py <file.pptx> [--json] [--no-render]
```

Checks: ZIP integrity; `[Content_Types].xml` present and in the default namespace
(a prefix is reported as an error); no `.rels` uses an absolute internal target;
every `sldMasterId` has an `id`; master/layout IDs are globally unique; and a real
render produces a non-empty PDF. Exit `0` only when every enabled check passes. If
LibreOffice is absent the render check is skipped and clearly flagged rather than
claimed as a pass.

### 4. Export — verified .pptx → base64 for the return trip

The merged file must leave the sandbox the same way inputs came in: as base64.

```bash
python scripts/pptx_to_b64.py <input.pptx> [--out file.txt] [--json]
```

Use `--out` to write the base64 to a file (recommended for large decks). It
refuses to export anything that is not a valid PPTX and verifies a decode
round-trip so a truncated encoding is caught here, not in the user's PowerPoint.

## Delivering the result (Copilot Studio)

Keep the out-of-the-box SharePoint tools as-is. The base64 from step 4 is what you
hand to your upload path. **Never read, print, chunk, or reconstruct the base64 in
the model** — pass it as a variable reference from export straight into the upload
action. The recommended upload is a Power Automate flow whose input is a
`contentBase64` string and whose *Create file* action sets File Content to
`base64ToBinary(triggerBody()?['contentBase64'])`, so the decode happens
server-side and the bytes never travel through the model by value. Return the
file's `webUrl` (and its `Length`, to compare against the exported byte count as a
final integrity check) and give the user the link.

## Suggested agent step order

1. Resolve each file and get its content as base64 (`$content` from *Get file
   content using path* is already base64 — use it verbatim, do not re-encode).
2. `b64_to_pptx.py` per deck → verified `inN.pptx`. If any returns `ok: false`,
   stop: the source is corrupt and merging cannot help.
3. `pptx_merge.py` → `merged.pptx`.
4. `verify_pptx.py merged.pptx` → must pass, or stop and report the errors.
5. `pptx_to_b64.py merged.pptx --out merged.b64`.
6. Upload via the flow (passing the base64 by reference) and return the link.

## Requirements

`lxml` for the merge and validate steps (`pip install lxml --break-system-packages`
if not already present in the sandbox). LibreOffice (`soffice`) for the render
gate in step 3 — if unavailable, validation runs structural-only and says so.
Ingest and export use the Python standard library only. No network calls; the
skill never uploads or downloads anything itself.
