---
name: conditional-access-review
description: >-
  Use this skill whenever the user shares an exported set of Microsoft Entra
  Conditional Access policies (Graph JSON, PowerShell export, or a pasted
  policy list) and asks for a review, gap analysis, or health check, before
  recommending any change to a Conditional Access policy.
---

Review a Conditional Access policy set from an export and report coverage
gaps, risky exclusions, conflicts, and configuration health, as
recommendations only.

## Instructions

1. Get the export. Accepted: Graph API JSON
   (`GET /identity/conditionalAccess/policies`), a PowerShell/Microsoft Graph
   PowerShell SDK export, or a clearly structured pasted list of policies with
   their conditions and controls. If what's given is missing conditions or
   grant controls, ask for the full export rather than guessing at what a
   policy does.

2. State this limit up front: this is a **review of the exported
   configuration**, not a live tenant assessment. It cannot see actual sign-in
   logs, real user/group membership, sign-in risk data, or which policies are
   actually enforcing vs. report-only in practice beyond what the export's
   `state` field says.

3. For every policy, resolve `state`: `enabled`, `disabled`, or
   `enabledForReportingButNotEnforced`. Treat report-only and disabled policies
   as providing **zero** enforced coverage. Call this out explicitly wherever
   the user's tenant coverage looks fine only because a report-only policy is
   being counted.

4. Build a coverage matrix: which combinations of user population, app or
   resource, and sign-in risk actually have an enforced grant control, and
   which don't. Call out the standard high-value coverage checks by name:
   - MFA required for all users (or all admins, at minimum) on all cloud apps
   - Legacy authentication blocked
   - High-risk sign-ins and high-risk users blocked or forced to secure
     password change
   - Device compliance or hybrid-join required for sensitive apps
   - Admin roles covered by phishing-resistant MFA or Privileged Identity
     Management-gated access

5. Check for the following, reporting every hit:
   - **Exclusions**: any policy excluding a broad group (e.g. "All Users" minus
     a large security group) without an emergency access account rationale.
     Flag any policy that does *not* exclude a break-glass/emergency access
     account, since Microsoft's guidance is to exclude those accounts from
     every Conditional Access policy.
   - **No emergency access accounts found at all** in any policy's exclusions.
     Flag this as a standalone finding regardless of individual policy design.
   - **Conflicts**: two policies targeting the same scope with contradictory
     grant controls (one blocks, one grants) where evaluation order or an
     "OR" of controls could produce a weaker-than-intended result.
   - **Redundant policies**: multiple enabled policies enforcing the same
     control on the same scope. A maintenance and audit-trail risk even when
     harmless today.
   - **Guest/external user coverage**: whether external users are covered by
     the same or an equivalent baseline as internal users.
   - **Naming**: policies with generic names (`Policy1`, `CA01`) that make the
     tenant harder to audit.

6. Report findings by severity (Gap, Conflict, Hygiene), each as one row:

   | Severity | Finding | Affected policies | Recommendation |
   | --- | --- | --- | --- |
   | Gap | No enforced MFA policy covers guest users | none | Add guests to the MFA baseline policy or create a guest-specific policy |

   Close with a short "what's covered well" note. A review that only lists
   problems reads as less trustworthy than one that also confirms what's solid.

7. Recommendations are prose and example policy JSON/steps only. Never claim to
   have made a change.

## Guardrails

- Never ask the user to paste credentials, access tokens, or client secrets.
  The Graph export itself contains no secrets. If the user offers to paste an
  API call including a bearer token, tell them to strip it first.
- Never output a script or instruction whose effect is to change, disable, or
  delete a tenant's Conditional Access policy. Output the *recommended policy
  definition* or the *manual steps a Conditional Access Administrator would
  take*. The user or their admin executes it, not this skill.
- Always flag missing break-glass account exclusion, even if nothing else in
  the review turns up an issue.
- Don't speculate about why a policy was configured a certain way. Describe
  what it does, not the intent behind it, unless the user explains the intent.

## Tone

Direct and audit-style: finding, evidence from the export, concrete
recommendation. No alarmism. A coverage gap is a fact, not a crisis, unless
it's a genuinely severe one (no MFA baseline at all, no break-glass exclusion
anywhere).
