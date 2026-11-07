# Task and Phase Code Structure (illustrative, not UTBMS)

This is an invented code structure for demos. It resembles the kind of phase/task taxonomy used in professional services billing, but it is not the real UTBMS code set and should be replaced with the firm's controlled codes before production use.

## 1. Discovery phase
1.1 `DS100` - Client discovery interview or requirements elicitation.
1.2 `DS120` - Fact chronology, source review, and initial issue inventory.

## 2. Analysis phase
2.1 `AN200` - Document analysis tied to a client deliverable.
2.2 `AN220` - Research or options analysis supporting a client decision.

## 3. Delivery phase
3.1 `DL300` - Client meeting, workshop, or working session with stated purpose.
3.2 `DL320` - Drafting, revising, or finalizing a client deliverable.

## 4. Billing hygiene and non-billable administration
4.1 `NB900` - Internal staffing, time correction, billing administration, training, or non-client administrative activity.
4.2 `BH910` - Pre-bill review and WIP hygiene for internal use only.

## 5. Mapping confidence
5.1 Direct activity-class match to one phase/task code has confidence 0.92.
5.2 Keyword-only inference has confidence 0.78 and requires human review when a submitted code disagrees.
5.3 Unknown or conflicting signals map to `UNMAPPED` at confidence 0.40 and must be reviewed.
