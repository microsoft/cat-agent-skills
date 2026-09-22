# SOP Library — Standard Operating Procedures (controlled index)

Controlled index of the Standard Operating Procedures the Work Order Assistant retrieves and
grounds against. Each SOP lists the issue it addresses, its default remedy, the parts it calls for,
and the manual section that backs it. Cited in contract payloads as `sop-library.md #<section>`.

Grounded in site SOPs and OEM manuals. **An SOP default remedy is the starting point, not the
final answer** — where work-order history shows the default fix recurring, or a fix note supersedes
a listed part, the assistant surfaces the better remedy (`similar-work-rules.md` #3).

## 1. Gearbox oil-seal replacement — SOP-LUBE-07

- **Applies to:** conveyor / drive gearboxes presenting `oil_leak`, `seal_weep`, `high_temp`.
- **Default remedy:** replace the output-shaft oil seal, renew gear oil, replace the housing gasket;
  verify breather and oil level. Manual ref: Gearbox Manual GBX-40 §4.2.
- **Required parts:** `OS-45` output oil seal (x1), `GO-220` gear oil ISO VG220 (x4 L),
  `GK-12` housing gasket (x1).

## 2. Reciprocating-compressor intake-valve service — SOP-COMP-03

- **Applies to:** reciprocating air compressors presenting `low_discharge_pressure`, `unloading`,
  `short_cycling`, `valve_fault`.
- **Default remedy:** replace the intake valve kit, inspect the valve seat, reset unloader.
  Manual ref: Compressor Manual AC-90 §7.4.
- **Required parts:** `VK-100` intake valve kit (x1), `GS-88` valve cover gasket set (x1).
- **Note:** kit `VK-100` has a known premature-failure history on high-duty-cycle units; see fix
  notes and the parts catalog `superseded_by` column before ordering (`parts-readiness-rules.md` #2).

## 3. Mechanical-seal replacement — SOP-SEAL-02

- **Applies to:** pumps presenting `seal_weep`, `leak`, `low_flow`.
- **Default remedy:** replace the mechanical seal, inspect the shaft sleeve. Manual ref: Pump
  Manual CP-200 §6.1.
- **Required parts:** `MS-15` mechanical seal (x1), `SL-15` shaft sleeve (x1, if scored).

## 4. Bearing replacement — SOP-BRG-05

- **Applies to:** rotating equipment presenting `bearing_noise`, `vibration`, `high_temp`.
- **Default remedy:** replace bearings, verify lubrication and alignment. Manual ref: GBX-40 §6.3.
- **Required parts:** `BRG-30` bearing set (x1), grease `GR-2` (x1).

## 5. Using an SOP in a work-order write-up

1. Match the WO's issue keywords to the SOP that addresses them (this section index).
2. Carry the SOP's default remedy and required parts onto the contract as the **starting** plan.
3. Let `similar-work-rank` and `parts-readiness` test that plan against history and stock.
4. If a repeat-failure or a superseding part is found, the **next-best action** replaces the SOP
   default and the write-up flags that the SOP may need review.
