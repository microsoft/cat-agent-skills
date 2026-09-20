# Copilot Studio MCP Readiness

Paste an MCP server's tool definitions and find out what Copilot Studio will do
with them before you spend an afternoon on the wizard. The checks come from what
Microsoft documents, not from folklore, and each finding cites the article it
came from.

## The one it exists for

A tool with a `$ref` anywhere in its input or output schema is filtered out of
the tool list. No error, no warning, the tool is just not there. That is
documented behavior on the standard harness, and it is very hard to guess from
the outside. Four more schema shapes behave in their own surprising ways:

- `"type": ["string", "null"]` truncates the input schema.
- `exclusiveMinimum` as an integer throws a `System.FormatException`.
- `enum` inputs are read as plain strings, so the constraint is not enforced.
- SSE is gone since August 2025, so a server that only speaks it cannot connect.

## What you get back

A table of Check, Harness, Verdict, Evidence and Fix, then the blockers on their
own, then an ordered list of what to change on the server. Verdicts are BLOCKER,
FIX, WATCH, PASS or UNKNOWN, and UNKNOWN says what it would need to see.

Checks cover transport, supported primitives, tool input schemas, tool
descriptions as the routing signal, orchestration fit, authentication,
per-conversation footprint, and connector data policy.

## Harness scope

Microsoft documents MCP for two Copilot Studio harnesses and their constraints
differ, so the skill asks which one you are on before it reports anything.

- **Standard harness**: MCP runs over Power Platform connectors. The tool schema
  issues and the data policy behavior live here.
- **GitHub Copilot harness** (preview): MCP is added from the Tools dialog. The
  per-conversation footprint limits live here.

The Copilot chat harness is out of scope, because Microsoft does not document
MCP on it. The skill says so rather than guessing.

## Good to know

- It reviews the artifact you give it. A README about the server is not evidence
  about its schemas, and the skill will ask for the real thing.
- It will not state a limit Microsoft has not published. The concurrent server
  cap has no published number, so you get the behavior and the citation instead
  of an invented figure.
- It never connects the server or touches your tenant.
- Pair it with **Copilot Studio Topic Blueprint** when you are designing the
  agent that will consume the server.
