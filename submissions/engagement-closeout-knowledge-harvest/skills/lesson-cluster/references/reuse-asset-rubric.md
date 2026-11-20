# Reuse & Asset Rubric - Engagement Closeout
Deterministic scoring rules consumed by `asset_identify.py` (rules in `closeout_core.py`). Scores identify reuse value only; they do not determine confidentiality clearance.

## 1. Generalisability
### 1.1 Weight
Generalisability is weighted at 35 percent of the reuse score. Assets that express a pattern, checklist, control, prompt, architecture or decision approach independent of a single client score highest.

## 2. Effort to recreate
### 2.1 Weight
Effort to recreate is weighted at 25 percent. Assets that took substantial expert effort, facilitation, design or review are more valuable to harvest than low-effort status artifacts.

## 3. Decay and shelf-life
### 3.1 Weight
Shelf-life is weighted at 20 percent. Assets expected to remain useful for 18 months or more score high; assets that decay in under six months score low.

## 4. Client-specific dependency
### 4.1 Weight
Client-specific dependency is weighted as a 20 percent penalty. Assets that depend on client-specific configuration, org design, data, tooling or commercial terms score lower even if they were useful in the engagement.

## 5. Recommendation bands
### 5.1 Shortlist
Reuse score >= 70 and scoring confidence >= 0.70 produces `shortlist` for the Govern step.
### 5.2 Retain internally
Reuse score >= 50 and < 70 produces `retain_for_internal_reference`.
### 5.3 Archive
Reuse score < 50 produces `archive_with_engagement`.

## 6. Completeness gaps
### 6.1 Required deliverables
A required deliverable not marked complete is a closeout gap. The final deliverable index must name the gap rather than treating the package as complete.
