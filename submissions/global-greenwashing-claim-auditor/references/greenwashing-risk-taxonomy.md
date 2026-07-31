# Greenwashing Risk Taxonomy

## Purpose

This taxonomy classifies public environmental claims as **Green**, **Yellow**, or **Red**. It uses [Greenwashing-vocab.md](Greenwashing-vocab.md) as its controlled term reference and [greenwashing-analysis-research.md](greenwashing-analysis-research.md) as its legal foundation.

The rating is a compliance triage result, not a final legal conclusion.

## Jurisdiction model

Every assessed claim receives separate findings:

- `ANY`: universal vocabulary, evidence, scope, omission, imagery, and lifecycle screening;
- `CA`: Canadian Competition Act and Competition Bureau checks;
- `EU`: EU consumer-law checks;
- `UK`: UK consumer-law and CMA checks.

Do not merge the results into an unexplained global violation. Report each applicable jurisdiction independently. `ANY` identifies broadly problematic claim construction; only `CA`, `EU`, and `UK` identify the regional legal, regulatory, or guidance basis.

## Rating definitions

### Green - lower apparent risk

A claim is Green when it is:

- specific, measurable, and understandable;
- explicitly bounded to the correct product, component, process, facility, geography, and period;
- supported by current, credible evidence obtained before publication;
- consistent with the overall visual and textual impression;
- transparent about material limitations and lifecycle boundaries;
- linked to an eligible certification when a label is used.

**Action:** Approve through the normal claims-review process and retain the evidence record.

### Yellow - material review required

A claim is Yellow when it may be accurate but has one or more unresolved issues:

- ambiguous vocabulary from the Yellow list;
- missing or hard-to-find qualifications;
- unclear product, lifecycle, geography, or time boundary;
- evidence exists but does not exactly match the public wording;
- a comparison lacks one element such as its baseline or period;
- a future target lacks some milestones, resources, verification, or progress data;
- recyclability, compostability, or disposal depends on consumer access or special conditions;
- imagery or a label may imply more than the text states.

**Action:** Do not publish unchanged. Clarify the claim, collect evidence, or escalate to a subject-matter reviewer.

### Red - high risk or presumptively unacceptable

A claim is Red when it:

- is false, materially misleading, or contradicted by available evidence;
- uses a Red vocabulary pattern without a narrow, prominent, and supportable meaning;
- lacks required testing or substantiation;
- makes an absolute or whole-product claim from a limited attribute;
- hides material environmental trade-offs or conditions;
- uses an unverified certification-style label;
- relies on fine print to reverse the dominant impression;
- makes an offset-based product neutrality claim in the EU;
- presents a legal requirement as a special environmental benefit;
- makes a future claim with no concrete, realistic, verifiable plan.

**Action:** Block publication and require legal/compliance review or removal.

## Claim dimensions

Score every claim across the following dimensions.

| Dimension | Green | Yellow | Red |
|---|---|---|---|
| Vocabulary | Green pattern | Yellow term or qualified Red term | Unqualified Red term/pattern |
| Truth and accuracy | Fully supported | Uncertainty or evidence gap | False or contradicted |
| General impression | Matches literal claim | Could imply a broader benefit | Materially broader than evidence |
| Evidence | Current, credible, claim-matched, pre-publication | Partial, dated, indirect, or inaccessible | Missing, fabricated, or methodologically unsuitable |
| Scope | Product part/process/place/time clearly stated | One boundary unclear | Part-to-whole or activity-to-business overreach |
| Magnitude | Quantified without exaggeration | Improvement presented imprecisely | Trivial benefit portrayed as major |
| Lifecycle | Material stages addressed or boundary disclosed | One material stage uncertain | Material burden is hidden or shifted |
| Comparison | Comparator, baseline, method, period, and magnitude stated | One or two elements missing | Unfair, incomparable, or unverifiable |
| Future target | Plan, resources, milestones, progress, verification | Incomplete plan or weak accountability | Aspiration without a credible plan |
| Carbon and offsets | Gross footprint and reductions separated from offsets | Offset quality or residual emissions unclear | EU product neutrality based on external offsets |
| Labels and certification | Public-authority or eligible third-party scheme verified | Scheme or scope not fully verified | Self-created or false certification impression |
| Conditions and disposal | Conditions prominent and realistic | Conditions are technically available but not prominent | Required conditions are omitted or unavailable |

## Risk categories

### 1. Vague virtue claims

Examples: `green`, `eco-friendly`, `sustainable`, `clean`, `conscious`.

- **Green:** The term is replaced by a measurable attribute.
- **Yellow:** The term is immediately and prominently defined.
- **Red:** The term stands alone or implies broad lifecycle superiority.

### 2. Absolute and zero-impact claims

Examples: `zero emissions`, `pollution-free`, `environmentally safe`, `100% sustainable`.

- **Green:** Operational boundary is explicit, such as "no tailpipe emissions during use."
- **Yellow:** A broad phrase is qualified but residual impacts remain unclear.
- **Red:** The claim is absolute across an undefined lifecycle or impact category.

### 3. Carbon-neutrality and offset claims

- **Green:** Gross emissions, direct reductions, residual emissions, offsets, boundary, period, and methodology are separately disclosed.
- **Yellow:** The footprint is measured but offset quality, permanence, or boundary is unclear.
- **Red:** A product is promoted in the EU as climate/carbon neutral, reduced, or positive based on offsets outside its value chain.

### 4. Recycled, recyclable, biodegradable, and compostable claims

- **Green:** Percentage, component, conditions, standard, timeframe, and infrastructure access are stated.
- **Yellow:** Technically possible but consumer access or disposal conditions are uncertain.
- **Red:** The claim implies a disposal benefit that is unavailable in practice or applies only to packaging/a component while appearing to cover the whole product.

### 5. Comparative claims

- **Green:** Same function, common method, identified comparator, baseline, geography, period, and material difference.
- **Yellow:** The comparison is plausible but one required element is missing.
- **Red:** Cherry-picked, obsolete, incomparable, or unsupported baseline.

### 6. Future commitments

Examples: `net zero by 2040`, `100% renewable by 2030`.

- **Green:** Public plan, baseline, interim targets, resources, governance, progress metrics, and independent review.
- **Yellow:** Target is credible but one or more implementation elements are incomplete.
- **Red:** No plan, no meaningful steps, reliance on speculative technology without disclosure, or progress materially off track without correction.

### 7. Sustainability labels and seals

- **Green:** Scheme owner, criteria, scope, certificate, validity, and independent monitoring are verified.
- **Yellow:** Scheme exists but product scope, validity, or chain of custody is unclear.
- **Red:** Self-awarded badge, false endorsement, expired certification, or a seal designed to mimic independent approval.

### 8. Omission and burden shifting

- **Green:** Material trade-offs and limitations are disclosed prominently.
- **Yellow:** The claimed benefit is real but another lifecycle effect may offset it.
- **Red:** The communication highlights a small benefit while hiding a material negative impact or shifting it to another stage, geography, or stakeholder.

### 9. Legally required features

- **Green:** Compliance is stated factually without competitive differentiation.
- **Yellow:** It is unclear whether the attribute exceeds the legal minimum.
- **Red:** A mandatory feature is marketed as a special environmental advantage.

## Regional violation taxonomy

| Finding code | Tag | Default risk | Trigger |
|---|---|---|---|
| `ANY-VAGUE` | `ANY` | Yellow; Red when unqualified and broad | Vague virtue term creates an undefined environmental benefit |
| `ANY-ABSOLUTE` | `ANY` | Red | Absolute, zero-impact, or universal superiority wording lacks a complete supportable boundary |
| `ANY-EVIDENCE` | `ANY` | Yellow or Red | Evidence is missing, weak, outdated, indirect, or mismatched |
| `ANY-SCOPE` | `ANY` | Red | Claim generalizes from a part, process, facility, activity, or period to a larger subject |
| `ANY-OMISSION` | `ANY` | Yellow or Red | Material condition, limitation, or trade-off is omitted |
| `ANY-LABEL` | `ANY` | Yellow or Red | Wording or imagery implies independent certification that is not established |
| `CA-MISLEADING` | `CA` | Red | Literal meaning or general impression is materially false or misleading |
| `CA-PRODUCT-TEST` | `CA` | Red | Product environmental-benefit claim lacks adequate and proper pre-claim testing |
| `CA-BUSINESS-SUBSTANTIATION` | `CA` | Red | Business/activity environmental-benefit claim lacks adequate and proper substantiation |
| `CA-COMPARISON` | `CA` | Yellow or Red | Comparator or extent of difference is unclear |
| `CA-FUTURE` | `CA` | Yellow or Red | Future goal lacks a concrete, realistic, verifiable plan, interim targets, or meaningful action |
| `EU-GENERIC` | `EU` | Red from 2026-09-27 | Generic environmental claim lacks relevant recognized excellent environmental performance |
| `EU-LABEL` | `EU` | Red from 2026-09-27 | Sustainability label lacks a qualifying certification scheme or public authority |
| `EU-SCOPE` | `EU` | Red from 2026-09-27 | Whole-product/business claim concerns only one aspect or unrepresentative activity |
| `EU-OFFSET-PRODUCT` | `EU` | Red from 2026-09-27 | Product GHG neutrality/reduction/positive-impact claim relies on offsets outside the value chain |
| `EU-LEGAL-MINIMUM` | `EU` | Red from 2026-09-27 | Mandatory category-wide legal requirement is advertised as distinctive |
| `EU-FUTURE` | `EU` | Red when required elements are absent | Future claim lacks public verifiable commitments, a detailed plan, measurable targets, resources, or independent review |
| `EU-COMPARISON` | `EU` | Yellow or Red | Environmental comparison omits method, compared subjects/suppliers, or update process |
| `UK-TRUTH` | `UK` | Red | Claim is untruthful or inaccurate |
| `UK-CLARITY` | `UK` | Yellow or Red | Claim is unclear or ambiguous |
| `UK-OMISSION` | `UK` | Yellow or Red | Important information is hidden or omitted |
| `UK-COMPARISON` | `UK` | Yellow or Red | Comparison is unfair, unclear, or not meaningful |
| `UK-LIFECYCLE` | `UK` | Yellow or Red | Claim fails to consider the full lifecycle where relevant |
| `UK-EVIDENCE` | `UK` | Red | Claim lacks up-to-date, credible evidence |
| `UK-SUPPLY-CHAIN` | `UK` | Red | A supply-chain participant originates or repeats a claim it cannot verify |

## Deterministic rating rules

Apply these rules in order:

1. **Red override:** Assign Red if any jurisdiction-specific prohibition or Red condition applies.
2. **Create the `ANY` result:** Apply vocabulary, evidence, scope, lifecycle, imagery, omission, label, and comparison checks.
3. **Create regional results:** Independently apply `CA`, `EU`, and/or `UK` rules for every intended market.
4. **Evidence override:** Assign Red if a material claim requiring testing/substantiation has no suitable pre-publication evidence.
5. **Context adjustment:** Raise risk for scope, lifecycle, comparison, imagery, omission, future-plan, label, or offset defects.
6. **Green threshold:** Assign Green only when all material dimensions pass for that specific tag.
7. **Yellow default:** Assign Yellow when the claim is not clearly Green and no Red override has been established.
8. **Overall rating:** Use the highest risk among the applicable tagged findings, while retaining every regional finding.

## Recommended evidence record

For each claim retain:

- exact approved wording and image;
- product/service/business scope;
- markets and jurisdictions;
- owner and approval date;
- evidence source, method, date, and version;
- baseline, comparator, assumptions, and exclusions;
- lifecycle boundary;
- certification details;
- conditions for use or disposal;
- future-plan milestones and latest progress;
- expiry or mandatory review date.

## Examples

| Claim | Tag | Finding | Rating | Reason |
|---|---|---|---|---|
| "Eco-friendly bottle" | `ANY` | `ANY-VAGUE` | Red | Generic whole-product impression with no defined benefit |
| "Eco-friendly bottle" used in the EU after 2026-09-27 | `EU` | `EU-GENERIC` | Red | Generic environmental claim lacks recognized excellent environmental performance |
| "Eco-friendly bottle" in Canada | `CA` | `CA-MISLEADING` | Yellow or Red | General impression may exceed the evidence |
| "Eco-friendly bottle" in the UK | `UK` | `UK-CLARITY` | Yellow or Red | Claim is broad and ambiguous |
| "Bottle body contains 75% post-consumer recycled PET by weight; cap and label excluded" | `ANY` | No violation found | Green | Quantified, scoped, and qualified |
| "Recyclable packaging" | `ANY` | `ANY-OMISSION` | Yellow | Collection and processing access must be established |
| "Recyclable packaging" sold in the UK without disposal conditions | `UK` | `UK-OMISSION` | Yellow or Red | Material consumer conditions may be hidden |
| "Carbon neutral delivery" based only on purchased credits | `EU` | `EU-OFFSET-PRODUCT` | Red when it is a product/service claim covered by the rule | Offset-based greenhouse-gas neutrality claim |
| "We aim to be net zero by 2040" with no plan | `CA` | `CA-FUTURE` | Red | Future claim lacks substantiation and a clear plan |
| "We aim to be net zero by 2040" with no plan | `EU` | `EU-FUTURE` | Red | Required commitment and implementation elements are absent |
| Company-designed green leaf saying "Certified Sustainable" | `ANY` | `ANY-LABEL` | Red | Unverified certification impression |
| Company-designed green leaf saying "Certified Sustainable" in the EU | `EU` | `EU-LABEL` | Red | Ineligible sustainability label |
| Supplier claim repeated by a UK retailer without verification | `UK` | `UK-SUPPLY-CHAIN` | Red | The repeating business cannot verify the claim |
