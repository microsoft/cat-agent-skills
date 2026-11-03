#!/usr/bin/env python3
"""Turn a process graph (from parse_bpmn.py) into numbered, non-overlapping steps.

Usage:  python linearize.py graph.json [-o steps.json]

Method (deliberately NOT a recursive tree walk, which duplicates or swallows reconverging branches):
  1. DFS from the start event(s) to classify each edge as forward or back (loop).
  2. Kahn topological sort over forward edges only, ties broken left-to-right by diagram position.
  3. Number tasks, events, and gateways that SPLIT the flow. Pure merge/join gateways are passed through.
  4. For every parallel (AND) split, compute each pathway's exclusive steps by forward reachability,
     minus anything reachable from more than one branch (the join and everything after it).

Standard library only. Exit code: 0 ok, 2 completeness check failed.
"""
import argparse
import heapq
import json
import sys

sys.setrecursionlimit(20000)

SUBTYPE_LABEL = {'userTask': 'User task', 'serviceTask': 'Service task', 'manualTask': 'Manual task',
                 'scriptTask': 'Script task', 'businessRuleTask': 'Business rule task',
                 'sendTask': 'Send task', 'receiveTask': 'Receive task', 'callActivity': 'Call activity',
                 'subProcess': 'Sub-process', 'transaction': 'Sub-process', 'adHocSubProcess': 'Sub-process'}


def letters(i):
    s = ''
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def pair_link_events(nodes, edges, warnings):
    """Throw/catch Link events hand off by name, not by a drawn arrow. Add an explicit link edge."""
    has_in = {e['target'] for e in edges}
    has_out = {e['source'] for e in edges}
    groups = {}
    for nid, n in nodes.items():
        if n['kind'] != 'intermediate':
            continue
        role = n.get('link_role')
        if role is None:  # SVG input: infer from structure
            if nid in has_in and nid not in has_out:
                role = 'throw'
            elif nid in has_out and nid not in has_in:
                role = 'catch'
        name = (n.get('link_name') or n.get('name') or '').strip().lower()
        if role and name:
            groups.setdefault(name, {'throw': [], 'catch': []})[role].append(nid)
    added = []
    for name, g in groups.items():
        for nid in g['throw'] + g['catch']:
            nodes[nid]['link_role'] = 'throw' if nid in g['throw'] else 'catch'
        if len(g['catch']) == 1 and g['throw']:
            for t in g['throw']:
                added.append(dict(id=f'{t}__link', source=t, target=g['catch'][0], label='', kind='link',
                                  link_name=nodes[t].get('name') or name))
        elif g['throw'] or g['catch']:
            warnings.append(f'Link "{name}": expected exactly one catch event, found {len(g["catch"])} '
                            f'(throws: {len(g["throw"])}). Hand-off not drawn.')
    return edges + added


def build(graph):
    nodes, warnings = graph['nodes'], list(graph.get('warnings', []))
    edges = pair_link_events(nodes, list(graph['edges']), warnings)
    pos = lambda nid: (nodes[nid].get('x', 0), nodes[nid].get('y', 0), nid)

    out = {n: [] for n in nodes}
    indeg = {n: 0 for n in nodes}
    for i, e in enumerate(edges):
        out[e['source']].append(i)
        indeg[e['target']] += 1
    for n in out:
        out[n].sort(key=lambda i: pos(edges[i]['target']))

    # 1. classify back edges
    seeds = sorted([n for n in nodes if nodes[n]['kind'] == 'start'], key=pos)
    seeds += sorted([n for n in nodes if indeg[n] == 0 and n not in seeds], key=pos)
    state, back = {}, set()

    def dfs(u):
        state[u] = 1
        for i in out[u]:
            v = edges[i]['target']
            if state.get(v) == 1:
                back.add(i)
            elif v not in state:
                dfs(v)
        state[u] = 2

    for s in seeds + sorted(nodes, key=pos):
        if s not in state:
            dfs(s)

    # 2. Kahn over forward edges
    fwd = {n: [] for n in nodes}
    fin = {n: 0 for n in nodes}
    for i, e in enumerate(edges):
        if i not in back:
            fwd[e['source']].append(e['target'])
            fin[e['target']] += 1
    heap = [pos(n) for n in nodes if fin[n] == 0]
    heapq.heapify(heap)
    order = []
    while heap:
        _, _, u = heapq.heappop(heap)
        order.append(u)
        for v in fwd[u]:
            fin[v] -= 1
            if fin[v] == 0:
                heapq.heappush(heap, pos(v))

    # 3. which nodes become numbered steps
    def is_step(nid):
        n = nodes[nid]
        return n['kind'] != 'gateway' or len(out[nid]) >= 2

    numbered = [n for n in order if is_step(n)]
    num = {nid: i + 1 for i, nid in enumerate(numbered)}

    def resolve(i, seen=None):
        e, seen = edges[i], seen or set()
        v = e['target']
        if v in num:
            return [dict(label=e['label'], target=num[v], loopback=i in back, kind=e['kind'],
                         link_name=e.get('link_name', ''))]
        if v in seen or not out[v]:
            warnings.append(f'Connector gateway {v} leads nowhere; branch dropped.')
            return []
        res = []
        for j in out[v]:
            for b in resolve(j, seen | {v}):
                b['label'] = e['label'] or b['label']
                b['loopback'] = b['loopback'] or i in back
                res.append(b)
        return res

    steps = []
    for nid in numbered:
        n = nodes[nid]
        step = dict(number=num[nid], id=nid, kind=n['kind'], name=n.get('name', ''),
                    performer=n.get('performer', ''), description=n.get('description', ''),
                    annotation=n.get('annotation', ''), x=n.get('x', 0))
        if n['kind'] == 'activity':
            step['type_label'] = SUBTYPE_LABEL.get(n.get('subtype', ''), 'Task')
            step['name'] = step['name'] or f'(unnamed {step["type_label"].lower()})'
        elif n['kind'] == 'gateway':
            gt = n.get('gateway_type', 'Exclusive (XOR)')
            step['gateway_type'] = gt
            if gt.startswith('Parallel'):
                step['type_label'] = 'Parallel fork'
                step['name'] = step['name'] or 'Run in parallel'
            else:
                step['type_label'] = 'Decision'
                step['name'] = step['name'] or 'Decision (no question labelled)'
        elif n['kind'] == 'start':
            step['type_label'], step['name'] = 'Start', step['name'] or 'Process starts'
        elif n['kind'] == 'end':
            step['type_label'], step['name'] = 'End', step['name'] or 'Process ends'
        else:
            role = n.get('link_role')
            step['type_label'] = {'throw': 'Link throw', 'catch': 'Link catch'}.get(role, 'Event')
            if n.get('attached_to'):
                step['type_label'] = 'Boundary event'
            step['name'] = step['name'] or f'({n.get("event_type", "intermediate")} event)'
        branches = [b for i in out[nid] for b in resolve(i)]
        step['branches'] = branches
        if not branches and n['kind'] != 'end':
            warnings.append(f'Step {num[nid]} "{step["name"]}" has no outgoing flow and is not an end event.')
        if indeg[nid] == 0 and n['kind'] != 'start' and n.get('link_role') != 'catch':
            warnings.append(f'Step {num[nid]} "{step["name"]}" has no incoming flow (orphan or entry point).')
        steps.append(step)

    # 4. parallel pathways
    def reach(root_id):
        seen, stack = set(), [root_id]
        while stack:
            u = stack.pop()
            if u in seen:
                continue
            seen.add(u)
            stack.extend(fwd[u])
        return {num[x] for x in seen if x in num}

    by_num = {s['number']: s for s in steps}
    id_of = {v: k for k, v in num.items()}
    parallel = {}
    for s in steps:
        if s['kind'] != 'gateway' or not s.get('gateway_type', '').startswith('Parallel'):
            continue
        roots = []
        for b in s['branches']:
            if not b['loopback'] and b['target'] not in roots:
                roots.append(b['target'])
        if len(roots) < 2:
            continue
        sets = [reach(id_of[r]) for r in roots]
        shared = {x for i, a in enumerate(sets) for x in a if any(x in b for j, b in enumerate(sets) if j != i)}
        parallel[str(s['number'])] = dict(
            pathways=[dict(letter=letters(i), root=r, name=by_num[r]['name'],
                           steps=sorted(a - shared)) for i, (r, a) in enumerate(zip(roots, sets))],
            resume=min(shared) if shared else None)

    # completeness
    missing = sorted(nid for nid, n in nodes.items() if n['kind'] == 'activity' and nid not in num)
    return dict(steps=steps, parallel=parallel, warnings=warnings,
                stats=dict(steps=len(steps), loops=len(back), parallel_forks=len(parallel)),
                missing=missing)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('graph')
    ap.add_argument('-o', '--output', default='steps.json')
    args = ap.parse_args()
    with open(args.graph, encoding='utf-8') as fh:
        graph = json.load(fh)
    result = build(graph)
    print(f'steps={result["stats"]["steps"]} loops={result["stats"]["loops"]} '
          f'parallel_forks={result["stats"]["parallel_forks"]}', file=sys.stderr)
    for w in result['warnings']:
        print('WARNING:', w, file=sys.stderr)
    with open(args.output, 'w', encoding='utf-8') as fh:
        json.dump(result, fh, indent=2)
    if result['missing']:
        print('FATAL: activities missing from the numbered steps:', result['missing'], file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
