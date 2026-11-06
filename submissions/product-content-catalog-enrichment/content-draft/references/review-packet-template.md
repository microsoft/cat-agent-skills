# Review / Approval Packet - <batch_id>  (STATUS: DRAFT - nothing published)
Supplier: <supplier> | Channel: <channel> | Market: <market> | Engines: <provenance.engines>

## 1. Blockers (lead the packet)
| # | GTIN | item | blocker | rule | owner |
|---|------|------|---------|------|-------|
| 1 | <gtin> | <name> | GS1 check digit INVALID - record BLOCKED, not corrected | #1.1 | data steward / supplier |
| 2 | <gtin> | <name> | "<claim>" regulated_blocked - <detail> | #4.2 / #4.3 | claim owner |
| 3 | batch | - | completeness average <avg>% below floor <floor>% | #3.2 | steward |
Routing: blocked claims present -> CLAIM OWNER first, then steward.

## 2. Excluded from copy
| GTIN | term | verdict | why |
|------|------|---------|-----|
| <gtin> | <term> | regulated_blocked | no substantiation for <market> (#4.2); never softened (#4.3) |
| <gtin> | <term> | unapproved | approved only for GTIN <other> (#4.1) / romance term (#4.4) |
Supplier requests to keep excluded wording are noted here and declined; supplier legal review is not substantiation (#4.1).

## 3. Approved claims available
| GTIN | claim | substantiation | markets |
|------|-------|----------------|---------|
(None if the library holds nothing for these GTINs.)

## 4. Draft records
| GTIN | status (DRAFT / BLOCKED) | completeness | missing fields | title |
|------|--------------------------|--------------|----------------|-------|

### SKU <gtin> - <name> - DRAFT
Title: <name> - <color> <material>, <net_weight_g> g
Bullets: Material: <material> [row n] · Colour: <color> [row n] · Net weight: <g> g (<oz> oz, #2.2) · Country of origin: <country>
Description (<= 80 words): <attributes + approved claims only; [GAP: field] inline>
Trace: every statement -> attribute (row) or approved finding (substantiation).

### SKU <gtin> - <name> - BLOCKED (invalid GTIN, #1.1)
Held draft: <attributes available> [GAP: ...]. Not published-pending. Unblock: valid GTIN from supplier; missing fields; claim-owner decisions.

## 5. Comparison copy (attribute-only, DRAFT)
<like-for-like on shared attributes; state plainly when no hygiene/environmental comparison is possible because such claims are blocked>

## 6. Steward actions
- [ ] Claim owner: decide on <n> blocked claims (add substantiation to the library, or confirm exclusion)
- [ ] Data steward: corrected GTIN for <gtin>; missing fields <list> from supplier
- [ ] Steward: approve DRAFT records <list>; SKU <gtin> stays BLOCKED
- [ ] No taxonomy change requested / <unmapped fields> for PIM steward

## 7. Routing
Claim owner -> data steward -> channel publish (outside this plugin).
