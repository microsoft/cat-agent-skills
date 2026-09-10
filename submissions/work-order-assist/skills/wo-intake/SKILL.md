---
name: wo-intake
description: Pulls the current work order and its asset context into the mfg.work-order-assist.v1 contract inputs. Use when the user says "assemble the work order packet", "pull up WO <id>", "get me everything for this work order", "work order for <asset>", or when a Work Order Assistant run begins.
license: MIT
metadata:
  version: "1.0"
  author: Microsoft Manufacturing Skills
  category: Maintenance
---

# Work-Order Intake

## Purpose
Turn the current work order and its asset record into structured contract inputs: the work-order
identity, the asset identity and criticality, the normalized issue keywords, the applicable SOP,
and the parts that SOP calls for. This is the entry payload every later skill builds on.

## When to use
- "Assemble the packet for WO-4507" / "pull up the work order for compressor C-500".
- "Get me everything I need for this work order."
- Start of any Work Order Assistant run.

## Inputs
- Work order (TXT / JSON / CMMS extract): WO id, asset, problem description, type.
- Asset register (XLSX / CSV): asset name, class (A/B/C), redundancy, location.
- Emits inputs for contract `mfg.work-order-assist.v1`.

## Steps
1. Resolve the asset tag in the asset register; carry its `asset_class`, `asset_criticality`,
   `redundancy`, and `location` onto the contract.
2. Map the free-text problem to the controlled `issue_keywords` vocabulary in
   `references/sop-library.md` / `references/similar-work-rules.md` #1 (e.g. "keeps unloading,
   low discharge" -> `unloading`, `low_discharge_pressure`). Never invent a keyword.
3. Select the SOP that addresses the issue (`references/sop-library.md`) and carry its
   `sop_ref` (doc, section, default_remedy) and `required_parts[]` onto the contract.
4. Produce `wo-intake.json` with `contract_version`, `work_order_id`, `asset_id`, `component`,
   `asset_criticality`, `issue_keywords[]`, `sop_ref`, `required_parts[]`, and an empty `history{}`.

## Output
`wo-intake.json` conforming to the contract inputs — the entry payload of the flow.

## Grounding requirements
Every issue keyword cites the source line (work order or problem note). Asset attributes cite the
asset-register row. The SOP and its required parts cite `references/sop-library.md`.

## Constraints
- Issue-keyword vocabulary is fixed by the references #1 — map, do not guess.
- Do not rank prior work or check parts here — that is the Analyze skills' job (engine/LLM split).
- Never fabricate an asset attribute; a missing tag or criticality is an escalation.

## Escalation / uncertainty
- Asset tag not found, criticality missing, or the issue un-mappable to an SOP: stop and ask the
  planner; record it in the contract `escalations[]`.
