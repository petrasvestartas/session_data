# Assemble RESULTS.md from the intro text, the load table, the boolean summary, the chain runs and the image list.
#   make_results.py <intro.md> <load_table.tsv> <summary.md> <chain_ours.txt> <chain_occt.txt> <images dir> <rows.tsv> > RESULTS.md
import sys, csv, os, collections, math
intro, load_f, summary_f, chain_ours, chain_occt, images, rows_f = sys.argv[1:8]
print(open(intro).read())

print('## Load: every file through both STEP readers\n')
print('Columns: STEP faces = ADVANCED_FACE + FACE_SURFACE entities in the file; ours/OCCT faces and kinds are of the largest solid')
print('(kinds: plane, sphere, cylinder, cone, torus, free-form; ours from `nurbs_implicit::recognize` on its NURBS surfaces,')
print('OCCT from GeomAbs types); volumes in file units (OCCT scaled back from millimetres); `(mesh)` = ours volume_exact threw and')
print('the tessellated volume is shown; repaired = driver-side wire/face orientation repair (not kernel code, see above).\n')
rows = list(csv.reader(open(load_f), delimiter='\t'))
hdr = rows[0]
keep = [0, 1, 4, 5, 6, 7, 8, 9, 12, 13, 14, 15, 16, 17, 19, 20, 21, 22]
print('| ' + ' | '.join(hdr[i] for i in keep) + ' |')
print('|' + '---|' * len(keep))
for r in rows[1:]:
    print('| ' + ' | '.join((r[i] if i < len(r) else '').replace('|', '/') for i in keep) + ' |')
print()
print(open(summary_f).read())

print('## occt-booltest chain on the bottle (body ← body ∩ rotated(body), 5 iterations)\n')
print('Rotation about the axis through (0, 0, 38.5), the bottle\'s box centre. Columns: iteration, status, seconds, faces, volume.\n')
runs = collections.OrderedDict()
for fn in (chain_occt, chain_ours):
    for l in open(fn):
        w = l.split()
        if len(w) > 3 and w[2] == 'CHAIN':
            key = (w[0], w[1])
            vol = w[12] if w[4] == 'ok' else ' '.join(w[13:])[:90]
            runs.setdefault(key, []).append('%s %s %.3gs %s faces, %s' % (w[3], w[4], float(w[5]), w[6], vol) if w[4] == 'ok' else '%s FAIL %.3gs: %s' % (w[3], float(w[5]), vol))
print('| kernel | axis, degrees | iterations |\n|---|---|---|')
for (k, rot), its in runs.items():
    print('| %s | %s | %s |' % (k, rot, '<br>'.join(its)))
print()

print('## Pictures\n')
print('One per benchmarked part (its slab-cutter case `#box`) plus the forum rebuilds and part pairs. Top row ours, bottom row')
print('OCCT; columns operands A (grey) and B (tan), then A∩B, A∪B, A−B, B−A, A⊕B; red squares are vertices, black lines edges;')
print('counts under each panel, red where ours and OCCT differ; a failed boolean or load is an empty panel with its error.\n')
rows = {}
for l in list(csv.reader(open(rows_f), delimiter='\t'))[1:]:
    rows.setdefault(l[0], []).append(l)
print('| case | part | ours (repaired input) | OCCT | image |\n|---|---|---|---|---|')
for f in sorted(os.listdir(images)):
    if not f.endswith('.png'):
        continue
    n = f[4:-4]
    case = None
    for c in rows:
        if c.replace('#', '_') == n or ''.join(ch if ch.isalnum() or ch in '_.-' else '_' for ch in c) == n:
            case = c
    rr = [r for r in rows.get(case, []) if r[4] == 'rep'] or rows.get(case, [])
    ours = collections.Counter(r[6] for r in rr)
    occt = collections.Counter(r[14] for r in rr)
    part = rr[0][2] if rr else ''
    fmt = lambda c: ', '.join('%s %d' % (k, v) for k, v in sorted(c.items()))
    print('| `%s` | %s | %s | %s | [%s](images/%s) |' % (case or n, part, fmt(ours), fmt(occt), f, f))
print()
