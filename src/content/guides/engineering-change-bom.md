# Engineering Change & BOM

For the change board or design engineer holding an ECR that "looks minor" and needs to know
what it actually touches before anyone approves it.

It reads the ECR, the spec or drawing delta and the BOM, traces impact across the BOM with
where-used, classifies form/fit/function impact, flags interface violations, rolls up document
and inventory dispositions, and drafts the ECN with the affected-item list.

## How it works

1. Reads the ECR, spec/drawing delta and BOM.
2. Traces where-used across the BOM and classifies form/fit/function impact (deterministic).
3. Checks the change against drawing standards and design rules.
4. Drafts the ECN with the affected-item list.

## Example scenario

"Minor tolerance relax, savings already booked, push it through this week." The requester
checked the obvious assembly and it was fine.

Where-used returns a second one — a legacy assembly with an **interface-critical** link, where a
press-fit mate depends on the tight bore the change is relaxing. That escalates the impact class
to *function* with an interface violation. On top of that, the inspection plan for the affected
part is sitting at an obsolete revision, which blocks release outright, and the relaxed
press-fit band breaks a documented design rule.

A naive reviewer approves the minor change. The engines block it, and say exactly why.

## What you bring

The ECR, the BOM, the affected drawings or specs, inventory status, and your document register.

## Boundaries

Draft-first: the ECN is a draft for the change board. No PLM write-back.
