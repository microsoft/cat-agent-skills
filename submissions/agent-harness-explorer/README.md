# Agent Harness Explorer

A reusable **Agent Skill** for the CAT Agent Skills gallery that helps makers
**discover, understand, document, and monitor** the capabilities of an agent
harness.

It answers questions like:

- What can this harness do?
- Which Python libraries are installed, and which should I use for a task?
- What tools and MCP servers are available?
- What changed since my last snapshot / baseline?

The skill **prefers runtime observation over assumptions** and clearly
distinguishes what it *observed* from what a platform is *believed* to support.

---

## How the skill is used

This is an Agent Skill: the agent loads `SKILL.md` and follows its workflow,
running the bundled Python scripts to observe the runtime. You normally trigger
it with natural-language requests. Under the hood it runs standard-library-only
Python scripts (PyYAML is used if present, otherwise a built-in fallback parses
the catalog), so **no install step is required**.

### Talk to the agent

Ask things like:

| You say | The skill does |
| --- | --- |
| "What can this harness do?" / "Inspect the harness." | Runs passive probes and summarizes runtime + capabilities. |
| "Which Python libraries are installed?" | Captures a snapshot and renders the category-grouped inventory. |
| "What should I use to create Word documents?" | Looks up the curated catalog, confirms the package is installed, links its docs. |
| "Capture a snapshot." / "Remember this." | Captures, compares to the last snapshot, stores a compact copy in memory. |
| "Save this as my baseline." | Designates the current snapshot as the baseline. |
| "Compare with my baseline." / "What changed since last week?" | Diffs two snapshots by stable capability ID. |
| "Export the latest snapshot." | Emits JSON + Markdown for durable/shared retention. |

### Safety at a glance

- **Passive probes run by default** (versions, installed packages, OS/temp-dir
  metadata).
- **Active-safe probes are opt-in** (`--active-safe`): create+delete a temp
  file, run one benign command, and a single HTTPS request to `pypi.org`.
- **Active-sensitive actions never run** unless you explicitly direct them
  (installs, arbitrary shell/network, reading unrelated files).
- Secrets and full environment values are never recorded. See
  [`references/safety-boundaries.md`](references/safety-boundaries.md).

---

## Running the scripts directly

You can also run the pipeline yourself from the `scripts/` folder. Requires
Python 3.8+ (developed on 3.13); no third-party dependencies.

```bash
cd scripts

# 1. Capture a snapshot (passive by default)
python capture_snapshot.py \
  --catalog ../references/python-library-catalog.yaml \
  --out snapshot.json

# Optional: include opt-in active-safe probes and agent-observed tools/MCP
python capture_snapshot.py --active-safe --tools observations.json --out snapshot.json

# 2. Render the report (HTML is the default output)
python generate_html_report.py snapshot.json --out report.html

# Optional: Markdown outputs, only when you specifically want Markdown
python generate_markdown_report.py snapshot.json --out report.md
python generate_library_inventory.py snapshot.json --out inventory.md

# 3. Compare two snapshots (JSON or Markdown)
python compare_snapshots.py old_snapshot.json snapshot.json --markdown --out diff.md

# 4. Archive a timestamped capture (json + md + html + index.md)
python archive_snapshot.py --out-dir ./snapshot-archive
#    reuse an existing snapshot, or limit formats:
python archive_snapshot.py --snapshot snapshot.json --out-dir ./snapshot-archive
python archive_snapshot.py --out-dir ./snapshot-archive --formats json,md

# Inspect the fingerprint / canonical form of any snapshot
python canonicalize_snapshot.py snapshot.json
```

Individual probes can be run standalone too:

```bash
python inspect_python.py               # runtime + installed packages
python inspect_runtime.py --active-safe # OS/filesystem/subprocess/network
python inspect_tools.py --input observations.json  # tools/skills/MCP
```

### Tool / MCP observations file

A plain Python process cannot see the agent's tools, skills, or MCP servers —
only the agent can. To include them, the agent writes an `observations.json`
and passes it via `--tools`:

```json
{
  "tools": ["view", "edit", "grep"],
  "skills": ["pdf", "xlsx"],
  "mcpServers": ["github-mcp-server", "playwright"],
  "mcpTools": [{ "server": "playwright", "tool": "browser_click" }]
}
```

Without it, tool visibility is recorded as `not-visible` (never `unsupported`),
and comparisons treat any absence from a skipped probe as `unverified`.

---

## What a snapshot contains

A normalized, machine-readable capture of the observable harness:

- Snapshot metadata (id, timestamp, skill/probe/catalog versions)
- Python runtime metadata
- Enriched Python library inventory (name, version, category, description, docs)
- Other capabilities (filesystem, network, subprocess, tools, skills, MCP)
- Probe metadata, warnings, summary counts
- A `sha256:` **fingerprint** over the volatile-field-stripped capability set —
  identical fingerprints mean nothing observable changed.

Schema: [`assets/snapshot.schema.json`](assets/snapshot.schema.json).
Worked example: [`assets/snapshot-example.json`](assets/snapshot-example.json).

---

## Folder layout

```
agent-harness-explorer/
├── SKILL.md            # agent trigger + workflow instructions
├── metadata.json       # gallery catalog sidecar
├── README.md           # this file
├── references/         # docs the agent reads on demand
│   ├── python-library-catalog.yaml   # curated, version-independent catalog
│   ├── probe-catalog.md              # probes + capability-ID scheme
│   ├── comparison-rules.md           # how diffs are classified
│   ├── safety-boundaries.md          # passive / active-safe / sensitive
│   ├── memory-snapshot-protocol.md   # memory-first persistence
│   └── snapshot-history/             # timestamped example captures + index
├── scripts/            # standard-library-only Python
│   ├── inspect_python.py
│   ├── inspect_runtime.py
│   ├── inspect_tools.py
│   ├── capture_snapshot.py
│   ├── canonicalize_snapshot.py
│   ├── compare_snapshots.py
│   ├── generate_markdown_report.py
│   ├── generate_library_inventory.py
│   ├── generate_html_report.py
│   └── archive_snapshot.py
└── assets/
    ├── snapshot.schema.json
    ├── comparison.schema.json
    ├── snapshot-example.json
    └── report-template.md
```

---

## Snapshots and memory

Agent memory is the **default, user-specific** snapshot store — it needs no
setup but may not be durable or shareable, so exporting JSON + Markdown is
encouraged for anything you want to keep or share. Retention, baseline handling,
and the compact record shape are documented in
[`references/memory-snapshot-protocol.md`](references/memory-snapshot-protocol.md).
Optional external stores (SharePoint, Dataverse, GitHub, Blob) are only offered
when a compatible persistence tool is visible, and are never required.

---

## Extending the skill

- **Add a Python library** to `references/python-library-catalog.yaml`
  (name, import_name, category, description, documentation_url, tags), keeping
  entries sorted by name.
- **Add a probe** by creating `scripts/inspect_<thing>.py` that exposes
  `run(...) -> envelope`, wiring it into `capture_snapshot.py`, and (if it adds
  a new capability-ID namespace) mapping that namespace in
  `compare_snapshots.py`. See
  [`references/probe-catalog.md`](references/probe-catalog.md).

Contributions to the gallery follow the repo's `CONTRIBUTING.md`: edit files in
this `submissions/<slug>/` folder and open a PR — CI validates the metadata and
generates the published page and download bundle.
