#!/usr/bin/env python3
"""
Generic Scrollytelling Story Builder
=====================================
Usage:  python3 build_story.py <path_to_file> [output_dir]
Input:  .xlsx / .xls / .csv / .json
        (for this reference script, convert PDF tables to .xlsx/.csv first)
Output: A single self-contained, scroll-driven HTML story file.

Auto-detects:
  - Primary entity column  (the "who" or "what")
  - Primary metric column  (the "how much")
  - Secondary metric       (enables scatter/bubble chapter)
  - Time column            (enables trend chapter)
  - Geography column       (enables choropleth map chapter)
  - Category columns       (enables distribution chapter)

Chapters rendered depend on what is detected:
  Always:    Hero · Stats · Top-N bar · Hall of Fame · Top-5 records · Takeaways · Epilogue
  If geo:    Choropleth map (world ISO-3 / country names, or US states)
  If cat:    Category distribution chapter (chart type chosen by data)
  If time:   Trend over time (dual-axis line chart)
  If scatter: Entity volume vs secondary metric (bubble chart)

Rules followed:
  - Stat card data-suffix is always a short unit (M, B, k, %) — never prose or ranges
  - Full rendered stat string (prefix + number + suffix) kept ≤ 6 chars for .s-card
  - Wide dollar totals use .s-card-wide
  - Two separate IntersectionObservers: one for .reveal, one for counters
  - Charts rendered lazily (only when scrolled into view)
  - renderCategoryBar() and renderScatterBubble() helpers used for all bar/scatter charts
"""

import json, sys, re, math, sqlite3
import pandas as pd
from pathlib import Path

# ── 0. CLI ─────────────────────────────────────────────────────────────────────
if len(sys.argv) < 2:
    print(__doc__)
    sys.exit(1)

src     = Path(sys.argv[1])
out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/app/created")
out_dir.mkdir(parents=True, exist_ok=True)

# ── 1. Load ────────────────────────────────────────────────────────────────────
ext = src.suffix.lower()
if ext in ('.xlsx', '.xls'):
    sheets = pd.read_excel(src, sheet_name=None)
elif ext == '.csv':
    sheets = {'data': pd.read_csv(src)}
elif ext == '.json':
    sheets = {'data': pd.read_json(src)}
else:
    raise ValueError(f"Unsupported file type: {ext}")

# Primary sheet = largest by row count
primary_name, primary_df = max(sheets.items(), key=lambda kv: len(kv[1]))

# Load all sheets into SQLite for aggregations
conn = sqlite3.connect(':memory:')
for name, sdf in sheets.items():
    sdf.to_sql(re.sub(r'\W+', '_', name), conn, index=False)

def q(sql):
    return pd.read_sql_query(sql, conn)

# Auto-join secondary sheets onto primary via any shared column name
def build_joined(primary, sheets, primary_name):
    result = primary.copy()
    for name, sdf in sheets.items():
        if name == primary_name:
            continue
        shared = [c for c in sdf.columns if c in result.columns]
        if shared:
            new_cols = [c for c in sdf.columns if c not in result.columns]
            if new_cols:
                try:
                    result = result.merge(sdf[[shared[0]] + new_cols],
                                          on=shared[0], how='left')
                except Exception:
                    pass
    return result

df = build_joined(primary_df, sheets, primary_name)

# Drop rollup / grand-total summary rows (e.g. a State="Total" row) so they don't
# dominate rankings, double-count totals, or break geo matching.
_ROLLUP = {'total', 'totals', 'grand total', 'all', 'sum', 'overall'}
_obj_cols = df.select_dtypes(include='object').columns
if len(_obj_cols):
    _mask = df[_obj_cols].apply(
        lambda c: c.astype(str).str.strip().str.lower().isin(_ROLLUP)
    ).any(axis=1)
    df = df[~_mask].reset_index(drop=True)

df.to_sql('_main', conn, index=False, if_exists='replace')

def qm(sql):
    return pd.read_sql_query(sql.replace('FROM _tbl', 'FROM _main'), conn)

def sc(col):
    """Safe-quote a column name for SQLite."""
    return f'"{col}"'

def f0(v):
    """Float coercion with NULL/NaN safety for SQLite aggregates."""
    try:
        if pd.isna(v):
            return 0.0
    except Exception:
        pass
    try:
        return float(v)
    except Exception:
        return 0.0

# ── 2. Schema Detection ────────────────────────────────────────────────────────
US_STATES = {
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA',
    'KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
    'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT',
    'VA','WA','WV','WI','WY','DC'
}

US_STATE_NAMES = {
    'alabama':'AL','alaska':'AK','arizona':'AZ','arkansas':'AR','california':'CA',
    'colorado':'CO','connecticut':'CT','delaware':'DE','florida':'FL','georgia':'GA',
    'hawaii':'HI','idaho':'ID','illinois':'IL','indiana':'IN','iowa':'IA',
    'kansas':'KS','kentucky':'KY','louisiana':'LA','maine':'ME','maryland':'MD',
    'massachusetts':'MA','michigan':'MI','minnesota':'MN','mississippi':'MS',
    'missouri':'MO','montana':'MT','nebraska':'NE','nevada':'NV','new hampshire':'NH',
    'new jersey':'NJ','new mexico':'NM','new york':'NY','north carolina':'NC',
    'north dakota':'ND','ohio':'OH','oklahoma':'OK','oregon':'OR','pennsylvania':'PA',
    'rhode island':'RI','south carolina':'SC','south dakota':'SD','tennessee':'TN',
    'texas':'TX','utah':'UT','vermont':'VT','virginia':'VA','washington':'WA',
    'west virginia':'WV','wisconsin':'WI','wyoming':'WY','district of columbia':'DC',
}

def detect_schema(df):
    s = {
        'entity_col':       None,   # primary categorical: the "who/what"
        'metric_col':       None,   # primary numeric: the "how much"
        'secondary_metric': None,   # second numeric: enables scatter chapter
        'time_col':         None,   # temporal: enables trend chapter
        'time_is_year':     False,  # True = integer year column
        'geo_col':          None,   # geographic: enables map chapter
        'geo_type':         None,   # 'iso3' | 'us_state' | 'country_name'
        'cat_cols':         [],     # other low-cardinality categoricals
        'num_cols':         [],
        'total_rows':       len(df),
    }

    nums = df.select_dtypes(include='number').columns.tolist()
    s['num_cols'] = nums

    # ── Time column ────────────────────────────────────────────────────────────
    time_kw = ('year','date','month','time','period','quarter','week','yr')
    for col in df.columns:
        cl = col.lower()
        if any(kw in cl for kw in time_kw):
            if col in nums:
                med = df[col].dropna().median()
                if 1900 < med < 2200:
                    s['time_col'] = col
                    s['time_is_year'] = True
                    break
            else:
                try:
                    pd.to_datetime(df[col].dropna().iloc[:5])
                    s['time_col'] = col
                    break
                except Exception:
                    pass

    # ── Geography column ────────────────────────────────────────────────────────
    geo_kw = ('country', 'state', 'nation', 'code', 'iso', 'location')
    for col in df.columns:
        if col in nums:
            continue
        cl = col.lower()
        if not any(kw in cl for kw in geo_kw):
            continue
        vals = [str(v).strip() for v in df[col].dropna().unique()[:25] if v]
        if not vals:
            continue
        sample = vals[:10]
        sample_upper = [v.upper() for v in sample]
        # ISO-3 (e.g. BRA, VNM)
        if all(re.match(r'^[A-Z]{3}$', v) for v in sample_upper):
            s['geo_col'] = col; s['geo_type'] = 'iso3'; break
        # US 2-letter state codes
        if all(len(v) == 2 and v in US_STATES for v in sample_upper):
            s['geo_col'] = col; s['geo_type'] = 'us_state'; break
        # Full US state names (e.g. Alabama, California) → converted to codes later
        if all(v.strip().lower() in US_STATE_NAMES for v in sample):
            s['geo_col'] = col; s['geo_type'] = 'us_state'
            s['geo_name_to_code'] = True; break
        # Country names
        if 'country' in cl or 'nation' in cl:
            s['geo_col'] = col; s['geo_type'] = 'country_name'; break

    # ── Categorical columns ────────────────────────────────────────────────────
    skip = {s['geo_col'], s['time_col']}
    id_kw = ('id', '_id', 'key', 'index', 'num', 'no.')
    is_id_like = lambda col: any(col.lower().endswith(kw) or col.lower() == kw for kw in id_kw)
    cats = []
    for col in df.columns:
        if col in nums or col in skip:
            continue
        nu = df[col].nunique()
        if 2 <= nu <= 200:
            cats.append((col, nu))
    # High-cardinality order helps pick a useful primary entity.
    cats.sort(key=lambda x: x[1], reverse=True)
    # Category chapters should avoid identifier fields and prefer segment-style columns.
    non_id_cats = [(c, nu) for c, nu in cats if not is_id_like(c)]
    non_id_cats.sort(key=lambda x: x[1])  # lower-cardinality first for clearer distributions
    s['cat_cols'] = [c for c, _ in non_id_cats]

    # Entity = highest-cardinality categorical that isn't a plain ID column
    for col, nu in cats:
        if col in skip:
            continue
        if is_id_like(col):
            continue
        if nu >= 3:
            s['entity_col'] = col; break
    if not s['entity_col']:
        s['entity_col'] = s['geo_col']

    # ── Metric column ──────────────────────────────────────────────────────────
    metric_kw = ('value','amount','revenue','cost','sales','total','volume',
                 'export','import','spend','budget','price','usd','dollar','sum')
    best, best_sc = None, -1
    for col in nums:
        cl = col.lower()
        ks = sum(2 for kw in metric_kw if kw in cl)
        try:
            mag = math.log10(max(abs(float(df[col].dropna().median())), 1)) * 0.05
        except Exception:
            mag = 0
        total_sc = ks + mag
        if total_sc > best_sc:
            best_sc = total_sc; best = col
    if not best and nums:
        best = nums[0]
    s['metric_col'] = best

    others = [c for c in nums if c != best]
    if others:
        s['secondary_metric'] = others[0]

    return s


schema = detect_schema(df)
E  = schema['entity_col']
M  = schema['metric_col']
T  = schema['time_col']
G  = schema['geo_col']

# ── 3. Aggregations ────────────────────────────────────────────────────────────
A = {}

# Totals
row = qm(f'SELECT COUNT(*) c, SUM({sc(M)}) s, AVG({sc(M)}) av FROM _tbl').iloc[0]
A['total_count']  = int(row['c'])
A['total_metric'] = f0(row['s'])
A['avg_metric']   = f0(row['av'])

# Unique entity count
if E:
    A['entity_count'] = int(qm(f'SELECT COUNT(DISTINCT {sc(E)}) n FROM _tbl').iloc[0]['n'])

# Top 15 entities by metric sum
if E:
    top = qm(f'''
        SELECT {sc(E)} ent, SUM({sc(M)}) total, COUNT(*) cnt
        FROM _tbl GROUP BY {sc(E)} ORDER BY total DESC LIMIT 15
    ''')
    A['top15_names']    = top['ent'].astype(str).tolist()
    A['top15_values']   = [round(f0(v), 2) for v in top['total']]
    A['top15_counts']   = [int(v) for v in top['cnt']]
    A['top10_names']    = A['top15_names'][:10]
    A['top10_values']   = A['top15_values'][:10]
    if A['top15_names']:
        A['top_entity']     = A['top15_names'][0]
        A['top_entity_val'] = A['top15_values'][0]
        A['top_entity_pct'] = (
            round(A['top_entity_val'] / A['total_metric'] * 100, 1)
            if A['total_metric'] else 0.0
        )
    else:
        A['top_entity'] = '—'
        A['top_entity_val'] = 0.0
        A['top_entity_pct'] = 0.0

# Category distributions (first 2 non-entity categoricals, top 10 values each)
A['cat_data'] = {}
for col in [c for c in schema['cat_cols'] if c != E][:2]:
    cd = qm(f'''
        SELECT {sc(col)} cat, SUM({sc(M)}) val, COUNT(*) cnt
        FROM _tbl GROUP BY {sc(col)} ORDER BY val DESC LIMIT 10
    ''')
    A['cat_data'][col] = {
        'labels': cd['cat'].astype(str).tolist(),
        'values': [round(f0(v), 2) for v in cd['val']],
        'counts': [int(v) for v in cd['cnt']],
    }

# Time trend
if T:
    tr = qm(f'''
        SELECT {sc(T)} period, SUM({sc(M)}) total, COUNT(*) cnt, AVG({sc(M)}) avg_v
        FROM _tbl GROUP BY {sc(T)} ORDER BY {sc(T)}
    ''')
    A['trend_x']   = [str(v) for v in tr['period'].tolist()]
    A['trend_y']   = [round(f0(v), 2) for v in tr['total']]
    A['trend_cnt'] = [int(v) for v in tr['cnt']]
    A['trend_avg'] = [round(f0(v), 4) for v in tr['avg_v']]

# Geography
if G:
    gd = qm(f'''
        SELECT {sc(G)} geo, SUM({sc(M)}) val
        FROM _tbl GROUP BY {sc(G)} ORDER BY val DESC
    ''')
    A['geo_names']  = gd['geo'].astype(str).tolist()
    if schema.get('geo_name_to_code'):
        A['geo_codes'] = [US_STATE_NAMES.get(n.strip().lower(), n) for n in A['geo_names']]
    else:
        A['geo_codes'] = list(A['geo_names'])
    A['geo_values'] = [round(f0(v), 2) for v in gd['val']]

# Scatter: entity vs secondary metric
M2 = schema['secondary_metric']
if E and M2:
    sc2 = qm(f'''
        SELECT {sc(E)} ent, SUM({sc(M)}) xv, AVG({sc(M2)}) yv
        FROM _tbl GROUP BY {sc(E)} ORDER BY xv DESC LIMIT 10
    ''')
    A['scatter_entities'] = sc2['ent'].astype(str).tolist()
    A['scatter_x']        = [round(f0(v), 4) for v in sc2['xv']]
    A['scatter_y']        = [round(f0(v), 4) for v in sc2['yv']]

# Top 5 records by metric (keep only the most useful columns)
keep_cols = [c for c in [E, M, T, G, M2] if c] + \
            [c for c in schema['cat_cols'] if c != E][:2]
keep_cols = list(dict.fromkeys(keep_cols))  # dedupe, preserve order
top5_df = qm(f'SELECT * FROM _tbl ORDER BY {sc(M)} DESC LIMIT 5')
A['top5'] = top5_df[keep_cols].fillna('').to_dict(orient='records')

conn.close()

# ── 4. Formatting helpers ──────────────────────────────────────────────────────
is_currency = any(kw in (M or '').lower()
                  for kw in ('value','revenue','cost','price','spend','amount',
                              'usd','dollar','export','import'))
mpfx = '$' if is_currency else ''   # metric prefix

def fmt(v, decimals=1):
    """Human-readable metric value: 407_600_000_000 → '$407.6B'"""
    av = abs(v)
    if av >= 1e12: return f"{mpfx}{v/1e12:.{decimals}f}T"
    if av >= 1e9:  return f"{mpfx}{v/1e9:.{decimals}f}B"
    if av >= 1e6:  return f"{mpfx}{v/1e6:.{decimals}f}M"
    if av >= 1e3:  return f"{mpfx}{v/1e3:.{decimals}f}k"
    return f"{mpfx}{v:,.{decimals}f}"

def stat_counter_attrs(value):
    """
    Return (data-prefix, data-target, data-suffix) for a stat card counter.
    Suffix is always a short unit (B, M, k) — never prose. The full rendered
    string (prefix + target + suffix) is kept ≤ 6 chars so it fits a .s-card.
    """
    av = abs(value)
    pre = mpfx
    if av >= 1e9:   return pre, int(round(value / 1e9)),  'B'
    if av >= 1e6:   return pre, int(round(value / 1e6)),  'M'
    if av >= 1e3:   return pre, int(round(value / 1e3)),  'k'
    return pre, int(round(value)), ''

def s_card(value, label, delay=0.0, wide=False, raw_target=None,
           raw_prefix='', raw_suffix=''):
    """
    Render a stat card div.
    Pass raw_target to override value-based encoding (e.g. plain integer counts).
    """
    if raw_target is not None:
        pre, tgt, sfx = raw_prefix, raw_target, raw_suffix
    else:
        pre, tgt, sfx = stat_counter_attrs(value)
    cls = 's-card-wide' if wide else 's-card'
    dly = f' style="transition-delay:{delay:.1f}s"' if delay else ''
    return (f'<div class="{cls} reveal"{dly}>'
            f'<div class="num" data-prefix="{pre}" data-target="{tgt}"'
            f' data-suffix="{sfx}">0</div>'
            f'<div class="s-label">{label}</div></div>')

# Human-readable labels derived from detected column names
def col_label(col):
    if not col: return ''
    return (col.replace('_',' ').replace('(USD)','').replace('(tons)','')
               .replace('  ',' ').strip().title())

ds_name    = re.sub(r'[-_]+', ' ', src.stem).title()
entity_lbl = col_label(E) or 'Record'
metric_lbl = col_label(M) or 'Value'
time_lbl   = col_label(T) or 'Period'
geo_lbl    = col_label(G) or 'Location'
M2_lbl     = col_label(M2) or 'Secondary Metric'

def js_esc(s):
    """Escape a Python string for safe embedding inside a single-quoted JS string.
    A bare apostrophe (e.g. "Who's Buying") otherwise closes the string and throws a
    SyntaxError that silently kills the entire <script> block — blank charts + zero counters."""
    return str(s).replace('\\', '\\\\').replace("'", "\\'").replace('\n', ' ')

# JS-safe copies of every label that gets interpolated into a single-quoted JS string.
metric_lbl_js = js_esc(metric_lbl)
time_lbl_js   = js_esc(time_lbl)
M2_lbl_js     = js_esc(M2_lbl)
metric_prefix_js = js_esc(mpfx)

# ── 5. Chapter content ─────────────────────────────────────────────────────────
has_geo     = bool(G and A.get('geo_codes'))
has_trend   = bool(T and A.get('trend_x') and len(A['trend_x']) >= 3)
has_cat     = bool(A.get('cat_data'))
has_scatter = bool(A.get('scatter_x') and len(A['scatter_x']) > 4 and M2)

top_ent     = A.get('top_entity', '—')
top_ent_val = A.get('top_entity_val', 0)
top_ent_pct = A.get('top_entity_pct', 0)
total_fmt   = fmt(A['total_metric'])

# Chapter counter
_ch = 0
def ch():
    global _ch
    _ch += 1
    return f"Chapter {_ch:02d}"

# ── Stat splash ────────────────────────────────────────────────────────────────
stat_rows = []
row1 = s_card(0, 'Total Records', 0.0, raw_target=A['total_count'])
if E and 'entity_count' in A:
    row1 += s_card(0, f'Unique {entity_lbl}s', 0.1, raw_target=A['entity_count'])
stat_rows.append(f'<div class="stat-row">{row1}</div>')

# Wide card for the big dollar/metric total
stat_rows.append(f'<div class="stat-row">{s_card(A["total_metric"], f"Total {metric_lbl}", 0.2, wide=True)}</div>')

# Row 3: top entity + time range (if available)
row3 = ''
if 'top_entity_val' in A:
    row3 += s_card(top_ent_val, f'#1 {entity_lbl}: {top_ent}', 0.3)
if has_trend:
    row3 += (f'<div class="s-card reveal" style="transition-delay:.4s">'
             f'<div class="num">{A["trend_x"][0]}–{A["trend_x"][-1]}</div>'
             f'<div class="s-label">{time_lbl} Range</div></div>')
if row3:
    stat_rows.append(f'<div class="stat-row">{row3}</div>')

stat_html = '\n'.join(stat_rows)

# ── Top entities chapter ───────────────────────────────────────────────────────
top_ch_num = ch()
top_second = A['top15_names'][1] if len(A.get('top15_names', [])) > 1 else '—'
top_second_val = fmt(A['top15_values'][1]) if len(A.get('top15_values', [])) > 1 else ''
top_ch = f"""
<section class="chapter" id="ch-top" data-chapter="{top_ch_num}">
  <div class="c-inner flip">
    <div class="reveal" style="transition-delay:.2s">
      <div class="c-num">{top_ch_num}</div>
      <h2 class="c-head">{top_ent} leads —<br>by a <em>wide margin.</em></h2>
      <p class="c-body">
        When ranked by {metric_lbl.lower()}, <strong>{top_ent}</strong> sits at the top with
        <strong>{fmt(top_ent_val)}</strong> — a <strong>{top_ent_pct}%</strong> share of the
        {total_fmt} total. <strong>{top_second}</strong> is the next closest at {top_second_val},
        making the gap between first and second place hard to ignore.
      </p>
    </div>
    <div class="chart-box reveal">
      <div id="topChart" style="height:520px"></div>
    </div>
  </div>
</section>"""

# ── Map chapter ────────────────────────────────────────────────────────────────
map_ch_num = ch() if has_geo else None
if has_geo:
    gt = schema['geo_type']
    geo_scope = ('usa' if gt == 'us_state'
                 else 'world')
    geo_lmode = ('USA-states' if gt == 'us_state'
                 else 'ISO-3' if gt == 'iso3'
                 else 'country names')
    map_ch = f"""
<section class="chapter" id="ch-map" data-chapter="{map_ch_num}">
  <div class="c-inner full">
    <div class="reveal">
      <div class="c-num">{map_ch_num}</div>
      <h2 class="c-head">Where it all<br><em>comes from.</em></h2>
      <p class="c-body">
        Mapped by total {metric_lbl.lower()}, the geographic picture shows both where activity
        concentrates and where the long tail of smaller contributors fills in the edges.
        <strong>{A['geo_names'][0]}</strong> commands the largest footprint —
        {fmt(A['geo_values'][0])} — with the distribution skewing heavily toward the top few.
      </p>
    </div>
    <div class="chart-box reveal" style="transition-delay:.2s">
      <div id="mapChart" style="height:600px"></div>
    </div>
  </div>
</section>"""
else:
    map_ch = ''

# ── Category chapter ───────────────────────────────────────────────────────────
cat_ch_num = ch() if has_cat else None
if has_cat:
    first_cat_col  = list(A['cat_data'].keys())[0]
    first_cat_data = A['cat_data'][first_cat_col]
    top_cat_label  = first_cat_data['labels'][0]
    top_cat_val    = fmt(first_cat_data['values'][0])
    cat_col_label  = col_label(first_cat_col)
    cat_ch = f"""
<section class="chapter" id="ch-cat" data-chapter="{cat_ch_num}">
  <div class="c-inner">
    <div class="reveal">
      <div class="c-num">{cat_ch_num}</div>
      <h2 class="c-head">Not all {cat_col_label.lower()}s<br>are <em>equal.</em></h2>
      <p class="c-body">
        Breaking down by <strong>{cat_col_label}</strong>, <strong>{top_cat_label}</strong> accounts
        for the biggest share of {metric_lbl.lower()} at {top_cat_val}.
        The distribution below reveals which segments drive the majority of activity
        and which are minor contributors — a gap that's often larger than it looks in summary tables.
      </p>
    </div>
    <div class="chart-box reveal" style="transition-delay:.2s">
      <div id="catChart" style="height:460px"></div>
    </div>
  </div>
</section>"""
else:
    cat_ch = ''

# ── Scatter chapter ────────────────────────────────────────────────────────────
scat_ch_num = ch() if has_scatter else None
if has_scatter:
    scat_ch = f"""
<section class="chapter" id="ch-scat" data-chapter="{scat_ch_num}">
  <div class="c-inner flip">
    <div class="reveal" style="transition-delay:.2s">
      <div class="c-num">{scat_ch_num}</div>
      <h2 class="c-head">Volume vs.<br><em>{M2_lbl}.</em></h2>
      <p class="c-body">
        Plotting each <strong>{entity_lbl.lower()}</strong> by its total {metric_lbl.lower()} against
        its average {M2_lbl.lower()} reveals how the two metrics relate — and where
        <strong>the outliers live.</strong> Bubble size reflects total {metric_lbl.lower()}.
        Leaders in volume and leaders in {M2_lbl.lower()} are often <em>not</em> the same.
      </p>
    </div>
    <div class="chart-box reveal">
      <div id="scatChart" style="height:480px"></div>
    </div>
  </div>
</section>"""
else:
    scat_ch = ''

# ── Trend chapter ──────────────────────────────────────────────────────────────
trend_ch_num = ch() if has_trend else None
if has_trend:
    t_start = A['trend_x'][0]
    t_end   = A['trend_x'][-1]
    t_peak_idx = A['trend_y'].index(max(A['trend_y']))
    t_peak_period = A['trend_x'][t_peak_idx]
    t_peak_val    = fmt(A['trend_y'][t_peak_idx])
    trend_ch = f"""
<section class="chapter" id="ch-trend" data-chapter="{trend_ch_num}">
  <div class="c-inner full">
    <div class="reveal">
      <div class="c-num">{trend_ch_num}</div>
      <h2 class="c-head">How the numbers<br>moved over <em>time.</em></h2>
      <p class="c-body" style="max-width:680px">
        From <strong>{t_start}</strong> to <strong>{t_end}</strong>, total {metric_lbl.lower()} and
        average {M2_lbl.lower() if M2 else metric_lbl.lower()} per record tell different stories.
        The peak came in <strong>{t_peak_period}</strong> at {t_peak_val} —
        tracing this line reveals whether growth has been steady, cyclical, or punctuated by spikes.
      </p>
    </div>
    <div class="chart-box reveal" style="transition-delay:.2s;margin-top:2rem">
      <div id="trendChart" style="height:460px"></div>
    </div>
  </div>
</section>"""
else:
    trend_ch = ''

# ── Hall of fame chapter ───────────────────────────────────────────────────────
hall_ch_num = ch()
hall_ch = f"""
<div class="divider"><div class="divider-line"></div><div class="divider-text">The Champions</div></div>
<section class="chapter" id="ch-hall" data-chapter="{hall_ch_num}">
  <div class="c-inner full">
    <div class="reveal">
      <div class="c-num">{hall_ch_num}</div>
      <h2 class="c-head">Hall of <em>Champions.</em></h2>
      <p class="c-body">
        The top 10 <strong>{entity_lbl.lower()}s</strong> ranked by total {metric_lbl.lower()}.
        <strong>{top_ent}</strong> leads the field with {fmt(top_ent_val)}.
      </p>
    </div>
    <div id="hall-list" style="max-width:780px;margin:2rem auto 0"></div>
  </div>
</section>"""

# ── Top 5 records chapter ──────────────────────────────────────────────────────
rec_ch_num = ch()
rec_cards  = ''
for i, rec in enumerate(A['top5']):
    fields = ''.join(
        f'<span><span class="i-label">{col_label(k)}</span>'
        f'<strong>{fmt(v) if isinstance(v, (int,float)) and k == M else v}</strong></span>'
        for k, v in rec.items() if v != ''
    )
    rec_cards += f"""
      <div class="i-card reveal" style="transition-delay:{i*0.1:.1f}s">
        <div class="i-rank">#{i+1}</div>
        <div class="i-val">{fmt(rec.get(M, 0))}</div>
        <div class="i-entity">{rec.get(E,'')}</div>
        <div class="i-fields">{fields}</div>
      </div>"""

rec_ch = f"""
<div class="divider"><div class="divider-line"></div><div class="divider-text">Record Highs</div></div>
<section class="chapter" id="ch-rec" data-chapter="{rec_ch_num}">
  <div class="c-inner full">
    <div class="reveal">
      <div class="c-num">{rec_ch_num}</div>
      <h2 class="c-head">The top 5 individual<br><em>records.</em></h2>
      <p class="c-body">
        The five highest-value single records in the dataset — each one a peak moment
        worth examining up close.
      </p>
    </div>
    <div class="i-grid">{rec_cards}</div>
  </div>
</section>"""

# ── Takeaways chapter ─────────────────────────────────────────────────────────
tk_ch_num = ch()
# Build data-driven takeaways from what we know
takeaways = []
if 'top_entity_pct' in A:
    takeaways.append((
        '01', f'{top_ent} dominates.',
        f'<strong>{top_ent}</strong> accounts for {top_ent_pct}% of total {metric_lbl.lower()} '
        f'({fmt(top_ent_val)}). That level of concentration shapes the entire market.'))
if 'entity_count' in A:
    tail_count = A['entity_count'] - 3
    tail_txt = (f'The remaining {tail_count} {entity_lbl.lower()}s share the rest.'
                if tail_count > 0 else '')
    takeaways.append((
        '02', f'The top 3 carry most of the weight.',
        f'The top 3 {entity_lbl.lower()}s together account for '
        f'{round(sum(A["top15_values"][:3]) / A["total_metric"] * 100)}% '
        f'of all {metric_lbl.lower()}. {tail_txt}'))
if has_cat and A['cat_data']:
    ccol = list(A['cat_data'].keys())[0]
    cdat = A['cat_data'][ccol]
    takeaways.append((
        '03', f'{col_label(ccol)} splits tell the real story.',
        f'Within <strong>{col_label(ccol)}</strong>, <strong>{cdat["labels"][0]}</strong> leads '
        f'({fmt(cdat["values"][0])}), while <strong>{cdat["labels"][-1]}</strong> '
        f'trails at {fmt(cdat["values"][-1])}. '
        f'The gap between top and bottom is {round(cdat["values"][0]/max(cdat["values"][-1],1), 1)}×.'))
if has_trend:
    pct_change = ((A['trend_y'][-1] - A['trend_y'][0]) / max(abs(A['trend_y'][0]), 1) * 100)
    direction  = 'risen' if pct_change > 0 else 'fallen'
    takeaways.append((
        '04', f'The trend is {("up" if pct_change > 0 else "down")}.',
        f'Total {metric_lbl.lower()} has <strong>{direction} {abs(pct_change):.1f}%</strong> '
        f'from {A["trend_x"][0]} to {A["trend_x"][-1]} ({fmt(A["trend_y"][0])} → '
        f'{fmt(A["trend_y"][-1])}). '
        f'{"That momentum shows no sign of reversing." if pct_change > 0 else "Recovery will require structural change."}'))
if has_scatter:
    takeaways.append((
        '05', f'Scale and {M2_lbl.lower()} don\'t always align.',
        f'The highest-volume {entity_lbl.lower()}s don\'t automatically lead on '
        f'{M2_lbl.lower()}. '
        f'Smaller players often punch above their weight on quality metrics '
        f'while the biggest names compete on sheer volume.'))

tk_cards = ''
for i, (num, title, body) in enumerate(takeaways[:5]):
    tk_cards += (f'<div class="t-card reveal" style="transition-delay:{i*0.1:.1f}s">'
                 f'<div class="t-index">{num}</div>'
                 f'<h3>{title}</h3><p>{body}</p></div>')

tk_ch = f"""
<div class="divider"><div class="divider-line"></div><div class="divider-text">What It Means</div></div>
<section class="chapter" id="ch-tk" data-chapter="{tk_ch_num}">
  <div class="c-inner full">
    <div class="reveal">
      <div class="c-num">{tk_ch_num}</div>
      <h2 class="c-head">What to <em>remember.</em></h2>
      <p class="c-body">The five findings that define this dataset.</p>
    </div>
    <div class="takeaway-grid">{tk_cards}</div>
    <div class="next-steps reveal" style="transition-delay:.6s">
      <strong>Bottom line:</strong>
      {A['total_count']:,} records. {total_fmt} total {metric_lbl.lower()}.
      {A.get('entity_count', '—')} unique {entity_lbl.lower()}s.
      The data has spoken.
    </div>
  </div>
</section>"""

# ── 6. JS chart builders ───────────────────────────────────────────────────────
# Inject all aggregation data as a single JS constant
js_data = json.dumps(A).replace('</', '<\\/')

# Category chart: use renderCategoryBar helper
cat_js_calls = ''
if has_cat:
    ccol = list(A['cat_data'].keys())[0]
    cat_js_calls = f"""
  if (id==='ch-cat') {{
    renderCategoryBar('catChart',
      D.cat_data['{js_esc(ccol)}'].labels,
      D.cat_data['{js_esc(ccol)}'].values,
      {{xTitle: '{metric_lbl_js}', unit: ''}});
  }}"""

# Map JS
map_geo_type = schema.get('geo_type','iso3')
if map_geo_type == 'us_state':
    locationmode = 'USA-states'
    geo_cfg = "scope:'usa', bgcolor:'#111', landcolor:'#1a1a1a', showsubunits:true, subunitcolor:'#2a2a2a'"
elif map_geo_type == 'country_name':
    locationmode = 'country names'
    geo_cfg = "scope:'world', bgcolor:'#111', landcolor:'#1a1a1a', showcountries:true, countrycolor:'#2a2a2a', projection:{type:'natural earth'}"
else:  # iso3
    locationmode = 'ISO-3'
    geo_cfg = "scope:'world', bgcolor:'#111', landcolor:'#1a1a1a', showcountries:true, countrycolor:'#2a2a2a', projection:{type:'natural earth'}"

map_js = f"""
  if (id==='ch-map') {{
    Plotly.newPlot('mapChart', [{{
      type:'choropleth', locationmode:'{locationmode}',
      locations: D.geo_codes, z: D.geo_values,
      colorscale:[['0','#14001a'],['0.2','#3d0a33'],['0.5','#a855f7'],['0.8','#ff5fa2'],['1','#2ee6a6']],
      colorbar:{{title:{{text:'{metric_lbl_js}',font:{{color:'#bbb'}}}}, tickfont:{{color:'#bbb'}}}},
      hovertemplate:'%{{location}}: %{{z:,.0f}}<extra></extra>'
    }}], {{
      ...BG, geo:{{{geo_cfg}}}, margin:{{t:10,b:10,l:0,r:0}}
    }}, CFG);
  }}""" if has_geo else ''

# Scatter JS
scat_js = f"""
  if (id==='ch-scat') {{
    renderScatterBubble('scatChart', D.scatter_entities, D.scatter_x, D.scatter_y,
      {{xTitle:'{metric_lbl_js}', yTitle:'{M2_lbl_js}', size: D.scatter_x}});
  }}""" if has_scatter else ''

# Trend JS
trend_js = f"""
  if (id==='ch-trend') {{
    Plotly.newPlot('trendChart', [
      {{type:'scatter', mode:'lines+markers', name:'Total {metric_lbl_js}',
        x:D.trend_x, y:D.trend_y,
        line:{{color:'#ff5fa2',width:2.5}}, marker:{{size:6,color:'#ff5fa2'}},
        hovertemplate:'%{{x}}: %{{y:,.2f}}<extra></extra>'}},
      {{type:'scatter', mode:'lines+markers', name:'Avg {M2_lbl_js if M2 else metric_lbl_js} / record',
        x:D.trend_x, y:D.trend_avg, yaxis:'y2',
        line:{{color:'#2ee6a6',width:2,dash:'dot'}}, marker:{{size:5,color:'#2ee6a6'}},
        hovertemplate:'%{{x}}: %{{y:.4f}}<extra></extra>'}}
    ], {{
      ...BG,
      xaxis:{{...BG.xaxis, title:'{time_lbl_js}', type:'category'}},
      yaxis:{{...BG.yaxis, title:'Total {metric_lbl_js}'}},
      yaxis2:{{title:'Avg / record', overlaying:'y', side:'right',
        gridcolor:'transparent', tickfont:{{color:'#2ee6a6'}},
        titlefont:{{color:'#2ee6a6'}}, linecolor:'#2a2a2a'}},
      legend:{{x:.02,y:.98,font:{{color:'#bbb'}},bgcolor:'rgba(0,0,0,0)'}},
      margin:{{t:20,b:55,l:70,r:80}}
    }}, CFG);
  }}""" if has_trend else ''

# ── 7. Assemble HTML ───────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{ds_name} — Data Story</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --fire:#ff5fa2; --ember:#a855f7; --gold:#2ee6a6;
  --text:#f0ede8; --muted:#999; --card:#161616; --border:#252525;
}}
html{{scroll-behavior:smooth}}
body{{background:#0a0a0a;color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;overflow-x:hidden}}
#prog-bar{{position:fixed;top:0;left:0;height:3px;width:0%;
  background:linear-gradient(90deg,var(--fire),var(--gold));z-index:1000;transition:width .1s}}
#ch-tag{{position:fixed;top:10px;right:16px;font-size:.7rem;color:var(--muted);
  letter-spacing:.08em;z-index:1000;text-transform:uppercase}}
/* HERO */
#hero{{min-height:100vh;display:flex;flex-direction:column;align-items:center;
  justify-content:center;text-align:center;padding:2rem;
  background:radial-gradient(ellipse at 50% 40%,#14001a 0%,#0a0a0a 70%)}}
.hero-eyebrow{{font-size:.75rem;letter-spacing:.25em;color:var(--fire);
  text-transform:uppercase;margin-bottom:1.5rem}}
.hero-title{{font-size:clamp(3rem,8vw,6.5rem);font-weight:900;line-height:1.0;
  letter-spacing:-.03em;margin-bottom:1.5rem}}
.hero-title em{{font-style:normal;color:var(--fire)}}
.hero-sub{{font-size:clamp(1rem,2.5vw,1.3rem);color:var(--muted);max-width:600px;
  line-height:1.6;margin-bottom:3rem}}
.scroll-cue{{display:flex;flex-direction:column;align-items:center;gap:.5rem;
  color:var(--muted);font-size:.8rem;animation:bob 2s ease-in-out infinite}}
@keyframes bob{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(8px)}}}}
/* STATS */
#stats{{padding:6rem 2rem;background:#0d0d0d;text-align:center}}
.stat-eyebrow{{font-size:.7rem;letter-spacing:.2em;color:var(--fire);
  text-transform:uppercase;margin-bottom:3rem}}
.stat-row{{display:flex;flex-wrap:wrap;justify-content:center;gap:1.5rem;margin-bottom:1.5rem}}
.s-card{{background:var(--card);border:1px solid var(--border);border-radius:12px;
  padding:2rem 2.5rem;flex:1;min-width:220px;max-width:320px}}
.s-card-wide{{background:var(--card);border:1px solid var(--border);
  border-left:3px solid var(--fire);border-radius:12px;padding:2rem 3rem;
  width:100%;max-width:440px;margin:0 auto}}
.num{{font-size:clamp(2rem,5vw,3rem);font-weight:900;color:var(--fire);line-height:1}}
.s-card-wide .num{{font-size:clamp(2.2rem,5vw,3.5rem)}}
.s-label{{font-size:.75rem;color:var(--muted);text-transform:uppercase;
  letter-spacing:.1em;margin-top:.5rem}}
/* CHAPTERS */
.chapter{{padding:6rem 2rem}}
.chapter:nth-child(odd){{background:#0a0a0a}}
.chapter:nth-child(even){{background:#0d0d0d}}
.c-inner{{display:grid;grid-template-columns:1fr 1.4fr;gap:4rem;
  max-width:1200px;margin:0 auto;align-items:center}}
.c-inner.flip{{grid-template-columns:1.4fr 1fr}}
.c-inner.flip .reveal:first-child{{order:2}}
.c-inner.flip .chart-box{{order:1}}
.c-inner.full{{grid-template-columns:1fr;max-width:1060px}}
.c-num{{font-size:.7rem;letter-spacing:.2em;color:var(--fire);
  text-transform:uppercase;margin-bottom:1rem}}
.c-head{{font-size:clamp(2rem,4vw,3.2rem);font-weight:900;line-height:1.1;
  letter-spacing:-.02em;margin-bottom:1.2rem}}
.c-head em{{font-style:normal;color:var(--fire)}}
.c-body{{font-size:1.05rem;line-height:1.75;color:#ccc}}
.c-body strong{{color:var(--text)}}
.chart-box{{background:#111;border:1px solid var(--border);border-radius:12px;
  padding:1.2rem;overflow:hidden}}
/* REVEAL */
.reveal{{opacity:0;transform:translateY(28px);transition:opacity .65s ease,transform .65s ease}}
.reveal.vis{{opacity:1;transform:translateY(0)}}
/* DIVIDER */
.divider{{padding:3rem 2rem;text-align:center;background:#0a0a0a}}
.divider-line{{width:60px;height:2px;background:linear-gradient(90deg,var(--fire),var(--gold));
  margin:0 auto 1.5rem}}
.divider-text{{font-size:.7rem;letter-spacing:.25em;color:var(--muted);text-transform:uppercase}}
/* HALL OF FAME */
.s-row{{display:flex;align-items:center;gap:1rem;padding:.85rem 1.2rem;
  background:var(--card);border:1px solid var(--border);border-radius:8px;margin-bottom:.6rem;
  opacity:0;transform:translateX(-30px);transition:opacity .4s ease,transform .4s ease}}
.s-row.vis{{opacity:1;transform:translateX(0)}}
.s-rank{{font-size:.7rem;color:var(--muted);min-width:24px;text-align:right}}
.s-name{{font-weight:700;min-width:110px;font-size:.95rem}}
.s-bar-wrap{{flex:1;background:#1a1a1a;border-radius:4px;height:8px;overflow:hidden}}
.s-bar{{height:100%;background:linear-gradient(90deg,var(--fire),var(--gold));
  border-radius:4px;width:0;transition:width .6s ease}}
.s-val{{font-size:.8rem;color:var(--fire);min-width:80px;text-align:right;font-weight:700}}
/* RECORD CARDS */
.i-grid{{display:flex;flex-wrap:wrap;gap:1.2rem;justify-content:center;margin-top:2rem}}
.i-card{{background:var(--card);border:1px solid var(--border);border-left:3px solid var(--fire);
  border-radius:10px;padding:1.5rem;width:calc(33% - .8rem);min-width:240px;
  opacity:0;transform:translateY(30px);transition:opacity .5s ease,transform .5s ease}}
.i-card.vis{{opacity:1;transform:translateY(0)}}
.i-rank{{font-size:.65rem;letter-spacing:.15em;color:var(--fire);
  text-transform:uppercase;margin-bottom:.3rem}}
.i-val{{font-size:1.8rem;font-weight:900;color:var(--fire);margin-bottom:.2rem}}
.i-entity{{font-size:1rem;font-weight:700;margin-bottom:.8rem}}
.i-fields{{display:flex;flex-wrap:wrap;gap:.8rem}}
.i-fields span{{display:flex;flex-direction:column}}
.i-label{{font-size:.62rem;color:var(--muted);text-transform:uppercase;letter-spacing:.07em}}
.i-fields strong{{font-size:.9rem}}
/* TAKEAWAYS */
.takeaway-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));
  gap:1.2rem;margin-top:2.5rem}}
.t-card{{background:var(--card);border:1px solid var(--border);border-left:3px solid var(--fire);
  border-radius:10px;padding:1.5rem;
  opacity:0;transform:translateY(20px);transition:opacity .55s ease,transform .55s ease}}
.t-card.vis{{opacity:1;transform:translateY(0)}}
.t-index{{font-size:2rem;font-weight:900;color:var(--border);margin-bottom:.5rem}}
.t-card h3{{font-size:1rem;margin-bottom:.5rem;color:var(--text)}}
.t-card p{{font-size:.88rem;line-height:1.65;color:var(--muted)}}
.next-steps{{margin-top:2rem;text-align:center;font-size:.9rem;color:var(--muted);
  padding:1.2rem;border-top:1px solid var(--border)}}
.next-steps strong{{color:var(--fire)}}
/* EPILOGUE */
#epilogue{{min-height:60vh;display:flex;align-items:center;justify-content:center;
  text-align:center;padding:6rem 2rem;
  background:radial-gradient(ellipse at 50% 50%,#14001a 0%,#0a0a0a 65%)}}
.ep-badge{{display:inline-block;padding:.4rem 1.2rem;border:1px solid var(--fire);
  border-radius:20px;font-size:.7rem;letter-spacing:.2em;color:var(--fire);
  text-transform:uppercase;margin-bottom:2rem}}
.ep-title{{font-size:clamp(2rem,5vw,4rem);font-weight:900;line-height:1.1;margin-bottom:1.5rem}}
.ep-title em{{font-style:normal;color:var(--fire)}}
.ep-body{{font-size:1.1rem;color:var(--muted);max-width:600px;margin:0 auto;line-height:1.7}}
@media(max-width:768px){{
  .c-inner,.c-inner.flip{{grid-template-columns:1fr}}
  .c-inner.flip .reveal:first-child{{order:0}}
  .c-inner.flip .chart-box{{order:0}}
  .i-card{{width:100%}}
}}
</style>
</head>
<body>
<div id="prog-bar"></div>
<div id="ch-tag"></div>

<section id="hero">
  <div class="hero-eyebrow">Data Story &bull; {ds_name}</div>
  <h1 class="hero-title">The story<br>inside <em>{ds_name}.</em></h1>
  <p class="hero-sub">{A['total_count']:,} records.
    {total_fmt} in {metric_lbl.lower()}.
    {A.get('entity_count', len(A.get('top15_names',[])))}&nbsp;{entity_lbl.lower()}s.
    One complete picture.</p>
  <div class="scroll-cue">
    <span>Scroll to explore</span>
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M10 3v14M4 11l6 6 6-6" stroke="#999" stroke-width="1.5"
            stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  </div>
</section>

<section id="stats">
  <div class="stat-eyebrow">The numbers at a glance</div>
  {stat_html}
</section>

{top_ch}
{map_ch}
{cat_ch}
{scat_ch}
{trend_ch}
{hall_ch}
{rec_ch}
{tk_ch}

<section id="epilogue">
  <div>
    <div class="ep-badge reveal">{ds_name}</div>
    <h2 class="ep-title reveal" style="transition-delay:.15s">
      The data is clear.<br><em>The story is complete.</em>
    </h2>
    <p class="ep-body reveal" style="transition-delay:.3s">
      {A['total_count']:,} records examined. {total_fmt} in {metric_lbl.lower()} tracked.
      <strong>{top_ent}</strong> leads — and the numbers behind every other
      {entity_lbl.lower()} are just as real. This is what the data says.
    </p>
  </div>
</section>

<script>
const D = {js_data};
const METRIC_PREFIX = '{metric_prefix_js}';

const BG = {{
  paper_bgcolor:'#111', plot_bgcolor:'#111',
  font:{{color:'#bbb', size:11}},
  margin:{{t:16, b:52, l:58, r:18}},
  xaxis:{{gridcolor:'#1e1e1e', linecolor:'#2a2a2a'}},
  yaxis:{{gridcolor:'#1e1e1e', linecolor:'#2a2a2a'}}
}};
const CFG = {{responsive:true, displayModeBar:false}};
const rendered = {{}};

// ── Generic category-bar helper ────────────────────────────────────────────────
// Enforces: horizontal orientation, x/y from one paired-sorted list,
// low-variance zoom, length assertion.
function renderCategoryBar(divId, categories, values, opts) {{
  opts = opts || {{}};
  if (categories.length !== values.length)
    throw new Error(divId + ': length mismatch (' + categories.length + ' vs ' + values.length + ')');
  const pairs = categories.map((c,i) => [c, values[i]]);
  if (opts.categoryOrder) pairs.sort((a,b) => opts.categoryOrder.indexOf(a[0]) - opts.categoryOrder.indexOf(b[0]));
  else pairs.sort((a,b) => b[1] - a[1]);
  const cats = pairs.map(p => p[0]);
  const vals = pairs.map(p => p[1]);
  const spread = (Math.max(...vals) - Math.min(...vals)) / Math.max(...vals);
  const floor  = spread < 0.15 ? Math.min(...vals) - (Math.max(...vals) - Math.min(...vals)) * 0.5 : 0;
  Plotly.newPlot(divId, [{{
    type:'bar', orientation:'h', y:cats, x:vals,
    marker:{{color:'#ff5fa2', opacity:.9}},
    text:vals.map(v => opts.fmt ? opts.fmt(v) : v.toLocaleString()),
    textposition:'outside', textfont:{{color:'#aab'}},
    hovertemplate:'%{{y}}: %{{x}}<extra></extra>'
  }}], {{
    ...BG,
    xaxis:{{...BG.xaxis, title:opts.xTitle||'', range:[floor, Math.max(...vals)*1.18]}},
    yaxis:{{...BG.yaxis, type:'category', categoryorder:'total ascending', automargin:true}},
    margin:{{t:20,b:50,l:160,r:80}}
  }}, CFG);
}}

// ── Generic scatter/bubble helper ──────────────────────────────────────────────
// Enforces: log-scale detection, dtick:1 on log axes, greedy label placement.
function renderScatterBubble(divId, entities, x, y, opts) {{
  opts = opts || {{}};
  if (entities.length !== x.length || entities.length !== y.length)
    throw new Error(divId + ': length mismatch');
  const logX = opts.logX !== undefined ? opts.logX : (Math.max(...x) / Math.min(...x.filter(v=>v>0)) > 100);
  const logY = opts.logY !== undefined ? opts.logY : (Math.max(...y) / Math.min(...y.filter(v=>v>0)) > 100);
  const tx = v => logX ? Math.log10(Math.max(v,1e-9)) : v;
  const ty = v => logY ? Math.log10(Math.max(v,1e-9)) : v;
  const xs = x.map(tx), ys = y.map(ty);
  const xr = Math.max(...xs) - Math.min(...xs) || 1;
  const yr = Math.max(...ys) - Math.min(...ys) || 1;
  const nx = xs.map(v => (v - Math.min(...xs)) / xr);
  const ny = ys.map(v => (v - Math.min(...ys)) / yr);
  const sizes = opts.size || entities.map(()=>1);
  const order = entities.map((_,i)=>i).sort((a,b)=>sizes[b]-sizes[a]);
  const minGap = opts.labelMinGap || 0.06;
  const placed = [], showLabel = new Array(entities.length).fill(false);
  for (const i of order) {{
    if (!placed.some(j => Math.hypot(nx[i]-nx[j],ny[i]-ny[j]) < minGap))
      {{ showLabel[i]=true; placed.push(i); }}
  }}
  Plotly.newPlot(divId, [{{
    type:'scatter', mode:'markers+text',
    x, y, text: entities.map((n,i) => showLabel[i] ? n : ''),
    textposition:'top center', textfont:{{color:'#aab', size:10}},
    marker:{{
      size: sizes, sizemode:'area',
      sizeref: opts.size ? Math.max(...sizes)/40**2 : undefined,
      color:'#ff5fa2', opacity:.8, line:{{width:1,color:'#333'}}
    }},
    customdata: entities,
    hovertemplate:'<b>%{{customdata}}</b><br>x: %{{x:,.2f}}<br>y: %{{y:,.4f}}<extra></extra>'
  }}], {{
    ...BG,
    xaxis:{{...BG.xaxis, title:opts.xTitle||'', type:logX?'log':'linear', dtick:logX?1:undefined}},
    yaxis:{{...BG.yaxis, title:opts.yTitle||'', type:logY?'log':'linear', dtick:logY?1:undefined}},
    margin:{{t:20,b:50,l:60,r:20}}
  }}, CFG);
}}

// ── Progress bar ────────────────────────────────────────────────────────────────
window.addEventListener('scroll', () => {{
  const max = document.body.scrollHeight - window.innerHeight;
  document.getElementById('prog-bar').style.width = (window.scrollY/max*100)+'%';
}});

// ── Reveal observer (visual only — no counters here) ────────────────────────────
const revealObs = new IntersectionObserver(entries => {{
  entries.forEach(e => {{ if (e.isIntersecting) e.target.classList.add('vis'); }});
}}, {{threshold:0.12}});
document.querySelectorAll('.reveal').forEach(el => revealObs.observe(el));

// ── Counter observer (isolated, single-shot, guarded) ─────────────────────────
function counter(el) {{
  if (el.dataset.counted) return;
  el.dataset.counted='1';
  const target = +el.dataset.target;
  const prefix = el.dataset.prefix || '';
  const suffix = el.dataset.suffix || '';
  const dur = 1800, start = performance.now();
  function step(now) {{
    const p = Math.min((now-start)/dur, 1);
    const ease = 1-Math.pow(1-p,3);
    el.textContent = prefix + Math.round(ease*target).toLocaleString() + suffix;
    if (p<1) requestAnimationFrame(step);
  }}
  requestAnimationFrame(step);
}}
const counterObs = new IntersectionObserver(entries => {{
  entries.forEach(e => {{
    if (!e.isIntersecting) return;
    e.target.querySelectorAll('.num[data-target]').forEach(n => counter(n));
    counterObs.unobserve(e.target);
  }});
}}, {{threshold:0.3}});
document.querySelectorAll('.num[data-target]').forEach(n => {{
  counterObs.observe(n.closest('.s-card,.s-card-wide,.reveal') || n);
}});

// ── Chapter tag observer ────────────────────────────────────────────────────────
const chTag = document.getElementById('ch-tag');
const chObs = new IntersectionObserver(entries => {{
  entries.forEach(e => {{
    if (e.isIntersecting) chTag.textContent = e.target.dataset.chapter||'';
  }});
}}, {{threshold:0.3}});
document.querySelectorAll('[data-chapter]').forEach(el => chObs.observe(el));

// ── Chart observer (lazy render) ────────────────────────────────────────────────
function buildHall() {{
  const list = document.getElementById('hall-list');
  if (!list || !D.top10_names) return;
  const vals = D.top10_values;
  if (!vals || !vals.length) return;
  const vmax = Math.max(...vals);
  const vmin = Math.min(...vals);
  const spread = vmax ? (vmax - vmin) / vmax : 0;
  const floor = spread < 0.15 ? vmin - (vmax - vmin) * 0.5 : 0;
  const ceil = vmax ? vmax * 1.02 : 1;
  const den = (ceil - floor) || 1;
  const pct = v => Math.max(0, Math.min(100, ((v - floor) / den) * 100)).toFixed(1);
  D.top10_names.forEach((name,i) => {{
    const row = document.createElement('div');
    row.className='s-row'; row.style.transitionDelay=(i*.07)+'s';
    const rank = document.createElement('span');
    rank.className = 's-rank';
    rank.textContent = String(i + 1);
    const label = document.createElement('span');
    label.className = 's-name';
    label.textContent = String(name);
    const barWrap = document.createElement('div');
    barWrap.className = 's-bar-wrap';
    const bar = document.createElement('div');
    bar.className = 's-bar';
    bar.dataset.pct = pct(vals[i]);
    bar.style.width = '0%';
    barWrap.appendChild(bar);
    const val = document.createElement('span');
    val.className = 's-val';
    val.textContent = Number(vals[i]).toLocaleString();
    row.append(rank, label, barWrap, val);
    list.appendChild(row);
  }});
  list.querySelectorAll('.s-row').forEach((r,i) => {{
    setTimeout(()=>{{
      r.classList.add('vis');
      setTimeout(()=>{{r.querySelector('.s-bar').style.width=r.querySelector('.s-bar').dataset.pct+'%';}},350);
    }},i*90);
  }});
}}

function buildTopChart() {{
  if (!D.top15_names) return;
  const vals = D.top15_values.slice().reverse();
  const names = D.top15_names.slice().reverse();
  Plotly.newPlot('topChart', [{{
    type:'bar', orientation:'h', y:names, x:vals,
    marker:{{color:vals.map((_,i)=>i===vals.length-1?'#2ee6a6':'#ff5fa2'),opacity:.9}},
    text:vals.map(v=>v>=1e9?METRIC_PREFIX+(v/1e9).toFixed(1)+'B':v>=1e6?METRIC_PREFIX+(v/1e6).toFixed(1)+'M':METRIC_PREFIX+v.toLocaleString()),
    textposition:'outside', textfont:{{color:'#aab'}},
    hovertemplate:'%{{y}}: %{{x:,.2f}}<extra></extra>'
  }}], {{
    ...BG,
    xaxis:{{...BG.xaxis, title:'{metric_lbl_js}'}},
    yaxis:{{...BG.yaxis, automargin:true}},
    margin:{{t:20,b:50,l:120,r:90}}
  }}, CFG);
}}

const chartSections = document.querySelectorAll('section[id], #hall-list, [id="hall-list"]');

// All chart/section rendering lives in ONE named function so it can be driven by
// BOTH the IntersectionObserver AND the safety-net timeout below. The observer alone
// is not enough: if it never fires (no scroll, layout quirk, reduced-motion), sections
// would stay blank. The safety-net calls this for every section as a guaranteed fallback.
function renderSection(id) {{
  if (rendered[id]) return;
  rendered[id] = true;
  if (id==='ch-top')  buildTopChart();
  {map_js}
  {cat_js_calls}
  {scat_js}
  {trend_js}
  if (id==='ch-hall') buildHall();
  if (id==='ch-rec') {{
    document.querySelectorAll('.i-card').forEach((c,i)=>{{
      setTimeout(()=>c.classList.add('vis'),i*110);
    }});
  }}
  if (id==='ch-tk') {{
    document.querySelectorAll('.t-card').forEach((c,i)=>{{
      setTimeout(()=>c.classList.add('vis'),i*100);
    }});
  }}
}}

const sectionObs = new IntersectionObserver(entries => {{
  entries.forEach(e => {{ if (e.isIntersecting) renderSection(e.target.id); }});
}}, {{threshold:0.15}});
document.querySelectorAll('section[id]').forEach(s=>sectionObs.observe(s));

// ── Safety-net: if the observers never fire, force-render everything after 2.5s ──
// Must do ALL THREE things the observers do — reveal, count, AND render charts —
// otherwise a missed observer leaves blank charts and stat cards frozen at 0.
setTimeout(() => {{
  document.querySelectorAll('.reveal').forEach(el => el.classList.add('vis'));
  document.querySelectorAll('.num[data-target]').forEach(n => counter(n));
  document.querySelectorAll('section[id]').forEach(s => renderSection(s.id));
}}, 2500);
</script>
</body>
</html>"""

# ── 8. Write output ────────────────────────────────────────────────────────────
import datetime as _dt
slug     = re.sub(r'[^a-z0-9]+', '-', src.stem.lower()).strip('-')
out_path = out_dir / f"{slug}-story-{_dt.date.today():%Y-%m-%d}.html"
out_path.write_text(html, encoding='utf-8')

# Syntax-check the embedded JS before declaring success. A single stray character
# (e.g. an unescaped apostrophe) throws a SyntaxError that silently blanks the whole
# page. `node --check` catches it here instead of in the browser.
def _verify_js(page_html):
    import shutil, subprocess, tempfile, os
    node = shutil.which('node')
    if not node:
        print("Note: 'node' not found — skipping JS syntax check (install Node to enable).")
        return
    m = re.search(r'<script>(?!<)(.*?)</script>', page_html, re.S)
    if not m:
        return
    tf = tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8')
    try:
        tf.write(m.group(1)); tf.close()
        r = subprocess.run([node, '--check', tf.name], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"JS syntax error in generated story:\n{r.stderr.strip()}")
        print("JS syntax check passed (node --check).")
    finally:
        os.unlink(tf.name)

_verify_js(html)
print(f"Done! {len(html):,} chars written -> {out_path}")
