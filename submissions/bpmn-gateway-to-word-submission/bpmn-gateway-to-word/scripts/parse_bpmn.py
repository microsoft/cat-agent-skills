#!/usr/bin/env python3
"""Parse a BPMN diagram into a normalised process graph (JSON).

Usage:  python parse_bpmn.py <diagram.bpmn|.xml|.svg> [-o graph.json]

Input is auto-detected:
  * BPMN 2.0 XML  -> exact (sourceRef/targetRef). Preferred.
  * bpmn-js SVG   -> geometry-based reconstruction (no source/target in the file).

Standard library only. Exit code: 0 ok, 1 unreadable input, 2 parse failed sanity checks.
"""
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET

NUM = r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?'

TASK_TAGS = {'task', 'userTask', 'serviceTask', 'manualTask', 'scriptTask', 'businessRuleTask',
             'sendTask', 'receiveTask', 'callActivity', 'subProcess', 'transaction', 'adHocSubProcess'}
GATEWAY_TAGS = {'exclusiveGateway': 'Exclusive (XOR)', 'parallelGateway': 'Parallel (AND)',
                'inclusiveGateway': 'Inclusive (OR)', 'eventBasedGateway': 'Event-based',
                'complexGateway': 'Complex'}


def local(tag):
    return tag.split('}', 1)[-1] if isinstance(tag, str) else ''


def clean(text):
    return re.sub(r'\s+', ' ', text or '').strip()


# --------------------------------------------------------------------------- BPMN XML

def parse_xml(root):
    nodes, edges, warnings = {}, [], []
    lane_of, annotations, assoc = {}, {}, []
    bounds = {}

    # Diagram bounds (for left-to-right ordering only)
    for shape in root.iter():
        if local(shape.tag) == 'BPMNShape':
            for b in shape:
                if local(b.tag) == 'Bounds':
                    bounds[shape.get('bpmnElement')] = (float(b.get('x', 0)), float(b.get('y', 0)))

    for el in root.iter():
        if local(el.tag) == 'lane':
            for ref in el:
                if local(ref.tag) == 'flowNodeRef' and ref.text:
                    lane_of[ref.text.strip()] = el.get('name') or el.get('id')

    def doc_of(el):
        for c in el:
            if local(c.tag) == 'documentation':
                return clean(c.text)
        return ''

    for el in root.iter():
        t, eid = local(el.tag), el.get('id')
        if not eid:
            continue
        x, y = bounds.get(eid, (0.0, 0.0))
        name = clean(el.get('name'))
        if t == 'startEvent':
            nodes[eid] = dict(id=eid, kind='start', name=name, x=x, y=y)
        elif t == 'endEvent':
            nodes[eid] = dict(id=eid, kind='end', name=name, x=x, y=y)
        elif t in ('intermediateCatchEvent', 'intermediateThrowEvent', 'boundaryEvent'):
            n = dict(id=eid, kind='intermediate', name=name, x=x, y=y, subtype=t)
            for c in el:
                if local(c.tag) == 'linkEventDefinition':
                    n['link_name'] = clean(c.get('name')) or name
                    n['link_role'] = 'throw' if t == 'intermediateThrowEvent' else 'catch'
                elif local(c.tag).endswith('EventDefinition'):
                    n['event_type'] = local(c.tag)[:-len('EventDefinition')]
            if t == 'boundaryEvent':
                n['attached_to'] = el.get('attachedToRef')
            nodes[eid] = n
        elif t in TASK_TAGS:
            nodes[eid] = dict(id=eid, kind='activity', name=name, x=x, y=y, subtype=t,
                              description=doc_of(el))
            if t in ('subProcess', 'transaction', 'adHocSubProcess'):
                warnings.append(f'Sub-process "{name or eid}" is flattened: its inner steps are listed inline.')
        elif t in GATEWAY_TAGS:
            nodes[eid] = dict(id=eid, kind='gateway', name=name, x=x, y=y,
                              gateway_type=GATEWAY_TAGS[t])
        elif t == 'textAnnotation':
            for c in el:
                if local(c.tag) == 'text':
                    annotations[eid] = clean(c.text)
        elif t == 'association':
            assoc.append((el.get('sourceRef'), el.get('targetRef')))
        elif t == 'sequenceFlow':
            edges.append(dict(id=eid, source=el.get('sourceRef'), target=el.get('targetRef'),
                              label=name, kind='sequence'))

    for nid, n in nodes.items():
        if nid in lane_of:
            n['performer'] = lane_of[nid]
        if n.get('attached_to') in nodes:
            edges.append(dict(id=f'{nid}__boundary', source=n['attached_to'], target=nid,
                              label=f'on boundary event: {n["name"] or n.get("event_type", "event")}',
                              kind='boundary'))
    for a, b in assoc:
        for ann, other in ((a, b), (b, a)):
            if ann in annotations and other in nodes:
                nodes[other]['annotation'] = annotations[ann]

    edges = [e for e in edges if e['source'] in nodes and e['target'] in nodes]
    return dict(source_format='bpmn-xml', nodes=nodes, edges=edges, warnings=warnings)


# --------------------------------------------------------------------------- bpmn-js SVG

def get_translate(g):
    """bpmn-js writes matrix(a b c d e f); other tools write translate(x,y). Accept spaces or commas."""
    t = g.get('transform', '')
    m = re.search(r'matrix\(\s*(%s)(?:[\s,]+(%s)){5}\s*\)' % (NUM, NUM), t)
    if m:
        vals = [float(v) for v in re.findall(NUM, t)]
        return vals[4], vals[5]
    m = re.search(r'translate\(\s*(%s)(?:[\s,]+(%s))?\s*\)' % (NUM, NUM), t)
    if m:
        return float(m.group(1)), float(m.group(2) or 0)
    return None


def visual_of(g):
    for c in g:
        if 'djs-visual' in (c.get('class') or ''):
            return c
    return g


def visual_items(vis, name, parents):
    """Descendants of <vis> with tag `name`, skipping anything inside <marker>/<defs>."""
    out = []
    for el in vis.iter():
        if local(el.tag) != name:
            continue
        p, skip = parents.get(el), False
        while p is not None and p is not vis:
            if local(p.tag) in ('marker', 'defs'):
                skip = True
                break
            p = parents.get(p)
        if not skip:
            out.append(el)
    return out


def text_of(el):
    parts = [clean(t.text) for t in el.iter() if local(t.tag) in ('tspan',) and clean(t.text)]
    if not parts:
        parts = [clean(t.text) for t in el.iter() if local(t.tag) == 'text' and clean(t.text)]
    return clean(' '.join(parts))


def stroke_width(el):
    m = re.search(r'stroke-width\s*[:=]\s*"?(%s)' % NUM, (el.get('style') or '') + ' ' + (el.get('stroke-width') or ''))
    return float(m.group(1)) if m else 0.0


def classify_gateway(vis, parents):
    for p in visual_items(vis, 'path', parents):
        d = (p.get('d') or '').strip()
        if not d or len(d) > 400:
            continue
        low = d.lower()
        if low.startswith('m 23,10'):
            return 'Parallel (AND)'
        if low.startswith('m 16,15'):
            return 'Exclusive (XOR)'
    if visual_items(vis, 'circle', parents):
        return 'Inclusive (OR)'
    return 'Exclusive (XOR)'  # plain diamond = exclusive by BPMN definition


def bbox_of(g, vis, parents):
    tx, ty = get_translate(g) or (0.0, 0.0)
    poly = visual_items(vis, 'polygon', parents)
    if poly:
        pts = [float(v) for v in re.findall(NUM, poly[0].get('points', ''))]
        xs, ys = pts[0::2], pts[1::2]
        if xs and ys:
            return tx + min(xs), ty + min(ys), tx + max(xs), ty + max(ys)
    rects = visual_items(vis, 'rect', parents)
    if rects:
        r = rects[0]
        rx0, ry0 = float(r.get('x', 0)), float(r.get('y', 0))
        w, h = float(r.get('width', 100)), float(r.get('height', 80))
        return tx + rx0, ty + ry0, tx + rx0 + w, ty + ry0 + h
    circles = visual_items(vis, 'circle', parents)
    if circles:
        c = max(circles, key=lambda e: float(e.get('r', 0)))
        cx, cy, r = float(c.get('cx', 18)), float(c.get('cy', 18)), float(c.get('r', 18))
        return tx + cx - r, ty + cy - r, tx + cx + r, ty + cy + r
    return tx, ty, tx + 100, ty + 80


def connection_path(vis, parents):
    paths = visual_items(vis, 'path', parents)
    for p in paths:  # waypoint path carries data-corner-radius; arrowheads never do
        if p.get('data-corner-radius') is not None:
            return p
    return max(paths, key=lambda p: len(p.get('d', '')), default=None)


def endpoints(path):
    nums = [float(n) for n in re.findall(NUM, path.get('d', ''))]
    if len(nums) < 4:
        return None, None
    return (nums[0], nums[1]), (nums[-2], nums[-1])


def has_both_markers(path):
    st = path.get('style', '')
    return 'marker-start' in st and 'marker-end' in st


def dist_to_box(pt, b):
    dx = max(b['x0'] - pt[0], 0, pt[0] - b['x1'])
    dy = max(b['y0'] - pt[1], 0, pt[1] - b['y1'])
    return (dx * dx + dy * dy) ** 0.5


def nearest(pt, shapes):
    best, key = None, None
    for sid, b in shapes.items():
        k = (round(dist_to_box(pt, b), 3), (b['x1'] - b['x0']) * (b['y1'] - b['y0']))
        if key is None or k < key:
            best, key = sid, k
    return best, (key[0] if key else None)


SKIP_PREFIXES = ('Participant_', 'Lane_', 'Collaboration_', 'Process_')


def parse_svg(root):
    parents = {c: p for p in root.iter() for c in p}
    warnings, labels, flow_labels = [], {}, {}
    shapes, conns, notes = {}, {}, {}

    for g in root.iter():
        if local(g.tag) != 'g' or not g.get('data-element-id'):
            continue
        eid, cls = g.get('data-element-id'), (g.get('class') or '')
        vis = visual_of(g)
        if eid.endswith('_label'):
            base = eid[:-6]
            (flow_labels if base.startswith('Flow_') or 'djs-connection' in cls else labels)[base] = text_of(vis)
            continue
        is_conn = 'djs-connection' in cls or eid.startswith(('Flow_', 'Association_', 'MessageFlow_'))
        if is_conn:
            conns[eid] = (g, vis)
            continue
        if eid.startswith(SKIP_PREFIXES):
            continue
        if eid.startswith('TextAnnotation_'):
            notes[eid] = dict(text=text_of(vis), bbox=bbox_of(g, vis, parents))
            continue
        xy = get_translate(g)
        # Order matters: task icons (service-task gear) contain circles, so test for the task's rect first.
        if visual_items(vis, 'polygon', parents):
            kind = 'gateway'
        elif visual_items(vis, 'rect', parents):
            kind = 'activity'
        elif visual_items(vis, 'circle', parents):
            kind = 'event'
        else:
            continue  # data objects, groups, etc. are not process steps
        shapes[eid] = dict(g=g, vis=vis, kind=kind, xy=xy, text=text_of(vis),
                           bbox=bbox_of(g, vis, parents))

    nodes = {}
    for eid, s in shapes.items():
        x0, y0, x1, y1 = s['bbox']
        n = dict(id=eid, x=x0, y=y0, name=labels.get(eid) or s['text'])
        if s['kind'] == 'activity':
            n['kind'] = 'activity'
        elif s['kind'] == 'gateway':
            n['kind'] = 'gateway'
            n['gateway_type'] = classify_gateway(s['vis'], parents)
        else:
            circles = visual_items(s['vis'], 'circle', parents)
            if len(circles) >= 2:
                n['kind'] = 'intermediate'
            elif max(stroke_width(c) for c in circles) >= 3:
                n['kind'] = 'end'
            else:
                n['kind'] = 'start'
        nodes[eid] = n

    boxes = {k: dict(x0=s['bbox'][0], y0=s['bbox'][1], x1=s['bbox'][2], y1=s['bbox'][3]) for k, s in shapes.items()}
    note_boxes = {k: dict(x0=v['bbox'][0], y0=v['bbox'][1], x1=v['bbox'][2], y1=v['bbox'][3]) for k, v in notes.items()}
    edges, unresolved = [], 0
    for cid, (g, vis) in conns.items():
        p = connection_path(vis, parents)
        if p is None:
            continue
        a, b = endpoints(p)
        if a is None:
            continue
        if cid.startswith('Association_'):
            (sa, da), (sb, db) = nearest(a, {**boxes, **note_boxes}), nearest(b, {**boxes, **note_boxes})
            for ann, other in ((sa, sb), (sb, sa)):
                if ann in notes and other in nodes:
                    nodes[other]['annotation'] = notes[ann]['text']
            continue
        if has_both_markers(p):
            continue  # message flow: not part of the sequence-flow graph
        src, ds = nearest(a, boxes)
        tgt, dt = nearest(b, boxes)
        if src is None or tgt is None or ds > 30 or dt > 30:
            unresolved += 1
            warnings.append(f'Connection {cid}: endpoint not within 30px of a shape; skipped.')
            continue
        edges.append(dict(id=cid, source=src, target=tgt, label=flow_labels.get(cid, ''), kind='sequence'))
    return dict(source_format='bpmn-js-svg', nodes=nodes, edges=edges, warnings=warnings,
                _meta=dict(zero_positions=sum(1 for s in shapes.values() if s['xy'] is None or s['xy'] == (0.0, 0.0)),
                           shape_count=len(shapes), unresolved=unresolved))


# --------------------------------------------------------------------------- checks

def sanity_check(graph):
    """Print a verification summary. Return a list of FATAL problems."""
    fatal = []
    nodes, edges = graph['nodes'], graph['edges']
    meta = graph.pop('_meta', None)
    if meta and meta['shape_count'] > 3 and meta['zero_positions'] > 0.5 * meta['shape_count']:
        fatal.append('Most shapes have no usable transform: geometry matching would be meaningless.')
    if len(edges) > 3 and len({(e['source'], e['target']) for e in edges}) == 1:
        fatal.append('Every connection resolves to the same source and target (arrowhead/pool mis-match).')
    for e in edges:
        if e['source'] == e['target']:
            graph['warnings'].append(f'Edge {e["id"]} loops from a node to itself.')
    if not any(n['kind'] == 'start' for n in nodes.values()):
        graph['warnings'].append('No start event found.')
    connected = {e['source'] for e in edges} | {e['target'] for e in edges}
    for nid, n in nodes.items():
        if n['kind'] == 'activity' and nid not in connected:
            graph['warnings'].append(f'Activity "{n["name"] or nid}" has no sequence flow attached.')
    if not nodes:
        fatal.append('No process shapes found; this does not look like a BPMN diagram.')

    kinds = {}
    for n in nodes.values():
        kinds[n['kind']] = kinds.get(n['kind'], 0) + 1
    gts = {}
    for n in nodes.values():
        if n['kind'] == 'gateway':
            gts[n['gateway_type']] = gts.get(n['gateway_type'], 0) + 1
    print(f'format={graph["source_format"]} nodes={len(nodes)} edges={len(edges)} kinds={kinds} gateways={gts}',
          file=sys.stderr)
    for w in graph['warnings']:
        print('WARNING:', w, file=sys.stderr)
    for f in fatal:
        print('FATAL:', f, file=sys.stderr)
    return fatal


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input')
    ap.add_argument('-o', '--output', default='graph.json')
    args = ap.parse_args()
    try:
        root = ET.parse(args.input).getroot()
    except (ET.ParseError, OSError) as exc:
        print(f'FATAL: cannot read {args.input}: {exc}', file=sys.stderr)
        return 1
    if local(root.tag) == 'svg':
        graph = parse_svg(root)
    elif local(root.tag) == 'definitions':
        graph = parse_xml(root)
    else:
        print(f'FATAL: unsupported root element <{local(root.tag)}>.', file=sys.stderr)
        return 1
    fatal = sanity_check(graph)
    with open(args.output, 'w', encoding='utf-8') as fh:
        json.dump(graph, fh, indent=2)
    return 2 if fatal else 0


if __name__ == '__main__':
    sys.exit(main())
