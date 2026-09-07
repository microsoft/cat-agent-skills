# Greenwashing Vocabulary

**Purpose:** Controlled vocabulary for screening environmental claims. It is the core reference for [greenwashing-risk-taxonomy.md](greenwashing-risk-taxonomy.md) and [greenwashing-detection.md](greenwashing-detection.md).

## Jurisdiction tags

| Tag | Use |
|---|---|
| `ANY` | Vocabulary or presentation that is potentially problematic in any jurisdiction. This is a universal screening flag, not a claim that the same legal prohibition exists everywhere. |
| `CA` | Canadian Competition Act or Competition Bureau-specific concern. |
| `EU` | European Union-specific prohibition or requirement. |
| `UK` | United Kingdom consumer-law or CMA-specific concern. |

Unless a row says otherwise, every term in the Red and Yellow vocabulary tables is tagged `ANY`. A scanner must first create the `ANY` finding and then apply the regional overlays below. A single term can therefore have several tags.

## Important interpretation rule

A word is not greenwashing by itself. Ratings are **claim-risk priors**, not legal verdicts:

- **Green:** Usually lower risk because the wording is specific and bounded. Evidence is still required.
- **Yellow:** Ambiguous or highly context-dependent. Review evidence, scope, conditions, and overall impression.
- **Red:** Inherently broad, absolute, prohibited in some contexts, or strongly associated with misleading impressions. Escalate for manual review.

The complete claim, imagery, omissions, jurisdiction, evidence, and lifecycle impact can raise or lower the final rating.

## Red-rated terms and patterns (`ANY`)

| Term or pattern | Why it is high risk | Possible compliant alternative |
|---|---|---|
| `green` | Generic, undefined whole-product or whole-business impression | State the measured attribute and scope |
| `eco-friendly`, `environmentally friendly` | Implies broad environmental benefit, often across the lifecycle | "Packaging contains 80% post-consumer recycled fibre by weight" |
| `planet-friendly`, `earth-friendly`, `nature-friendly` | Emotional and unbounded environmental superiority | Describe the specific impact reduced |
| `environmentally safe`, `safe for the environment` | Absolute safety is rarely supportable across all impacts | Identify the tested substance, endpoint, and conditions |
| `zero impact`, `no environmental impact`, `impact-free` | Absolute claim across all environmental dimensions | Quantify the specific impact and boundary |
| `zero emissions`, `emissions-free` | Often omits upstream, energy, or lifecycle emissions | "No tailpipe emissions during operation" |
| `non-polluting`, `pollution-free` | Absolute and multi-dimensional | State the pollutant and test result |
| `100% sustainable`, `completely sustainable` | "Sustainable" is broad; absolute form magnifies the risk | Name the certified or measured attribute |
| `climate neutral`, `carbon neutral`, `CO2 neutral` | High-risk neutrality claim; product claims based on external offsets are prohibited in the EU from 2026-09-27 | Disclose measured footprint, reductions, boundary, and separate offsets |
| `carbon positive`, `climate positive`, `carbon negative` | Implies a net beneficial climate impact and requires unusually strong lifecycle evidence | Quantify removals and emissions separately |
| `net-zero product`, `net zero emissions` | Can imply zero lifecycle impact; often dependent on offsets or exclusions | Specify organizational boundary, target year, plan, and residual emissions |
| `guilt-free`, `conscious`, `responsible choice` | Implies broad environmental or ethical superiority without measurable content | State the concrete attribute |
| `chemical-free`, `toxin-free` | Scientifically overbroad unless the named chemical class is defined | "`X` not intentionally added; tested below `Y` limit" |
| `plastic-free` | High risk if coatings, components, labels, or packaging contain plastic | State the exact components covered |
| `waste-free`, `zero waste` | Often omits waste streams, geography, or diversion methods | State measured diversion rate and treatment hierarchy |
| `saves the planet`, `protects the planet` | Exaggerated causal impact | Quantify the demonstrated environmental outcome |
| `best for the environment`, `greenest`, `most sustainable` | Unqualified superiority claim | Identify comparator, method, market, and period |
| `certified green`, `eco-certified` without named scheme | May imply independent certification that does not exist | Name and link the eligible certification |
| self-created leaf, globe, recycling, or check-mark seal | Can create an unsupported certification impression | Clearly label as company information or use an eligible third-party label |
| environmental benefit that is legally required | Misrepresents mandatory compliance as a special benefit | Explain compliance without presenting it as differentiation |

## Region-specific vocabulary overlays

| Tag | Term or pattern | Regional treatment |
|---|---|---|
| `CA` | Any product environmental-benefit term | Requires adequate and proper testing supporting the exact product claim |
| `CA` | Any business/activity environmental-benefit term | Requires adequate and proper substantiation supporting the exact organization or activity claim |
| `CA` | `net zero by [year]`, `carbon neutral by [year]`, or another future goal | Requires a concrete, realistic, verifiable plan, interim targets, and meaningful steps |
| `CA` | `better`, `greener`, `less`, `reduced`, `more efficient` | Comparator and extent of difference should be specific |
| `CA` | Any term combined with broad green imagery or contradictory fine print | Evaluate the total general impression, not just literal wording |
| `EU` | `green`, `eco-friendly`, `environmentally friendly`, `biodegradable`, `biobased`, `energy efficient`, or similar generic term | Prohibited from 2026-09-27 unless recognized excellent environmental performance relevant to the claim is demonstrated |
| `EU` | `sustainable`, `responsible`, `conscious` | Particularly high risk because these may cover environmental and non-environmental characteristics; do not rely only on environmental performance |
| `EU` | `climate neutral`, `carbon neutral`, `CO2 neutral`, `carbon positive`, `climate positive`, `climate compensated`, `reduced climate impact` for a product | Prohibited from 2026-09-27 when based on greenhouse-gas offsetting outside the product's value chain |
| `EU` | `certified`, `verified`, `approved`, or a sustainability seal | Sustainability label must be established by a public authority or qualifying third-party certification scheme |
| `EU` | Whole-product or whole-business term supported only for packaging, a component, one facility, or an unrepresentative activity | Prohibited part-to-whole claim from 2026-09-27 |
| `EU` | `net zero by [year]` or another future performance claim | Requires public, objective, verifiable commitments; a detailed realistic plan; measurable time-bound targets; resources; and independent expert verification |
| `EU` | A legally mandatory environmental feature marketed as `special`, `green`, or `better` | Prohibited from 2026-09-27 when the legal requirement applies to all products in the category |
| `UK` | `green`, `eco-friendly`, `sustainable`, `natural`, or another broad term | Must be clear, accurate, and normally reflect the full lifecycle when it creates a broad lifecycle impression |
| `UK` | `recyclable`, `compostable`, `biodegradable`, `reusable` | Conditions, consumer action, and realistic infrastructure access must not be omitted |
| `UK` | `better`, `greener`, `less`, `reduced`, `most sustainable` | Comparison must be fair, meaningful, and clear |
| `UK` | `certified`, `verified`, supplier environmental claim, or third-party badge | Business repeating the claim must hold or obtain credible evidence; supplier assurance alone may be insufficient |
| `UK` | Any claim with a material caveat in small print, a link, or another page | Important information must not be hidden; the primary claim must remain clear and non-misleading |

### EU red-flag override (`EU`)

From September 27, 2026, treat the following EU consumer-facing practices as **Red regardless of supporting copy**:

- A generic environmental claim without recognized excellent environmental performance relevant to the claim.
- A sustainability label not established by a public authority or qualifying third-party certification scheme.
- A whole-product or whole-business claim that actually applies only to one aspect.
- A product greenhouse-gas neutrality, reduction, or positive-impact claim based on offsetting emissions outside the product's value chain.

## Yellow-rated terms and patterns (`ANY`)

| Term or pattern | Required review |
|---|---|
| `sustainable`, `sustainably sourced` | Define the environmental dimensions, chain-of-custody boundary, standard, and evidence |
| `natural`, `all natural` | Explain what natural means and why it produces an environmental benefit |
| `clean`, `cleaner` | Identify the pollutant, baseline, method, and scope |
| `low carbon`, `lower carbon`, `reduced carbon` | Provide a lifecycle boundary, baseline, period, units, and reduction percentage |
| `carbon conscious`, `climate smart` | Define the measurable attribute; avoid broad lifestyle implications |
| `net zero by [year]` | Require a realistic plan, interim targets, resources, progress reporting, and treatment of residual emissions |
| `renewable`, `made with renewable energy` | State percentage, facility/process boundary, time period, and certificate treatment |
| `recycled`, `made with recycled material` | State percentage by weight and whether it applies to product, component, or packaging |
| `recyclable` | Verify design and actual collection, sorting, and reprocessing availability in the target market |
| `biodegradable` | State medium, conditions, test standard, timeframe, and disposal route |
| `compostable` | Distinguish home from industrial composting and verify local access |
| `degradable`, `oxo-degradable` | Determine what remains after degradation and whether the claim creates a disposal benefit |
| `reusable`, `refillable` | Establish expected cycles, return/refill infrastructure, and break-even point |
| `circular`, `circular product` | Define material loops, retained value, recovery rate, and system boundary |
| `responsibly sourced`, `ethical`, `conscious` | Define criteria, verification, geography, and whether the claim is environmental, social, or both |
| `non-toxic`, `safer`, `healthy` | Identify hazard endpoints, exposure assumptions, comparison, and test basis |
| `organic`, `bio-based`, `plant-based` | Verify certification or composition and avoid implying lower lifecycle impact without evidence |
| `locally sourced`, `local` | Define distance/geography and do not assume local means lower impact |
| `energy efficient`, `water efficient` | State the recognized rating or measured baseline and use conditions |
| `reduced packaging`, `less waste` | Identify comparator, material, weight/volume change, and period |
| `offset`, `compensated`, `carbon credit` | Separate gross emissions, direct reductions, residual emissions, and credit details |
| `certified`, `verified`, `approved` | Name the body, standard, scope, certificate status, and public verification link |
| `up to X% less` | Check that typical results and qualifying conditions are prominent |
| `helps`, `supports`, `contributes to` | Confirm a demonstrable causal contribution and avoid using weak verbs to mask no evidence |

## Green-rated terms and patterns (`ANY`, subject to regional checks)

Green-rated wording should normally contain a **measured attribute + explicit scope + baseline or standard + period/conditions**.

| Preferred pattern | Example |
|---|---|
| Quantified recycled content | "Bottle body contains 75% post-consumer recycled PET by weight; cap and label excluded." |
| Bounded reduction | "Uses 18% less electricity per cycle than model X under test method Y." |
| Clear baseline and period | "Scope 1 and 2 emissions were 12% lower in FY2025 than the FY2022 baseline." |
| Operational boundary | "Produces no tailpipe emissions during use; electricity-generation emissions are not included." |
| Renewable-energy percentage | "The named facility matched 100% of its 2025 purchased electricity with renewable-energy certificates." |
| Qualified recyclability | "The uncoated paper carton is accepted in curbside paper programs serving 82% of Canadian households; remove the plastic spout." |
| Qualified compostability | "Certified industrially compostable to EN 13432; not suitable for home composting." |
| Specific sourcing certification | "Wood fibre is FSC Mix certified; certificate code and scope: [identifier]." |
| Specific ecolabel | "Certified under the EU Ecolabel for [product group], licence [identifier]." |
| Transparent comparison | "Packaging weight decreased from 40 g to 32 g per unit between the 2024 and 2025 designs." |
| Evidence-linked statement | "Test report [identifier], dated [date], supports this claim under [method]." |
| Bounded future target | "Reduce absolute Scope 1 and 2 emissions 50% by 2030 from a 2020 baseline; current reduction is 22%; plan and annual progress are linked." |

## Visual and contextual vocabulary (`ANY`)

Scanners must also flag non-text signals:

| Tag | Signal | Default rating |
|---|---|---|
| `ANY` | Unexplained leaf, tree, globe, water droplet, or recycling-loop icon | Yellow |
| `ANY` | Green or earth-tone branding combined with an environmental term | Yellow |
| `ANY`, `EU`, `UK` | Seal or badge that resembles third-party certification | Red unless verified; apply the applicable label rules |
| `ANY`, `CA`, `UK` | Nature imagery implying a whole-product benefit unsupported by the text | Yellow, or Red if materially misleading |
| `ANY`, `CA`, `UK` | Small-print qualification that contradicts a headline | Red |
| `ANY` | QR code or link to accessible evidence that supports the exact claim | Green evidence signal, but not a cure for a misleading headline |

## Term normalization

Detection should be case-insensitive and account for:

- hyphens and spaces: `eco-friendly`, `eco friendly`;
- spelling variants: `fiber/fibre`, `labeled/labelled`;
- carbon notation: `CO2`, `CO₂`, `CO2e`, `CO₂e`;
- inflections: `recycle`, `recycled`, `recyclable`;
- implied claims in product or campaign names;
- hashtags: `#sustainable`, `#green`, `#netzero`;
- combinations that increase risk, such as `100%` + `sustainable`, or `certified` + an unnamed seal.

## Sources

The ratings implement the screening principles documented in:

- [Greenwashing Legal and Regulatory Research](greenwashing-analysis-research.md)
- [Competition Bureau Canada guidance](https://competition-bureau.canada.ca/en/deceptive-marketing-practices/greenwashing-guidance-businesses)
- [EU Directive 2024/825](https://eur-lex.europa.eu/eli/dir/2024/825/oj/eng)
- [UK CMA Green Claims Code](https://www.gov.uk/government/publications/green-claims-code-making-environmental-claims/green-claims-and-your-business)
