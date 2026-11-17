# Flow JSON to Azure Function

Converts a Power Automate cloud flow definition (JSON) into a deployable **Python Azure Function** (Azure Functions Python v2 model), preserving the flow's triggers, conditions, loops, variables, expressions, and connector operations. It also produces a PDF analysis report and a deployment ZIP.

## What you need to use this skill

1. **The flow's workflow JSON.** One Power Automate workflow definition per run (typically `Workflows/<FlowName>-<GUID>.json` from an exported solution).
2. **The `solution-package-extractor` skill (companion, not included here).** Use it to pull the workflow JSON for every flow out of a Power Platform solution `.zip`. It is optional if you already have the flow JSON. It is available in the [Flow2Function repo](https://github.com/KamalikaBalaji1/Flow2Function).
3. **The sample Azure Function project (included in `assets/`).** The skill uses it as the template for the generated package:
   - `function_app.py` — placeholder HTTP handler that gets replaced by the converted logic
   - `host.json`
   - `requirements.txt`
   - `.funcignore`

## What you get back

- A complete `function_app.py` implementing the flow's logic.
- A deployment ZIP (`function_app.py`, `host.json`, `requirements.txt`, `.funcignore`).
- A PDF analysis report: flow structure, Power Automate to Python mapping, connector analysis, configuration requirements, assumptions, and the full generated code.

## Notes

- Connectors with no direct Python equivalent are marked `TODO` with their configuration requirements.
- Secrets and connection details are never hard-coded. Supply them through Azure Function application settings.
- Review the generated code before deploying.
