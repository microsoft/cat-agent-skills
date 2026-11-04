# Decision guide — SAP ↔ Power Platform

Baseline: Microsoft Learn, checked 2026-10-21 (see `sources.md`). Re-check items marked *verify*.
The IDs (P1–P9) are internal shorthand for this file — use the plain pattern names with users.

## 1. Fact sheet

| Fact | Typical values | Why it matters |
| --- | --- | --- |
| Business scenario | e.g. approve POs, look up stock, create sales orders | read vs write, user vs system |
| Consumer | Copilot Studio agent, Power Apps (canvas/model-driven), Power Automate cloud flow, Power Pages, Power BI, Power Automate desktop | some patterns only fit some consumers |
| SAP product | R/3, ECC, S/4HANA on-premises, S/4HANA private cloud / RISE, S/4HANA Cloud public edition, SuccessFactors, Ariba, Concur, BW/BW4HANA | decides protocol (section 2) |
| SAP hosting / network | on-premises behind firewall, Azure (native or RISE), other cloud | gateway vs Cloud Connector vs VNet peering |
| Interfaces available | BAPI/RFC (standard or Z), OData (SAP Gateway / RAP / released APIs), SOAP, IDoc, none (GUI only) | decides connector |
| Middleware in place | on-premises data gateway, Azure API Management, Azure Logic Apps, SAP BTP (API Management, Integration Suite, Cloud Connector), SAP MCP Gateway | reuse beats new infrastructure |
| Identity requirement | per-user SSO with SAP authorizations and audit (principal propagation) vs technical/service user | decides identity chain |
| Identity providers | Microsoft Entra ID only, Entra federated with SAP Cloud Identity Services, Kerberos/AD, certificates | |
| Direction & timing | interactive request/response, batch, event-driven outbound from SAP (IDoc, events) | Logic Apps for inbound/IDoc/volume |
| Volume & latency | users, calls per day, payload size | gateway clustering, APIM throttling |
| Constraints | data residency, DLP policies, security reviews, team skills (Azure vs BTP vs ABAP) | tie-breakers |

## 2. Protocol by SAP product (Microsoft Learn)

| SAP application | Protocols | Authentication |
| --- | --- | --- |
| R/3, SAP ECC | BAPI/RFC (OData only if SAP Gateway services are set up) | SAP user, Kerberos |
| S/4HANA on-premises, native, private cloud | BAPI/RFC, OData | SAP user, Kerberos |
| S/4HANA Cloud public edition | OData | OAuth |
| SAP SuccessFactors | OData, HTTPS | OAuth |

## 3. Pattern catalog

| ID | Pattern | Use when | Needs | Identity options |
| --- | --- | --- | --- | --- |
| P1 | **SAP ERP connector + on-premises data gateway + SAP .NET Connector (NCo)** | BAPI/RFC/IDoc functions (standard or custom) on ECC / S/4HANA on-prem or private cloud; existing ABAP logic to reuse | Windows VM ≥ 8 GB RAM near SAP; gateway cluster for production; one gateway per environment; 64-bit NCo downloaded from SAP (S-user); RFC ports open (Microsoft docs: 33XX single app server, 39XX load-balanced; XX = system number — confirm with Basis); SNC for encryption | SAP user, Windows, Entra ID via Kerberos (SSO), Entra ID via certificates (SSO) |
| P2 | **SAP OData connector through the on-premises data gateway** | OData services exist, SAP behind firewall, simplest start, SSO not required | Gateway (same region as the environment); OData services activated in SAP Gateway | Basic (named or technical user) |
| P3 | **SAP OData connector + Azure API Management** (VNet peering if SAP on Azure/RISE; APIM self-hosted gateway for hybrid) | OData; per-user SSO; SAP on Azure or strong Azure skills; need throttling, monitoring, one API front door | APIM; Entra app registrations; SAML trust in SAP; network path (VNet peering or self-hosted gateway) | Entra ID → APIM converts OAuth token to SAML → SAP (principal propagation) |
| P4 | **SAP BTP (SAP API Management / Integration Suite) + SAP Cloud Connector** | BTP already connected to the SAP backend; SAP-centric governance | BTP subaccount, Cloud Connector, destinations; SAP OData or HTTP connector | Entra ID federated (OIDC) into SAP Cloud Identity Services; principal propagation through Cloud Connector (short-lived X.509); OAuth 2.0 on SAP OData connector *(preview — verify)* |
| P5 | **SAP MCP Gateway on SAP Integration Suite** | Copilot Studio agent that should discover and call many SAP APIs/iFlows as MCP tools, with SAP-managed auth, rate limits, observability | SAP Integration Suite with MCP Gateway *(verify availability)*; MCP tool in Copilot Studio | Same identity chain as P4 |
| P6 | **Custom connector via API Management** (Azure or SAP) | Only SOAP or custom REST services; complex request shaping | APIM to expose SOAP as REST; OpenAPI definition | Depends on APIM policy (prefer Entra SSO as in P3) |
| P7 | **Azure Logic Apps SAP connector** (Standard built-in: no gateway when in an integrated VNet) | Events or IDocs **from** SAP, high volume/batch, long-running or stateful integration; Power Platform calls it through HTTP/custom connector | Logic Apps Standard, VNet integration, NCo | Logic Apps connection identity; expose to Power Platform via APIM |
| P8 | **Power Automate desktop with SAP GUI automation (RPA)** | No API exists and building one isn't possible soon; low volume; tactical | SAP GUI scripting enabled on server and client; machines for attended/unattended runs | Named SAP GUI user |
| P9 | **Analytics connectors** (Power BI SAP HANA/BW; Agent Builder OData knowledge for read-only grounding) | Reporting or read-only Q&A, not transactions | HANA ODBC or NCo for BW | Per connector |

Accelerators to mention when they fit:
- **SAP Procurement template** (SAP Base + SAP Procurement solutions, SAP Setup Assistant) — built on P1.
- **SAP Supplier Self Service** (Power Pages) — extends the procurement template.
- Templates and prebuilt agents: `github.com/microsoft/Templates-for-Power-Platform`.

## 4. Decision rules

1. **S/4HANA Cloud public edition, SuccessFactors, Ariba, Concur** → OData/HTTP only: P3, P4 or P5.
   No RFC.
2. **Reuse existing BAPIs/Z-RFCs and no OData service** → P1. For new builds, Microsoft recommends
   exposing an existing OData service, or developing one — mention RAP/CDS as the longer-term path.
3. **OData + per-user SSO + SAP on Azure/RISE + Azure skills** → P3 with VNet peering.
4. **BTP + Cloud Connector already in place** → P4 (reuse beats new infrastructure).
5. **Agent needing many SAP operations chosen dynamically, Integration Suite available** → P5; keep
   P3/P4 actions for critical write operations that need fixed, reviewed inputs.
6. **Inbound from SAP (IDoc, events), batch or high volume** → add P7 alongside the interactive
   pattern.
7. **GUI only** → P8 as a bridge, with a plan to expose an API; never as the long-term design for
   high-volume writes.
8. **Read-only reporting** → P9, not a transactional connector.
9. **Identity:** if users must see only what SAP authorizes them to, or actions must be audited per
   user, require per-user SSO (P1 Kerberos/certificates, P3 APIM-SAML, P4/P5 Cloud Identity
   Services). A shared technical user is acceptable only for system processes or non-sensitive reads,
   and its licensing must be confirmed with SAP (do not judge it yourself).
10. **Consumer specifics:** Copilot Studio can call SAP ERP/OData connectors directly as tools or via
    agent flows (add logic before/after the call); Power Apps usually calls through flows for
    BAPIs; Power Pages for external users needs extra care on identity mapping and exposure.
11. **Writes through BAPIs:** plan commit handling (`BAPI_TRANSACTION_COMMIT`, stateful sessions)
    and read the `RETURN` messages; plan idempotency for retries.
12. **Ties:** choose what the team already runs and can operate (gateway vs APIM vs BTP).

## 5. Production checklist (any pattern)

- Separate dev/test/prod environments, each with its own gateway / API endpoints.
- Gateway in a high-availability cluster; monitor gateway and APIM.
- DLP policy that classifies the SAP connectors and blocks unintended combinations.
- Connection references and environment variables in solutions; no credentials in flows or apps.
- Least-privilege SAP roles for technical users; SNC or TLS everywhere.
- Load estimate against SAP (EarlyWatch, peak users); throttling at APIM/BTP.
- Clean core: prefer released APIs; avoid modifications.
- Error handling: SAP return messages surfaced to users; retries safe for writes.

## 6. Roles

| Role | Typical tasks |
| --- | --- |
| SAP Basis | RFC/technical users and roles, SNC, OData service activation, trust (SAML/certificates), ports |
| SAP BTP admin | Cloud Connector, destinations, Cloud Identity Services, Integration Suite / MCP Gateway |
| Microsoft Entra admin | App registrations, enterprise apps, Kerberos delegation, federation with SAP Cloud Identity Services |
| Azure admin | API Management, VNet peering, Logic Apps |
| Power Platform admin | Gateway install/cluster, environments, DLP, connection sharing |
| Maker / developer | Flows, apps, agent tools, solution packaging |
