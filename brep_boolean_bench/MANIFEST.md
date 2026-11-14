# brep_boolean_bench: STEP parts for BRep boolean benchmarks

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

## github_misc

| file | size | solids | faces | surface kinds | source | license |
|---|---|---|---|---|---|---|
| `as1-ac-214.stp` | 81 KB | 18 | 160 | plane 90, cylinder 70 | https://raw.githubusercontent.com/FreeCAD/FreeCAD/8280c2e41ab06f138fc35da83ab1b1fb9723714e/data/tests/Step/as1-ac-214.stp | LGPL-2.1-or-later (FreeCAD repository test data) |
| `nema-17-bracket.step` | 162 KB | 1 | 42 | plane 24, cylinder 18 | https://raw.githubusercontent.com/gumyr/build123d/42ea4f7dcfc3d4aa6ee81b88e558197576ff6273/docs/topology_selection/examples/nema-17-bracket.step | Apache-2.0 (build123d repository) |

## hf_brepground

| file | size | solids | faces | surface kinds | source | license |
|---|---|---|---|---|---|---|
| `00015160_chamfer_12.step` | 257 KB | 1 | 53 | plane 13, cylinder 23, cone 3, torus 8, free-form 6 | https://huggingface.co/datasets/jhlee11/BRepGround/resolve/3b963b0bac7fbdd54785a09f7f32405652c8e76a/assets/test-00001-of-00002.zip (member steps/00015160_chamfer_12.step) | CC BY 4.0, (c) 2026 Jiahao Li, Qingwang Zhang, Qiuyu Chen, Guozhan Qiu, Yunzhong Lou, Xiangdong Zhou |
| `00019536_chamfer_10.step` | 32 KB | 1 | 10 | plane 4, cylinder 2, torus 3, free-form 1 | https://huggingface.co/datasets/jhlee11/BRepGround/resolve/3b963b0bac7fbdd54785a09f7f32405652c8e76a/assets/test-00001-of-00002.zip (member steps/00019536_chamfer_10.step) | CC BY 4.0, (c) 2026 Jiahao Li, Qingwang Zhang, Qiuyu Chen, Guozhan Qiu, Yunzhong Lou, Xiangdong Zhou |
| `00042148_fillet_11.step` | 518 KB | 1 | 120 | plane 15, cylinder 51, torus 32, free-form 22 | https://huggingface.co/datasets/jhlee11/BRepGround/resolve/3b963b0bac7fbdd54785a09f7f32405652c8e76a/assets/test-00001-of-00002.zip (member steps/00042148_fillet_11.step) | CC BY 4.0, (c) 2026 Jiahao Li, Qingwang Zhang, Qiuyu Chen, Guozhan Qiu, Yunzhong Lou, Xiangdong Zhou |
| `00071814_fillet_15.step` | 366 KB | 1 | 80 | plane 20, cylinder 37, torus 13, free-form 10 | https://huggingface.co/datasets/jhlee11/BRepGround/resolve/3b963b0bac7fbdd54785a09f7f32405652c8e76a/assets/test-00001-of-00002.zip (member steps/00071814_fillet_15.step) | CC BY 4.0, (c) 2026 Jiahao Li, Qingwang Zhang, Qiuyu Chen, Guozhan Qiu, Yunzhong Lou, Xiangdong Zhou |
| `00089757_fillet_16.step` | 152 KB | 1 | 38 | plane 17, cylinder 15, torus 4, free-form 2 | https://huggingface.co/datasets/jhlee11/BRepGround/resolve/3b963b0bac7fbdd54785a09f7f32405652c8e76a/assets/test-00001-of-00002.zip (member steps/00089757_fillet_16.step) | CC BY 4.0, (c) 2026 Jiahao Li, Qingwang Zhang, Qiuyu Chen, Guozhan Qiu, Yunzhong Lou, Xiangdong Zhou |
| `00161395_chamfer_16.step` | 250 KB | 1 | 50 | plane 20, sphere 2, cylinder 20, torus 2, free-form 6 | https://huggingface.co/datasets/jhlee11/BRepGround/resolve/3b963b0bac7fbdd54785a09f7f32405652c8e76a/assets/test-00001-of-00002.zip (member steps/00161395_chamfer_16.step) | CC BY 4.0, (c) 2026 Jiahao Li, Qingwang Zhang, Qiuyu Chen, Guozhan Qiu, Yunzhong Lou, Xiangdong Zhou |
| `00170968_fillet_10.step` | 178 KB | 1 | 46 | plane 13, cylinder 16, torus 15, free-form 2 | https://huggingface.co/datasets/jhlee11/BRepGround/resolve/3b963b0bac7fbdd54785a09f7f32405652c8e76a/assets/test-00001-of-00002.zip (member steps/00170968_fillet_10.step) | CC BY 4.0, (c) 2026 Jiahao Li, Qingwang Zhang, Qiuyu Chen, Guozhan Qiu, Yunzhong Lou, Xiangdong Zhou |
| `00171214_fillet_11.step` | 172 KB | 1 | 19 | plane 5, cylinder 9, cone 2, torus 2, free-form 1 | https://huggingface.co/datasets/jhlee11/BRepGround/resolve/3b963b0bac7fbdd54785a09f7f32405652c8e76a/assets/test-00001-of-00002.zip (member steps/00171214_fillet_11.step) | CC BY 4.0, (c) 2026 Jiahao Li, Qingwang Zhang, Qiuyu Chen, Guozhan Qiu, Yunzhong Lou, Xiangdong Zhou |
| `00275424_fillet_17.step` | 74 KB | 1 | 21 | plane 6, cylinder 6, cone 3, torus 4, free-form 2 | https://huggingface.co/datasets/jhlee11/BRepGround/resolve/3b963b0bac7fbdd54785a09f7f32405652c8e76a/assets/test-00001-of-00002.zip (member steps/00275424_fillet_17.step) | CC BY 4.0, (c) 2026 Jiahao Li, Qingwang Zhang, Qiuyu Chen, Guozhan Qiu, Yunzhong Lou, Xiangdong Zhou |
| `00290572_chamfer_12.step` | 157 KB | 1 | 42 | plane 19, cylinder 16, torus 6, free-form 1 | https://huggingface.co/datasets/jhlee11/BRepGround/resolve/3b963b0bac7fbdd54785a09f7f32405652c8e76a/assets/test-00001-of-00002.zip (member steps/00290572_chamfer_12.step) | CC BY 4.0, (c) 2026 Jiahao Li, Qingwang Zhang, Qiuyu Chen, Guozhan Qiu, Yunzhong Lou, Xiangdong Zhou |

## hf_brepmfr

| file | size | solids | faces | surface kinds | source | license |
|---|---|---|---|---|---|---|
| `0m-3623639.stp` | 44 KB | 3 | 34 | plane 10, cylinder 24 | https://huggingface.co/datasets/Silly98/BrepMFR/resolve/a32f70fd92513bf4b6514d54ed68a851c2c25b3c/0m-3623639.stp | apache-2.0 (dataset card); provenance of the parts not stated, see note |
| `107050503-m8u-8700-a267.stp` | 65 KB | 1 | 36 | plane 16, cylinder 20 | https://huggingface.co/datasets/Silly98/BrepMFR/resolve/a32f70fd92513bf4b6514d54ed68a851c2c25b3c/107050503-m8u-8700-a267.stp | apache-2.0 (dataset card); provenance of the parts not stated, see note |
| `16P-03303.step` | 1660 KB | 2 | 261 | plane 51, cylinder 54, cone 31, free-form 125 | https://huggingface.co/datasets/Silly98/BrepMFR/resolve/a32f70fd92513bf4b6514d54ed68a851c2c25b3c/16P-03303.step | apache-2.0 (dataset card); provenance of the parts not stated, see note |
| `sample_round.stp` | 639 KB | 1 | 14 | plane 3, cylinder 3, torus 4, free-form 4 | https://huggingface.co/datasets/Silly98/BrepMFR/resolve/a32f70fd92513bf4b6514d54ed68a851c2c25b3c/sample_round.stp | apache-2.0 (dataset card); provenance of the parts not stated, see note |
| `sample_round_1.stp` | 95 KB | 1 | 14 | plane 3, cylinder 5, torus 6 | https://huggingface.co/datasets/Silly98/BrepMFR/resolve/a32f70fd92513bf4b6514d54ed68a851c2c25b3c/sample_round_1.stp | apache-2.0 (dataset card); provenance of the parts not stated, see note |
| `sample_round_2.stp` | 473 KB | 1 | 15 | plane 3, cylinder 4, torus 6, free-form 2 | https://huggingface.co/datasets/Silly98/BrepMFR/resolve/a32f70fd92513bf4b6514d54ed68a851c2c25b3c/sample_round_2.stp | apache-2.0 (dataset card); provenance of the parts not stated, see note |
| `zip_chainlinkouter00.stp` | 50 KB | 1 | 40 | plane 12, cylinder 28 | https://huggingface.co/datasets/Silly98/BrepMFR/resolve/a32f70fd92513bf4b6514d54ed68a851c2c25b3c/stp.zip (member stp/Chain Link Outer_chainlinkouter00.stp) | apache-2.0 (dataset card); provenance of the parts not stated, see note |
| `zip_cylinder400bore000.stp` | 506 KB | 1 | 188 | plane 34, sphere 8, cylinder 72, cone 2, torus 60, free-form 12 | https://huggingface.co/datasets/Silly98/BrepMFR/resolve/a32f70fd92513bf4b6514d54ed68a851c2c25b3c/stp.zip (member stp/cylinder 4.00 bore_cylinder400bore000.stp) | apache-2.0 (dataset card); provenance of the parts not stated, see note |
| `zip_cylinder600bore000.stp` | 418 KB | 1 | 184 | plane 42, cylinder 74, cone 4, torus 44, free-form 20 | https://huggingface.co/datasets/Silly98/BrepMFR/resolve/a32f70fd92513bf4b6514d54ed68a851c2c25b3c/stp.zip (member stp/cylinder 6.00 bore_cylinder600bore000.stp) | apache-2.0 (dataset card); provenance of the parts not stated, see note |
| `zip_defaultamacchina000.stp` | 139 KB | 14 | 82 | plane 78, cylinder 2, free-form 2 | https://huggingface.co/datasets/Silly98/BrepMFR/resolve/a32f70fd92513bf4b6514d54ed68a851c2c25b3c/stp.zip (member stp/Compressore ATLAS COPCO FLX07_defaultamacchina000.stp) | apache-2.0 (dataset card); provenance of the parts not stated, see note |
| `zip_dfautbrutdusinage0001.stp` | 736 KB | 35 | 490 | plane 252, cylinder 226, torus 12 | https://huggingface.co/datasets/Silly98/BrepMFR/resolve/a32f70fd92513bf4b6514d54ed68a851c2c25b3c/stp.zip (member stp/ECH skid maintien de pression Limoges_dfautbrutdusinage0001.stp) | apache-2.0 (dataset card); provenance of the parts not stated, see note |
| `zip_doorlatchvonduprin0001.stp` | 125 KB | 1 | 58 | plane 14, sphere 4, cylinder 26, cone 2, torus 4, free-form 8 | https://huggingface.co/datasets/Silly98/BrepMFR/resolve/a32f70fd92513bf4b6514d54ed68a851c2c25b3c/stp.zip (member stp/door latch Von Duprin 230L 06 SP28 LHR_doorlatchvonduprin0001.stp) | apache-2.0 (dataset card); provenance of the parts not stated, see note |
| `zip_dripmanifold0.stp` | 88 KB | 1 | 66 | plane 16, cylinder 28, cone 18, torus 4 | https://huggingface.co/datasets/Silly98/BrepMFR/resolve/a32f70fd92513bf4b6514d54ed68a851c2c25b3c/stp.zip (member stp/DRIP MANIFOLD_dripmanifold0.stp) | apache-2.0 (dataset card); provenance of the parts not stated, see note |
| `zip_ea0000006992revit.stp` | 848 KB | 21 | 367 | plane 126, sphere 6, cylinder 125, cone 96, torus 12, free-form 2 | https://huggingface.co/datasets/Silly98/BrepMFR/resolve/a32f70fd92513bf4b6514d54ed68a851c2c25b3c/stp.zip (member stp/ea0000006992revit.stp) | apache-2.0 (dataset card); provenance of the parts not stated, see note |
| `zip_ea0000006997revit.stp` | 111 KB | 1 | 75 | plane 30, cylinder 37, cone 4, torus 4 | https://huggingface.co/datasets/Silly98/BrepMFR/resolve/a32f70fd92513bf4b6514d54ed68a851c2c25b3c/stp.zip (member stp/ea0000006997revit.stp) | apache-2.0 (dataset card); provenance of the parts not stated, see note |
| `zip_ea0000007008revit.stp` | 167 KB | 1 | 68 | plane 24, cylinder 36, torus 8 | https://huggingface.co/datasets/Silly98/BrepMFR/resolve/a32f70fd92513bf4b6514d54ed68a851c2c25b3c/stp.zip (member stp/ea0000007008revit.stp) | apache-2.0 (dataset card); provenance of the parts not stated, see note |

## hf_zero_to_cad

| file | size | solids | faces | surface kinds | source | license |
|---|---|---|---|---|---|---|
| `13e02b4d-d613-422b-6a17-390f6402693a.cadquery.py` | 1 KB | - | - | - | https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100 (row uuid 13e02b4d-d613-422b-6a17-390f6402693a, column cadquery_file) | apache-2.0 (dataset card) |
| `13e02b4d-d613-422b-6a17-390f6402693a.step` | 147 KB | 1 | 39 | plane 9, sphere 8, cylinder 17, cone 1, torus 4 | https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100 (row uuid 13e02b4d-d613-422b-6a17-390f6402693a, column step_file) | apache-2.0 (dataset card) |
| `3692c35e-1985-41b6-b45d-edc922a59854.cadquery.py` | 2 KB | - | - | - | https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100 (row uuid 3692c35e-1985-41b6-b45d-edc922a59854, column cadquery_file) | apache-2.0 (dataset card) |
| `3692c35e-1985-41b6-b45d-edc922a59854.step` | 509 KB | 1 | 124 | plane 76, cylinder 4, cone 10, torus 10, free-form 24 | https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100 (row uuid 3692c35e-1985-41b6-b45d-edc922a59854, column step_file) | apache-2.0 (dataset card) |
| `3bbf8b2b-5a16-b6b4-0c60-4df743e5e0bc.cadquery.py` | 2 KB | - | - | - | https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100 (row uuid 3bbf8b2b-5a16-b6b4-0c60-4df743e5e0bc, column cadquery_file) | apache-2.0 (dataset card) |
| `3bbf8b2b-5a16-b6b4-0c60-4df743e5e0bc.step` | 450 KB | 1 | 99 | plane 23, sphere 16, cylinder 52, torus 8 | https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100 (row uuid 3bbf8b2b-5a16-b6b4-0c60-4df743e5e0bc, column step_file) | apache-2.0 (dataset card) |
| `45278456-3334-0c11-81a7-458fce65d6d7.cadquery.py` | 2 KB | - | - | - | https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100 (row uuid 45278456-3334-0c11-81a7-458fce65d6d7, column cadquery_file) | apache-2.0 (dataset card) |
| `45278456-3334-0c11-81a7-458fce65d6d7.step` | 507 KB | 1 | 38 | plane 7, cylinder 4, free-form 27 | https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100 (row uuid 45278456-3334-0c11-81a7-458fce65d6d7, column step_file) | apache-2.0 (dataset card) |
| `4b3aaa7b-f278-fc6a-8f9f-28fd4893be76.cadquery.py` | 1 KB | - | - | - | https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100 (row uuid 4b3aaa7b-f278-fc6a-8f9f-28fd4893be76, column cadquery_file) | apache-2.0 (dataset card) |
| `4b3aaa7b-f278-fc6a-8f9f-28fd4893be76.step` | 52 KB | 1 | 14 | plane 6, cylinder 8 | https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100 (row uuid 4b3aaa7b-f278-fc6a-8f9f-28fd4893be76, column step_file) | apache-2.0 (dataset card) |
| `56155734-8313-cde8-e96a-dbb3bbe3ba2f.cadquery.py` | 2 KB | - | - | - | https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100 (row uuid 56155734-8313-cde8-e96a-dbb3bbe3ba2f, column cadquery_file) | apache-2.0 (dataset card) |
| `56155734-8313-cde8-e96a-dbb3bbe3ba2f.step` | 104 KB | 1 | 35 | plane 13, sphere 4, cylinder 10, cone 6, torus 2 | https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100 (row uuid 56155734-8313-cde8-e96a-dbb3bbe3ba2f, column step_file) | apache-2.0 (dataset card) |
| `5c6512ae-9182-fc5e-05b1-b23c3735d060.cadquery.py` | 1 KB | - | - | - | https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100 (row uuid 5c6512ae-9182-fc5e-05b1-b23c3735d060, column cadquery_file) | apache-2.0 (dataset card) |
| `5c6512ae-9182-fc5e-05b1-b23c3735d060.step` | 136 KB | 1 | 50 | plane 39, cylinder 2, cone 4, free-form 5 | https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100 (row uuid 5c6512ae-9182-fc5e-05b1-b23c3735d060, column step_file) | apache-2.0 (dataset card) |
| `89ded05a-e2be-350b-db33-e42eb475ce39.cadquery.py` | 1 KB | - | - | - | https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100 (row uuid 89ded05a-e2be-350b-db33-e42eb475ce39, column cadquery_file) | apache-2.0 (dataset card) |
| `89ded05a-e2be-350b-db33-e42eb475ce39.step` | 223 KB | 1 | 58 | plane 24, sphere 10, cylinder 18, cone 2, free-form 4 | https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100 (row uuid 89ded05a-e2be-350b-db33-e42eb475ce39, column step_file) | apache-2.0 (dataset card) |
| `8bccb9ee-085e-5ce4-75ab-15c7ee2cab24.cadquery.py` | 2 KB | - | - | - | https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100 (row uuid 8bccb9ee-085e-5ce4-75ab-15c7ee2cab24, column cadquery_file) | apache-2.0 (dataset card) |
| `8bccb9ee-085e-5ce4-75ab-15c7ee2cab24.step` | 190 KB | 1 | 62 | plane 15, sphere 8, cylinder 31, torus 8 | https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100 (row uuid 8bccb9ee-085e-5ce4-75ab-15c7ee2cab24, column step_file) | apache-2.0 (dataset card) |
| `916572bc-ac4f-03d6-fc3d-1670590c4ce4.cadquery.py` | 1 KB | - | - | - | https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100 (row uuid 916572bc-ac4f-03d6-fc3d-1670590c4ce4, column cadquery_file) | apache-2.0 (dataset card) |
| `916572bc-ac4f-03d6-fc3d-1670590c4ce4.step` | 159 KB | 1 | 47 | plane 12, cylinder 12, cone 15, torus 8 | https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100 (row uuid 916572bc-ac4f-03d6-fc3d-1670590c4ce4, column step_file) | apache-2.0 (dataset card) |

## mcneel_rebuilt

| file | size | solids | faces | surface kinds | source | license |
|---|---|---|---|---|---|---|
| `mesh_blob_80.step` | 183 KB | 1 | 80 | plane 80 | generated by tools/gen_forum.py (OCCT 8.0.1 via cadquery-ocp); rebuilds the configuration of a McNeel forum thread, no forum file used | own work for this bench (same terms as this repository) |
| `threaded_rod_cutter.step` | 53 KB | 1 | 5 | plane 2, free-form 3 | generated by tools/gen_forum.py (OCCT 8.0.1 via cadquery-ocp); rebuilds the configuration of a McNeel forum thread, no forum file used | own work for this bench (same terms as this repository) |

## nist_edm

| file | size | solids | faces | surface kinds | source | license |
|---|---|---|---|---|---|---|
| `260012.stp` | 600 KB | 1 | 147 | plane 53, cylinder 54, cone 11, torus 29 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/Parasolid/NIST/Pete_Brown/260012/260012.step.hh.sat.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `DoubleCam1.stp` | 52 KB | 1 | 35 | plane 12, cylinder 11, cone 4, torus 8 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/ICEM-CDC/Fixture_Models/DoubleCam1/DoubleCam1.hh.sat.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `KnurledKnob10.stp` | 17 KB | 1 | 11 | plane 3, cylinder 6, cone 2 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/ICEM-CDC/Fixture_Models/KnurledKnob10/KnurledKnob10.hh.sat.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `NC_DRIVE.stp` | 53 KB | 1 | 20 | free-form 20 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/SDRC_I-DEAS/NC_DRIVE/NC_DRIVE.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `RestButton1.stp` | 21 KB | 1 | 15 | plane 3, cylinder 4, cone 4, torus 4 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/ICEM-CDC/Fixture_Models/RestButton1/RestButton1.hh.sat.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `anc101_a.stp` | 197 KB | 1 | 127 | plane 55, cylinder 68, cone 4 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/Parasolid/NIST/Bill_Regli/anc101_a/anc101_a.hh.sat.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `bellow.stp` | 104 KB | 1 | 68 | plane 2, cylinder 2, cone 64 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/NIST/Manfred_Osti/spectrometer/bellow/bellow.prt.hh.sat.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `bolt.stp` | 73 KB | 1 | 46 | plane 20, sphere 8, cylinder 18 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/PTC/V18/asmdes18/parts/bolt.prt.hh.sat.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `chamber.stp` | 133 KB | 1 | 50 | plane 15, sphere 4, cylinder 27, torus 2, free-form 2 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/VDS/chamber/chamber.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `clevis21.stp` | 93 KB | 1 | 66 | plane 30, cylinder 24, cone 12 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/STEP/STI/clevis21/clevis21.hh.sat.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `flange.stp` | 132 KB | 2 | 102 | plane 14, cylinder 60, cone 8, torus 20 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/Parasolid/NIST/Pete_Brown/flange/flange.step.hh.sat.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `fork.stp` | 436 KB | 1 | 106 | plane 29, cylinder 47, torus 16, free-form 14 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/VDS/fork/fork.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `gear_40.stp` | 687 KB | 1 | 456 | plane 352, cylinder 104 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/PTC/Legos/stepmodels/gear_40.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `interactingPockets.stp` | 98 KB | 1 | 66 | plane 30, cylinder 36 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/STEP/STI/interactingPockets/interactingPockets.hh.sat.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `main_block.stp` | 211 KB | 1 | 160 | plane 55, cylinder 84, cone 3, torus 18 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/NIST/Manfred_Osti/spectrometer/main_block/main_block.hh.sat.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `moon_buggy.stp` | 265 KB | 1 | 113 | plane 28, sphere 8, cylinder 26, cone 4, torus 40, free-form 7 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/STEP/STI/moon_buggy/moon_buggy.hh.sat.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `mt_jaw_half_finish-mach-bup.stp` | 328 KB | 1 | 169 | plane 118, cylinder 42, cone 5, torus 2, free-form 2 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/VDS/mt_jaw_half_finish-mach-bup/mt_jaw_half_finish-mach-bup.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `needle-nose-inch.stp` | 98 KB | 1 | 31 | plane 18, cylinder 5, torus 4, free-form 4 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/CMU/Tools/needle-nose-inch.hh.sat.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `screw_driver1.stp` | 381 KB | 1 | 107 | plane 5, sphere 2, cylinder 14, cone 14, torus 50, free-form 22 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/CMU/Tools/screw_driver1.hh.sat.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `sh-r44356-000-u.stp` | 34 KB | 1 | 21 | plane 5, cylinder 8, torus 8 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/Sandia/Randy_Wilson/discriminator/sh-r44356-000-u/sh-r44356-000-u.hh.sat.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `sh-r44363-000-u-compressed.stp` | 38 KB | 1 | 30 | plane 2, cylinder 8, torus 20 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/Sandia/Randy_Wilson/discriminator/sh-r44363-000-u-compressed/sh-r44363-000-u-compressed.hh.sat.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `stock.stp` | 1494 KB | 1 | 85 | plane 23, cylinder 27, cone 4, torus 16, free-form 15 | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/Parasolid/NIST/Pete_Brown/Torpedo_Motor/stock/stock.hh.sat.stp | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |
| `swivel1-Part.step` | 21 KB | 0 | - | - | https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a/models/UMD/swivel1-Part/swivel1-Part.step | Public domain in the US (NIST terms, LICENSE.md of the repository; keep its notice) |

## occt_booltest

| file | size | solids | faces | surface kinds | source | license |
|---|---|---|---|---|---|---|
| `bottle.step` | 212 KB | 2 | 72 | plane 13, sphere 16, cylinder 32, torus 9, free-form 2 | https://raw.githubusercontent.com/kaige/occt-booltest/bb9b85a52dcf0e6ff421390371b27b741bb9b5fe/corpus-index/bottle.step | CC-BY-4.0 (corpus data, per the repository README; code MIT; no LICENSE file in the repository) |

## occt_data

| file | size | solids | faces | surface kinds | source | license |
|---|---|---|---|---|---|---|
| `Bottom_from_brep.step` | 2247 KB | 1 | 323 | plane 52, sphere 8, cylinder 111, cone 3, torus 28, free-form 121 | https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/4dbfdcc448c0b3e565488afcd626c84483172db9/data/occ/Bottom.brep, converted to STEP AP214 with tools/brep2step.py (largest solid) | LGPL-2.1 with the OCCT exception (OCCT repository data) |
| `CrankArm_from_brep.step` | 417 KB | 1 | 49 | plane 19, cylinder 9, cone 5, free-form 16 | https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/4dbfdcc448c0b3e565488afcd626c84483172db9/data/occ/CrankArm.brep, converted to STEP AP214 with tools/brep2step.py (largest solid) | LGPL-2.1 with the OCCT exception (OCCT repository data) |
| `MODERN_MVCooker_1_from_brep.step` | 44 KB | 1 | 15 | plane 13, cylinder 2 | https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/4dbfdcc448c0b3e565488afcd626c84483172db9/data/occ/MODERN_MVCooker_1.brep, converted to STEP AP214 with tools/brep2step.py (largest solid) | LGPL-2.1 with the OCCT exception (OCCT repository data) |
| `MODERN_Table_1_from_brep.step` | 61 KB | 1 | 22 | plane 12, cylinder 10 | https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/4dbfdcc448c0b3e565488afcd626c84483172db9/data/occ/MODERN_Table_1.brep, converted to STEP AP214 with tools/brep2step.py (largest solid) | LGPL-2.1 with the OCCT exception (OCCT repository data) |
| `Pump_Nut_from_brep.step` | 111 KB | 1 | 25 | plane 8, cylinder 1, cone 14, torus 2 | https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/4dbfdcc448c0b3e565488afcd626c84483172db9/data/occ/Pump_Nut.brep, converted to STEP AP214 with tools/brep2step.py (largest solid) | LGPL-2.1 with the OCCT exception (OCCT repository data) |
| `Pump_TopCover_from_brep.step` | 84 KB | 1 | 8 | plane 2, sphere 2, cylinder 2, free-form 2 | https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/4dbfdcc448c0b3e565488afcd626c84483172db9/data/occ/Pump_TopCover.brep, converted to STEP AP214 with tools/brep2step.py (largest solid) | LGPL-2.1 with the OCCT exception (OCCT repository data) |
| `bottle_from_brep.step` | 241 KB | 1 | 71 | plane 13, sphere 16, cylinder 31, torus 9, free-form 2 | https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/4dbfdcc448c0b3e565488afcd626c84483172db9/data/occ/bottle.brep, converted to STEP AP214 with tools/brep2step.py (largest solid) | LGPL-2.1 with the OCCT exception (OCCT repository data) |
| `linkrods.step` | 1751 KB | 1 | 37 | plane 6, cylinder 4, torus 9, free-form 18 | https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/4dbfdcc448c0b3e565488afcd626c84483172db9/data/step/linkrods.step | LGPL-2.1 with the OCCT exception (OCCT repository data) |
| `screw.step` | 86 KB | 1 | 10 | plane 4, cylinder 1, cone 2, torus 3 | https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/4dbfdcc448c0b3e565488afcd626c84483172db9/data/step/screw.step | LGPL-2.1 with the OCCT exception (OCCT repository data) |

Total 21.6 MB in 83 files.

## Sources found but not taken

| source | what it is | license | why not taken |
|---|---|---|---|
| github.com/kaige/occt-booltest release assets `booltest-corpus-step-v1-core.zip` / `-full.zip` | 2389 body1/body3 STEP pairs from rotating and intersecting the bottle | corpus CC-BY-4.0 | not downloaded; the same kind of pairs is regenerated here from `bottle.step` (rotated copies, chain) |
| DeCoDELab/CADBench (Hugging Face) | parquet shards with a `step` column, 18,000 samples from DeepCAD, Fusion 360, ABC, MCB, Objaverse | none stated in the card | no license; mixes sources with non-commercial terms (Fusion 360 Gallery) |
| YuXingyao/HoLa-BRep | DeepCAD test set, 9 GB zip | "upstream-terms" | size; terms of the upstream sets |
| jingwei-xu-00/Omni-CAD | CAD sequences | MIT | needs preprocessing to get STEP; 1.2 GB |
| VladPyatov/CADFS | CAD dataset | - | 84 GB |
| Liyuan03/BrepLLM_data | BRep descriptions | - | JSON only, no STEP |
| Sandflow/sand3d-cad | CAD scenes | - | USDA meshes, no BRep |
| markov-ai/cad-1000-hours | CAD screen recordings | cc-by-nc | video, non-commercial |
| ABC dataset, Fusion 360 Gallery | large CAD corpora | Onshape terms / non-commercial research | redistribution not allowed |
| FreeCAD `data/tests/Step/as1-ac-214_small.stp`, `geometry_out.stp` | test files | LGPL-2.1+ | duplicates of AS1 / not solids |
| CadQuery `tests/testdata/red_cube_blue_cylinder.step` | test file | Apache-2.0 | two primitives only |
| OCCT `data/occ/*.brep` not converted (Motor-c, Axis_of_bearing, MODERN_Sink, hammer, shell1, ...) | sample shapes | LGPL-2.1 + exception | assemblies of many solids, open shells or faces only |
| McNeel forum t/163125, t/123416, t/213347, t/216730, t/52492 (and tag `boolean`: t/200748 "Boolean with pipes", t/194822, t/219099, t/217652, t/213879) | boolean failure reports with .3dm (one .step in t/216730, .gh in t/52492) | forum content, no redistribution license | not downloaded; t/163125, t/213347, t/216730, t/123416 rebuilt as own geometry (`mcneel_rebuilt/` and primitive cases in `results/cases.tsv`) |
| NIST engineering-design-models, the other 2388 STEP files | 1990s parts | public domain (US) | kept the set small; any of them can be added with the same `fetch.sh` pattern |

## Not committed

`hf_brepmfr/` (16 files from Silly98/BrepMFR) and their pictures are on disk only: the dataset card says apache-2.0,
but the parts look like vendor models (Atlas Copco, Von Duprin, Revit families) and the uploader gives no origin.
`fetch.sh` downloads them again.
