# Executed production examples

## Native media placement and export

`agents/create-agent/tests/skills/sales-production.test.ts` executes this skill's real
[production helper](../scripts/production.cjs) with installed PptxGenJS in Node.
The structural inputs are the repository's system-context PNG and direction SVG,
copied to a temporary workspace. They are engineering fixtures, not recommended
Sales visuals or evidence of executive-summary quality.

The executed sequence is:

```js
const plan = {
  tokens: { colors: { canvas: 'FFFFFF', ink: '172B4D' }, fonts: { body: 'Arial' } },
  slots: [
    { id: 'context', type: 'image', role: 'system context' },
    { id: 'direction', type: 'icon', role: 'next action' }
  ]
};
const guard = production(deck, plan, manifest);
const slide = deck.addSlide();
slide.addText('Evidence and next action', { x: 0.5, y: 0.3, w: 8, h: 0.5 });
guard.place('context', slide, { x: 0.5, y: 1, w: 6, h: 3 });
guard.place('direction', slide, { x: 7, y: 1, w: 1, h: 1 });
await deck.writeFile({ fileName: outputPath });
const evidence = guard.seal();
```

Here `deck` is a real PptxGenJS instance; `manifest` contains each slot's absolute
existing file path and `success: true`. ZIP inspection finds native slide text and
embedded PNG/SVG media. Evidence reports `placement-recorded`, one placement per
asset and the helper's actual SHA-256. Missing, failed, relative, empty, changed
or unplaced assets fail; a zero-width placement fails.

## Authorized text-only export

A second executed case uses no slots and exemptions for both image and icon,
each with `authority: 'user'` or `'host'` and the reason
`Text-only presentation required`. It exports native text and reports `exempted`
with no assets. A `model` authority is rejected. The test supplies an explicit
restriction; the model cannot manufacture that authority in a real request.

## Executive-summary acceptance boundary

These examples prove helper/export compatibility, not render quality or a
validated starter design. For an actual leadership summary, use source-backed
results, forecast uncertainty and decisions as the focal exhibits; preserve the
membership behind totals and the full decision/action lookup. Those checks,
host design selection, brand fidelity, successful workspace design Write then
separate full Read, and final rendering require the real task's evidence.
Tokens in the plan are not proof that every native object uses those tokens.
