# Workspace Inventory Rules
## 1. Inventory scope
### 1.1 Explicit inventory required
Only listed systems/workspaces can appear in the checklist.
### 1.2 Missing is not empty
A missing inventory holds with `HOLD-MISSING-WORKSPACE-INVENTORY` and the checklist is empty. Only a well-formed header (every required column, #1.3) with no rows is an explicitly empty inventory, which means no requests; a zero-byte or whitespace-only file has no header and is malformed (#1.3). A missing or malformed inventory holds the wall stage as well as the checklist: `wall_check` sets the wall decision and the knowledge digest to hold, so no clear decision and no allowed-knowledge list is produced while the inventory is absent or unusable, and every later stage that re-derives the wall (`access_checklist`, `verify_render`) applies the same single check (`wall_check.inventory_problem`) and raises the same hold.
### 1.3 Malformed inventory holds
An inventory without `workspace_id`, `workspace_type`, `default_permission`, `depends_on_knowledge` and `data_classification` columns holds with `HOLD-MALFORMED-WORKSPACE-INVENTORY` (the wall decision and knowledge digest hold too, #1.2) and requests nothing, and so does an inventory that repeats a `workspace_id` on more than one row (compared in canonical ID form: NFKC, format characters stripped, case folded, whitespace and `-`/`_`/`.` separators folded; confidentiality-and-ethical-wall-rules.md #1.3), because a repeated key would let one row hide another's classification. Required columns are checked from the header, whether or not any rows follow. A row with a blank `workspace_id`, no requested or default permission, an unrecognised default permission, or more fields than the header is `not_requested_invalid_row` with a hold; permissions never fall back to a default. A `workspace_id` that is not an identifier (1-64 letters, digits, `.`, `_` or `-`; no spaces or prose; confidentiality-and-ethical-wall-rules.md #1.3) stops every stage with an input error that does not repeat it. A malformed inventory's original rows are screened for instructions and other clients before it is emptied, so a flagged or other-client cell still raises its own hold. A row with any cell naming another client or matter is that client's workspace: it is quarantined, never requested, denied, held or listed by its supplied ID or name, and named only by its positional hold (`raw/workspace-inventory.csv row N.<column>`; confidentiality-and-ethical-wall-rules.md #3.3). The row's grammar (identifier, permissions, classification, `depends_on_knowledge`, field count) is checked on its cells as read before it is quarantined or denied: an invalid other-client row also holds with `HOLD-INVALID-WORKSPACE-ROW` at `raw/workspace-inventory.csv row N` (fixed vocabulary, no cell value), and an invalid row the wall denies stays `denied_by_wall` and also holds.
## 2. Dependency on knowledge clearance
### 2.1 Prior-knowledge dependency
Workspaces marked dependent on prior knowledge inherit knowledge holds or denials.
### 2.2 Restricted workspace denial
Client-confidential or restricted workspaces are denied when wall rules deny the joiner. Workspace IDs are matched in canonical form, so a register denying `ws-a-plan` denies inventory `WS-A-PLAN`; held and name-withheld workspace IDs are matched the same way.
### 2.3 Unknown classification fails closed
Only `internal` and `public` are non-confidential, and only an explicit false/no/0 `depends_on_knowledge` is independent of prior knowledge. Blank or unrecognised values are treated as client-confidential and knowledge-dependent, escalated, and the row is `not_requested_invalid_row` with a hold.
## 3. Checklist output
### 3.1 Draft request only
The checklist describes draft requests and never provisions.
### 3.2 Excess requests flagged
Access above role ceiling, or an unrecognised requested permission, is `not_requested_exceeds_role`, never added.
### 3.3 Pending wall review holds the pack
The pack is `on_hold_internal_only` whenever there is an open hold, the wall decision is `hold`, or any workspace is `hold_pending_wall_review`; `mobilization_pack.hold_reasons` lists which.
