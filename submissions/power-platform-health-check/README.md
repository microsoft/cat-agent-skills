# Power Platform Health Check

Give the agent an environment URL and one or more solution names, and it checks every component in those solutions without changing anything.

## What it checks

- Tables, columns, option sets and relationships exist
- Cloud flows and workflows are activated and have content
- Web resources, forms and views are non-empty
- Plug-in assemblies exist and plug-in steps are enabled
- Model-driven and canvas apps exist (model-driven apps are published)
- Environment variables have a value; connection references are bound
- Each solution has no missing dependencies

Every component is rated PASS, WARN or FAIL, and the agent summarizes the findings with suggested fixes. It never applies fixes unless asked.

## Requirements

- Python 3.8+ (standard library only)
- Read access to the environment, via a service principal (`POWERPLATFORM_SP_APP_ID`, `POWERPLATFORM_SP_TENANT_ID`, `POWERPLATFORM_SP_CLIENT_SECRET`) or a token in `DATAVERSE_ACCESS_TOKEN`

## Example prompt

> Run a health check on https://contoso.crm.dynamics.com for the solutions `ContosoCore` and `ContosoFlows`.

A passing report confirms structure and state only; it does not replace functional testing.
