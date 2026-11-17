# Positioning guide — Joule vs Copilot Studio, and where to extend SAP

Baseline 2026-10-21. Both areas move fast: re-check items marked *verify* (see `sources.md`).
Stay vendor-neutral: describe each option's centre of gravity; never disparage either vendor; never
compare prices or licences (refer to the Microsoft and SAP account teams).
The IDs (J1–J6, E1–E5) are internal shorthand for this file — use the plain names with users.

## A. Joule, Microsoft 365 Copilot, Copilot Studio — which assistant layer?

### The short answer to "why Copilot Studio if we have Joule?"

They have different centres of gravity and are designed to work together:
- **Joule** is SAP's assistant, built into SAP cloud applications. It knows SAP business context and
  standard SAP processes; it's extended with **Joule Studio** (SAP Build / SAP Business AI Platform).
- **Microsoft 365 Copilot / Copilot Studio** live where people already work (Teams, Outlook,
  Microsoft 365 Copilot, websites) and orchestrate **across** SAP, non-SAP systems and Microsoft 365
  data. Copilot Studio builds custom agents; Foundry covers advanced multi-agent and pro-code cases.
- Microsoft describes three complementary layers: out-of-the-box **Joule ↔ Copilot** integration,
  custom agents in **Copilot Studio**, and enterprise AI in **Foundry**.

### Options

| ID | Option | What it is | Best when | Limits / prerequisites |
| --- | --- | --- | --- | --- |
| J1 | **Joule ↔ Microsoft Copilot managed integration** | Bidirectional: "@Joule …" from Microsoft 365 Copilot or Teams is routed to Joule; Joule can use Microsoft 365 context (mail, chats) | Quick value, no custom development; standard Joule scenarios | Only Joule's built-in capabilities — **not** routed to Copilot Studio agents; SAP cloud apps (S/4HANA Cloud private/public, SuccessFactors, selected Ariba — *verify list*); trust between SAP Cloud Identity Services and Entra ID with user mapping |
| J2 | **Copilot Studio agent → SAP** (patterns P1–P5) | Custom agent calling SAP via connectors or the SAP MCP Gateway | Company-specific process, cross-system (SAP + non-SAP + Microsoft 365), users in Teams/M365/web, also on-prem ECC/S/4HANA | You design, secure and operate it; identity chain per pattern |
| J3 | **Copilot Studio ↔ Joule agents via A2A** | Copilot Studio delegates a task to a specialised Joule agent through SAP's Agent Gateway or SAP Integration Suite A2A connectivity | Microsoft-side orchestrator that should reuse SAP-built agents instead of re-implementing SAP logic | *Verify availability*: SAP documents bidirectional third-party communication through Agent Gateway as not yet GA (Oct 2026); IAS App2App trust |
| J4 | **Employee Self-Service agent handoff to Joule** | Microsoft's ESS agent hands off HR/SAP questions to the Joule agent in the Copilot agent store | HR/employee self-service front door in Microsoft 365 | Joule agent must be available to users in Microsoft 365 |
| J5 | **Joule Studio custom skills and agents** | Low-code (SAP Build) or pro-code skills/agents deployed alongside Joule | Users live in SAP apps (Fiori, SuccessFactors); SAP-centric processes; SAP Build lifecycle | Joule and SAP Build prerequisites (IAS, SAP Build Process Automation); *verify current product naming* ("Joule Studio Classic" vs "Joule Studio") |
| J6 | **Copilot Studio agent embedded in SAP UIs** | Copilot Studio agent placed in SAP Fiori launchpad or SAP Build Work Zone (web channel) | Need a custom cross-system agent inside the SAP UI | Web channel auth and SSO design |

**MCP vs A2A** (SAP Architecture Center): use MCP when Copilot Studio should *call SAP capabilities as
tools*; use A2A when it should *delegate a task to a specialised SAP agent*.

### Decision criteria

| Question | Leans Joule (J1/J5) | Leans Copilot Studio (J2/J6) | Both (J1+J2, J3, J4) |
| --- | --- | --- | --- |
| Where do users spend their day? | SAP apps (Fiori, SuccessFactors) | Teams, Outlook, M365 Copilot, websites | Mixed populations |
| Scope of the task | SAP-only, standard SAP process | Spans SAP + non-SAP + Microsoft 365 data | SAP step inside a wider process |
| SAP release | SAP cloud apps (S/4HANA Cloud, SuccessFactors) | Any, including ECC and on-prem S/4HANA | — |
| Standard vs custom | Joule already covers it | Company-specific logic or UX | Standard part in Joule, custom part in Copilot Studio |
| Team skills / platform | SAP Build, BTP | Power Platform, Azure | — |
| Identity | SAP Cloud Identity Services centre | Entra ID centre | IAS ↔ Entra trust (needed for J1, J3, many P4/P5) |

Rules:
1. If Joule already does it and users are in SAP or can say "@Joule" in Copilot → J1, don't rebuild.
2. If the process crosses systems or needs Microsoft 365 context and custom logic → Copilot Studio (J2).
3. If an SAP-built Joule agent already encapsulates complex SAP logic → prefer delegating (J3) over
   re-implementing it, once available.
4. One identity foundation (Entra ID ↔ SAP Cloud Identity Services trust) serves J1, J3, P4 and P5 — 
   recommend setting it up once.
5. Avoid two assistants answering the same question in the same channel; define a "front door" per
   persona and hand off between agents.

## B. Extend inside SAP or outside? (Fiori vs Power Apps and friends)

### Clean core first

SAP's clean-core approach classifies extensions by how safely they survive upgrades. SAP's Clean
Core Check (ATC, since August 2025) distinguishes **released APIs (Level A)** from **classic APIs**
and less safe usages (*verify the current level definitions in SAP's clean-core extensibility
guide*). For Power Platform: consume **released** OData/APIs or documented classic BAPIs through
the connectors; avoid custom RFCs that read internal tables directly; wrap classic BAPIs with SAP's
recommended wrappers when building ABAP Cloud extensions.

### Options

| ID | Where | Option | Best when |
| --- | --- | --- | --- |
| E1 | In SAP, on-stack | **Key-user extensibility** (custom fields and logic, Fiori adaptation) | Small changes to standard SAP apps; business experts; stays in SAP UX |
| E2 | In SAP, on-stack | **Developer extensibility** (ABAP Cloud, RAP, Fiori elements apps) | Logic must run next to SAP data in the same transaction (LUW), high volume, strict consistency |
| E3 | SAP BTP, side-by-side | **SAP Build Apps / Build Code / CAP / Fiori on BTP, SAP Build Process Automation, Work Zone** | SAP-centric extension, SAP UX (Fiori design), SAP lifecycle, users in SAP launchpad |
| E4 | Microsoft, side-by-side | **Power Apps (canvas/model-driven), Power Pages, Power Automate, Copilot Studio** with P1–P9 | Users in Teams/M365/mobile/frontline; mixes SAP with Microsoft 365, Dataverse or non-SAP data; offline mobile with Dataverse; Microsoft-skilled team; approvals in Teams/Outlook |
| E5 | UI automation | **Power Automate desktop / SAP Build Process Automation RPA** | No API, tactical, low volume (bridge only) |

### Decision criteria

| Criterion | Leans SAP (E1–E3) | Leans Microsoft (E4) |
| --- | --- | --- |
| Primary users | SAP power users in Fiori launchpad | Occasional, frontline, mobile, managers in Teams, external partners |
| Data | Almost all SAP | SAP + Microsoft 365 / Dataverse / other systems |
| Transaction semantics | Must be in the SAP LUW, complex validations, high volume | Simple reads/writes through released APIs or BAPIs |
| UX standard | Fiori design consistency matters | Teams/M365 integration, custom branding, rapid iteration |
| Offline / mobile | — | Power Apps offline with Dataverse |
| External users | SAP portals / Work Zone | Power Pages |
| Skills and ALM | ABAP / SAP BTP / SAP Build teams | Power Platform / fusion teams, Managed Environments |
| Process orchestration | Process lives inside SAP (SAP Build Process Automation, SAP workflow) | Process spans Microsoft 365 and several systems (Power Automate) |

Rules:
1. Change the standard SAP app's own fields/logic → E1/E2, not Power Apps.
2. New lightweight experience for non-SAP users, or one that mixes data sources → E4.
3. Heavy transactional logic → keep it in SAP (E2/E3) and expose a released API; let Power Platform
   be the experience/orchestration layer on top.
4. Many successful landscapes combine them: Fiori for SAP power users, Power Apps/Teams for
   occasional users and approvals, both on the same released APIs.
5. Whatever side you build on: the same clean-core rules apply to the APIs consumed, and SAP
   authorizations still apply — do not judge licensing implications of users acting on SAP data
   through non-SAP UIs; refer to the SAP account team.

## Myths to correct gently

- "Joule replaces Copilot Studio" / "Copilot Studio duplicates Joule" → different centres of gravity;
  Microsoft and SAP ship an integration between them.
- "Power Apps breaks clean core" → not when it consumes released APIs side-by-side; it can help keep
  the core clean.
- "Fiori and Power Apps compete" → they often serve different personas on the same APIs.
