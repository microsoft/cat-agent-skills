# SKU eligibility rules: starting checklist, not a source of prices

These are structural, slow-changing eligibility rules, the kind of thing that
doesn't move month to month. **Prices, SKU names, and message/Copilot Credit
mechanics move constantly and are never listed here.** Always verify a rule
below is still current before relying on it; official docs win over this file.

## Microsoft 365 Copilot (the add-on, Chat/Word/Excel/PowerPoint/Teams/Outlook)

- Requires an eligible base subscription first: Microsoft 365 Business
  Basic/Standard/Premium, Microsoft 365 E3/E5/E7, Microsoft 365 F1/F3, Office
  365 E1/E1 Plus/E3/E5, Office 365 F3, Microsoft 365/Office 365 A-series
  (education), or a qualifying Teams plan. No base plan, no Copilot add-on.
- The user's primary mailbox must be in Exchange Online. On-premises or
  hybrid mailboxes don't support Copilot's mailbox grounding.
- Microsoft 365 E7 already includes the Microsoft 365 Copilot add-on. Don't
  recommend buying it separately for an E7 tenant.
- Power Platform licensing (Power Apps, Power Automate premium connectors,
  Dataverse capacity) is **never** included with a Microsoft 365 Copilot
  license. It's always its own line item.

## Copilot Studio

Three separate paths. Check which one already fits before recommending a new
purchase:

1. **Included via Microsoft 365 Copilot license.** Agent capability used
   inside Microsoft 365 Copilot, Teams, or SharePoint (classic answers,
   generative answers, Graph tenant grounding) doesn't consume the separate
   Copilot Studio message/credit meter.
2. **Copilot Studio for Microsoft Teams plan.** A subset of Copilot Studio
   capability bundled into select Microsoft 365 + Power Platform + Teams
   subscriptions, for agents published to Teams using classic orchestration.
   Cheaper than standalone Copilot Studio but capability-limited. Confirm the
   use case fits before recommending it over the full product.
3. **Standalone Copilot Studio.** A free per-maker user license plus a
   prepaid Copilot Credit / message pack at the tenant level. Needed for
   generative orchestration, non-Teams channels, or capability beyond what the
   Teams plan bundle covers.

## Government cloud

GCC/GCC High/DoD availability and feature parity consistently lag commercial.
Never assume a commercial-cloud feature or price applies; verify separately
for the target cloud.

## When two paths tie

If a narrow, agent-only use case is covered equally by the Microsoft 365
Copilot add-on and by standalone Copilot Studio, the deciding factor is usually
whether the org already has (or needs) Microsoft 365 Copilot for other reasons.
Present the cost of each path rather than picking one.
