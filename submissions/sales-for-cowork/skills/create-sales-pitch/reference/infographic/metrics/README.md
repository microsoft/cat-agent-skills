# Metrics and signed reconciliation

For original authoring and donor adaptation, preserve material precision in
displayed values, units and signs. Set and inspect number formats; accurate
caches/workbooks do not prevent displayed labels from rounding away meaning.

## KPI dashboard

Asset: `create-sales-pitch/reference/infographic/metrics/kpi-dashboard.pptx`.

- **Use:** related metrics with definitions, units, periods, source and comparison
  basis. Attainment requires compatible target/actual; forecasts need their state.
- **Adapt:** extract useful metrics/charts, emphasize one trend or number and
  reflow support. Do not shrink an entire dashboard into a small region or invent
  metrics to occupy its panels.
- **Preserve:** value/state pairing and evidence hierarchy, with each native chart's
  embedded workbook. Update data, formulas/ranges, caches, labels and geometry
  together. Nonnegative columns use a zero baseline.
- **Data/media:** remove unsupported targets or trends. An actual above target
  needs an actual/target comparison, not a negative donut remainder. Independent
  values do not form an attainment ring. Icons may identify useful concepts.

## Signed variance bridge

Asset: `create-sales-pitch/reference/infographic/metrics/signed-variance-bridge.pptx`.
Native shapes, not a native chart: no Excel Edit Data is implied.

- **Use:** complete compatible opening + signed drivers = closing, with unit,
  period and state. Causal driver wording needs causal evidence.
- **Adapt:** actual driver count and supporting label space. Keep fractional
  amounts visible; explanations are optional when they add meaning.
- **Preserve/recompute:** a common scale including zero, cumulative endpoints,
  signed floating drivers and connected totals. Each driver's incoming total is
  the previous outgoing total; its outgoing total includes its signed change.
  Draw that span and connect successive endpoints, including closing.
  Total bars start at zero; update every bar, connector and label.
  No independent nudging or minimum-height clamps for small values.
- **Fallback:** incomplete drivers are a partial signed comparison, not a complete
  Waterfall. Use a direct label/leader for tiny values without altering scale.
  No decorative imagery is needed.

Source identities and chart/shape distinctions are recorded in `../manifest.json`.
