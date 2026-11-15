# Companies House Verification skill

| File | Purpose |
| --- | --- |
| `SKILL.md` | The skill (instructions, workflow, rules). |
| `assets/companies-house-connector.swagger.json` | Custom connector (OpenAPI 2.0) providing the tools the skill calls. |
| `references/api-reference.md` | Endpoint, field and status reference. |
| `scripts/ch_lookup.py` | Optional CLI to test your API key. |

## Setup in Copilot Studio

1. **Get an API key**: https://developer.company-information.service.gov.uk/ → register → *Create an application* → add a **REST** key.
2. **Create the connector**: make.powerapps.com → *Custom connectors* → *New custom connector* → *Import an OpenAPI file* → `assets/companies-house-connector.swagger.json`.
   On *Security*, authentication type **Basic authentication** (parameter labels: "API key" / "Password (leave blank)"). Create it.
3. **Create a connection** (*Test* tab → *New connection*): username = your API key; password = leave blank. If the portal insists on a password, instead set authentication to *No authentication* and on the *Definition* tab add the policy template **Set HTTP header**: name `Authorization`, value `Basic <base64 of "APIKEY:">`.
   Test `GetCompanyProfile` with `00445790` → expect `company_status: active`.
4. **Add the tools to the agent**: Copilot Studio → agent → *Tools* → *Add a tool* → *Connector* → *Companies House Verification*; add all operations with your connection.
5. **Add the skill**: download the skill bundle from the gallery and add it under the agent's *Skills*. If your tenant has no Skills option, paste the body of `SKILL.md` into the agent's *Instructions*.
6. **Optional – save to Dataverse**: the agent also needs Dataverse tools (e.g. the Dataverse MCP server or connector) with rights to the `account` table. For the first "create this company in Dynamics 365" request, the user also needs schema/form customisation rights (System Customizer), as the skill creates the Companies House columns and a **Companies House Information** tab on the Account form.
7. **Test**:
   - "Does Tesco PLC exist at Companies House?"
   - "Give me the details of company 00445790."
   - "Who are the current directors of 00445790?"
   - "What is the SIC code and incorporation date of Acme Widgets Ltd?"
   - "Is company 12345678 active?"
   - "Create this company in Dynamics 365 Dataverse account table."

## Notes
- Free API; 600 requests / 5 minutes.
- Keep the API key only in the connection, never in instructions.
- Public register data only; not a substitute for formal KYC/AML checks.
