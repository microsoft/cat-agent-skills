---
name: flow-json-to-azurefunction
description: This skill analyzes a Power Automate cloud flow definition provided as JSON and converts the flow logic into a deployable Python Azure Function.
---
The skill must:

1. Analyze the complete Power Automate JSON.
2. Understand the trigger, actions, variables, conditions, loops, expressions, dependencies, and connectors.
3. Map the Power Automate workflow to equivalent Python logic.
4. Generate a complete Python Azure Function using the Azure Functions Python v2 programming model.
5. Generate an analysis explaining how the Power Automate flow was converted.
6. Generate a PDF report containing the analysis and generated Azure Function code.
7. Generate a complete Azure Function deployment ZIP package.
8. Write the generated PDF and ZIP to `/app/created/` and return them as attachments in the same turn (not base64).

The generated Azure Function must implement the actual logic contained in the supplied Power Automate JSON. It must not generate a generic placeholder function.

---

# When to use this skill

Use this skill when:

* A user wants to migrate a Power Automate cloud flow to Azure Functions.
* A user provides an exported Power Automate workflow JSON.
* A user wants to convert Power Automate actions and expressions into Python.
* A user wants to replace complex Power Automate processing with Python code.
* A user wants a deployable Azure Function generated from an existing Power Automate flow.
* A user wants an analysis/report of the Power Automate to Azure Function conversion.
* A user wants a ready-to-deploy Azure Function ZIP package.

---

# Input

The primary input is a **Power Automate workflow definition JSON**.

The JSON can contain:

* `properties`
* `connectionReferences`
* `definition`
* `triggers`
* `actions`
* `runAfter`
* `parameters`
* `$authentication`
* `$connections`
* connector definitions
* Power Automate expressions
* Dataverse actions
* HTTP actions
* variables
* conditions
* loops
* scopes
* compose actions
* other Power Platform actions

The user may provide the JSON directly as text or as an uploaded file.

The complete JSON must be analyzed before generating the Azure Function.

Do not base the conversion only on a partial section of the JSON.

---

# Reference Azure Function Project

A sample Azure Functions Python v2 project is included in this repository as the structural reference for the generated deployment package. Use it as the authoritative template for the project layout, `host.json`, and `requirements.txt`.

Reference project location (relative to this skill folder):

```text
assets/
├── .funcignore
├── function_app.py
├── host.json
└── requirements.txt
```

The reference project contains:

* `function_app.py` — Azure Functions Python v2 model. It declares
  `app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)` and a sample
  `@app.route(route="hello")` HTTP handler. This placeholder handler must be
  **replaced** with the converted Power Automate implementation.
* `host.json` — v2 host configuration with Application Insights sampling and the
  Microsoft Azure Functions Extension Bundle `[4.*, 5.0.0)`.
* `requirements.txt` — baseline `azure-functions` dependency.
* `.funcignore` — standard ignore list (`.git*`, `.vscode`, `__pycache__`, `.venv`,
  `local.settings.json`, `tests`, `.pytest_cache`).

Preserve the reference project structure where applicable.

The generated implementation must replace the sample `hello` function logic with the converted Power Automate implementation while keeping the v2 `FunctionApp` app object and auth level from the reference.

If the reference project is not available, generate the standard Azure Functions Python v2 structure:

```text
flow2function_<sanitized_flow_name>.zip
├── .funcignore
├── function_app.py
├── host.json
└── requirements.txt
```

Do not add unrelated files.

---

# Processing Logic

## 1. Parse and normalize the Power Automate JSON

Identify the workflow definition under the appropriate JSON section, typically:

```text
properties.definition
```

Extract:

* workflow name if available
* trigger(s)
* actions
* action names
* action types
* action inputs
* action outputs
* `runAfter`
* variables
* connector references
* expressions
* nested actions

Ignore deployment metadata that is not required to reproduce the workflow behavior.

Do not expose authentication secrets or connection secrets in the generated output.

---

# 2. Analyze the trigger

Identify the Power Automate trigger.

For example:

```text
type: Request
kind: Button
```

must be interpreted as an HTTP-style trigger.

If the trigger defines an input schema, preserve that schema in the Azure Function.

For example, if the trigger accepts:

```json
{
  "text": "standard"
}
```

the generated Azure Function must read and validate `text`.

The generated Azure Function should use:

```python
import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
```

and an HTTP route such as:

```python
@app.route(route="flow2function", methods=["POST"])
def flow2function(req: func.HttpRequest) -> func.HttpResponse:
    ...
```

The route name should be derived from the flow name when practical.

---

# 3. Analyze all actions

Identify every action in the Power Automate workflow.

For each action determine:

* action name
* action type
* inputs
* expressions
* outputs
* dependencies
* connector
* operation
* position in execution sequence
* whether it is inside a condition or loop

Do not omit actions.

Actions must be converted according to their semantics rather than merely copied as JSON.

---

# 4. Preserve execution dependencies

Power Automate uses `runAfter` to control execution dependencies.

Example:

```json
"runAfter": {
    "List_rows": [
        "Succeeded"
    ]
}
```

means that the dependent action must execute after `List_rows` succeeds.

The generated Python implementation must preserve these dependencies.

Do not assume that the order of keys in the JSON alone determines execution order.

For simple sequential flows, generate sequential Python statements.

For independent actions, parallel execution may be introduced only when it does not alter the original behavior.

---

# 5. Convert Power Automate variables

Convert Power Automate variables to local Python variables.

### Array

Power Automate:

```text
InitializeVariable
type: array
```

Python:

```python
processed_orders = []
```

### Float

Power Automate:

```text
type: float
```

Python:

```python
discounted_price = 0.0
```

### String

Use:

```python
value = ""
```

### Integer

Use:

```python
value = 0
```

Variables must be scoped to the function invocation.

Do not use global mutable variables.

---

# 6. Convert Compose actions

Convert `Compose` actions into equivalent Python expressions.

For example:

```text
@mul(
    int(items('Apply_to_each')?['new_quantity']),
    float(items('Apply_to_each')?['new_unitprice'])
)
```

should become equivalent Python logic:

```python
quantity = int(order.get("new_quantity"))
unit_price = float(order.get("new_unitprice"))
total_price = quantity * unit_price
```

Use meaningful variable names.

Do not retain meaningless names such as `Compose`, `Compose_1`, etc., unless necessary for traceability.

---

# 7. Convert Power Automate expressions

Translate Power Automate expressions into equivalent Python.

Use these mappings where applicable:

| Power Automate           | Python                                                                                                                                                                                                                            |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mul(a,b)`             | `a * b`                                                                                                                                                                                                                         |
| `add(a,b)`             | `a + b`                                                                                                                                                                                                                         |
| `sub(a,b)`             | `a - b`                                                                                                                                                                                                                         |
| `div(a,b)`             | Integer division when both`a` and `b` are integers (truncated result, e.g. `div(5,2)` is `2`); true division (`a / b`) when either is a float. A zero divisor is an error, as in the flow.                              |
| `int(x)`               | `int(x)`                                                                                                                                                                                                                        |
| `float(x)`             | `float(x)`                                                                                                                                                                                                                      |
| `string(x)`            | Type-aware conversion:`null` becomes `""`; strings are unchanged; objects and arrays are serialized with `json.dumps(x)`; booleans become `"true"`/`"false"`; numbers use their plain text form. Do not use `str(x)`. |
| `equals(a,b)`          | `a == b`                                                                                                                                                                                                                        |
| `greater(a,b)`         | `a > b`                                                                                                                                                                                                                         |
| `greaterOrEquals(a,b)` | `a >= b`                                                                                                                                                                                                                        |
| `less(a,b)`            | `a < b`                                                                                                                                                                                                                         |
| `lessOrEquals(a,b)`    | `a <= b`                                                                                                                                                                                                                        |
| `and(a,b)`             | `a and b`                                                                                                                                                                                                                       |
| `or(a,b)`              | `a or b`                                                                                                                                                                                                                        |
| `not(x)`               | `not x`                                                                                                                                                                                                                         |
| `take(array,n)`        | `array[:n]`                                                                                                                                                                                                                     |
| `length(array)`        | `len(array)`                                                                                                                                                                                                                    |

Use type-aware conversions for `div` and `string` so calculations and connector payloads preserve the source Power Automate behavior.

Also translate:

```text
triggerBody()?['property']
```

to the corresponding HTTP request property.

Translate:

```text
items('Apply_to_each')?['property']
```

to the current Python loop item.

Translate:

```text
variables('VariableName')
```

to the corresponding Python variable.

Do not perform blind string substitution.

The generated Python must preserve expression semantics.

---

# 8. Convert conditions

Convert Power Automate `If` actions to Python `if`, `elif`, and `else`.

For example:

```text
equals(triggerBody()?['text'], 'standard')
```

becomes:

```python
if text == "standard":
```

Nested conditions must remain logically equivalent.

For example, if the Power Automate flow contains:

```text
if total > 5000
    discounted = total * 0.8
else
    if total > 1000
        discounted = total * 0.85
    else
        discounted = total
```

the generated Python must preserve the exact decision tree.

Do not change thresholds, comparison operators, or discount values.

---

# 9. Convert Apply to each

Convert `Foreach` actions into Python `for` loops.

Example:

```text
@take(body('List_rows')?['value'], 200)
```

becomes:

```python
for order in orders[:200]:
    ...
```

If the source iterates through the entire collection, preserve that behavior.

Preserve all nested actions within the loop.

---

# 10. Convert Dataverse operations

When a Dataverse connector is present, identify:

* table/entity name
* operation
* filters
* selected fields
* parameters
* returned data
* dependency on other actions

For example:

```text
connector:
shared_commondataserviceforapps

operation:
ListRecords

entity:
new_orderses
```

must be represented by an appropriate Python Dataverse implementation.

Use the Dataverse Web API or an appropriate supported Python integration.

Use environment variables for configuration.

Example:

```python
import os

dataverse_url = os.environ["DATAVERSE_URL"]
```

Do not hard-code:

* tenant IDs
* client IDs
* client secrets
* access tokens
* connection strings

If the exact authentication mechanism cannot be determined from the JSON, mark it as a configuration requirement in the report.

Do not invent credentials.

---

# 11. Convert other connectors

For each connector:

1. Identify connector name.
2. Identify operation.
3. Identify inputs.
4. Identify outputs.
5. Determine the closest Python implementation.
6. Preserve the operation's behavior.

Examples:

| Connector          | Python implementation                  |
| ------------------ | -------------------------------------- |
| Dataverse          | Dataverse Web API / appropriate client |
| HTTP               | `requests` or `httpx`              |
| Azure Blob Storage | `azure-storage-blob`                 |
| Azure Service Bus  | `azure-servicebus`                   |
| SQL                | `pyodbc` or appropriate SQL client   |
| Microsoft Graph    | Microsoft Graph API/SDK                |
| SharePoint         | Microsoft Graph / SharePoint API       |

If an exact connector implementation cannot be determined, clearly identify it as:

```text
TODO: Connector implementation requires additional configuration.
```

Do not fabricate functionality.

---

# 12. Generate Azure Function

Generate a complete `function_app.py`.

The function must:

* use Python Azure Functions v2
* use `azure.functions`
* use an HTTP trigger when appropriate
* parse request JSON
* validate inputs
* execute converted workflow logic
* interact with required connectors
* preserve conditions and loops
* preserve variables
* return structured JSON
* log useful processing information
* handle exceptions

Use:

```python
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
```

unless the reference sample uses another valid configuration.

The function must be complete.

Do not provide only a code fragment.

---

# 13. Error handling

The generated function must include appropriate error handling.

Use:

```python
import logging
```

and:

```python
try:
    ...
except Exception:
    logging.exception("Error processing flow")
    return func.HttpResponse(
        "An error occurred while processing the request.",
        status_code=500
    )
```

Do not expose internal exception details to the caller.

Do not hide errors.

Preserve meaningful failure behavior from the original workflow where possible.

---

# 14. Logging

Include useful logging for:

* function invocation
* major processing stages
* connector calls where appropriate
* number of records processed
* failures

Do not log:

* passwords
* access tokens
* client secrets
* connection strings
* sensitive request payloads unless explicitly required

---

# 15. Generate conversion analysis

The skill must generate a detailed analysis explaining the conversion.

The analysis must contain:

### Executive Summary

Explain:

* what the Power Automate flow does
* why it is suitable for migration
* what was converted
* what the Azure Function provides

### Flow Structure

Describe:

* trigger
* variables
* actions
* conditions
* loops
* connectors
* output

### Power Automate to Python Mapping

Use a table:

| Power Automate Component | Python Azure Function Equivalent |
| ------------------------ | -------------------------------- |
| Trigger                  | HTTP-triggered Azure Function    |
| InitializeVariable       | Python variable                  |
| Compose                  | Python expression                |
| Condition                | `if/elif/else`                 |
| Apply to each            | `for` loop                     |
| Connector                | Python SDK/API                   |
| Append to array          | `list.append()`                |
| Response                 | `HttpResponse`                 |

### Business Logic Conversion

Explain the actual business rules identified from the JSON.

Do not provide generic explanations when the JSON contains specific logic.

### Connector Analysis

List all connectors detected and how they were mapped.

### Configuration Requirements

List required Azure Function Application Settings.

### Assumptions and Limitations

Clearly distinguish:

* confirmed from JSON
* inferred behavior
* missing information
* connector implementation requiring configuration

### Generated Azure Function

Include the complete generated `function_app.py` code.

The code must be shown in monospace formatting with indentation preserved.

---

# 16. Render PDF report

Generate a PDF report using `reportlab`.

The report must contain an index/table of contents for navigation.

The PDF should contain:

1. Title
2. Generation timestamp
3. Flow name
4. Executive summary
5. Flow structure
6. Power Automate component analysis
7. Power Automate → Python mapping
8. Business logic conversion
9. Connector analysis
10. Configuration requirements
11. Assumptions and limitations
12. Complete generated `function_app.py`

The generated Python code must appear at the end of the PDF in monospace formatting with indentation preserved.

The PDF must be readable even when the generated code is long.

File naming convention:

```text
flow2function_<sanitized_flow_name>.pdf
```

Never use the raw flow name directly in a filename. Derive `<sanitized_flow_name>` using the rules below.

## Sanitizing artifact filenames

Apply these deterministic rules to the flow name to produce `<sanitized_flow_name>`:

1. Allow only letters, numbers, `.`, `_`, and `-`.
2. Replace path separators (`/`, `\`), control characters, quotes, wildcards (`*`, `?`), and any other invalid filename characters with `_`.
3. Collapse repeated underscores into a single `_`.
4. Reject the name if it is empty, `.`, or `..`, or if it is a Windows reserved device name (`CON`, `PRN`, `AUX`, `NUL`, `COM1`-`COM9`, `LPT1`-`LPT9`, with or without an extension). When rejected, fall back to a safe default such as `flow`.
5. Cap the sanitized name at a fixed maximum length (for example 80 characters) **before** adding the `flow2function_` prefix and the file extension.

Compute `<sanitized_flow_name>` once and reuse it for both the PDF and the ZIP filenames.

Write the PDF and ZIP only to `/app/created/`. Never write to a path built from the raw flow name.

---

# 17. Generate Azure Function deployment ZIP

Generate a complete Azure Function deployment ZIP.

The ZIP must contain:

```text
flow2function_<sanitized_flow_name>.zip
├── .funcignore
├── function_app.py
├── host.json
└── requirements.txt
```

All files must be at the root of the ZIP.

There must NOT be an additional parent folder.

Do not include:

* temporary files
* analysis files
* PDF files
* `.git`
* `__pycache__`
* unrelated files

---

# 18. function_app.py

The ZIP must contain the exact generated Azure Function implementation.

The generated code must replace any placeholder/sample implementation from the reference project.

The file must be named exactly:

```text
function_app.py
```

---

# 19. host.json

Use the reference project's `host.json`. The reference configuration is:

```json
{
  "version": "2.0",
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "excludedTypes": "Request"
      }
    }
  },
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.*, 5.0.0)"
  }
}
```

If no reference project is available, generate a valid minimal Azure Functions host configuration:

```json
{
  "version": "2.0"
}
```

Do not modify unrelated configuration from a supplied reference project unless required for the generated function.

---

# 20. requirements.txt

Generate a `requirements.txt` containing the packages actually required by the generated function.

At minimum include:

```text
azure-functions
```

Add connector packages only when they are used.

Examples:

```text
azure-functions
requests
azure-identity
```

Do not automatically add `reportlab` to the Azure Function deployment package unless the generated Azure Function itself uses ReportLab.

The PDF is generated by the migration/reporting process, not necessarily by the deployed Azure Function.

---

# 21. File generation

The skill must produce:

1. PDF analysis report
2. Azure Function deployment ZIP

The generated `function_app.py` must be contained inside the ZIP.

Do not return `function_app.py` as a separate file attachment unless explicitly requested.

The PDF must contain the generated code for review.

Write both the PDF and the ZIP to `/app/created/`, and return them as attachments in the same turn.

Return a compact JSON object containing:

```json
{
  "flowName": "...",
  "triggerType": "...",
  "actionsAnalyzed": 0,
  "connectorsDetected": [],
  "conversionSummary": "...",
  "recommendation": "...",
  "analysisSummary": "...",
  "zipFileName": "flow2function_<sanitized_flow_name>.zip",
  "pdfFileName": "flow2function_<sanitized_flow_name>.pdf",
  "functionAppFileName": "function_app.py"
}
```

Keep the JSON/chat response to compact textual metadata. `analysisSummary` must be a short summary (a few sentences) of what the flow does and how it was converted. Do not include the generated code or the full analysis in the response; the full analysis and the generated code are contained in the PDF and the ZIP.

Write both artifacts to `/app/created/` and return them as attachments in the same turn. In Copilot Studio, a file written to `/app/created/` is surfaced as a downloadable attachment. Do not just report that the files were created.

Do not include `pdfBase64` or `zipBase64`, or any other base64-encoded artifact content, in the response.

`functionAppFileName` must always be:

```text
function_app.py
```

---

# 23. Content Negotiation

The generated Azure Function itself should support normal HTTP JSON responses.

In Copilot Studio, artifacts are delivered by writing them to `/app/created/` (see section 22); the endpoint behavior below applies only if a separate custom HTTP endpoint serves the artifacts.

If a custom HTTP endpoint is responsible for serving generated artifacts, support:

```text
Accept: application/pdf
```

or:

```text
?format=pdf
```

to return the generated PDF.

Support:

```text
?format=zip
```

to return the generated Azure Function ZIP.

Direct artifact responses must be binary and use these headers:

| Artifact | Content-Type        | Content-Disposition                                                |
| -------- | ------------------- | ------------------------------------------------------------------ |
| PDF      | `application/pdf` | `attachment; filename="flow2function_<sanitized_flow_name>.pdf"` |
| ZIP      | `application/zip` | `attachment; filename="flow2function_<sanitized_flow_name>.zip"` |

If no format is specified, return compact JSON metadata (see section 22) and deliver both the PDF and the ZIP as attachments by writing them to `/app/created/`. Do not embed base64 payloads in the JSON.

---

# Important Rules

1. The Power Automate JSON is the source of truth for the workflow logic.
2. Analyze the complete JSON before generating code.
3. Do not invent business logic.
4. Do not omit actions.
5. Do not change conditions or thresholds.
6. Preserve loops and loop limits.
7. Preserve variable behavior.
8. Preserve `runAfter` dependencies.
9. Translate Power Automate expressions into semantically equivalent Python.
10. Use the Azure Functions Python v2 programming model.
11. Generate `function_app.py`, not C#.
12. Generate a deployment-ready ZIP.
13. Generate a PDF analysis report.
14. Include the complete generated Python code in the PDF.
15. Keep `.funcignore`, `function_app.py`, `host.json`, and `requirements.txt` at the root of the ZIP.
16. Do not include an extra parent folder in the ZIP.
17. Do not include secrets in code, PDF, ZIP, or JSON response.
18. Use environment variables for configuration.
19. Do not expose access tokens or connection secrets.
20. Do not silently invent connector implementations.
21. Clearly identify assumptions and TODOs.
22. The generated code must be real Python code, not pseudocode.
23. The generated ZIP must contain the same `function_app.py` code shown in the PDF.
24. Do not include `reportlab` in the Azure Function requirements unless the generated Azure Function itself requires it.
25. The migration process must generate both the analysis report and deployment package.
26. The final output must include both the PDF and the ZIP, written to `/app/created/` and returned as attachments in the same turn.
27. Never use the raw flow name in a PDF or ZIP filename. Always use `<sanitized_flow_name>`.
28. Never include base64 PDF or ZIP payloads in the model or JSON response.
