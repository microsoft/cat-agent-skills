# Greenwashing Detection Method

## Purpose

This procedure scans documents, web content, advertisements, labels, presentations, images, and social posts for potential greenwashing.

It uses:

- [Greenwashing-vocab.md](Greenwashing-vocab.md) as the controlled vocabulary and initial term-risk prior;
- [greenwashing-risk-taxonomy.md](greenwashing-risk-taxonomy.md) as the classification rules; and
- [greenwashing-analysis-research.md](greenwashing-analysis-research.md) as the jurisdictional baseline.

The scanner identifies risk for human review. It does not determine legal liability.

## Jurisdiction tags and finding behavior

| Tag | Scanner behavior |
|---|---|
| `ANY` | Always run. Detects vocabulary and claim-construction risks that would be problematic in any jurisdiction. |
| `CA` | Run for Canadian publication or audiences. Reports Canadian Competition Act and Competition Bureau issues. |
| `EU` | Run for EU publication or audiences. Reports EU consumer-law issues and date-dependent Directive (EU) 2024/825 prohibitions. |
| `UK` | Run for UK publication or audiences. Reports UK consumer-law and CMA issues. |

The scanner must emit separate findings for each tag. An `ANY` finding must not be mislabeled as an `EU`, `UK`, or `CA` legal violation. Conversely, passing the `ANY` vocabulary check does not prevent a regional violation.

## Required inputs

1. Content files or URLs.
2. Intended publication jurisdiction tags: `CA`, `EU`, `UK`, or all three for global content.
3. Publication date and channel.
4. Claim evidence, if available.
5. Product, service, business, campaign, and audience metadata.

If the jurisdiction is unknown, run `ANY`, `CA`, `EU`, and `UK`; mark regional applicability as unconfirmed and require jurisdiction review.

## End-to-end workflow

### Step 1: Ingest and normalize

- Extract text from DOCX, PDF, PPTX, HTML, spreadsheets, email, and social content.
- Use OCR for scanned pages and text embedded in images.
- Preserve page, slide, sheet, cell, paragraph, URL, and image coordinates.
- Extract alt text, captions, footnotes, disclaimers, hyperlinks, hashtags, product names, logos, and badge text.
- Normalize case, punctuation, hyphens, spelling variants, CO2 notation, and whitespace.
- Keep the original text for exact quotations.

### Step 2: Segment the content

Create analysis units at:

- headline;
- sentence;
- bullet;
- product tile;
- table row/cell;
- label or package panel;
- image plus adjacent text;
- claim plus its qualification, evidence link, or footnote.

Do not evaluate a sentence in isolation when the general impression depends on nearby imagery, headings, or fine print.

### Step 3: Detect candidate environmental claims

Flag a unit when it contains:

- a Red, Yellow, or Green term from [Greenwashing-vocab.md](Greenwashing-vocab.md);
- environmental entities such as emissions, climate, energy, water, waste, biodiversity, materials, sourcing, pollution, toxicity, durability, repairability, or circularity;
- comparative language: `less`, `lower`, `better`, `reduced`, `more`, `best`;
- future language: `will`, `target`, `goal`, `by 2030`, `net zero`;
- certification language, seals, badges, or approval imagery;
- implied environmental meaning from names, colours, icons, or nature imagery;
- a statement that downplays a negative impact.

### Step 4: Parse each claim

Extract:

| Field | Question |
|---|---|
| Claim text | What exact words and implied message are presented? |
| Claim subject | Product, component, packaging, service, facility, activity, brand, or whole business? |
| Environmental attribute | Carbon, energy, waste, water, materials, toxicity, biodiversity, sourcing, circularity, or other? |
| Claim type | Absolute, comparative, quantified, certification, disposal, future target, or neutrality? |
| Geography | Where is the claim and benefit applicable? |
| Period | What measurement or target period applies? |
| Lifecycle boundary | Sourcing, production, transport, use, end of life, or full lifecycle? |
| Comparator | Compared with what product, baseline, method, and period? |
| Qualification | Are conditions prominent and understandable? |
| Evidence reference | What report, test, standard, certificate, or dataset supports it? |

### Step 5: Apply the vocabulary prior

1. Match normalized terms and visual patterns against the `ANY` tables in [Greenwashing-vocab.md](Greenwashing-vocab.md).
2. Record every `ANY` match, not just the highest-risk match.
3. Match the content against the `CA`, `EU`, and `UK` regional overlays for the applicable markets.
4. Record vocabulary matches as `{term, tag, rating, rule}`.
5. Set a separate initial rating for each applicable tag.
6. Do not lower a Red term merely because a footnote exists; first determine whether the qualification changes the dominant impression.
7. A Green wording pattern is not automatically approved. It must pass the evidence, scope, and regional checks.

### Step 6: Run evidence checks

For every material claim, determine whether evidence:

- existed before publication;
- tests or measures the actual product, service, business, or activity claimed;
- uses a method fit for the claim;
- covers the same geography, period, conditions, and lifecycle boundary;
- supports the exact magnitude and wording;
- is current and version-controlled;
- is independent where certification or verification is represented;
- discloses assumptions, exclusions, uncertainty, and limitations;
- can be retrieved by reviewers.

Assign Red if required testing or substantiation is absent or unsuitable.

### Step 7: Run claim-quality checks

#### General impression

Compare the literal text with the impression created by:

- headline prominence;
- images and colour;
- logos and labels;
- nearby product grouping;
- omitted context;
- footnote size and placement.

#### Scope

Flag part-to-whole errors:

- packaging benefit presented as a product benefit;
- one facility presented as the whole company;
- one product line presented as the whole range;
- a short period presented as permanent performance.

#### Lifecycle

Check sourcing, production, distribution, use, maintenance, and end of life. Flag a claim when a material impact is omitted or shifted elsewhere.

#### Comparison

Require:

- named or clearly defined comparator;
- same function and use conditions;
- common method and assumptions;
- baseline year/version;
- measured difference;
- current information.

#### Future claims

Require:

- defined baseline and target boundary;
- measurable, time-bound interim milestones;
- implementation actions;
- allocated resources and accountable owner;
- progress measurement;
- corrective process;
- independent verification where required.

#### Labels

Verify:

- scheme owner;
- public criteria;
- third-party independence;
- certificate number and validity;
- certified product/site/process scope;
- monitoring and non-compliance process.

#### Carbon and offsets

Separate:

1. Gross emissions.
2. Direct value-chain reductions.
3. Residual emissions.
4. Removals.
5. Purchased credits or offsets.

For EU consumer-facing content from September 27, 2026, assign Red when a product neutrality, reduced-impact, or positive-impact claim is based on offsetting outside the product's value chain.

### Step 8: Apply jurisdiction rules

#### `ANY` - universal vocabulary and claim-quality checks

- Flag vague, absolute, exaggerated, or unsupported environmental language.
- Flag part-to-whole scope errors, material omissions, contradictory fine print, and unverified certification impressions.
- Flag weak or mismatched evidence, unfair comparisons, and undisclosed lifecycle boundaries.
- Use `ANY-*` finding codes from [greenwashing-risk-taxonomy.md](greenwashing-risk-taxonomy.md).

#### `CA` - Canada

- Evaluate literal meaning and general impression.
- Require adequate and proper testing for product environmental-benefit claims.
- Require adequate and proper substantiation for business or activity environmental-benefit claims.
- Treat vague, exaggerated, comparative, and unsupported future claims as escalation signals.
- Emit `CA-MISLEADING`, `CA-PRODUCT-TEST`, `CA-BUSINESS-SUBSTANTIATION`, `CA-COMPARISON`, or `CA-FUTURE` as applicable.

#### `EU` - European Union

For content used from September 27, 2026, apply Red overrides for:

- unsupported generic environmental claims;
- ineligible sustainability labels;
- part-to-whole claims;
- offset-based product greenhouse-gas neutrality/reduction/positive-impact claims;
- legal requirements presented as distinctive benefits.

Also flag future claims lacking a public, detailed, realistic, measurable, time-bound, independently verified plan.

Emit `EU-GENERIC`, `EU-LABEL`, `EU-SCOPE`, `EU-OFFSET-PRODUCT`, `EU-LEGAL-MINIMUM`, `EU-FUTURE`, or `EU-COMPARISON` as applicable. Store the effective date used in the finding.

#### `UK` - United Kingdom

Apply the CMA tests for truth, clarity, material omissions, fair comparisons, lifecycle consideration, and current credible evidence. Include supply-chain claims repeated by retailers, brands, platforms, and distributors.

Emit `UK-TRUTH`, `UK-CLARITY`, `UK-OMISSION`, `UK-COMPARISON`, `UK-LIFECYCLE`, `UK-EVIDENCE`, or `UK-SUPPLY-CHAIN` as applicable.

### Step 9: Assign the final rating

Use the deterministic rules in [greenwashing-risk-taxonomy.md](greenwashing-risk-taxonomy.md):

1. Create an `ANY` rating from universal vocabulary and claim-quality checks.
2. Create a separate rating for every applicable region: `CA`, `EU`, and/or `UK`.
3. Apply Red legal or evidence overrides only to the tag whose rule creates the override.
4. Raise each tag's risk for its applicable failures.
5. Assign Green only when all material dimensions pass for that tag.
6. Set `overall_risk_rating` to the highest tagged rating without discarding lower-rated or passed regional results.

## Optional numeric prioritization

Use this score only to order the review queue; the categorical override rules remain controlling.

| Factor | Points |
|---|---:|
| Red vocabulary or visual pattern | 20 |
| Yellow vocabulary | 8 |
| Missing or unsuitable evidence | 25 |
| Part-to-whole or unclear scope | 15 |
| Material lifecycle omission | 12 |
| Unfair or undefined comparison | 10 |
| Unsupported future target | 12 |
| Unverified label/certification | 15 |
| Offset-dependent neutrality claim | 20 |
| Hidden or contradictory qualification | 15 |

- **0-15:** Green candidate, subject to all mandatory checks.
- **16-39:** Yellow.
- **40 or more:** Red.
- Any Red override remains Red regardless of score.

## Required output

Produce one record per claim:

```json
{
  "source": "file-or-url",
  "location": "page/slide/sheet/cell/paragraph/coordinates",
  "claim_text": "Exact quoted claim",
  "implied_claim": "Environmental impression created by text and visuals",
  "vocabulary_matches": [
    {
      "term": "eco-friendly",
      "tag": "ANY",
      "rating": "Red",
      "rule": "ANY-VAGUE"
    }
  ],
  "claim_subject": "product|component|packaging|service|business|activity",
  "claim_type": "absolute|comparative|quantified|future|label|offset|disposal",
  "applicable_jurisdictions": ["CA", "EU", "UK"],
  "evidence_status": "verified|partial|missing|not_provided",
  "findings": [
    {
      "tag": "ANY",
      "finding_code": "ANY-VAGUE",
      "source_type": "vocabulary",
      "rating": "Red",
      "reason": "Generic whole-product claim"
    },
    {
      "tag": "EU",
      "finding_code": "EU-GENERIC",
      "source_type": "law",
      "rating": "Red",
      "effective_date": "2026-09-27",
      "reason": "Generic environmental claim without recognized excellent environmental performance"
    },
    {
      "tag": "CA",
      "finding_code": "CA-MISLEADING",
      "source_type": "law_and_guidance",
      "rating": "Yellow",
      "reason": "General impression requires evidence and scope review"
    },
    {
      "tag": "UK",
      "finding_code": "UK-CLARITY",
      "source_type": "law_and_guidance",
      "rating": "Yellow",
      "reason": "Claim is broad and ambiguous"
    }
  ],
  "overall_risk_rating": "Red",
  "required_action": "approve|revise|substantiate|remove|legal_review",
  "suggested_rewrite": "Specific, bounded alternative wording",
  "reviewer_notes": ""
}
```

## Rewrite method

For Yellow or Red wording, construct a safer claim using:

> **Measured attribute + exact subject/scope + value and unit + baseline/comparator + method/standard + period + material conditions/exclusions**

Example:

- **Original:** "Our new bottle is eco-friendly."
- **Rewrite:** "The bottle body contains 75% post-consumer recycled PET by weight; the cap and label are excluded. Composition verified using [method/report]."

Do not invent missing evidence, percentages, certifications, or environmental benefits. If support is unavailable, recommend removing the claim.

## Quality-control sampling

- Manually review all Red claims.
- Manually review all claims with certification, carbon neutrality, net-zero, recyclability, biodegradability, compostability, or future targets.
- Sample at least 20% of Yellow claims.
- Sample Green claims to test false-negative rates.
- Track reviewer disagreement by category and update [Greenwashing-vocab.md](Greenwashing-vocab.md) only through a documented governance process.

## Limitations

- Keyword matching cannot determine truth.
- Evidence quality often requires scientific, engineering, lifecycle, or legal expertise.
- Market infrastructure changes recyclability and compostability outcomes.
- Sector-specific rules may be stricter than this general framework.
- Translations can change claim meaning and must be reviewed in the publication language.
- Laws and regulatory guidance change; review the legal research before material deployments.
