# MANIFEST.md of brep_boolean_bench: per file source, license, size, faces, surface kinds (from the OCCT load).
#   gen_manifest.py <bench_root> <occt_load.txt> > MANIFEST.md
import sys, os, re, collections
root, occt_load = sys.argv[1:3]
occt = {}
for line in open(occt_load):
    w = line.split()
    if w and w[0] == 'LOAD':
        occt[w[1]] = {'solids': int(w[6]) if w[2] == 'ok' else 0, 'list': []}
    elif w and w[0] == 'SOLID':
        occt[w[1]]['list'].append((int(w[3]), w[7][6:]))

NIST = 'https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/'
nist_paths = {
    'RestButton1.stp': 'models/ICEM-CDC/Fixture_Models/RestButton1/RestButton1.hh.sat.stp',
    'KnurledKnob10.stp': 'models/ICEM-CDC/Fixture_Models/KnurledKnob10/KnurledKnob10.hh.sat.stp',
    'sh-r44356-000-u.stp': 'models/Sandia/Randy_Wilson/discriminator/sh-r44356-000-u/sh-r44356-000-u.hh.sat.stp',
    'sh-r44363-000-u-compressed.stp': 'models/Sandia/Randy_Wilson/discriminator/sh-r44363-000-u-compressed/sh-r44363-000-u-compressed.hh.sat.stp',
    'DoubleCam1.stp': 'models/ICEM-CDC/Fixture_Models/DoubleCam1/DoubleCam1.hh.sat.stp',
    'NC_DRIVE.stp': 'models/SDRC_I-DEAS/NC_DRIVE/NC_DRIVE.stp',
    'needle-nose-inch.stp': 'models/CMU/Tools/needle-nose-inch.hh.sat.stp',
    'bolt.stp': 'models/PTC/V18/asmdes18/parts/bolt.prt.hh.sat.stp',
    'chamber.stp': 'models/VDS/chamber/chamber.stp',
    'bellow.stp': 'models/NIST/Manfred_Osti/spectrometer/bellow/bellow.prt.hh.sat.stp',
    'flange.stp': 'models/Parasolid/NIST/Pete_Brown/flange/flange.step.hh.sat.stp',
    'fork.stp': 'models/VDS/fork/fork.stp',
    'screw_driver1.stp': 'models/CMU/Tools/screw_driver1.hh.sat.stp',
    'moon_buggy.stp': 'models/STEP/STI/moon_buggy/moon_buggy.hh.sat.stp',
    '260012.stp': 'models/Parasolid/NIST/Pete_Brown/260012/260012.step.hh.sat.stp',
    'main_block.stp': 'models/NIST/Manfred_Osti/spectrometer/main_block/main_block.hh.sat.stp',
    'mt_jaw_half_finish-mach-bup.stp': 'models/VDS/mt_jaw_half_finish-mach-bup/mt_jaw_half_finish-mach-bup.stp',
    'stock.stp': 'models/Parasolid/NIST/Pete_Brown/Torpedo_Motor/stock/stock.hh.sat.stp',
    'interactingPockets.stp': 'models/STEP/STI/interactingPockets/interactingPockets.hh.sat.stp',
    'clevis21.stp': 'models/STEP/STI/clevis21/clevis21.hh.sat.stp',
    'swivel1-Part.step': 'models/UMD/swivel1-Part/swivel1-Part.step',
    'anc101_a.stp': 'models/Parasolid/NIST/Bill_Regli/anc101_a/anc101_a.hh.sat.stp',
    'gear_40.stp': 'models/PTC/Legos/stepmodels/gear_40.stp',
}
zipnames = {
    'zip_chainlinkouter00.stp': 'Chain Link Outer_chainlinkouter00.stp',
    'zip_defaultamacchina000.stp': 'Compressore ATLAS COPCO FLX07_defaultamacchina000.stp',
    'zip_dripmanifold0.stp': 'DRIP MANIFOLD_dripmanifold0.stp',
    'zip_dfautbrutdusinage0001.stp': 'ECH skid maintien de pression Limoges_dfautbrutdusinage0001.stp',
    'zip_cylinder400bore000.stp': 'cylinder 4.00 bore_cylinder400bore000.stp',
    'zip_cylinder600bore000.stp': 'cylinder 6.00 bore_cylinder600bore000.stp',
    'zip_doorlatchvonduprin0001.stp': 'door latch Von Duprin 230L 06 SP28 LHR_doorlatchvonduprin0001.stp',
    'zip_ea0000006992revit.stp': 'ea0000006992revit.stp',
    'zip_ea0000006997revit.stp': 'ea0000006997revit.stp',
    'zip_ea0000007008revit.stp': 'ea0000007008revit.stp',
}


def source(rel):
    d, f = rel.split('/', 1)
    if d == 'nist_edm':
        return NIST + nist_paths[f], 'Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice)'
    if d == 'hf_brepmfr':
        base = 'https://huggingface.co/datasets/Silly98/BrepMFR/resolve/a32f70fd92513bf4b6514d54ed68a851c2c25b3c/'
        if f.startswith('zip_'):
            return base + 'stp.zip (member stp/%s)' % zipnames[f], 'apache-2.0 (dataset card); provenance of the parts not stated, see note'
        return base + f, 'apache-2.0 (dataset card); provenance of the parts not stated, see note'
    if d == 'hf_brepground':
        return ('https://huggingface.co/datasets/jhlee11/BRepGround/resolve/3b963b0bac7fbdd54785a09f7f32405652c8e76a/'
                'assets/test-00001-of-00002.zip (member steps/%s)' % f), 'CC BY 4.0, (c) 2026 Jiahao Li, Qingwang Zhang, Qiuyu Chen, Guozhan Qiu, Yunzhong Lou, Xiangdong Zhou'
    if d == 'hf_zero_to_cad':
        u = f.split('.')[0]
        return ('https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100 '
                '(row uuid %s, column %s)' % (u, 'cadquery_file' if f.endswith('.py') else 'step_file')), 'apache-2.0 (dataset card)'
    if d == 'occt_data':
        base = 'https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/4dbfdcc448c0b3e565488afcd626c84483172db9/'
        if f.endswith('_from_brep.step'):
            return base + 'data/occ/%s.brep, converted to STEP AP214 with tools/brep2step.py (largest solid)' % f[:-len('_from_brep.step')], 'LGPL-2.1 with the OCCT exception (OCCT repository data)'
        return base + 'data/step/' + f, 'LGPL-2.1 with the OCCT exception (OCCT repository data)'
    if d == 'github_misc':
        if f.startswith('nema'):
            return 'https://raw.githubusercontent.com/gumyr/build123d/42ea4f7dcfc3d4aa6ee81b88e558197576ff6273/docs/topology_selection/examples/nema-17-bracket.step', 'Apache-2.0 (build123d repository)'
        return 'https://raw.githubusercontent.com/FreeCAD/FreeCAD/8280c2e41ab06f138fc35da83ab1b1fb9723714e/data/tests/Step/as1-ac-214.stp', 'LGPL-2.1-or-later (FreeCAD repository test data)'
    if d == 'occt_booltest':
        return 'https://raw.githubusercontent.com/kaige/occt-booltest/bb9b85a52dcf0e6ff421390371b27b741bb9b5fe/corpus-index/bottle.step', 'CC-BY-4.0 (corpus data, per the repository README; code MIT; no LICENSE file in the repository)'
    if d == 'mcneel_rebuilt':
        return 'generated by tools/gen_forum.py (OCCT 8.0.1 via cadquery-ocp); rebuilds the configuration of a McNeel forum thread, no forum file used', 'own work for this bench (same terms as this repository)'
    return '?', '?'


KIND = ['plane', 'sphere', 'cylinder', 'cone', 'torus', 'free-form']
rows = collections.defaultdict(list)
for dp, dn, fn in os.walk(root):
    for f in fn:
        p = os.path.join(dp, f)
        rel = os.path.relpath(p, root)
        if '/' not in rel or rel.startswith(('tools/', 'images/', 'results/')):
            continue
        if not re.search(r'\.(stp|step|py)$', f, re.I):
            continue
        url, lic = source(rel)
        o = occt.get(p)
        faces = kinds = solids = '-'
        if o and o['list']:
            solids = o['solids']
            faces = sum(x[0] for x in o['list'])
            tot = [0] * 6
            for _, k in o['list']:
                for i, v in enumerate(k.split(',')):
                    tot[i] += int(v)
            kinds = ', '.join('%s %d' % (KIND[i], tot[i]) for i in range(6) if tot[i])
        elif o:
            solids = 0
        rows[rel.split('/')[0]].append((rel, os.path.getsize(p), solids, faces, kinds, url, lic))

print('''# brep_boolean_bench: STEP parts for BRep boolean benchmarks

Real and non-primitive solids (fillets, rounds, chamfers, free-form NURBS, threads, pockets, thin walls) collected on
2026-11-14 for comparing session_cpp booleans with OCCT. `fetch.sh` re-downloads everything from the pinned revisions;
`tools/` holds the drivers, `RESULTS.md` the results. Faces, solids and surface kinds below are from OCCT 8.0.1's STEP
reader over all solids of the file (free-form = B-spline, Bezier, surface of revolution or extrusion, offset).

Files are kept only where the source states a license that allows redistribution. Notes per source:

- **nist_edm**: NIST Engineering Design Model Repository (github.com/usnistgov/engineering-design-models), 1990s
  industry parts. Public domain in the US; keep the NIST notice of its LICENSE.md with the files. 23 of 2411 STEP files
  taken, chosen over vendors and surface kinds; `swivel1-Part.step` is AP203 with FACE_SURFACE faces (kept on purpose).
  The repository itself is 7 GB; files were fetched sparsely, no LFS stubs among them.
- **hf_brepmfr**: Hugging Face Silly98/BrepMFR, dataset card license apache-2.0. The files look like third-party vendor
  parts (Atlas Copco, Von Duprin, Revit exports); the uploader states apache-2.0 but not their origin. Review before
  committing; the license is the uploader's claim.
- **hf_brepground**: Hugging Face jhlee11/BRepGround, CC BY 4.0. Attribution: "BRepGround, Jiahao Li, Qingwang Zhang,
  Qiuyu Chen, Guozhan Qiu, Yunzhong Lou and Xiangdong Zhou, ICML 2026, arXiv:2603.11831,
  https://huggingface.co/datasets/jhlee11/BRepGround". Ten of the 857 solids of shard test-00001, spread over 10 to 120
  faces, preferring B-spline and torus faces, one per parent model. The zip itself is not kept.
- **hf_zero_to_cad**: Hugging Face ADSKAILab/Zero-To-CAD-1m, apache-2.0. Ten test rows over 14 to 124 faces; the STEP
  is the dataset's own `step_file` column (no CadQuery run needed); the CadQuery source of each row is kept beside it.
- **occt_data**: Open CASCADE repository sample data (LGPL-2.1 with the OCCT exception). `screw.step`, `linkrods.step`
  as is; seven `.brep` samples converted to STEP with OCCT (largest solid of the file).
- **github_misc**: build123d `nema-17-bracket.step` (Apache-2.0), FreeCAD `as1-ac-214.stp` (LGPL-2.1+, an assembly of
  plates, brackets, bolts and nuts).
- **occt_booltest**: the STEP input of github.com/kaige/occt-booltest (the OCCT tutorial bottle with its thread), whose
  corpus data is CC-BY-4.0 per its README.
- **mcneel_rebuilt**: own geometry rebuilding two McNeel forum failures (helical thread cutter, t/216730; closed solid of
  mesh triangles, t/123416). The forum attachments themselves (.3dm, and one .step) are not redistributable (forum
  terms) and were not downloaded.
''')
total = 0
for d in sorted(rows):
    print('## %s\n' % d)
    print('| file | size | solids | faces | surface kinds | source | license |')
    print('|---|---|---|---|---|---|---|')
    for rel, size, solids, faces, kinds, url, lic in sorted(rows[d]):
        total += size
        print('| `%s` | %s | %s | %s | %s | %s | %s |' % (rel.split('/', 1)[1], '%.0f KB' % (size / 1024), solids, faces, kinds, url, lic))
    print()
print('Total %.1f MB in %d files.' % (total / 1048576, sum(len(v) for v in rows.values())))
