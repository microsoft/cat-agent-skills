# Copilot API Plugin Readiness

Paste the OpenAPI file behind a declarative agent action, and the plugin
manifest if you have one, and find out what Microsoft 365 Copilot will do with
it before you provision anything. Every check comes from a Microsoft Learn
article, and each finding names the one it came from.

## The ones it exists for

The usual mistakes are all documented, just not in one place:

- An `operationId` like `get-items`. Function names must match
  `^[A-Za-z0-9_]+$`, so no function can ever bind to it.
- An object inside an object in a request body, or a `oneOf` anywhere. Both are
  on the unsupported list. Flatten the schema.
- An OAuth client credentials flow. Only authorization code, with or without
  PKCE, is supported.
- A missing `info.description`. It becomes the plugin description, which is
  what the model routes on.

## What you get back

A table of Check, Where, Verdict, Evidence and Fix, then the blockers on their
own, then one ordered list of changes to the OpenAPI file and the manifest.
Verdicts are BLOCKER, FIX, WATCH, PASS or UNKNOWN.

The skill ships `scripts/check_openapi.py`, a standard library Python checker
for the mechanical part: operation IDs, descriptions, unsupported schema shapes,
security schemes, function binding, confirmations and card actions. The agent
runs it when it can run code, then does the judgment checks itself.

```
python scripts/check_openapi.py openapi.yaml --manifest ai-plugin.json
```

## Good to know

- **Learn contradicts itself on one point, and the skill says so.** The API key
  article documents keys in a custom header or a query parameter. The known
  issues page lists exactly those as unsupported. You get a WATCH with both
  links, and the bearer token form as the safe option.
- A plain `$ref` is fine for API plugins. That rule belongs to Copilot Studio
  MCP tools, and the skill does not mix the two up.
- It covers API plugins only. Copilot Studio REST API tools, custom connectors
  and MCP plugins have their own rules. For MCP servers in Copilot Studio, use
  **Copilot Studio MCP Readiness**.
- A clean report is not a runtime test. It never calls your API, provisions the
  agent or touches your tenant.
