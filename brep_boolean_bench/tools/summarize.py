# Join the boolean result files into per-op rows and summary tables (markdown on stdout, TSV beside).
#   summarize.py cases.tsv bool_occt.txt bool_ours_rep.txt bool_ours_raw.txt load_table.tsv out_rows.tsv > summary.md
import sys, collections, statistics, math, csv
cases_f, occt_f, rep_f, raw_f, load_f, rows_f = sys.argv[1:7]
OPS = ['intersection', 'union', 'a-b', 'b-a', 'xor']
cases = collections.OrderedDict()
for l in open(cases_f):
    w = l.rstrip('\n').split('\t')
    if len(w) >= 5:
        cases[w[0]] = {'a': w[1], 'b': w[2], 'group': w[3], 'part': w[4]}


def parse(fn):
    d = {}
    try:
        lines = open(fn, errors='replace').read().splitlines()
    except FileNotFoundError:
        return d
    for l in lines:
        c, side, rest = l.split('\t', 2)
        w = rest.split()
        op, st = w[1], w[2]
        r = {'status': st, 's': float(w[3]) if w[3] not in ('-',) else math.nan, 'msg': ''}
        if st == 'ok':
            r.update(faces=int(w[4]), edges=int(w[5]), verts=int(w[6]), valid=int(w[7]), solid=int(w[8]))
            vol = w[10] if len(w) > 10 else 'nan'
            r['mesh_volume'] = vol.endswith('(mesh)')
            try:
                r['vol'] = float(vol.replace('(mesh)', ''))
            except ValueError:
                r['vol'] = math.nan
            r['msg'] = ' '.join(w[11:])
        else:
            r['msg'] = ' '.join(w[11:]) if len(w) > 11 else ' '.join(w[4:])
        d[(c, op)] = r
    return d


occt, rep, raw = parse(occt_f), parse(rep_f), parse(raw_f)
matched = set()
for r in csv.reader(open(load_f), delimiter='\t'):
    try:
        if r[20] == '1' and float(r[22]) < 1e-2:
            matched.add(r[0])
    except (ValueError, IndexError):
        pass


def rel(a, b, scale):
    if math.isnan(a) or math.isnan(b):
        return math.nan
    return abs(abs(a) - abs(b)) / max(abs(scale), 1e-300)


def consistent(res, c):
    # kernel-internal volume identities: |A∪B| = |A−B| + |B−A| + |A∩B|, |A⊕B| = |A−B| + |B−A|
    try:
        i, u, ab, ba, x = (abs(res[(c, op)]['vol']) for op in OPS)
    except KeyError:
        return None
    if any(math.isnan(v) for v in (i, u, ab, ba, x)):
        return None
    s = max(u, 1e-300)
    return max(abs(u - (ab + ba + i)) / s, abs(x - (ab + ba)) / s)


rows = []
for c, info in cases.items():
    # scale for volume differences: OCCT union volume (or largest result)
    vols = [abs(occt[(c, op)]['vol']) for op in OPS if (c, op) in occt and occt[(c, op)]['status'] == 'ok' and not math.isnan(occt[(c, op)]['vol'])]
    scale = max(vols) if vols else math.nan
    for op in OPS:
        o = occt.get((c, op))
        for name, res in (('rep', rep), ('raw', raw)):
            u = res.get((c, op))
            if not o and not u:
                continue
            row = {'case': c, 'group': info['group'], 'part': info['part'], 'op': op, 'series': name,
                   'matched': info['part'] in matched or not info['a'].startswith('step=') and not info['b'].startswith('step=')}
            for tag, r in (('ours', u), ('occt', o)):
                if r is None:
                    row[tag + '_status'] = 'not run'
                    continue
                row[tag + '_status'] = r['status']
                row[tag + '_s'] = r['s']
                row[tag + '_msg'] = r['msg']
                if r['status'] == 'ok':
                    for k in ('faces', 'edges', 'verts', 'valid', 'solid', 'vol'):
                        row[tag + '_' + k] = r[k]
            if u and o and u['status'] == 'ok' and o['status'] == 'ok':
                row['dvol'] = rel(u['vol'], o['vol'], scale if not math.isnan(scale) and scale > 0 else max(abs(o['vol']), 1e-300))
            rows.append(row)

keys = ['case', 'group', 'part', 'op', 'series', 'matched', 'ours_status', 'ours_s', 'ours_faces', 'ours_edges', 'ours_verts', 'ours_valid',
        'ours_solid', 'ours_vol', 'occt_status', 'occt_s', 'occt_faces', 'occt_edges', 'occt_verts', 'occt_valid', 'occt_solid', 'occt_vol',
        'dvol', 'ours_msg', 'occt_msg']
with open(rows_f, 'w') as f:
    f.write('\t'.join(keys) + '\n')
    for r in rows:
        f.write('\t'.join(str(r.get(k, '')) for k in keys) + '\n')


def summary(sel, title):
    sel = [r for r in sel if r.get('ours_status', 'not run') != 'not run']
    n = len(sel)
    if not n:
        return
    def cnt(tag, pred):
        return sum(1 for r in sel if pred(r, tag))
    ok = lambda r, t: r.get(t + '_status') == 'ok'
    print('### %s (%d booleans)\n' % (title, n))
    print('| | ours | OCCT |\n|---|---|---|')
    print('| result returned | %d | %d |' % (cnt('ours', ok), cnt('occt', ok)))
    print('| failed with an error | %d | %d |' % (cnt('ours', lambda r, t: r.get(t + '_status') == 'FAIL'), cnt('occt', lambda r, t: r.get(t + '_status') == 'FAIL')))
    print('| timeout / crash | %d | %d |' % (cnt('ours', lambda r, t: r.get(t + '_status') in ('TIMEOUT', 'CRASH')), cnt('occt', lambda r, t: r.get(t + '_status') in ('TIMEOUT', 'CRASH'))))
    print('| returned non-empty but not valid (ours is_valid, OCCT BRepCheck) | %d | %d |' % (cnt('ours', lambda r, t: ok(r, t) and r.get(t + '_faces', 0) > 0 and not r.get(t + '_valid')), cnt('occt', lambda r, t: ok(r, t) and r.get(t + '_faces', 0) > 0 and not r.get(t + '_valid'))))
    print('| returned, valid, not a closed solid (ours is_solid; OCCT: no solid) | %d | %d |' % (
        cnt('ours', lambda r, t: ok(r, t) and r.get(t + '_valid') and not r.get(t + '_solid') and r.get(t + '_faces', 0) > 0),
        cnt('occt', lambda r, t: ok(r, t) and r.get(t + '_valid') and not r.get(t + '_solid') and r.get(t + '_faces', 0) > 0)))
    print('| empty result | %d | %d |' % (cnt('ours', lambda r, t: ok(r, t) and r.get(t + '_faces', 0) == 0), cnt('occt', lambda r, t: ok(r, t) and r.get(t + '_faces', 0) == 0)))
    both = [r for r in sel if ok(r, 'ours') and ok(r, 'occt')]
    dv = [r['dvol'] for r in both if 'dvol' in r and not math.isnan(r['dvol'])]
    if dv:
        print('| both returned: volume agrees to 1e-6 / 1e-3 / worse (of the larger result volume of the case) | %d / %d / %d | |' % (
            sum(1 for x in dv if x <= 1e-6), sum(1 for x in dv if 1e-6 < x <= 1e-3), sum(1 for x in dv if x > 1e-3)))
        same = sum(1 for r in both if r.get('ours_faces') == r.get('occt_faces'))
        print('| both returned: same face count | %d of %d | |' % (same, len(both)))
    for label, ops in (('single booleans (∩, ∪, A−B, B−A)', OPS[:4]), ('xor (OCCT: two cuts and a fuse)', OPS[4:])):
        t = [(r['ours_s'], r['occt_s']) for r in both if r['op'] in ops and r.get('occt_s', 0) > 0]
        if t:
            ratios = [a / b for a, b in t]
            print('| time, %s, both returned (%d): total s | %.3g | %.3g |' % (label, len(t), sum(a for a, _ in t), sum(b for _, b in t)))
            print('| time ratio ours/OCCT, %s: median, total | %.3g, %.3g | |' % (label, statistics.median(ratios), sum(a for a, _ in t) / sum(b for _, b in t)))
    ta = [r['ours_s'] for r in sel if r.get('ours_status') in ('ok', 'FAIL') and not math.isnan(r.get('ours_s', math.nan))]
    tb = [r['occt_s'] for r in sel if r.get('occt_status') in ('ok', 'FAIL') and not math.isnan(r.get('occt_s', math.nan))]
    if ta and tb:
        print('| time of every boolean that ended (ok or error), total s | %.3g | %.3g |' % (sum(ta), sum(tb)))
    print()


print('## Boolean summary\n')
allocct = [r for (c, op), r in occt.items()]
print('### OCCT over every case (%d booleans in %d cases)\n' % (len(allocct), len({c for c, _ in occt})))
print('| returned | error | timeout/crash | non-empty and not valid (BRepCheck) | empty |\n|---|---|---|---|---|')
print('| %d | %d | %d | %d | %d |\n' % (sum(1 for r in allocct if r['status'] == 'ok'), sum(1 for r in allocct if r['status'] == 'FAIL'),
      sum(1 for r in allocct if r['status'] in ('TIMEOUT', 'CRASH')), sum(1 for r in allocct if r['status'] == 'ok' and r['faces'] > 0 and not r['valid']),
      sum(1 for r in allocct if r['status'] == 'ok' and r['faces'] == 0)))
rep_rows = [r for r in rows if r['series'] == 'rep']
raw_rows = [r for r in rows if r['series'] == 'raw']
summary([r for r in raw_rows], 'ours as the reader delivers the parts (raw), all cases')
summary([r for r in rep_rows if r['matched'] and r['group'] in ('rot', 'cutter')], 'ours with driver-side orientation repair, parts whose repaired volume matches OCCT (< 1e-2): rotated copies and cutters')
summary([r for r in rep_rows if r['matched'] and r['group'] == 'rot'], '... of which rotated copies of the part (occt-booltest style)')
summary([r for r in rep_rows if r['matched'] and r['group'] == 'cutter'], '... of which box, cylinder and sphere cutters')
summary([r for r in rep_rows if not r['matched'] and r['group'] in ('rot', 'cutter')], 'ours with repair, parts whose repaired volume does NOT match OCCT (inputs differ; success counts only)')
summary([r for r in rep_rows if r['group'] in ('forum', 'pair')], 'forum rebuilds and part pairs')

# OCCT internal consistency and per-kernel volume identities
print('## Volume identities per kernel\n')
print('Per case: max(| |A∪B| − (|A−B| + |B−A| + |A∩B|) |, | |A⊕B| − (|A−B| + |B−A|) |) / |A∪B|, over cases where all five returned.\n')
print('| series | cases | ≤ 1e-6 | ≤ 1e-3 | worse |\n|---|---|---|---|---|')
for name, res, filt in (('OCCT', occt, lambda c: True), ('ours (repaired input, matched parts + forum/pairs)', rep,
                         lambda c: cases[c]['part'] in matched or cases[c]['group'] in ('forum', 'pair'))):
    vals = [v for v in (consistent(res, c) for c in cases if filt(c)) if v is not None]
    if vals:
        print('| %s | %d | %d | %d | %d |' % (name, len(vals), sum(1 for v in vals if v <= 1e-6), sum(1 for v in vals if 1e-6 < v <= 1e-3), sum(1 for v in vals if v > 1e-3)))
print()
bad = [(c, consistent(occt, c)) for c in cases]
bad = [(c, v) for c, v in bad if v is not None and v > 1e-3]
if bad:
    print('OCCT cases breaking the identities by more than 1e-3: ' + ', '.join('`%s` (%.2g)' % (c, v) for c, v in bad) + '\n')
inv = sorted({c for (c, op), r in occt.items() if r['status'] == 'ok' and r['faces'] > 0 and not r['valid']})
if inv:
    print('OCCT cases with a BRepCheck-invalid result: ' + ', '.join('`%s` (%s)' % (c, '/'.join(op for op in OPS if (c, op) in occt and occt[(c, op)]['status'] == 'ok' and occt[(c, op)]['faces'] > 0 and not occt[(c, op)]['valid'])) for c in inv) + '\n')

# error messages of ours, grouped
print('## Our error messages (repaired series), by count\n')
msgs = collections.Counter()
for r in rep_rows:
    if r.get('ours_status') in ('FAIL', 'TIMEOUT', 'CRASH'):
        m = r.get('ours_msg', '')
        m = m.split(':')[0] if ':' in m and len(m) > 90 else m
        msgs[(r['ours_status'], m[:140])] += 1
print('| status | message (to the first colon) | booleans |\n|---|---|---|')
for (st, m), k in msgs.most_common(25):
    print('| %s | %s | %d |' % (st, m.replace('|', '/'), k))
print()
print('## OCCT failures\n')
msgs = collections.Counter()
for (c, op), r in occt.items():
    if r['status'] != 'ok':
        msgs[(r['status'], r['msg'][:100])] += 1
    elif not r.get('valid'):
        msgs[('invalid', 'BRepCheck_Analyzer: not valid')] += 1
print('| status | message | booleans |\n|---|---|---|')
for (st, m), k in msgs.most_common(15):
    print('| %s | %s | %d |' % (st, m.replace('|', '/'), k))
print()
