# Join ours_load.txt and occt_load.txt into one row per file (markdown) + a TSV.
#   load_table.py ours_load.txt occt_load.txt bench_root out.md out.tsv
import sys, re, collections, os
ours_f, occt_f, root, out_md, out_tsv, rep_f = sys.argv[1:7]


def parse_ours(fn):
  ours = collections.OrderedDict()
  for line in open(fn, errors='replace'):
      w = line.split()
      if not w:
          continue
      if w[0] == 'LOAD':
          ours[w[1]] = {'status': w[2], 'read_s': float(w[4]), 'n': int(w[6]) if len(w) > 6 else 0, 'msg': ' '.join(w[7:]), 'breps': []}
      elif w[0] == 'BREP':
          k = re.search(r'kinds=(\S+)', line).group(1)
          tail = line.split('kinds=')[1].split()
          ours[w[1]]['breps'].append({'faces': int(w[3]), 'edges': int(w[4]), 'verts': int(w[5]), 'valid': int(w[8]), 'solid': int(w[9]),
                                      'kinds': k, 'vol': tail[2] if len(tail) > 2 else '-'})
      elif w[0] == 'DIAG':
          ours[w[1]]['breps'][-1]['diag'] = ' '.join(x for x in w[3:] if not x.endswith('=0'))
      elif w[0] == 'EXIT':
          if w[1] in ours:
              ours[w[1]]['exit'] = int(w[2])
          else:
              ours[w[1]] = {'status': 'CRASH' if w[2] != '124' else 'TIMEOUT', 'read_s': 0, 'n': 0, 'msg': 'exit ' + w[2], 'breps': [], 'exit': int(w[2])}
  return ours


ours = parse_ours(ours_f)
rep = parse_ours(rep_f)
occt = collections.OrderedDict()
for line in open(occt_f, errors='replace'):
    w = line.split()
    if not w:
        continue
    if w[0] == 'LOAD':
        occt[w[1]] = {'status': w[2], 'read_s': float(w[4]), 'n': int(w[6]), 'solids': []}
    elif w[0] == 'SOLID':
        occt[w[1]]['solids'].append({'faces': int(w[3]), 'edges': int(w[4]), 'verts': int(w[5]), 'valid': int(w[6]),
                                     'kinds': w[7][6:], 'vol': w[9]})


def big(lst):
    return max(lst, key=lambda b: abs(float(b['vol'].replace('(mesh)', ''))) if b['vol'] not in ('-', 'nan') else -1) if lst else None


rows = []
for path in sorted(set(ours) | set(occt)):
    o, c = ours.get(path), occt.get(path)
    rel = os.path.relpath(path, root)
    ob, cb = big(o['breps']) if o else None, big(c['solids']) if c else None
    stepfaces = sum(1 for l in open(path, errors='replace') if re.match(r'\s*#\d+\s*=\s*(ADVANCED_FACE|FACE_SURFACE)\b', l))
    def fv(b):
        try:
            return float(b['vol'].replace('(mesh)', ''))
        except Exception:
            return float('nan')
    dv = ''
    if ob and cb:
        a, b = abs(fv(ob)), abs(fv(cb))
        dv = '%.2e' % (abs(a - b) / max(b, 1e-300))
    r_ = rep.get(path)
    rb = big(r_['breps']) if r_ else None
    dr = ''
    if rb and cb:
        a, b = fv(rb), fv(cb)
        dr = '%.2e' % (abs(a - b) / max(abs(b), 1e-300))
    rows.append([rel, stepfaces,
                 (o['status'] if o else '-'), ('%.3g' % o['read_s']) if o else '-', (o['n'] if o else 0),
                 ob['faces'] if ob else 0, ob['valid'] if ob else '-', ob['solid'] if ob else '-', ob['kinds'] if ob else '-', ob['vol'] if ob else '-',
                 (c['status'] if c else '-'), ('%.3g' % c['read_s']) if c else '-', (c['n'] if c else 0),
                 cb['faces'] if cb else 0, cb['valid'] if cb else '-', cb['kinds'] if cb else '-', cb['vol'] if cb else '-', dv,
                 (o.get('msg', '') if o else ''), (ob or {}).get('diag', ''),
                 rb['solid'] if rb else '-', rb['vol'] if rb else '-', dr])
hdr = ['file', 'STEP faces', 'ours', 'ours read s', 'ours breps', 'ours faces*', 'ours is_valid', 'ours is_solid', 'ours kinds p,s,c,k,t,f',
       'ours volume', 'OCCT', 'OCCT read s', 'OCCT solids', 'OCCT faces*', 'OCCT valid', 'OCCT kinds p,s,c,k,t,f', 'OCCT volume', 'rel. vol diff', 'ours message', 'why not solid (ours raw)', 'ours repaired is_solid', 'ours repaired volume', 'repaired rel. vol diff']
with open(out_tsv, 'w') as f:
    f.write('\t'.join(hdr) + '\n')
    for r in rows:
        f.write('\t'.join(map(str, r)) + '\n')
with open(out_md, 'w') as f:
    f.write('| ' + ' | '.join(hdr) + ' |\n|' + '---|' * len(hdr) + '\n')
    for r in rows:
        f.write('| ' + ' | '.join(str(x).replace('|', '/') for x in r) + ' |\n')
print(len(rows), 'rows')
