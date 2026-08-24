# HOL Guard

HOL Guard protects local AI harnesses before tools run. This gallery skill teaches an agent to use the real `hol-guard` runtime and the separate `plugin-scanner` verifier rather than reimplementing security checks in prompts.

It covers installing HOL Guard, enabling Guard-owned protection for supported harnesses, reviewing approvals and receipts, and verifying agent plugins, skills, MCP servers, and marketplace packages.

```bash
pipx install hol-guard
hol-guard status
hol-guard detect --json
```

Protect a supported harness through Guard itself:

```bash
hol-guard bootstrap
hol-guard install <harness>
hol-guard run <harness> --dry-run
hol-guard run <harness>
hol-guard status
```

For package verification, install the scanner separately:

```bash
pipx install plugin-scanner
plugin-scanner lint .
plugin-scanner verify .
```

Project: https://hol.org/guard

Source: https://github.com/hashgraph-online/hol-guard
