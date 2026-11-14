# Comparison pictures (ours top, OCCT bottom; operands, ∩, ∪, A−B, B−A, ⊕) for chosen cases.
#   make_pics.py <cases.tsv> <bool_ours.txt> <bool_occt.txt> <dumps dir> <pics dir> <out images dir> <regex> [--repair]
# Writes ours_<n>.json / occt_<n>.json into the pics dir (page.html + shoot.cjs live there) and shoots cmp_<n>.png.
import sys, os, re, json, subprocess
cases_f, ours_f, occt_f, dumps, pics, images, rx = sys.argv[1:8]
repair = '--repair' in sys.argv
T = os.path.dirname(os.path.abspath(__file__))
OPS = ['intersection', 'union', 'a-b', 'b-a', 'xor']
EMPTY = {'pos': [], 'idx': [], 'edges': [], 'verts': [], 'counts': [0, 0, 0]}


def safe(name):
    return re.sub(r'[^A-Za-z0-9_.-]', '_', name)


def lines(fn):
    d = {}
    for l in open(fn, errors='replace'):
        c, side, rest = l.rstrip('\n').split('\t', 2)
        w = rest.split()
        d[(c, w[1])] = w
    return d


ours, occt = lines(ours_f), lines(occt_f)
cases = [l.rstrip('\n').split('\t') for l in open(cases_f) if l.strip()]
cases = [c for c in cases if re.search(rx, c[0])]
jobs = []
for c in cases:
    cid, a, b = c[0], c[1], c[2]
    n = safe(cid)
    # operands, ours
    env = dict(os.environ)
    if repair:
        env['REPAIR'] = '1'
    opf = os.path.join(dumps, 'ours_%s_operands.json' % n)
    err = ''
    if not os.path.exists(opf):
        p = subprocess.run([os.path.join(T, 'ours_step_bench'), 'dumpops', a, b, opf], capture_output=True, text=True, env=env, timeout=600)
        if p.returncode != 0 or not os.path.exists(opf):
            err = (p.stderr.strip().splitlines() or ['operands failed'])[-1]
    try:
        ops_json = json.load(open(opf))
    except Exception:
        ops_json = [dict(EMPTY, error='load: ' + (err or 'failed')), dict(EMPTY)]
    panels = list(ops_json)
    for op in OPS:
        w = ours.get((cid, op))
        f = os.path.join(dumps, 'ours_%s_%s.json' % (n, op))
        if w and w[2] == 'ok' and os.path.exists(f):
            panels.append(json.load(open(f)))
        else:
            msg = ' '.join(w[2:3] + w[11:]) if w else 'not run'
            if w and w[2] == 'FAIL':
                msg = 'FAIL ' + ' '.join(w[11:])
            panels.append(dict(EMPTY, error=msg))
    json.dump(panels, open(os.path.join(pics, 'ours_%s.json' % n), 'w'))
    f = os.path.join(dumps, 'occt_%s.json' % n)
    oc = json.load(open(f)) if os.path.exists(f) else [dict(EMPTY, error='OCCT not run'), dict(EMPTY)] + [dict(EMPTY) for _ in OPS]
    for i, op in enumerate(OPS):
        w = occt.get((cid, op))
        if w and w[2] != 'ok' and i + 2 < len(oc):
            oc[i + 2]['error'] = 'FAIL ' + ' '.join(w[11:])
        elif w and w[2] == 'ok' and w[7] == '0' and i + 2 < len(oc):
            oc[i + 2]['counts'] = oc[i + 2]['counts']
    json.dump(oc, open(os.path.join(pics, 'occt_%s.json' % n), 'w'))
    title = '%s — %s%s' % (cid, c[4] if len(c) > 4 else '', '  (ours: STEP reader + driver-side orientation repair)' if repair and 'step=' in a + b else '')
    jobs.append([n, title])
for k in range(0, len(jobs), 8):
    batch = jobs[k:k + 8]
    subprocess.run(['node', os.path.join(pics, 'shoot.cjs'), pics, json.dumps(batch)], cwd=pics, timeout=1800,
                   env=dict(os.environ, NODE_PATH='/opt/node-tools/node_modules'))
    for n, _ in batch:
        src = os.path.join(pics, 'cmp_%s.png' % n)
        if os.path.exists(src):
            os.replace(src, os.path.join(images, 'cmp_%s.png' % n))
            print('image', n)
        else:
            print('MISSING', n)
