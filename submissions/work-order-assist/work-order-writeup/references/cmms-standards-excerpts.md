# CMMS & Reliability Standards — controlled excerpts

Reference excerpts that ground the Work Order Assistant's assembly and prioritization language.
Paraphrased for internal use; cited in contract payloads as `cmms-standards-excerpts.md #<section>`.

## 1. Work-order documentation quality (CMMS/EAM best practice)

A complete work-order write-up carries, at minimum: the asset identity and location, the problem
statement, the applicable SOP/manual reference, the parts required (with stock status), the
similar past work considered, the recommended next action, and any open escalations. A write-up
that omits parts readiness or prior-work context forces the technician to re-search — the exact
waste this assistant removes.

## 2. Asset criticality (ISO 55000-aligned)

Assets are classed by consequence of failure:
- **Class A — critical:** failure stops production or trips a safety/utility system; often no
  installed redundancy. Work is expedited and parts shortages are escalated immediately.
- **Class B — essential:** failure degrades output or has partial redundancy.
- **Class C — non-critical:** failure is tolerable until the next planned window.

Criticality drives how hard a parts shortage or a recurring failure is escalated, not whether the
write-up is produced.

## 3. Recurring failure and root-cause analysis (RCM)

Reliability-centered maintenance holds that a corrective action which must be repeated on the same
asset for the same failure is not a solution — it is a deferred root cause. When the CMMS history
shows the same remedy applied three or more times with the fault returning, open a root-cause
analysis rather than repeating the remedy. The assistant enforces this in `similar-work-rules.md`
#3.1 and #4.3.

## 4. Storeroom & MRO coordination

Job readiness depends on parts availability. Before a work order is scheduled, its parts should be
confirmed in the storeroom or reserved/expedited. Superseded parts must be procured as their
current replacement, never re-ordered as the obsolete number. For class-A assets, any shortage is
communicated to the planner and storeroom lead so the job is expedited (`parts-readiness-rules.md`
#3.3).

## 5. Scope note

This assistant assembles and drafts; it does not schedule work, commit stock, or write back to the
CMMS/EAM. Those actions remain with the planner and the system of record. Auto-scheduling and
inventory commitment are a separate Wave 3 capability.
