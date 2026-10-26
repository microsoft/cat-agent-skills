# Change Rules (cited as change-rules.md #<n>; engine constants mirror these sections)
## 1. Impact classification
dimension_change / tolerance_relax / tolerance_tighten -> fit (function if the characteristic is an interface); material_change -> function; finish_change -> form (function if a note marks the surface critical); note_change -> form.
## 2. Interface rule
A change touching a characteristic on a part with any interface-critical where-used link is an INTERFACE VIOLATION candidate: the mating part relies on the current definition. Requires mating-part analysis and change-board review; never a "minor" change.
## 3. Document rule
Any dimensional or tolerance change updates EVERY drawing and inspection plan referencing the characteristic. A referencing document at an obsolete revision blocks release until updated.
## 4. Inventory disposition
form -> use-up permitted; fit -> use-up only with QE concurrence, WIP review required; function -> hold WIP and on-hand pending change-board decision.
## 5. Confidence floor
Where-used trace incomplete (missing parent links) -> confidence < 0.75, block the ECN, escalate to PLM data owner.
