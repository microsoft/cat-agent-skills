# EU Greenwashing Analysis

A skill that reviews product descriptions, marketing text, packaging copy, and
catalog entries for **greenwashing** — misleading or unsubstantiated
environmental claims — and produces a structured findings report aligned with
current EU rules:

- **EU Directive 2024/825** (amending the Unfair Commercial Practices
  Directive 2005/29/EC) — bans generic environmental claims that cannot be
  substantiated.
- **Green Claims Directive** (proposal COM/2023/166) — substantiation and
  communication requirements for explicit environmental claims.

## What it does

For any submitted text, the skill:

1. Extracts every environmental / sustainability claim.
2. Assesses each claim against seven greenwashing criteria (vagueness,
   life-cycle scope, verifiability, misleading comparison, offset reliance,
   unsupported labels, forward-looking wording).
3. Assigns a risk level per claim (🔴 High / 🟡 Medium / 🟢 Low).
4. Emits a standardized findings block per flagged claim with the exact quote,
   regulation reference, issue, and recommended correction.
5. Closes with a summary count, overall compliance posture, and top priority
   action.

If no environmental claims are found the skill returns
`"No environmental claims detected — Out of Scope."` and stops.

## When to use it

Trigger this skill when the user asks to:

- Review a product description, catalog entry, or landing page for
  greenwashing.
- Check marketing copy for EU environmental-claims compliance.
- Audit sustainability wording before publication.
- Rewrite a claim to be Green Claims Directive–compliant.

## When *not* to use it

- Non-environmental compliance reviews (accessibility, GDPR, medical claims).
- Country-specific environmental rules outside the EU (US FTC Green Guides,
  UK CMA Green Claims Code, etc.). This skill covers EU scope only.

## Output shape

Per flagged claim:

```
Product Claim: <quote>
Risk Level: 🔴 High / 🟡 Medium / 🟢 Low
Regulation Reference: <directive + article>
Issue: <what's wrong>
Recommended Correction: <compliant rewrite or action>
```

Plus a final summary with totals per risk level, overall compliance posture,
and the single most urgent corrective step.
