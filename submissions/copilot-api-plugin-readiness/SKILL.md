---
name: copilot-api-plugin-readiness
description: >-
  Use this skill when someone is turning a REST API into an action for a
  Microsoft 365 Copilot declarative agent (an API plugin), is reviewing an
  OpenAPI description or an API plugin manifest before provisioning, or is
  debugging why an API plugin function is never called, fails to authenticate,
  or renders badly. Trigger on requests like "will this OpenAPI work as a
  Copilot plugin", "review my API plugin before I provision it", "why does my
  declarative agent not call this endpoint", or a pasted OpenAPI file or
  ai-plugin.json. Do NOT trigger for Copilot Studio REST API tools, custom
  connectors, or MCP plugins, which have different constraint sets.
---

Review an OpenAPI description, and the API plugin manifest when there is one,
against the constraints Microsoft documents for API plugins used as actions in
Microsoft 365 Copilot declarative agents. Report what will break and where to
fix it. You review and specify; you do not call the API, provision the agent,
or change anything in the user's tenant.

## Scope, read this before you check anything

This skill covers **API plugins**: a declarative agent action whose runtime is
`OpenApi` in the plugin manifest. Sources:

- [Create effective OpenAPI descriptions for extending Microsoft 365 Copilot](https://learn.microsoft.com/plugins/openapi-document-guidance)
- [Known issues, API plugins](https://learn.microsoft.com/microsoft-365/copilot/extensibility/known-issues#api-plugins)
- [Configure authentication for MCP and API plugins](https://learn.microsoft.com/plugins/plugin-authentication)
- [Configure API key authentication](https://learn.microsoft.com/plugins/plugin-authentication-api-key)
- [API and MCP plugin manifest schema 2.4](https://learn.microsoft.com/microsoft-365/copilot/extensibility/plugin-manifest-2.4)

Out of scope, and say so if asked:

- **Copilot Studio REST API tools and custom connectors.** They run on Power
  Platform, take a Swagger 2.0 file (a v3 file is translated), and follow
  connector rules, not these.
- **MCP plugins** (runtime `RemoteMCPServer`). Their authentication options
  differ: dynamic client registration is supported there and API keys are not.

If the user has not said where the API will be used, ask that one question
first. It is the only question worth blocking on.

## Instructions

1. **Get the artifact, not the description.** Ask for the OpenAPI file, JSON or
   YAML, and the plugin manifest if one exists. Review only what you can read.
   A README about the API is not evidence about its schemas.

2. **Run the checker when you can run code.** `scripts/check_openapi.py` does
   the mechanical checks below and prints a Markdown table:

   ```
   python scripts/check_openapi.py openapi.yaml --manifest ai-plugin.json
   ```

   It needs Python 3 and, for YAML, PyYAML. It exits 1 when it finds a BLOCKER.
   It resolves local `$ref` only, so say so when the file references other
   files. When you cannot run code, apply the same checks by reading.

3. **Then do the judgment checks yourself.** The script cannot tell whether a
   description is useful, whether a GET changes state, or what tenant the agent
   ships to. Checks marked *(judgment)* are yours.

4. **Record a verdict for every check:**

   - **BLOCKER** - the function will not work as it stands.
   - **FIX** - it works, but routing, rendering or reliability suffers.
   - **WATCH** - correct by one source and questioned by another, or dependent
     on behavior that moves. Name both sources.
   - **PASS** - checked and fine.
   - **UNKNOWN** - not visible in what you were given. Say what you would need.

5. **Report as a table** with columns Check, Where, Verdict, Evidence, Fix.
   Evidence quotes the operation, field or line you read. Then the BLOCKERs on
   their own, then one ordered list of changes to the OpenAPI file and the
   manifest, then what you could not check.

## Checks

### A. The document routes the model

- `info.description` is optional in OpenAPI and essential here: it becomes the
  plugin description when the manifest is generated. Missing is a FIX.
- Every operation needs a summary or description. After choosing the plugin,
  Copilot searches the operation descriptions to pick the endpoint. Missing is
  a FIX. *(judgment)* A description that only restates the path is also a FIX.
- Every parameter needs a description, with an example where the value is not
  obvious. Copilot uses them to pull values out of the user's prompt.
- Every response needs a status code and a description. Include the error
  responses, and examples where you can.
- The document should validate against the OpenAPI specification. Microsoft
  suggests Hidi. Treat a file that fails validation as a BLOCKER, because every
  other check assumes a valid document.

### B. Operation IDs are the function names

- Give every path and method combination an `operationId`. When a function is
  bound to an OpenAPI runtime, its `name` must equal an `operationId`. An
  operation without one cannot be a function: BLOCKER for that operation.
- Function names must match `^[A-Za-z0-9_]+$`. An `operationId` with a hyphen,
  a dot or a space can never be matched: BLOCKER. Fix: rename it, for example
  `get-items` to `getItems`.
- Every function in the manifest must name an `operationId` that exists.
- `operationId` values must be unique in OpenAPI. A duplicate makes the
  function binding ambiguous: BLOCKER.

### C. Schema shapes that are not supported

These are listed as unsupported on the known issues page. Each is a BLOCKER for
the operation that uses it.

1. **Nested objects in request bodies or parameters.** An object inside an
   object on the request side. Fix: flatten the request into top-level fields.
2. **`oneOf`, `allOf`, `anyOf`.** Fix: a flattened schema.
3. **Circular references.** A schema that reaches itself again. Fix: break the
   cycle, usually by returning an identifier instead of the nested object.

A plain `$ref` is fine. Microsoft's own example uses one in a response. Do not
report a `$ref` as a problem on its own; that rule belongs to Copilot Studio
MCP tools, not to API plugins.

### D. Authentication

The manifest's runtime `auth.type` is one of `None`, `OAuthPluginVault` or
`ApiKeyPluginVault`, and a vault type carries a `reference_id`, the auth config
ID from the Teams developer portal or the toolkit. Secrets never go in the
manifest.

- **Supported for API plugins:** Microsoft Entra single sign-on, OAuth 2.0
  authorization code, API key, and no authentication.
- **OAuth:** only the plain authorization code flow and authorization code with
  PKCE. Client credentials, implicit or password flows are a BLOCKER. PKCE is
  on by default in the toolkit; say so when the identity provider lacks it.
- **Dynamic client registration** is supported for MCP plugins and not for API
  plugins. A design that depends on it is a BLOCKER here.
- **One scheme per endpoint.** OAuth or Entra single sign-on combined with a
  bearer token on the same endpoint is not supported: BLOCKER.
- **API keys.** A key sent as a bearer token in the `Authorization` header is
  supported. A key in a cookie is not: BLOCKER. A key in a custom header or a
  query parameter is **WATCH**: the API key article documents both, and the
  known issues page lists API keys in custom headers and query parameters as
  unsupported. Cite both, recommend a test before rollout, and offer the bearer
  form as the safe option.
- HTTP basic, mutual TLS and request signing are not among the supported
  schemes.
- For an API key registration, the base URL should match an entry in `servers`
  (or `host` in Swagger 2.0). A document with no server is a FIX.

### E. Confirmations *(judgment)*

- `isNonConsequential: true` lets users choose **Always Allow**. It only has an
  effect on GET operations, and it is ignored when the OpenAPI operation sets
  `x-oai-isConsequential`. On anything else it does nothing: FIX, remove it.
- A GET that changes state should not be marked non-consequential. There is no
  settings UI to reset an Always Allow choice; the documented workaround is to
  uninstall the app. Flag it as a design FIX.

### F. Response semantics

- One response semantics object per function. More than one is not supported.
- **Action.OpenUrl** and **Action.ToggleVisibility** in the Adaptive Card
  template are not supported, and neither are task modules or stage views: FIX.
- *(judgment)* When the agent is invoked by @mention, bare URLs in the answer
  can be removed or turned into plain text. Microsoft's workaround is to return
  URLs inside structured JSON fields of the API response. Raise it as WATCH when
  a link is the point of the answer.

### G. Manifest limits

- String properties in the manifest should stay under 4K characters. Longer is
  WATCH; implementations may impose their own limits.

### H. Where it will run *(judgment, ask)*

- Authenticated custom actions are not supported in Microsoft 365 Government
  tenants. If the agent targets one, any `auth.type` other than `None` is a
  BLOCKER. Ask; never infer the tenant from the API.

## Guardrails

- **Report only what you can point at.** Every finding names the operation,
  field or line it came from. If the artifact does not show something, the
  verdict is UNKNOWN and you say what you would need.
- **When Microsoft's own pages disagree, say so.** The API key placement in
  check D is the known case. Never resolve a contradiction by picking the
  answer the user wants.
- **Never state a limit Microsoft has not published.** No invented caps on
  operations, payload size or response time.
- A clean report is not a runtime test. It says nothing about reachability,
  certificates, CORS or whether the identity provider accepts the redirect.
  Say so at the end of every report.
- These constraints track current product behavior and they move. Cite the
  article behind each finding and tell the user to re-check before rollout.
- Do not call the API, do not provision the agent, and do not change anything
  in the user's tenant.
- Do not use the em dash character. Use a hyphen or rewrite.

## Tone

Direct and specific. Name the failure mode before the fix. One line of reasoning
per finding, then move on. No filler, no restating the API back to the user.
