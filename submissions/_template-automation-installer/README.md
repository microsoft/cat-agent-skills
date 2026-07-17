# Scout automation installer template

> **Heads up:** this README is contributor guidance for the template. If you keep
> a `README.md` in your own submission it **becomes the main content** on the
> gallery detail page — so replace this text with a human-facing overview of your
> automation, or delete the file to fall back to the auto-generated page.

Copy this folder to `submissions/<your-slug>/` to submit a **Scout automation
installer** — a `.zip` that installs an automation via an `INSTALL.md` (install
procedure + the automation prompt) plus one or more JSON config files the
automation consumes. Use this when the automation is set up by *following
instructions* (e.g. it calls `m_create_automation` and writes a personal config)
rather than shipped as a directly-importable schedule+steps `.json`.

See [`../vacation-urgent-forwarder/`](../vacation-urgent-forwarder) for a
complete working example.

## What to put here

```
submissions/<your-slug>/
├── metadata.json       # catalog sidecar (this file's sibling) — tweak or delete
│                       #  name/description; they fall back to the automation
└── <your-installer>.zip   # the installer package (add this yourself)
    ├── INSTALL.md      # required: install procedure + the automation prompt
    └── config.example.json   # required: one or more JSON config file(s)
```

The submission is auto-detected as an **automation installer** because the
single `.zip` payload contains an `INSTALL.md` and at least one JSON file (and no
root `SKILL.md` or `manifest.json`). Do **not** set `platforms` in
`metadata.json` — the importer forces `["Scout"]`. The exact `.zip` you submit is
what's offered for download and shipped verbatim.

## Required contents

Validation is intentionally minimal (`scripts/validate-automation.ts`):

- an **`INSTALL.md`** must be present and non-empty;
- at least **one JSON config file** (`*.json`, other than the `metadata.*`
  sidecar) must be present.

The JSON config files are **not** parsed or schema-validated — ship them however
your automation expects to read them. Because the `.zip` is published verbatim,
strip any personal paths or secrets first, and include only files the installing
agent needs.

## Validate locally

```bash
npm run check:submissions    # thorough validation, writes nothing
npm run import:submissions   # generate the installer page + published .zip
npm run build
```
