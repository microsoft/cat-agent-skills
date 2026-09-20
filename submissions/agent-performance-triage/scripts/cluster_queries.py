#!/usr/bin/env python3
"""
Cluster an agent's unanswered / unresolved queries by intent.

Twenty phrasings of one gap are one backlog item, not twenty. This groups raw
query text into intent clusters, sizes each cluster by volume, labels it with
its distinguishing terms and a representative query, and emits a table ready to
be classified (content gap / retrieval gap / capability gap / out of scope) and
assigned an owner.

Usage:
    python3 cluster_queries.py queries.txt
    python3 cluster_queries.py queries.csv --column query --volume-column count
    python3 cluster_queries.py queries.txt --threshold 0.35 --csv backlog.csv

Input:
    .txt  one query per line
    .csv  a text column, optionally a volume/occurrence column

Standard library only. No network access. Nothing leaves this machine.

Limitation, stated up front: this groups by SHARED WORDS, not by meaning. It
will not merge "how much holiday do I have left" with "check remaining vacation
days" — no token in common. Treat the output as a first pass that collapses the
obvious duplicates, then merge synonym clusters by hand before writing the
backlog. Scan the single-phrasing clusters at the bottom of the table
specifically: that is where synonym splits hide.

Privacy: query text can carry personal data. Confirm the export is
de-identified or that you are authorized to handle it BEFORE running this, and
pass --examples 0 when the output will circulate.
"""

import argparse
import csv
import math
import re
import sys
from collections import Counter, defaultdict

# Deliberately small: stopping too much destroys short-query signal.
STOPWORDS = set("""
a an the this that these those there here of in on at to for from by with without
about into over under again further then once and or but if because as until while
is am are was were be been being do does did doing have has had having
i me my we our you your he she it they them his her its their what which who whom
how when where why can could should would will shall may might must not no nor
please tell show give need want get find make help hi hello hey thanks thank
do you know are able possible
il lo la i gli le un uno una di a da in con su per tra fra e o ma se perche come
dove quando chi che cosa non mi ti si ci vi sono e' ho hai ha abbiamo avete hanno
posso puoi puo possiamo potete possono vorrei voglio serve grazie ciao
""".split())

TOKEN_RE = re.compile(r"[a-z0-9àèéìòù']+")


def normalize(text):
    """Lowercase, tokenize, drop stopwords, crude singularization."""
    toks = []
    for t in TOKEN_RE.findall(text.lower()):
        if t in STOPWORDS or len(t) < 2:
            continue
        if len(t) > 4 and t.endswith("s") and not t.endswith("ss"):
            t = t[:-1]          # policies -> policie, payslips -> payslip
        if len(t) > 5 and t.endswith("ie"):
            t = t[:-2] + "y"    # policie -> policy
        toks.append(t)
    return toks


def tfidf(docs):
    """docs: list[list[str]] -> list[dict[str, float]], L2-normalized."""
    n_docs = len(docs)
    df = Counter()
    for toks in docs:
        df.update(set(toks))

    vectors = []
    for toks in docs:
        tf = Counter(toks)
        vec = {}
        for term, count in tf.items():
            idf = math.log((n_docs + 1) / (df[term] + 1)) + 1.0
            vec[term] = (1 + math.log(count)) * idf
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        vectors.append({k: v / norm for k, v in vec.items()})
    return vectors, df


def cosine(a, b):
    if len(a) > len(b):
        a, b = b, a
    return sum(w * b.get(term, 0.0) for term, w in a.items())


def cluster(vectors, weights, threshold):
    """Leader clustering by descending volume, then a centroid merge pass.

    Weighting by volume first means high-traffic queries seed the clusters,
    which keeps cluster labels representative of where the traffic actually is.
    """
    order = sorted(range(len(vectors)), key=lambda i: -weights[i])
    clusters = []            # list of {"members": [...], "centroid": {...}}

    for i in order:
        best, best_sim = None, threshold
        for c in clusters:
            sim = cosine(vectors[i], c["centroid"])
            if sim >= best_sim:
                best, best_sim = c, sim
        if best is None:
            clusters.append({"members": [i], "centroid": dict(vectors[i])})
        else:
            best["members"].append(i)
            _fold(best["centroid"], vectors[i], len(best["members"]))

    # Merge pass: leader clustering is order-dependent, this recovers splits.
    merged = True
    while merged:
        merged = False
        for a in range(len(clusters)):
            for b in range(a + 1, len(clusters)):
                if cosine(clusters[a]["centroid"], clusters[b]["centroid"]) >= threshold + 0.1:
                    clusters[a]["members"] += clusters[b]["members"]
                    for term, w in clusters[b]["centroid"].items():
                        clusters[a]["centroid"][term] = (
                            clusters[a]["centroid"].get(term, 0.0) + w) / 2
                    _renorm(clusters[a]["centroid"])
                    del clusters[b]
                    merged = True
                    break
            if merged:
                break
    return clusters


def _fold(centroid, vec, count):
    for term, w in vec.items():
        centroid[term] = centroid.get(term, 0.0) + (w - centroid.get(term, 0.0)) / count
    _renorm(centroid)


def _renorm(vec):
    norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
    for k in vec:
        vec[k] /= norm


def label(centroid, k=3):
    top = sorted(centroid.items(), key=lambda kv: -kv[1])[:k]
    return " / ".join(t for t, _ in top) if top else "(unlabelled)"


def medoid(members, vectors, centroid):
    return max(members, key=lambda i: cosine(vectors[i], centroid))


def read_input(path, column, volume_column):
    """Returns [(query_text, volume)]. Identical queries are collapsed."""
    rows = []
    if path.lower().endswith((".csv", ".tsv")):
        delim = "\t" if path.lower().endswith(".tsv") else ","
        with open(path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh, delimiter=delim)
            if not reader.fieldnames:
                sys.exit("error: CSV has no header row")
            col = column or reader.fieldnames[0]
            if col not in reader.fieldnames:
                sys.exit(f"error: column '{col}' not found. Columns: {reader.fieldnames}")
            for r in reader:
                text = (r.get(col) or "").strip()
                if not text:
                    continue
                vol = 1.0
                if volume_column:
                    raw = (r.get(volume_column) or "1").strip().replace(",", "")
                    try:
                        vol = float(raw or 1)
                    except ValueError:
                        vol = 1.0
                rows.append((text, vol))
    else:
        with open(path, encoding="utf-8-sig") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append((line, 1.0))

    collapsed = defaultdict(float)
    for text, vol in rows:
        collapsed[text] += vol
    return sorted(collapsed.items(), key=lambda kv: -kv[1])


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help=".txt (one query per line) or .csv/.tsv")
    ap.add_argument("--column", help="CSV column holding the query text (default: first)")
    ap.add_argument("--volume-column", help="CSV column holding occurrence counts")
    ap.add_argument("--threshold", type=float, default=0.15,
                    help="similarity threshold 0-1; lower = fewer, broader clusters. "
                         "0.15 suits short queries; raise toward 0.3 for long verbose "
                         "ones (default 0.15)")
    ap.add_argument("--min-size", type=int, default=1,
                    help="clusters smaller than this are pooled into a long tail")
    ap.add_argument("--examples", type=int, default=3,
                    help="example queries shown per cluster (0 to suppress)")
    ap.add_argument("--csv", metavar="PATH", help="also write the backlog skeleton here")
    args = ap.parse_args()

    rows = read_input(args.input, args.column, args.volume_column)
    if not rows:
        sys.exit("error: no queries found in input")

    texts = [t for t, _ in rows]
    weights = [v for _, v in rows]
    docs = [normalize(t) for t in texts]

    empty = [i for i, d in enumerate(docs) if not d]
    if empty:
        print(f"note: {len(empty)} quer{'y' if len(empty) == 1 else 'ies'} reduced to "
              f"nothing after stopword removal; grouped as 'unclassifiable'",
              file=sys.stderr)

    keep = [i for i, d in enumerate(docs) if d]
    vectors, _ = tfidf([docs[i] for i in keep])
    idx_map = {new: old for new, old in enumerate(keep)}
    clusters = cluster(vectors, [weights[i] for i in keep], args.threshold)

    total_volume = sum(weights)
    results = []
    for c in clusters:
        vol = sum(weights[idx_map[m]] for m in c["members"])
        rep = idx_map[medoid(c["members"], vectors, c["centroid"])]
        results.append({
            "label": label(c["centroid"]),
            "volume": vol,
            "distinct_queries": len(c["members"]),
            "share": vol / total_volume if total_volume else 0.0,
            "representative": texts[rep],
            "examples": [texts[idx_map[m]] for m in c["members"][:args.examples]],
        })
    results.sort(key=lambda r: -r["volume"])

    big = [r for r in results if r["distinct_queries"] >= args.min_size]
    tail = [r for r in results if r["distinct_queries"] < args.min_size]

    print(f"# Unanswered query clusters — {args.input}")
    print()
    plural = "cluster" if len(results) == 1 else "clusters"
    print(f"{len(texts)} distinct queries, {total_volume:,.0f} total occurrences, "
          f"grouped into {len(results)} {plural} at threshold {args.threshold}.")
    print()
    print("| # | Cluster | Occurrences | Share | Distinct phrasings | Representative query |")
    print("|---:|---|---:|---:|---:|---|")
    for i, r in enumerate(big, 1):
        rep = r["representative"] if args.examples else "(suppressed)"
        print(f"| {i} | {r['label']} | {r['volume']:,.0f} | {r['share']:.1%} "
              f"| {r['distinct_queries']} | {rep} |")
    if tail:
        tv = sum(r["volume"] for r in tail)
        print(f"| — | long tail ({len(tail)} clusters below --min-size) | {tv:,.0f} "
              f"| {tv / total_volume:.1%} | {sum(r['distinct_queries'] for r in tail)} | — |")
    print()

    if args.examples:
        print("## Cluster detail")
        print()
        for i, r in enumerate(big, 1):
            print(f"**{i}. {r['label']}** — {r['volume']:,.0f} occurrences "
                  f"({r['share']:.1%})")
            for ex in r["examples"]:
                print(f"  - {ex}")
            print()

    print("## Next step")
    print()
    print("Clustering here is lexical, not semantic: synonym pairs (holiday / vacation, "
          "MFA / locked out) stay split. Scan the single-phrasing clusters and merge those "
          "by hand before writing the backlog.")
    print()
    print("Then classify each cluster and name an owner. A cluster without an owner does "
          "not ship.")
    print()
    print("- **content gap** — nobody has written the answer → content author")
    print("- **retrieval gap** — the answer exists but is not reachable → agent builder")
    print("- **capability gap** — needs an action or integration, not a document")
    print("- **out of scope** — build a clean decline plus a redirect; cheap, and it counts "
          "as a resolution")

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["cluster", "occurrences", "share", "distinct_phrasings",
                        "representative_query", "classification", "root_cause",
                        "proposed_change", "target_artifact", "owner", "effort",
                        "expected_impact", "success_metric"])
            for r in big:
                w.writerow([r["label"], f"{r['volume']:.0f}", f"{r['share']:.4f}",
                            r["distinct_queries"], r["representative"],
                            "", "", "", "", "", "", "", ""])
        print(f"\n[backlog skeleton written to {args.csv}]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
