# Sources

Baseline date: **2026-10-21**. Pages marked **verify** change most often; check them at runtime when a
Microsoft Learn tool or web search is available, and cite what you used.

| Topic | Source | Verify |
| --- | --- | --- |
| Connection options, auth types per connector | https://learn.microsoft.com/power-platform/sap/connect/connect-power-platform-and-sap | **verify** |
| SAP ERP connector setup (gateway, NCo) | https://learn.microsoft.com/power-platform/sap/connect/sap-erp-connector | |
| SAP ERP connector reference (actions, prerequisites) | https://learn.microsoft.com/connectors/saperp/ | **verify** |
| SAP OData connector setup | https://learn.microsoft.com/power-platform/sap/connect/sap-odata-connector | |
| SAP OData connector reference | https://learn.microsoft.com/connectors/sapodata/ | **verify** |
| SSO: Entra ID → API Management → SAP (SAML) | https://learn.microsoft.com/power-platform/sap/connect/entra-id-apim-oauth | |
| SSO: Entra ID with Kerberos (SAP ERP connector) | https://learn.microsoft.com/power-platform/sap/connect/entra-id-kerberos | |
| SSO: Entra ID with certificates (SAP ERP connector) | https://learn.microsoft.com/power-platform/sap/connect/entra-id-certs | |
| OAuth 2.0 on SAP OData connector (preview) | https://learn.microsoft.com/power-platform/sap/connect/sap-oauth | **verify** |
| Secure Network Communications | https://learn.microsoft.com/power-platform/sap/connect/secure-network-communications | |
| Architecture workflow, connectivity option table | https://learn.microsoft.com/azure/cloud-adoption-framework/scenarios/sap/sap-power-platform-architecture-workflow | |
| Landing zone extension for Power Platform | https://learn.microsoft.com/azure/cloud-adoption-framework/scenarios/sap/sap-power-platform-extend-landing-zone | |
| Copilot Studio with SAP (patterns, protocol/auth table) | https://learn.microsoft.com/azure/sap/microsoft-ai/copilot-studio/copilot-with-sap-overview | **verify** |
| Pattern: APIM + VNet peering | https://learn.microsoft.com/azure/sap/microsoft-ai/copilot-studio/architecture-apim-virtual-network | |
| Pattern: on-premises data gateway (BAPI/RFC/OData) | https://learn.microsoft.com/azure/sap/microsoft-ai/copilot-studio/architecture-on-premises-data-gateway | |
| Pattern: SAP BTP + API Management + Cloud Connector | https://learn.microsoft.com/azure/sap/microsoft-ai/copilot-studio/architecture-business-technology-platform-api | |
| Pattern: SAP MCP Gateway on Integration Suite | https://learn.microsoft.com/azure/sap/microsoft-ai/copilot-studio/architecture-mcp-gateway-integration-suite | **verify** |
| SSO with SAP Cloud Identity Services + principal propagation | https://learn.microsoft.com/azure/sap/microsoft-ai/copilot-studio/sso-entra-id-sap-cloud-identity-services | **verify** |
| Logic Apps SAP connector (built-in vs managed, IDoc) | https://learn.microsoft.com/azure/logic-apps/connectors/sap | |
| Templates and prebuilt agents for SAP | https://learn.microsoft.com/power-platform/sap/templates/overview | **verify** |
| SAP Procurement template | https://learn.microsoft.com/power-platform/sap/templates/sap-procurement/overview | |
| Reference architecture: Power Platform + SAP | https://learn.microsoft.com/power-platform/architecture/reference-architectures/arch-pattern-sap | |
| Power Automate desktop: SAP GUI RPA playbook | https://learn.microsoft.com/power-automate/guidance/rpa-sap-playbook/action-based-sap-gui-automation-manually-overview | |
| On-premises data gateway HA clusters | https://learn.microsoft.com/data-integration/gateway/service-gateway-high-availability-clusters | |
| SAP API policy (licensing/usage questions → SAP account team) | https://help.sap.com/doc/sap-api-policy/latest/en-US/API_Policy_latest.pdf | **verify** |
| SAP Business Accelerator Hub (released APIs) | https://api.sap.com/ | |
| SAP Connector for Microsoft .NET (download) | https://support.sap.com/en/product/connectors/msnet.html | |
| **Positioning: Joule, Copilot, extensibility** | | |
| About SAP with Microsoft AI (three layers: Joule+Copilot, Copilot Studio, Foundry) | https://learn.microsoft.com/azure/sap/microsoft-ai/about-sap-with-microsoft-ai | **verify** |
| Joule and Microsoft Copilot integration (setup, supported apps, limits) | https://learn.microsoft.com/azure/sap/microsoft-ai/joule/joule-copilot-overview | **verify** |
| SAP Help: integrating Joule with Microsoft 365 Copilot (supported apps) | https://help.sap.com/docs/joule/integrating-joule-with-sap/integrating-joule-with-microsoft-365-copilot | **verify** |
| Employee Self-Service agent handoff (incl. SAP Joule) | https://learn.microsoft.com/microsoft-365/copilot/employee-self-service/agent-handoff | |
| Extend SAP by using Microsoft Power Platform (clean core, components) | https://learn.microsoft.com/azure/cloud-adoption-framework/scenarios/sap/sap-power-platform-fundamental | |
| Embedding a Copilot Studio agent in SAP Fiori launchpad / SAP Build Work Zone ("Websites" section) | https://learn.microsoft.com/azure/sap/microsoft-ai/copilot-studio/copilot-with-sap-overview | |
| SAP Architecture Center: Extend Joule with Joule Studio (Classic) | https://github.com/SAP/architecture-center/blob/main/docs/ref-arch/RA0024/3-extend-joule-with-joule-studio/readme.md | **verify** |
| SAP Architecture Center: Building AI agents with Joule Studio | https://github.com/SAP/architecture-center/blob/main/docs/ref-arch/RA0029/2-building-ai-agents-with-joule-studio/readme.md | **verify** |
| SAP Architecture Center: Joule agents via Agent Gateway / A2A (GA status) | https://github.com/SAP/architecture-center/blob/main/docs/ref-arch/RA0029/5-integrate-joule-agents-and-tools-into-your-ecosystem/readme.md | **verify** |
| SAP Architecture Center: Copilot Studio with SAP MCP Gateway (MCP vs A2A) | https://github.com/SAP/architecture-center/blob/main/docs/ref-arch/RA0029/10-third-party-mcp-access/1-copilot-studio-with-mcp/readme.md | **verify** |
| SAP clean core: released and classic APIs, Clean Core Check | https://github.com/SAP/abap-atc-cr-cv-s4hc | **verify** |
| SAP clean-core extensibility guide (levels, extension styles) | search: `SAP clean core extensibility white paper` on sap.com / SAP Community | **verify** |

The SAP Architecture Center is published as Markdown on GitHub (`github.com/SAP/architecture-center`),
which is easier to read with fetch tools than help.sap.com.

Search hints when a link has moved: `site:learn.microsoft.com "SAP OData connector" authentication`,
`site:learn.microsoft.com "Copilot Studio" SAP architecture`.
