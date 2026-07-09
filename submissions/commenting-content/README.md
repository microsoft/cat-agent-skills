# commenting-content Skill

Analyzes a `.docx` or `.pptx` file, researches its topic using available sources, and injects native comments authored by **Copilot Studio AI** — without modifying the original content.

---

## What It Does

1. Detects whether the attached file is `.docx` or `.pptx`
2. Analyzes the content to find slides/paragraphs that need commentary
3. Researches the topic using internal docs, emails, Teams messages, and web sources
4. Injects native comments (Word bubble comments / PowerPoint comments) into the file
5. Returns the commented file and a chat summary of findings

---

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Skill entry point — routing logic and top-level guidelines |
| `REFERENCE-DOCX.md` | Full workflow + instructions for `.docx` files |
| `REFERENCE-PPTX.md` | Full workflow + instructions for `.pptx` files |
| `scripts/inject-comments-docx.py` | Python injection engine for Word documents |
| `scripts/inject-comments-pptx.py` | Python injection engine for PowerPoint presentations |

---

## Injection Scripts

Both scripts are driven by `sys.argv` and a JSON comments file — no hardcoded filenames or comment text.

### `scripts/inject-comments-docx.py`

```bash
python scripts/inject-comments-docx.py <input.docx> <output.docx> <comments.json>
```

**`comments.json` format:**
```json
[
  {
    "id": 0,
    "search_phrase": "verbatim phrase from the target paragraph",
    "paragraphs": ["Comment line 1", "Comment line 2"]
  }
]
```

- `search_phrase` must be copied **verbatim from `word/document.xml`** — curly quotes, em dashes, etc. must match exactly or the comment will silently fail to anchor.
- Requires `lxml` (`pip install lxml`)

---

### `scripts/inject-comments-pptx.py`

```bash
python scripts/inject-comments-pptx.py <input.pptx> <output.pptx> <comments.json>
```

**`comments.json` format:**
```json
[
  {
    "slide": 1,
    "idx": 1,
    "text": "Comment text here",
    "x": 1270,
    "y": 1270
  }
]
```

- `slide` is 1-based
- `idx` must be unique per slide
- `x` / `y` are EMU positions on the slide (`1270` is a safe top-left default)
- Multiple comments on the same slide are grouped into a single comment file for that slide

---

## Sandbox Execution Notes

See [`REFERENCE-PPTX.md`](./REFERENCE-PPTX.md#sandbox-execution-tips) for the confirmed working sandbox pattern.

**Quick summary:**
- Remove any pre-existing read-only output file at `/app/created/` before writing
- Write the script to `/app/workspace/`, then run via `python3 -c "exec(open('/app/workspace/script.py').read())"` inside the double-nested `sandbox-exec → bash → sandbox-exec → python3 -c` pattern
- Only write final output to `/app/created/` — `/tmp/` is not writable from Python in the sandbox

---

## Comment Guidelines

- **Never modify original content** — comments only
- **Author:** always `Copilot Studio AI`
- Use 🐛 for context, citations, definitions, and improvements
- Use 🧹 for inaccuracies, ambiguities, contradictions, and missing info
- Only comment where it genuinely helps — not every sentence/slide
- Run the injection script **once** from the original input file — never re-run against a previously produced output
