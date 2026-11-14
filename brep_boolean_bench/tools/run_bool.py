# Run the boolean cases on one kernel, one process per (case, op) for ours and per case for OCCT.
#   run_bool.py ours|occt <cases.tsv> <out.txt> [--repair] [--jobs N] [--dump DIR] [--filter REGEX] [--limit S]
# out lines: case <TAB> side <TAB> BOOL op status bool_s faces edges vertices valid solid vol_s volume [message]
import sys, os, subprocess, re, time, json, concurrent.futures as cf

T = os.path.dirname(os.path.abspath(__file__))
PY = '/tmp/claude-0/-home-user/8b288b7c-72c4-56e2-9565-a39939e050f9/scratchpad/ocp/venv/bin/python'
OPS = ['intersection', 'union', 'a-b', 'b-a', 'xor']
side, cases_f, out_f = sys.argv[1:4]
args = sys.argv[4:]
repair = '--repair' in args
jobs = int(args[args.index('--jobs') + 1]) if '--jobs' in args else 2
dump = args[args.index('--dump') + 1] if '--dump' in args else None
filt = re.compile(args[args.index('--filter') + 1]) if '--filter' in args else None
limit = float(args[args.index('--limit') + 1]) if '--limit' in args else 120.0
cases = [l.rstrip('\n').split('\t') for l in open(cases_f) if l.strip() and not l.startswith('#')]
if filt:
    cases = [c for c in cases if filt.search(c[0])]
label = side + ('_rep' if repair else '')
done = set()
if os.path.exists(out_f):
    for l in open(out_f):
        w = l.split('\t')
        if len(w) > 2:
            done.add((w[0], w[2].split()[1]))


def safe(name):
    return re.sub(r'[^A-Za-z0-9_.-]', '_', name)


def run_ours(case, op):
    cid, a, b = case[0], case[1], case[2]
    env = dict(os.environ)
    if repair:
        env['REPAIR'] = '1'
    cmd = [os.path.join(T, 'ours_step_bench'), 'bool', a, b, op]
    if dump:
        cmd.append(os.path.join(dump, 'ours_%s_%s.json' % (safe(cid), op)))
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=limit + 120, env=env,
                           preexec_fn=lambda: __import__('resource').setrlimit(__import__('resource').RLIMIT_AS, (6 << 30, 6 << 30)))
        lines = [l for l in p.stdout.splitlines() if l.startswith('BOOL')]
        if lines:
            line = lines[-1]
            w = line.split()
            if w[2] == 'ok' and float(w[3]) > limit:
                line = line + ' (over the %gs limit)' % limit
            return line
        return 'BOOL %s CRASH %.3f 0 0 0 0 0 - - exit %s %s' % (op, time.time() - t0, p.returncode, (p.stderr.strip().splitlines() or [''])[-1][:200])
    except subprocess.TimeoutExpired:
        return 'BOOL %s TIMEOUT %.3f 0 0 0 0 0 - - wall limit %gs' % (op, time.time() - t0, limit + 120)


def run_occt(case):
    cid, a, b = case[0], case[1], case[2]
    cmd = [PY, '-I', os.path.join(T, 'occt_step_bench.py'), 'bool', a, b]
    if dump:
        cmd.append(os.path.join(dump, 'occt_%s.json' % safe(cid)))
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        lines = [l for l in p.stdout.splitlines() if l.startswith('BOOL')]
        got = {l.split()[1]: l for l in lines}
        return [got.get(op, 'BOOL %s CRASH %.3f 0 0 0 0 0 - - exit %s' % (op, time.time() - t0, p.returncode)) for op in OPS]
    except subprocess.TimeoutExpired:
        return ['BOOL %s TIMEOUT 900 0 0 0 0 0 - - case wall limit 900s' % op for op in OPS]


with open(out_f, 'a') as out:
    if side == 'occt':
        for case in cases:
            if all((case[0], op) in done for op in OPS):
                continue
            for line in run_occt(case):
                out.write('%s\t%s\t%s\n' % (case[0], label, line))
            out.flush()
    else:
        todo = [(c, op) for c in cases for op in OPS if (c[0], op) not in done]
        with cf.ThreadPoolExecutor(max_workers=jobs) as ex:
            futs = {ex.submit(run_ours, c, op): (c, op) for c, op in todo}
            for f in cf.as_completed(futs):
                c, op = futs[f]
                out.write('%s\t%s\t%s\n' % (c[0], label, f.result()))
                out.flush()
