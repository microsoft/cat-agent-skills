# Secrets Leak Guardrail

Before code, logs, or an exported file leave the conversation, this skill
scans for the credential shapes that show up by accident: an AWS key pasted
into a debugging session, a GitHub token left in a `.env` dump, a connection
string with a live password in it.

## How it works

`scripts/scan_secrets.py` does two passes: known credential formats by regex
(AWS, GitHub, GitLab, Slack, Google, JWTs, PEM keys, bearer tokens,
`password=` connection strings), plus a Shannon-entropy check on any
`SECRET`/`TOKEN`/`PASSWORD`-named assignment that doesn't match a known
format, catching the vendor-specific key formats the regex list doesn't know
about yet. Every finding is reported, never silently fixed. The agent asks
before stripping anything, since a docs example and a live credential can look
identical to a regex.

## Usage

```bash
python scripts/scan_secrets.py path/to/file-or-folder
python scripts/scan_secrets.py path/to/file --json
echo "some pasted text" | python scripts/scan_secrets.py -
```

No dependencies beyond the Python standard library.

## Limits

This is a pattern scanner, not a secrets-management tool. It won't catch a
credential format it doesn't know, and the entropy check is a heuristic that
can both miss short low-entropy passwords and flag legitimate random IDs. It
buys a last-look-before-sharing check, not a guarantee.

---

Skill by Tim Karlsson (╯°□°)╯︵ ┻━┻ Works 60% of the time, every time.
