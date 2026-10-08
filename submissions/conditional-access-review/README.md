# Conditional Access Review

Paste in an export of your Microsoft Entra Conditional Access policies and get
back a coverage matrix, a gap list, and a conflict/hygiene check, grounded in
Microsoft's own Conditional Access deployment guidance.

## What it checks

- **Coverage**: is MFA actually enforced (not just report-only) for all users,
  legacy auth blocked, high-risk sign-ins handled, admin roles protected,
  guests included?
- **Break-glass exclusion**: Microsoft's guidance is that every Conditional
  Access policy should exclude at least one emergency access account. This
  skill treats a missing exclusion as a standalone finding on its own, not just
  a detail of one policy.
- **Conflicts**: two policies covering the same scope with contradictory
  controls.
- **Hygiene**: redundant policies, generic names, broad exclusions with no
  stated rationale.

## Getting an export

```
GET https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies
```

via Graph Explorer or the Microsoft Graph PowerShell SDK
(`Get-MgIdentityConditionalAccessPolicy`). Strip any bearer token before
pasting. The policy JSON itself contains no secrets, but an API call copied
wholesale might.

## What it won't do

It never outputs a script that changes, disables, or deletes a policy. Every
recommendation is either a policy definition to review with a Conditional
Access Administrator, or the manual steps to take in the Entra admin center.
You make the change, not the skill. It also can't see real sign-in logs, risk
data, or actual group membership: everything is inferred from the exported
configuration.

## Reference

[Plan a Conditional Access deployment](https://learn.microsoft.com/entra/identity/conditional-access/plan-conditional-access)
· [Manage emergency access accounts](https://learn.microsoft.com/entra/identity/role-based-access-control/security-emergency-access)
· [Block legacy authentication](https://learn.microsoft.com/entra/identity/conditional-access/policy-block-legacy-authentication)

---

Skill by Tim Karlsson (╯°□°)╯︵ ┻━┻ Works 60% of the time, every time.
