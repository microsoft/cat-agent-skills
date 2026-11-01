# Refinement template guide

The skill answers first, using stated assumptions. It then closes with a **Refine this answer**
section containing a copy-paste template, pre-filled with the values the answer used, which the user
edits and sends back.

## Rules

- **Pre-fill every line** with the value used in the answer. Mark guesses with `(assumed)` and
  known facts with `(given)`; this shows the user which corrections matter most.
- **Only decisive fields**: 6–10 lines for the question type (sets below). Drop lines that don't
  affect this case. Always end with `Anything else:`.
- **Options in square brackets** after each value, short and separated by `|`, so the user can pick
  one by overwriting the value. Keep each line under ~140 characters.
- **Put the template in a fenced code block** (```` ```text ````) so chat hosts show a copy button
  and keep the line breaks.
- **Introduce it in one line**: say that values marked `(assumed)` are the main guesses and that
  correcting them changes the answer most. Mention that partial edits are fine and "not sure" is a
  valid value.
- **Never include** fields for passwords, host names, client numbers, user IDs or keys.
- Keep the template the same between turns (same order and labels) so the user can reuse it.

## Handling the reply

1. Accept the filled template, a partial template, or plain sentences. Map each value to the fact
   sheet and set its source to `user`.
2. For `not sure`, keep the assumption and give the matching hint from the table below in one line.
3. Start the reply with **What changed**: the facts that changed and whether the recommendation
   changed (for example "SAP OData connector via Azure API Management → SAP BTP with Cloud
   Connector, because BTP with Cloud Connector already exists"; or
   "recommendation unchanged, confidence medium → high").
4. Re-run the decision, render the next report version, and end again with the template showing the
   updated values, leaving only the remaining assumptions marked `(assumed)`.
5. When nothing is assumed any more, replace the template with a one-line offer of follow-ups
   (compare an alternative, single sign-on deep dive, prerequisites per team).

## Field sets

### Connectivity

```text
Scenario: <value> (assumed|given)          [read | create/update/approve | both | events from SAP]
SAP system: <value>                        [ECC | S/4HANA on-prem | RISE/private cloud | S/4HANA Cloud public | SuccessFactors/Ariba/Concur]
Hosting: <value>                           [own data centre | Azure | other cloud]
Consumer: <value>                          [Copilot Studio agent | Power Apps | Power Automate | Power Pages (external) | Power BI]
Interfaces available: <value>              [standard BAPI/RFC | custom Z-RFC | OData / released APIs | SOAP | SAP GUI only | not sure]
Already in place: <value>                  [data gateway | Azure API Mgmt | Logic Apps | BTP + Cloud Connector | Integration Suite | none]
SAP must see each user: <value>            [yes, per-user SSO | technical user is fine | mixed]
Entra ID ↔ SAP Cloud Identity Services: <value>   [trust exists | no | planned | not sure]
Volume per day: <value>                    [< 1,000 | 1,000–100,000 | > 100,000 or batches]
Constraints: <value>                       [data residency | no new Azure | no new BTP | SAP-skilled team | Microsoft-skilled team | none]
Anything else:
```

### Assistant positioning (Joule vs Microsoft 365 Copilot vs Copilot Studio)

```text
Users work mainly in: <value>              [SAP apps (Fiori, SuccessFactors) | Teams/Outlook/M365 Copilot | both | external]
Assistant should: <value>                  [answer standard SAP questions | company-specific process | cross-system SAP + non-SAP + M365]
Joule enabled for: <value>                 [S/4HANA Cloud | SuccessFactors | planned | no]
Microsoft 365 Copilot licences: <value>    [all users | some users | none]
SAP release: <value>                       [ECC | S/4HANA on-prem | RISE/private cloud | S/4HANA Cloud public]
Build and run team: <value>                [SAP/BTP | Power Platform | fusion team]
One entry point for users: <value>         [yes | no | not sure]
Anything else:
```

### Where to extend (in SAP vs Power Platform)

```text
Building: <value>                          [change standard SAP app | new app on SAP data | app mixing SAP + other data | workflow/approval | external portal]
Users: <value>                             [SAP power users | occasional users | frontline/mobile | offline needed | external]
Logic inside the SAP transaction: <value>  [yes | no | not sure]
Team skills: <value>                       [ABAP/Fiori | SAP Build/BTP | Power Platform | mixed]
SAP release / clean core: <value>          [S/4HANA Cloud public | RISE with clean-core program | on-prem, no program | ECC]
UX standard: <value>                       [Fiori mandatory | Teams/M365 first | none]
Anything else:
```

For mixed questions, merge the sets and remove duplicate lines.

## Hints for "not sure"

| Field | One-line hint to give the user |
| --- | --- |
| SAP system / hosting | Ask SAP Basis, or check SAP GUI menu System → Status |
| Interfaces available | SAP Basis can check SAP Gateway service maintenance (transaction /IWFND/MAINT_SERVICE); released APIs are listed in SAP Business Accelerator Hub; function modules in transaction SE37 |
| Data gateway | Power Platform admin center → Data → On-premises data gateways |
| BTP / Cloud Connector / Integration Suite | Ask the SAP BTP team or the owner of the BTP global account |
| Entra ID ↔ SAP Cloud Identity Services | Ask the identity team whether SAP Cloud Identity Services trusts Entra ID |
| Joule enabled | Ask the SAP team which SAP cloud apps have Joule activated |

## Example closing section (connectivity)

**Refine this answer** — values marked `(assumed)` are my main guesses; correct any line (or write
"not sure") and send it back:

```text
Scenario: read and approve purchase orders (given)          [read | create/update/approve | both | events from SAP]
SAP system: S/4HANA on RISE (given)                          [ECC | S/4HANA on-prem | RISE/private cloud | S/4HANA Cloud public]
Hosting: Azure (given)                                       [own data centre | Azure | other cloud]
Consumer: Copilot Studio agent in Teams (given)
Interfaces available: released OData APIs (assumed)          [standard BAPI/RFC | custom Z-RFC | OData | SOAP | SAP GUI only | not sure]
Already in place: none (assumed)                             [data gateway | Azure API Mgmt | BTP + Cloud Connector | Integration Suite | none]
SAP must see each user: yes, per-user SSO (given)            [yes | technical user is fine | mixed]
Entra ID ↔ SAP Cloud Identity Services: not sure (assumed)   [trust exists | no | planned | not sure]
Volume per day: < 1,000 (assumed)                            [< 1,000 | 1,000–100,000 | > 100,000]
Anything else:
```
