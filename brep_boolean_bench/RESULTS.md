# BRep booleans on real STEP parts: session_cpp against OCCT (2026-11-14)

73 STEP files from seven sources (`MANIFEST.md`): 23 NIST industry parts from the 1990s, 16 + 10 + 10 Hugging Face
parts (BrepMFR, BRepGround fillet/chamfer states, Zero-To-CAD CadQuery parts), 9 Open CASCADE samples, build123d's
NEMA-17 bracket, FreeCAD's AS1 assembly, the occt-booltest bottle and two rebuilds of McNeel forum failures. Each
file goes through both STEP readers, then booleans: the part against a copy of itself turned 30° about x and 5° about
z through its box centre (occt-booltest style), the part against a slab-shaped box across its longest direction, a
cylinder through its centre along its shortest direction and a sphere near a box corner; the seven forum rebuilds and
three part pairs; and the occt-booltest chain (body ← body ∩ rotated body, five times) on the bottle. All five
operations each: A∩B, A∪B, A−B, B−A, A⊕B.

## Setup

- **Ours**: session_cpp `6c50b89e` (worktree `$S/wt_step`, Release `-O3`, kernel sources unchanged), driver
  `tools/ours_step_bench.cpp` linked with `$S/fuzz/build.sh`. One process per boolean, 120 s boolean limit (process
  killed at 240 s with its volume), 6 GB address-space cap. Validity: `BRep::is_valid()` and `is_solid()`; volume
  `volume_exact()`, the tessellated `volume()` when that throws (marked `(mesh)`).
- **OCCT**: 8.0.1 through the `cadquery-ocp` 8.0.1.1.0 wheel (`tools/occt_step_bench.py`; the C++ oracle build at
  `$S/occt_build` has no DataExchange toolkits). `BRepAlgoAPI_Common/Fuse/Cut`, xor = Fuse(Cut(a,b), Cut(b,a)) as in
  `docs/validation/occt_bench`; validity `BRepCheck_Analyzer`; volume `BRepGProp`. OCCT's reader converts lengths to
  millimetres, ours keeps file units: OCCT shapes are scaled back to file units (inch, metre files).
- Same operands on both sides: the solid of largest volume of the file (ours: largest |volume|, vertex-box volume when
  that is not finite), the same moves; cutters are each kernel's own primitives (ours NURBS, OCCT analytic) of the same
  size and pose (`tools/gen_cases.py`, placements from OCCT's bounding box).
- Machine: 4 cores, 15 GB, shared with other agents (load average 5 to 9 throughout); single-threaded on both sides.
  Times are noisy; ratios are what to read. The VM has no cpufreq files, so throttling could not be checked.
- **Two series for ours.** *raw*: the BReps exactly as `read_file_step_breps` returns them. *repaired*: the same BReps
  after a driver-side topology repair, not kernel code (`repair()` in `tools/ours_step_bench.cpp`, `REPAIR=1`): a wire
  that is open as read but closes when walked backwards gets its edge order reversed, shell face uses are flipped so
  every edge is used once each way, and the shell is flipped when its volume is negative. It only exists to separate
  the reader's orientation bug (below) from the booleans.

## Findings

1. **The STEP reader does not deliver solids.** Of 73 files our reader returns BReps for 70; the largest BRep is
   `is_solid()` in 2 (the all-planar `mesh_blob_80`, and in `zip_ea0000006992revit.stp` a two-face sphere-like body that
   happens to be the largest by our volume). Three causes, all in `src/file_step.cpp`:
   - *FACE_BOUND with orientation `.F.`*: each edge's direction is flipped (`le.reversed = oe_orient != b->orient`,
     lines 2548 and 2891) but the loop order is not reversed, so the wire does not chain (`open_wires` in the load
     table equals the number of `.F.` bounds in nearly every file; OCCT and Creo write `.F.` bounds routinely).
   - *ADVANCED_FACE with same_sense `.F.`*: faces whose bounds are all `.T.` still come out with edges used twice in
     the same direction (NIST files: `edges_same_direction_twice` with zero open wires), so the face's sense is not
     carried into its use in the shell.
   - *Parse*: `parse_step_file` finds the data section with `text.find("DATA")` (line 438), so a header string that
     contains DATA (`'MATRA-DATAVISION'` in OCCT's own `screw.step` and `linkrods.step`) makes the whole file parse to
     nothing: 0 points, 0 BReps, no error. With the header string changed, screw.step loads (10 faces). Also
     `FACE_SURFACE` (AP203, `swivel1-Part.step`) is not read: 0 BReps, no error.
   Faces that fail inside the reader are dropped silently (`add_face` returns without a face), so a wrong part loads
   without any error.
2. **Booleans reject every raw part at once**: "Native BRep Booleans require closed oriented solid operands", in a
   fraction of a millisecond. Only cases built from our own primitives (forum rebuilds) and the planar mesh solid run.
3. **After the repair** 57 of 72 parts are `is_solid()`, and 26 have a volume within 1e-2 of OCCT's (15 within 1e-6).
   The others still have NURBS surfaces that fail `is_valid()`, wires that are open for another reason (edges missing
   from the loop) or faces whose trims are wrong (volume off, or tessellation throws "Trim triangulation could not
   preserve a boundary constraint").
4. **Even on repaired parts whose volume matches OCCT, almost every boolean fails**: 37 of 650 return, 25 of them on
   the all-planar mesh solid and 12 where the cutter does not touch the part; the rest fail in 0.01 to 3 s with
   certification errors about the *input* trims: "Split curve/trim correspondence is mismatched: Certified
   common-interval point residual exceeds tolerance", "Required edge event lacks an original raw curve/trim law",
   "edge and pcurve disagree inside their ranges; tolerance=1e-07 ... surface=13x2 CVs", "Analytic pullback did not
   obtain a complete paired-parameter certificate". The tell: on the NEMA bracket with a cylinder that misses it,
   A∩B (empty) and B−A succeed while A∪B and A−B fail, i.e. the part's own faces fail the checks before any
   intersection is involved. Passing tolerance 1e-6 ... 1e-3 to the boolean (driver `TOL`) gives the same error on the
   bracket. Likely cause, not proven: the reader writes many pcurves as sampled degree-1 polylines (`PCURVES` lines of
   `results/ours_load*.txt`: on the bracket 36 of 240 pcurves are degree 1 with more than 4 control points) and
   converts analytic surfaces to multi-span NURBS, so curve and pcurve agree only to the sampling error, far above
   the booleans' 1e-7 certificates.
5. **A memory-safety crash and a silent wrong result** (both on driver-repaired input):
   - `hf_brepground/00019536_chamfer_10.step` against itself turned 30° about x or 5° about z aborts the process in
     every operation with `*** stack smashing detected ***` (SIGABRT, a stack buffer overrun inside the kernel), after
     0.15 to 0.4 s. Reproduce: `REPAIR=1 tools/ours_step_bench bool "step=<bench>/hf_brepground/00019536_chamfer_10.step"
     "step=<bench>/hf_brepground/00019536_chamfer_10.step|r=1,0,0,30,<centre from results/cases.tsv>" intersection`.
   - `nist_edm/bellow.stp` (repaired volume equal to OCCT's to 12 digits) with a cylinder down its bore, not touching
     it: ours returns A∩B = the whole cylinder and B−A = empty, both `is_valid` and `is_solid`; OCCT returns A∩B empty
     and B−A = the cylinder, and OCCT's point classifier puts the cylinder's centre outside the bellow. Ours
     classifies the disjoint cylinder as inside the part (`images/cmp_nist_edm__bellow_cyl.png`). A∪B, A−B and A⊕B
     fail ("pcurve reparameterization is unresolved").
6. **Where the input is clean, ours is right**: all six forum rebuilds that run (box minus a cylinder with
   coplanar caps, minus a cone on the bottom face, wall lining minus stud and coplanar brace, 80-triangle mesh solid
   minus a cone) and the mesh solid against its cutters agree with OCCT to 1e-6 in volume with identical face counts;
   their single booleans take about 3 times OCCT's time. The rod minus a helical thread cutter (pipe shell from
   STEP) fails ("Cutter midpoint is on the boundary without established overlap ownership", B−A "Split produced
   invalid BRep references"); its STEP-read cutter also tessellates with visible artefacts.
   The mesh solid against itself turned 5° and 30° (443 faces in its xor) also matches OCCT face for face, to 1e-12
   in volume, at 3 to 6 times OCCT's time.
7. **OCCT returns a result for nearly every boolean, not always a correct one**: of 1850 booleans 1843 return
   (6 NotDone, 1 killed after 590 s on `bellow#rot30x` xor), 69 non-empty results fail `BRepCheck_Analyzer`, and 38 of
   365 complete cases break the volume identities by more than 1e-3, 12 of them by 1e297 to inf (a result volume of that
   size returned with status OK), 11 of the 12 on the 5° and 30° self-rotations: the silent garbage that occt-booltest
   describes.

## What was verified, what was not

- Verified: both readers on every file (faces, kinds, validity, volume); every listed boolean on both kernels with
  the recorded status, counts, validity and volume; volume identities per kernel; pictures for every part.
- Not verified: our results against OCCT where ours fails (no result to compare); OCCT results are compared to ours
  and to its own identities, not to an independent ground truth; the cause in finding 4 is inferred from the error
  texts and pcurve statistics, not traced in code; raw-series rows of the slab case ran with the first box placement
  (before the cutter was moved to a slab), which does not matter because they fail on operand A before B is used;
  timings come from a loaded shared machine; the repaired series uses driver code that changes the reader's output.

## Load: every file through both STEP readers

Columns: STEP faces = ADVANCED_FACE + FACE_SURFACE entities in the file; ours/OCCT faces and kinds are of the largest solid
(kinds: plane, sphere, cylinder, cone, torus, free-form; ours from `nurbs_implicit::recognize` on its NURBS surfaces,
OCCT from GeomAbs types); volumes in file units (OCCT scaled back from millimetres); `(mesh)` = ours volume_exact threw and
the tessellated volume is shown; repaired = driver-side wire/face orientation repair (not kernel code, see above).

| file | STEP faces | ours breps | ours faces* | ours is_valid | ours is_solid | ours kinds p,s,c,k,t,f | ours volume | OCCT solids | OCCT faces* | OCCT valid | OCCT kinds p,s,c,k,t,f | OCCT volume | rel. vol diff | why not solid (ours raw) | ours repaired is_solid | ours repaired volume | repaired rel. vol diff |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| github_misc/as1-ac-214.stp | 53 | 5 | 18 | 1 | 0 | 6,0,12,0,0,0 | 530730.320583(mesh) | 18 | 18 | 1 | 6,0,12,0,0,0 | 530575.222039 | 2.92e-04 | edges_same_direction_twice=8 | 1 | 530575.222039 | 0.00e+00 |
| github_misc/nema-17-bracket.step | 42 | 1 | 42 | 0 | 0 | 24,0,18,0,0,0 | 7290.69589676(mesh) | 1 | 42 | 1 | 24,0,18,0,0,0 | 7061.15530179 | 3.25e-02 | open_wires=24 edges_same_direction_twice=68 | 1 | 7061.15530179 | 0.00e+00 |
| hf_brepground/00015160_chamfer_12.step | 53 | 1 | 53 | 0 | 0 | 13,0,23,1,0,16 | nan(mesh) | 1 | 53 | 1 | 13,0,23,3,8,6 | 12357.254171 | nan | invalid_surfaces=4 open_wires=16 edges_same_direction_twice=55 | 0 | nan(mesh) | nan |
| hf_brepground/00019536_chamfer_10.step | 10 | 1 | 10 | 0 | 0 | 4,0,2,0,3,1 | 558093.460933(mesh) | 1 | 10 | 1 | 4,0,2,0,3,1 | 991596.281952 | 4.37e-01 | open_wires=4 edges_same_direction_twice=5 | 1 | nan(mesh) | nan |
| hf_brepground/00042148_fillet_11.step | 120 | 1 | 120 | 0 | 0 | 15,0,51,0,0,54 | nan(mesh) | 1 | 120 | 1 | 15,0,51,0,32,22 | 14763.1293904 | nan | open_wires=64 edges_same_direction_twice=109 | 1 | nan(mesh) | nan |
| hf_brepground/00071814_fillet_15.step | 80 | 1 | 80 | 0 | 0 | 20,0,37,0,4,19 | nan(mesh) | 1 | 80 | 1 | 20,0,37,0,13,10 | 18626.4128714 | nan | open_wires=53 edges_same_direction_twice=94 | 1 | 16291.4936849 | 1.25e-01 |
| hf_brepground/00089757_fillet_16.step | 38 | 1 | 38 | 0 | 0 | 17,0,15,0,1,5 | nan(mesh) | 1 | 38 | 1 | 17,0,15,0,4,2 | 6617.54825101 | nan | open_wires=16 edges_same_direction_twice=54 | 1 | nan(mesh) | nan |
| hf_brepground/00161395_chamfer_16.step | 50 | 1 | 50 | 0 | 0 | 20,2,20,0,0,8 | nan(mesh) | 1 | 50 | 1 | 20,2,20,0,2,6 | 15147772.7491 | nan | open_wires=20 edges_same_direction_twice=26 | 1 | 15146800.6548 | 6.42e-05 |
| hf_brepground/00170968_fillet_10.step | 46 | 1 | 46 | 0 | 0 | 13,0,16,0,14,3 | nan(mesh) | 1 | 46 | 1 | 13,0,16,0,15,2 | 84325.3519881 | nan | open_wires=22 edges_same_direction_twice=61 | 1 | nan(mesh) | nan |
| hf_brepground/00171214_fillet_11.step | 19 | 1 | 19 | 0 | 0 | 5,0,9,0,0,5 | 638835.17156(mesh) | 1 | 19 | 1 | 5,0,9,2,2,1 | 747962.535308 | 1.46e-01 | open_wires=6 edges_same_direction_twice=12 | 1 | 769610.718293 | 2.89e-02 |
| hf_brepground/00275424_fillet_17.step | 21 | 1 | 21 | 0 | 0 | 6,0,6,3,4,2 | 770602.430259(mesh) | 1 | 21 | 1 | 6,0,6,3,4,2 | 640454.868384 | 2.03e-01 | open_wires=3 edges_same_direction_twice=6 | 1 | nan(mesh) | nan |
| hf_brepground/00290572_chamfer_12.step | 42 | 1 | 42 | 0 | 0 | 19,0,16,0,0,7 | nan(mesh) | 1 | 42 | 1 | 19,0,16,0,6,1 | 8593.10967125 | nan | open_wires=16 edges_same_direction_twice=32 | 1 | 8646.47873725 | 6.21e-03 |
| hf_brepmfr/0m-3623639.stp | 34 | 3 | 26 | 0 | 0 | 6,0,20,0,0,0 | 681.021201489(mesh) | 3 | 26 | 1 | 6,0,20,0,0,0 | 14351.3890037 | 9.53e-01 | open_wires=26 edges_same_direction_twice=28 | 1 | 15448.3748241 | 7.64e-02 |
| hf_brepmfr/107050503-m8u-8700-a267.stp | 44 | 5 | 36 | 0 | 0 | 16,0,20,0,0,0 | nan(mesh) | 1 | 36 | 1 | 16,0,20,0,0,0 | 4.34439271948 | nan | open_wires=42 edges_same_direction_twice=36 | 1 | 7.99077454937 | 8.39e-01 |
| hf_brepmfr/16P-03303.step | 261 | 2 | 59 | 1 | 0 | 21,3,20,0,0,15 | 15.3171392413(mesh) | 2 | 59 | 1 | 21,0,20,15,0,3 | 14.9981573341 | 2.13e-02 | edges_same_direction_twice=27 | 1 | 19.4141920027(mesh) | 2.94e-01 |
| hf_brepmfr/sample_round.stp | 14 | 1 | 14 | 0 | 0 | 3,0,3,0,0,8 | 64176490.0936(mesh) | 1 | 14 | 1 | 3,0,3,0,4,4 | 126138195.332 | 4.91e-01 | open_wires=11 edges_same_direction_twice=10 | 1 | 85380279.9359 | 3.23e-01 |
| hf_brepmfr/sample_round_1.stp | 14 | 1 | 14 | 0 | 0 | 3,0,5,0,0,6 | nan(mesh) | 1 | 14 | 1 | 3,0,5,0,6,0 | 126039786.215 | nan | open_wires=11 edges_same_direction_twice=2 | 1 | 45009035.567 | 6.43e-01 |
| hf_brepmfr/sample_round_2.stp | 15 | 1 | 15 | 0 | 0 | 3,0,4,0,0,8 | 38076708.3017(mesh) | 1 | 15 | 1 | 3,0,4,0,6,2 | 113705314.062 | 6.65e-01 | open_wires=12 edges_same_direction_twice=6 | 1 | 4441118.74385 | 9.61e-01 |
| hf_brepmfr/zip_chainlinkouter00.stp | 40 | 1 | 40 | 0 | 0 | 12,0,28,0,0,0 | 336.178234902(mesh) | 1 | 40 | 1 | 12,0,28,0,0,0 | 1214.34409131 | 7.23e-01 | open_wires=32 edges_same_direction_twice=36 | 1 | 1214.34409131 | 0.00e+00 |
| hf_brepmfr/zip_cylinder400bore000.stp | 188 | 1 | 188 | 0 | 0 | 34,8,72,0,2,72 | nan(mesh) | 1 | 188 | 1 | 34,8,72,2,60,12 | 254.914351935 | nan | open_wires=178 edges_same_direction_twice=144 | 1 | nan(mesh) | nan |
| hf_brepmfr/zip_cylinder600bore000.stp | 184 | 1 | 184 | 0 | 0 | 42,0,74,0,4,64 | nan(mesh) | 1 | 184 | 1 | 42,0,74,4,44,20 | 261.518937695 | nan | open_wires=172 edges_same_direction_twice=136 | 1 | nan(mesh) | nan |
| hf_brepmfr/zip_defaultamacchina000.stp | 82 | 14 | 4 | 0 | 0 | 0,0,2,0,0,2 | 137513496.909(mesh) | 14 | 4 | 1 | 0,0,2,0,0,2 | 100066706.901 | 3.74e-01 | open_wires=2 edges_same_direction_twice=2 | 1 | 99994460.5875 | 7.22e-04 |
| hf_brepmfr/zip_dfautbrutdusinage0001.stp | 490 | 35 | 6 | 0 | 0 | 6,0,0,0,0,0 | 87500000(mesh) | 35 | 6 | 1 | 6,0,0,0,0,0 | 87500000 | 0.00e+00 | open_wires=6 edges_same_direction_twice=4 | 1 | nan(mesh) | nan |
| hf_brepmfr/zip_doorlatchvonduprin0001.stp | 58 | 1 | 58 | 0 | 0 | 14,4,26,0,0,14 | nan(mesh) | 1 | 58 | 1 | 14,4,26,2,4,8 | 376484.013554 | nan | open_wires=57 edges_same_direction_twice=52 | 1 | 375838.302855 | 1.72e-03 |
| hf_brepmfr/zip_dripmanifold0.stp | 66 | 1 | 66 | 0 | 0 | 16,0,28,0,0,22 | nan(mesh) | 1 | 66 | 1 | 16,0,28,18,4,0 | 5091.41960661 | nan | open_wires=54 edges_same_direction_twice=42 | 1 | 4903.91258667 | 3.68e-02 |
| hf_brepmfr/zip_ea0000006992revit.stp | 370 | 22 | 2 | 1 | 1 | 0,2,0,0,0,0 | 8580.2376481 | 21 | 68 | 1 | 8,0,26,24,8,2 | 799375.332053 | 9.89e-01 |  | 0 | nan(mesh) | nan |
| hf_brepmfr/zip_ea0000006997revit.stp | 75 | 1 | 75 | 0 | 0 | 30,0,37,1,0,7 | nan(mesh) | 1 | 75 | 1 | 30,0,37,4,4,0 | 10131989.6751 | nan | open_wires=74 edges_same_direction_twice=53 | 1 | 1739025.28701 | 8.28e-01 |
| hf_brepmfr/zip_ea0000007008revit.stp | 68 | 1 | 68 | 0 | 0 | 24,2,36,0,0,6 | nan(mesh) | 1 | 68 | 1 | 24,0,36,0,8,0 | 543814.064071 | nan | open_wires=58 edges_same_direction_twice=58 | 1 | 401441.991132 | 2.62e-01 |
| hf_zero_to_cad/13e02b4d-d613-422b-6a17-390f6402693a.step | 39 | 1 | 39 | 0 | 0 | 9,8,17,0,0,5 | nan(mesh) | 1 | 39 | 1 | 9,8,17,1,4,0 | 8796.53612651 | nan | open_wires=18 edges_same_direction_twice=26 | 1 | 8832.77894718 | 4.12e-03 |
| hf_zero_to_cad/3692c35e-1985-41b6-b45d-edc922a59854.step | 124 | 1 | 124 | 0 | 0 | 76,0,4,3,4,37 | 60939.9271996(mesh) | 1 | 124 | 1 | 76,0,4,10,10,24 | 74962.8207951 | 1.87e-01 | open_wires=76 edges_same_direction_twice=122 | 1 | nan(mesh) | nan |
| hf_zero_to_cad/3bbf8b2b-5a16-b6b4-0c60-4df743e5e0bc.step | 99 | 1 | 99 | 0 | 0 | 23,16,52,0,0,8 | nan(mesh) | 1 | 99 | 1 | 23,16,52,0,8,0 | 47778.1959053 | nan | open_wires=51 edges_same_direction_twice=95 | 1 | 47691.7044444 | 1.81e-03 |
| hf_zero_to_cad/45278456-3334-0c11-81a7-458fce65d6d7.step | 38 | 1 | 38 | 0 | 0 | 7,0,4,0,0,27 | nan(mesh) | 1 | 38 | 1 | 7,0,4,0,0,27 | 44804.7519849 | nan | open_wires=19 edges_same_direction_twice=50 | 1 | 52201.6367992 | 1.65e-01 |
| hf_zero_to_cad/4b3aaa7b-f278-fc6a-8f9f-28fd4893be76.step | 14 | 1 | 14 | 0 | 0 | 6,0,8,0,0,0 | 19660.1050395(mesh) | 1 | 14 | 1 | 6,0,8,0,0,0 | 52927.5411778 | 6.29e-01 | open_wires=8 edges_same_direction_twice=22 | 1 | 52927.5411778 | 0.00e+00 |
| hf_zero_to_cad/56155734-8313-cde8-e96a-dbb3bbe3ba2f.step | 35 | 1 | 35 | 0 | 0 | 13,4,10,0,0,8 | nan(mesh) | 1 | 35 | 1 | 13,4,10,6,2,0 | 19372.5382065 | nan | open_wires=15 edges_same_direction_twice=20 | 1 | nan(mesh) | nan |
| hf_zero_to_cad/5c6512ae-9182-fc5e-05b1-b23c3735d060.step | 50 | 1 | 50 | 0 | 0 | 40,0,2,0,0,8 | nan(mesh) | 1 | 50 | 1 | 39,0,2,4,0,5 | 23756.9131195 | nan | open_wires=31 edges_same_direction_twice=56 | 1 | 23645.1760208 | 4.70e-03 |
| hf_zero_to_cad/89ded05a-e2be-350b-db33-e42eb475ce39.step | 58 | 1 | 58 | 0 | 0 | 24,10,18,0,0,6 | nan(mesh) | 1 | 58 | 1 | 24,10,18,2,0,4 | 10008.4985742 | nan | open_wires=26 edges_same_direction_twice=56 | 1 | 9996.95296595 | 1.15e-03 |
| hf_zero_to_cad/8bccb9ee-085e-5ce4-75ab-15c7ee2cab24.step | 62 | 1 | 62 | 0 | 0 | 15,8,31,0,0,8 | nan(mesh) | 1 | 62 | 1 | 15,8,31,0,8,0 | 19520.8977489 | nan | open_wires=39 edges_same_direction_twice=61 | 1 | 19520.8977489 | 0.00e+00 |
| hf_zero_to_cad/916572bc-ac4f-03d6-fc3d-1670590c4ce4.step | 47 | 1 | 47 | 0 | 0 | 12,0,12,11,8,4 | 102926.304379(mesh) | 1 | 47 | 1 | 12,0,12,15,8,0 | 26664.6969523 | 2.86e+00 | open_wires=21 edges_same_direction_twice=19 | 1 | nan(mesh) | nan |
| mcneel_rebuilt/mesh_blob_80.step | 80 | 1 | 80 | 1 | 1 | 80,0,0,0,0,0 | 28263.2867334 | 1 | 80 | 1 | 80,0,0,0,0,0 | 28263.2867334 | 0.00e+00 |  | 1 | 28263.2867334 | 0.00e+00 |
| mcneel_rebuilt/threaded_rod_cutter.step | 5 | 1 | 5 | 0 | 0 | 2,0,1,0,0,2 | 5.92930252452e-13(mesh) | 1 | 5 | 1 | 2,0,0,0,0,3 | 169.331839697 | 1.00e+00 | open_wires=4 edges_same_direction_twice=3 | 1 | 169.331434383 | 2.39e-06 |
| nist_edm/260012.stp | 147 | 1 | 147 | 0 | 0 | 53,1,46,3,2,42 | nan(mesh) | 1 | 147 | 1 | 53,0,54,11,29,0 | 29612667552.2 | nan | invalid_surfaces=3 open_wires=20 edges_same_direction_twice=175 | 0 | nan(mesh) | nan |
| nist_edm/DoubleCam1.stp | 34 | 1 | 34 | 1 | 0 | 12,0,10,0,0,12 | nan(mesh) | 1 | 35 | 1 | 12,0,11,4,8,0 | 0.476367472982 | nan | edges_same_direction_twice=35 | 1 | 0.476367472982 | 0.00e+00 |
| nist_edm/KnurledKnob10.stp | 11 | 1 | 11 | 1 | 0 | 3,0,6,0,0,2 | 0.17458579042(mesh) | 1 | 11 | 1 | 3,0,6,2,0,0 | 0.219507791095 | 2.05e-01 | edges_same_direction_twice=4 | 1 | 0.219507791095 | 0.00e+00 |
| nist_edm/NC_DRIVE.stp | 20 | 1 | 20 | 0 | 0 | 9,0,3,0,0,8 | nan(mesh) | 1 | 20 | 1 | 0,0,0,0,0,20 | 4122781.80714 | nan | invalid_surfaces=6 open_wires=20 edges_same_direction_twice=10 | 0 | nan(mesh) | nan |
| nist_edm/RestButton1.stp | 15 | 1 | 15 | 1 | 0 | 3,0,4,0,0,8 | 0.0264312311724(mesh) | 1 | 15 | 1 | 3,0,4,4,4,0 | 0.0335097407011 | 2.11e-01 | edges_same_direction_twice=9 | 1 | 0.0335097407011 | 0.00e+00 |
| nist_edm/anc101_a.stp | 127 | 1 | 127 | 1 | 0 | 55,0,68,0,0,4 | nan(mesh) | 1 | 127 | 1 | 55,0,68,4,0,0 | 8108593.2422 | nan | edges_same_direction_twice=60 | 1 | 8114016.93429 | 6.69e-04 |
| nist_edm/bellow.stp | 68 | 1 | 68 | 1 | 0 | 2,0,2,0,0,64 | 186553.868245(mesh) | 1 | 68 | 1 | 2,0,2,64,0,0 | 187300.867305 | 3.99e-03 | edges_same_direction_twice=4 | 1 | 187300.867305 | 0.00e+00 |
| nist_edm/bolt.stp | 46 | 1 | 46 | 1 | 0 | 20,8,18,0,0,0 | 27316.8015509(mesh) | 1 | 46 | 1 | 20,8,18,0,0,0 | 27636.3072568 | 1.16e-02 | edges_same_direction_twice=36 | 1 | 27636.2622604 | 1.63e-06 |
| nist_edm/chamber.stp | 50 | 1 | 50 | 1 | 0 | 15,4,27,0,0,4 | 53946.269084(mesh) | 1 | 50 | 1 | 15,4,27,0,2,2 | 263099.637401 | 7.95e-01 | edges_same_direction_twice=57 | 1 | 17644.8169856 | 9.33e-01 |
| nist_edm/clevis21.stp | 66 | 1 | 66 | 1 | 0 | 30,0,24,0,0,12 | 1620499.93175(mesh) | 1 | 66 | 1 | 30,0,24,12,0,0 | 1712743.56874 | 5.39e-02 | edges_same_direction_twice=32 | 1 | 1712743.56874 | 0.00e+00 |
| nist_edm/flange.stp | 102 | 2 | 51 | 1 | 0 | 7,0,30,0,0,14 | 3892441642.6(mesh) | 2 | 51 | 1 | 7,0,30,4,10,0 | 74715267699.1 | 9.48e-01 | edges_same_direction_twice=36 | 1 | 74715267697.7 | 1.87e-11 |
| nist_edm/fork.stp | 106 | 1 | 106 | 0 | 0 | 29,0,47,0,0,30 | nan(mesh) | 1 | 106 | 1 | 29,0,47,0,16,14 | 1934375.24906 | nan | open_wires=1 edges_same_direction_twice=103 | 0 | nan(mesh) | nan |
| nist_edm/gear_40.stp | 456 | 1 | 456 | 0 | 0 | 352,0,104,0,0,0 | 1.90446134058e-06(mesh) | 1 | 456 | 1 | 352,0,104,0,0,0 | 3.14887271485e-06 | 3.95e-01 | open_wires=468 edges_same_direction_twice=524 | 1 | 3.14887271485e-06 | 0.00e+00 |
| nist_edm/interactingPockets.stp | 66 | 1 | 66 | 1 | 0 | 30,0,36,0,0,0 | 9092.63721306(mesh) | 1 | 66 | 1 | 30,0,36,0,0,0 | 12083.6947163 | 2.48e-01 | edges_same_direction_twice=100 | 1 | 12083.6947163 | 0.00e+00 |
| nist_edm/main_block.stp | 160 | 1 | 160 | 0 | 0 | 55,3,84,0,15,3 | nan(mesh) | 1 | 160 | 1 | 55,0,84,3,18,0 | 509.957067057 | nan | open_wires=6 edges_same_direction_twice=134 | 0 | nan(mesh) | nan |
| nist_edm/moon_buggy.stp | 113 | 1 | 113 | 0 | 0 | 28,8,26,2,19,30 | nan(mesh) | 1 | 113 | 1 | 28,8,26,4,40,7 | 1678598797.09 | nan | open_wires=20 edges_same_direction_twice=45 | 0 | nan(mesh) | nan |
| nist_edm/mt_jaw_half_finish-mach-bup.stp | 169 | 1 | 169 | 0 | 0 | 118,1,41,0,0,9 | nan(mesh) | 1 | 169 | 1 | 118,0,42,5,2,2 | 2550072.33927 | nan | open_wires=3 edges_same_direction_twice=81 | 0 | nan(mesh) | nan |
| nist_edm/needle-nose-inch.stp | 31 | 1 | 31 | 1 | 0 | 18,0,5,0,0,8 | 1.06529521907(mesh) | 1 | 31 | 1 | 18,0,5,0,4,4 | 0.887571332604 | 2.00e-01 | edges_same_direction_twice=53 | 1 | 0.715348586163 | 1.94e-01 |
| nist_edm/screw_driver1.stp | 107 | 1 | 107 | 0 | 0 | 5,3,14,4,2,79 | nan(mesh) | 1 | 107 | 1 | 5,2,14,14,50,22 | 23729.3651387 | nan | invalid_surfaces=1 open_wires=51 edges_same_direction_twice=128 | 0 | nan(mesh) | nan |
| nist_edm/sh-r44356-000-u.stp | 21 | 1 | 21 | 1 | 0 | 5,3,8,0,3,2 | nan(mesh) | 1 | 21 | 1 | 5,0,8,0,8,0 | 0.00780025400077 | nan | edges_same_direction_twice=23 | 1 | 0.00746780273956 | 4.26e-02 |
| nist_edm/sh-r44363-000-u-compressed.stp | 30 | 1 | 30 | 1 | 0 | 2,0,8,0,0,20 | 6.71402496175e-05(mesh) | 1 | 30 | 1 | 2,0,8,0,20,0 | 6.91481368876e-05 | 2.90e-02 | edges_same_direction_twice=2 | 1 | 6.63003995669e-05 | 4.12e-02 |
| nist_edm/stock.stp | 85 | 1 | 85 | 0 | 0 | 23,0,27,0,5,30 | nan(mesh) | 1 | 85 | 1 | 23,0,27,4,16,15 | 90.8262796648 | nan | open_wires=5 edges_same_direction_twice=120 | 0 | nan(mesh) | nan |
| nist_edm/swivel1-Part.step | 14 | 0 | 0 | - | - | - | - | 0 | 0 | - | - | - |  |  | - | - |  |
| occt_booltest/bottle.step | 72 | 2 | 68 | 0 | 0 | 13,16,30,0,1,8 | nan(mesh) | 2 | 68 | 1 | 13,16,30,0,9,0 | 6945.94428106 | nan | open_wires=33 edges_same_direction_twice=31 | 1 | nan(mesh) | nan |
| occt_data/Bottom_from_brep.step | 323 | 1 | 323 | 0 | 0 | 52,8,110,1,4,148 | nan(mesh) | 1 | 323 | 1 | 52,8,111,3,28,121 | 310019.710505 | nan | invalid_surfaces=1 open_wires=176 edges_same_direction_twice=325 | 0 | nan(mesh) | nan |
| occt_data/CrankArm_from_brep.step | 49 | 1 | 49 | 0 | 0 | 19,0,11,5,0,14 | nan(mesh) | 1 | 49 | 1 | 19,0,9,5,0,16 | 38682.8877705 | nan | open_wires=25 edges_same_direction_twice=64 | 0 | nan(mesh) | nan |
| occt_data/MODERN_MVCooker_1_from_brep.step | 15 | 1 | 15 | 0 | 0 | 13,0,2,0,0,0 | 5546.89893139(mesh) | 1 | 15 | 1 | 13,0,2,0,0,0 | 17993.1238898 | 6.92e-01 | open_wires=7 edges_same_direction_twice=20 | 1 | 17993.1238898 | 0.00e+00 |
| occt_data/MODERN_Table_1_from_brep.step | 22 | 1 | 22 | 0 | 0 | 12,0,10,0,0,0 | 13158.7015272(mesh) | 1 | 22 | 1 | 12,0,10,0,0,0 | 30649.4813642 | 5.71e-01 | open_wires=12 edges_same_direction_twice=14 | 1 | 13193.8091214(mesh) | 5.70e-01 |
| occt_data/Pump_Nut_from_brep.step | 25 | 1 | 25 | 0 | 0 | 8,0,1,0,2,14 | 21700.1373492(mesh) | 1 | 25 | 1 | 8,0,1,14,2,0 | 24130.3105554 | 1.01e-01 | open_wires=9 edges_same_direction_twice=16 | 1 | 38107.8751111 | 5.79e-01 |
| occt_data/Pump_TopCover_from_brep.step | 8 | 1 | 8 | 0 | 0 | 2,2,2,0,0,2 | 144024.234534(mesh) | 1 | 8 | 1 | 2,2,2,0,0,2 | 2495451.33124 | 9.42e-01 | open_wires=3 edges_same_direction_twice=5 | 1 | 1707627.93547(mesh) | 3.16e-01 |
| occt_data/bottle_from_brep.step | 71 | 1 | 71 | 0 | 0 | 13,16,30,0,1,11 | nan(mesh) | 1 | 71 | 1 | 13,16,31,0,9,2 | 6962.95413339 | nan | open_wires=34 edges_same_direction_twice=31 | 0 | nan(mesh) | nan |
| occt_data/linkrods.step | 37 | 0 | 0 | - | - | - | - | 1 | 37 | 1 | 6,0,4,0,9,18 | 3.84700170816 |  |  | - | - |  |
| occt_data/screw.step | 10 | 0 | 0 | - | - | - | - | 1 | 10 | 1 | 4,0,1,2,3,0 | 3788.27059337 |  |  | - | - |  |

## Boolean summary

### OCCT over every case (1850 booleans in 370 cases)

| returned | error | timeout/crash | non-empty and not valid (BRepCheck) | empty |
|---|---|---|---|---|
| 1843 | 6 | 1 | 69 | 73 |

### ours as the reader delivers the parts (raw), all cases (707 booleans)

| | ours | OCCT |
|---|---|---|
| result returned | 35 | 706 |
| failed with an error | 662 | 1 |
| timeout / crash | 0 | 0 |
| returned non-empty but not valid (ours is_valid, OCCT BRepCheck) | 0 | 14 |
| returned, valid, not a closed solid (ours is_solid; OCCT: no solid) | 0 | 0 |
| empty result | 2 | 18 |
| both returned: volume agrees to 1e-6 / 1e-3 / worse (of the larger result volume of the case) | 35 / 0 / 0 | |
| both returned: same face count | 35 of 35 | |
| time, single booleans (∩, ∪, A−B, B−A), both returned (28): total s | 1.7 | 0.652 |
| time ratio ours/OCCT, single booleans (∩, ∪, A−B, B−A): median, total | 3.16, 2.61 | |
| time, xor (OCCT: two cuts and a fuse), both returned (7): total s | 0.382 | 0.497 |
| time ratio ours/OCCT, xor (OCCT: two cuts and a fuse): median, total | 1.96, 0.769 | |
| time of every boolean that ended (ok or error), total s | 2.23 | 460 |

### ours with driver-side orientation repair, parts whose repaired volume matches OCCT (< 1e-2): rotated copies and cutters (650 booleans)

| | ours | OCCT |
|---|---|---|
| result returned | 37 | 648 |
| failed with an error | 613 | 1 |
| timeout / crash | 0 | 1 |
| returned non-empty but not valid (ours is_valid, OCCT BRepCheck) | 0 | 8 |
| returned, valid, not a closed solid (ours is_solid; OCCT: no solid) | 0 | 0 |
| empty result | 6 | 25 |
| both returned: volume agrees to 1e-6 / 1e-3 / worse (of the larger result volume of the case) | 35 / 0 / 2 | |
| both returned: same face count | 35 of 37 | |
| time, single booleans (∩, ∪, A−B, B−A), both returned (32): total s | 7.04 | 1.8 |
| time ratio ours/OCCT, single booleans (∩, ∪, A−B, B−A): median, total | 2.55, 3.91 | |
| time, xor (OCCT: two cuts and a fuse), both returned (5): total s | 1.38 | 1.12 |
| time ratio ours/OCCT, xor (OCCT: two cuts and a fuse): median, total | 1.01, 1.23 | |
| time of every boolean that ended (ok or error), total s | 1.38e+03 | 682 |

### ... of which rotated copies of the part (occt-booltest style) (260 booleans)

| | ours | OCCT |
|---|---|---|
| result returned | 10 | 258 |
| failed with an error | 250 | 1 |
| timeout / crash | 0 | 1 |
| returned non-empty but not valid (ours is_valid, OCCT BRepCheck) | 0 | 4 |
| returned, valid, not a closed solid (ours is_solid; OCCT: no solid) | 0 | 0 |
| empty result | 0 | 15 |
| both returned: volume agrees to 1e-6 / 1e-3 / worse (of the larger result volume of the case) | 10 / 0 / 0 | |
| both returned: same face count | 10 of 10 | |
| time, single booleans (∩, ∪, A−B, B−A), both returned (8): total s | 5.05 | 1.27 |
| time ratio ours/OCCT, single booleans (∩, ∪, A−B, B−A): median, total | 4.03, 3.97 | |
| time, xor (OCCT: two cuts and a fuse), both returned (2): total s | 1.21 | 0.846 |
| time ratio ours/OCCT, xor (OCCT: two cuts and a fuse): median, total | 1.47, 1.43 | |
| time of every boolean that ended (ok or error), total s | 1.17e+03 | 633 |

### ... of which box, cylinder and sphere cutters (390 booleans)

| | ours | OCCT |
|---|---|---|
| result returned | 27 | 390 |
| failed with an error | 363 | 0 |
| timeout / crash | 0 | 0 |
| returned non-empty but not valid (ours is_valid, OCCT BRepCheck) | 0 | 4 |
| returned, valid, not a closed solid (ours is_solid; OCCT: no solid) | 0 | 0 |
| empty result | 6 | 10 |
| both returned: volume agrees to 1e-6 / 1e-3 / worse (of the larger result volume of the case) | 25 / 0 / 2 | |
| both returned: same face count | 25 of 27 | |
| time, single booleans (∩, ∪, A−B, B−A), both returned (24): total s | 1.99 | 0.528 |
| time ratio ours/OCCT, single booleans (∩, ∪, A−B, B−A): median, total | 2.2, 3.76 | |
| time, xor (OCCT: two cuts and a fuse), both returned (3): total s | 0.174 | 0.276 |
| time ratio ours/OCCT, xor (OCCT: two cuts and a fuse): median, total | 0.829, 0.63 | |
| time of every boolean that ended (ok or error), total s | 210 | 48.6 |

### ours with repair, parts whose repaired volume does NOT match OCCT (inputs differ; success counts only) (358 booleans)

| | ours | OCCT |
|---|---|---|
| result returned | 2 | 358 |
| failed with an error | 336 | 0 |
| timeout / crash | 10 | 0 |
| returned non-empty but not valid (ours is_valid, OCCT BRepCheck) | 0 | 9 |
| returned, valid, not a closed solid (ours is_solid; OCCT: no solid) | 0 | 0 |
| empty result | 1 | 6 |
| both returned: volume agrees to 1e-6 / 1e-3 / worse (of the larger result volume of the case) | 0 / 0 / 2 | |
| both returned: same face count | 0 of 2 | |
| time, single booleans (∩, ∪, A−B, B−A), both returned (2): total s | 0.00938 | 0.0239 |
| time ratio ours/OCCT, single booleans (∩, ∪, A−B, B−A): median, total | 0.387, 0.393 | |
| time of every boolean that ended (ok or error), total s | 246 | 300 |

### forum rebuilds and part pairs (50 booleans)

| | ours | OCCT |
|---|---|---|
| result returned | 30 | 50 |
| failed with an error | 20 | 0 |
| timeout / crash | 0 | 0 |
| returned non-empty but not valid (ours is_valid, OCCT BRepCheck) | 0 | 0 |
| returned, valid, not a closed solid (ours is_solid; OCCT: no solid) | 0 | 0 |
| empty result | 2 | 4 |
| both returned: volume agrees to 1e-6 / 1e-3 / worse (of the larger result volume of the case) | 30 / 0 / 0 | |
| both returned: same face count | 30 of 30 | |
| time, single booleans (∩, ∪, A−B, B−A), both returned (24): total s | 1.49 | 0.543 |
| time ratio ours/OCCT, single booleans (∩, ∪, A−B, B−A): median, total | 5.88, 2.75 | |
| time, xor (OCCT: two cuts and a fuse), both returned (6): total s | 0.395 | 0.422 |
| time ratio ours/OCCT, xor (OCCT: two cuts and a fuse): median, total | 2.27, 0.934 | |
| time of every boolean that ended (ok or error), total s | 42.2 | 42.8 |

## Volume identities per kernel

Per case: max(| |A∪B| − (|A−B| + |B−A| + |A∩B|) |, | |A⊕B| − (|A−B| + |B−A|) |) / |A∪B|, over cases where all five returned.

| series | cases | ≤ 1e-6 | ≤ 1e-3 | worse |
|---|---|---|---|---|
| OCCT | 365 | 278 | 49 | 38 |
| ours (repaired input, matched parts + forum/pairs) | 11 | 11 | 0 | 0 |

OCCT cases breaking the identities by more than 1e-3: `hf_brepground__00015160_chamfer_12#rot5z` (2.5e+304), `hf_brepground__00019536_chamfer_10#rot5z` (2e+306), `hf_brepground__00071814_fillet_15#rot5z` (0.79), `hf_brepmfr__sample_round#rot5z` (inf), `hf_brepmfr__sample_round_1#rot5z` (0.0083), `hf_brepmfr__sample_round_2#rot30x` (1.3e+308), `hf_brepmfr__sample_round_2#rot5z` (0.01), `hf_brepmfr__zip_defaultamacchina000#rot30x` (inf), `hf_brepmfr__zip_ea0000006992revit#rot5z` (1.9), `hf_brepmfr__zip_ea0000006997revit#rot30x` (0.2), `hf_brepmfr__zip_ea0000007008revit#rot5z` (1.1e+306), `hf_zero_to_cad__3692c35e-1985-41b6-b45d-edc922a59854#rot30x` (0.25), `hf_zero_to_cad__45278456-3334-0c11-81a7-458fce65d6d7#rot30x` (67), `hf_zero_to_cad__45278456-3334-0c11-81a7-458fce65d6d7#rot5z` (9e+304), `hf_zero_to_cad__8bccb9ee-085e-5ce4-75ab-15c7ee2cab24#rot30x` (0.035), `hf_zero_to_cad__916572bc-ac4f-03d6-fc3d-1670590c4ce4#rot30x` (0.15), `mcneel_rebuilt__threaded_rod_cutter#rot30x` (3.2e+302), `mcneel_rebuilt__threaded_rod_cutter#rot5z` (0.5), `nist_edm__260012#cyl` (0.81), `nist_edm__RestButton1#rot30x` (0.54), `nist_edm__RestButton1#rot5z` (6.7e+298), `nist_edm__RestButton1#cyl` (3.8e+298), `nist_edm__flange#rot5z` (0.0017), `nist_edm__fork#rot30x` (3.9e+306), `nist_edm__fork#rot5z` (0.041), `nist_edm__gear_40#rot30x` (0.15), `nist_edm__main_block#rot5z` (0.19), `nist_edm__main_block#box` (0.0012), `nist_edm__moon_buggy#rot5z` (0.66), `nist_edm__mt_jaw_half_finish-mach-bup#rot5z` (6.3), `nist_edm__sh-r44356-000-u#rot5z` (8.4e+297), `nist_edm__sh-r44356-000-u#sph` (0.025), `nist_edm__sh-r44363-000-u-compressed#rot30x` (0.32), `nist_edm__sh-r44363-000-u-compressed#rot5z` (0.031), `occt_data__Bottom_from_brep#rot30x` (4.1e+03), `occt_data__CrankArm_from_brep#rot30x` (0.46), `occt_data__CrankArm_from_brep#rot5z` (0.0079), `occt_data__bottle_from_brep#rot30x` (0.097)

OCCT cases with a BRepCheck-invalid result: `hf_brepground__00015160_chamfer_12#rot5z` (a-b/b-a/xor), `hf_brepground__00019536_chamfer_10#rot30x` (xor), `hf_brepground__00071814_fillet_15#rot30x` (xor), `hf_brepground__00071814_fillet_15#rot5z` (union/b-a/xor), `hf_brepground__00170968_fillet_10#rot30x` (union), `hf_brepground__00290572_chamfer_12#box` (union/a-b/xor), `hf_brepground__00290572_chamfer_12#rot5z` (b-a), `hf_brepmfr__sample_round#rot30x` (xor), `hf_brepmfr__sample_round#rot5z` (a-b/xor), `hf_brepmfr__sample_round_1#rot30x` (xor), `hf_brepmfr__sample_round_1#rot5z` (xor), `hf_brepmfr__sample_round_2#rot30x` (xor), `hf_brepmfr__sample_round_2#rot5z` (xor), `hf_zero_to_cad__3692c35e-1985-41b6-b45d-edc922a59854#rot30x` (xor), `hf_zero_to_cad__45278456-3334-0c11-81a7-458fce65d6d7#rot30x` (b-a), `hf_zero_to_cad__916572bc-ac4f-03d6-fc3d-1670590c4ce4#rot30x` (xor), `mcneel_rebuilt__threaded_rod_cutter#rot30x` (b-a), `nist_edm__260012#cyl` (a-b/xor), `nist_edm__RestButton1#rot30x` (xor), `nist_edm__chamber#rot30x` (intersection/union/a-b/b-a/xor), `nist_edm__chamber#rot5z` (intersection/union), `nist_edm__flange#rot5z` (xor), `nist_edm__fork#rot30x` (xor), `nist_edm__fork#rot5z` (intersection/union/a-b/b-a/xor), `nist_edm__gear_40#box` (xor), `nist_edm__main_block#rot30x` (union/xor), `nist_edm__main_block#rot5z` (intersection/union/a-b/xor), `nist_edm__moon_buggy#rot5z` (intersection/union/a-b/b-a/xor), `nist_edm__mt_jaw_half_finish-mach-bup#rot5z` (union/xor), `nist_edm__screw_driver1#rot30x` (xor), `nist_edm__sh-r44356-000-u#rot5z` (xor), `nist_edm__sh-r44363-000-u-compressed#rot5z` (xor), `occt_booltest__bottle#rot30x` (xor), `occt_data__Bottom_from_brep#rot5z` (union/a-b/b-a), `occt_data__Pump_TopCover_from_brep#sph` (union/a-b/xor), `occt_data__bottle_from_brep#rot30x` (xor), `occt_data__linkrods#rot30x` (xor), `occt_data__linkrods#sph` (union/b-a)

## Our error messages (repaired series), by count

| status | message (to the first colon) | booleans |
|---|---|---|
| FAIL | Split curve/trim correspondence is mismatched | 195 |
| FAIL | Analytic pullback did not obtain a complete paired-parameter certificate | 190 |
| FAIL | Required edge event lacks an original raw curve/trim law | 144 |
| FAIL | Native BRep Booleans require closed oriented solid operands | 80 |
| FAIL | Support inventory curve lacks original paired agreement | 69 |
| FAIL | Native SSI could not resolve an overlapping rational hull pair | 49 |
| FAIL | Interference lacks whole original paired agreement | 31 |
| FAIL | Native plane section point did not converge | 31 |
| FAIL | Analytic section pcurve has no certified original raw parameter law | 20 |
| FAIL | Curve intersection has a constant input or tolerance below coordinate resolution | 19 |
| FAIL | Empty support inventory has unowned original root graphs | 19 |
| FAIL | Analytic raw seam crossing has no geometric event | 19 |
| FAIL | BRep solid classification requires closed oriented solids | 15 |
| CRASH | exit -6 *** stack smashing detected ***: terminated | 10 |
| FAIL | Unresolved curve/surface root enclosure | 10 |
| FAIL | Native Boolean face classification is unresolved | 10 |
| FAIL | Native SSI fitted section does not cover its certified starting seed | 10 |
| FAIL | Unresolved curve/surface coincidence or excessive root count | 10 |
| FAIL | edge and pcurve disagree inside their ranges; tolerance=9.9999999999999995e-08; world=2 CVs [0,1]; pcurve=2 CVs [0,1]; surface=13x2 CVs | 9 |
| FAIL | pcurve reparameterization is unresolved | 9 |
| FAIL | Native Boolean has no resolved interior witness or has unsupported coincidence | 5 |
| FAIL | Tangent fan has an unresolved common endpoint | 5 |
| FAIL | Unowned interior trim loop | 5 |
| FAIL | Boundary event has invalid original raw coordinates | 5 |
| FAIL | Cutter midpoint is on the boundary without established overlap ownership | 4 |

## OCCT failures

| status | message | booleans |
|---|---|---|
| invalid | BRepCheck_Analyzer: not valid | 69 |
| FAIL | NotDone | 6 |
| CRASH | exit -9 | 1 |


## occt-booltest chain on the bottle (body ← body ∩ rotated(body), 5 iterations)

Rotation about the axis through (0, 0, 38.5), the bottle's box centre. Columns: iteration, status, seconds, faces, volume.

| kernel | axis, degrees | iterations |
|---|---|---|
| occt | 1,0,0,15 | 1 ok 2.52s 224 faces, 999.427888958<br>2 ok 9.27s 229 faces, 552.401939227<br>3 ok 1.96s 164 faces, 358.508569312<br>4 ok 0.735s 156 faces, 285.079280188<br>5 ok 0.799s 204 faces, 247.518625887 |
| occt | 1,1,1,45 | 1 ok 2.08s 124 faces, 223.77173035<br>2 ok 1.69s 39 faces, 5.79626842593<br>3 ok 0.638s 16 faces, 1.07002377199<br>4 ok 1.13s 20 faces, 0.570528058152<br>5 ok 0.506s 24 faces, 0.413806837984 |
| occt | 0,0,1,5 | 1 ok 3.07s 155 faces, 2956.05329139<br>2 ok 6.23s 228 faces, 2067.55028545<br>3 ok 8.14s 265 faces, 1682.77976361<br>4 ok 8.82s 330 faces, 1453.33888405<br>5 ok 10.9s 387 faces, 1299.03744014 |
| occt | 0,1,0,90 | 1 ok 0.517s 80 faces, 373.789983454<br>2 ok 1.41s 80 faces, 373.789983454<br>3 ok 1.44s 80 faces, 373.789983454<br>4 ok 1.53s 80 faces, 373.789983454<br>5 ok 1.42s 80 faces, 373.789983454 |
| ours_raw | 1,0,0,15 | 1 FAIL 0.000133s: Native BRep Booleans require closed oriented solid operands |
| ours_raw | 1,1,1,45 | 1 FAIL 0.000133s: Native BRep Booleans require closed oriented solid operands |
| ours_raw | 0,0,1,5 | 1 FAIL 0.000112s: Native BRep Booleans require closed oriented solid operands |
| ours_raw | 0,1,0,90 | 1 FAIL 0.000108s: Native BRep Booleans require closed oriented solid operands |
| ours_rep | 1,0,0,15 | 1 FAIL 0.0058s: Native SSI fitted section does not cover its certified starting seed |
| ours_rep | 1,1,1,45 | 1 FAIL 0.464s: Support inventory curve lacks original paired agreement |
| ours_rep | 0,0,1,5 | 1 FAIL 1.58s: Native SSI could not resolve an overlapping rational hull pair: {"depth":48,"root_found":f |
| ours_rep | 0,1,0,90 | 1 FAIL 3.28s: Analytic pullback did not obtain a complete paired-parameter certificate: Certified endpoi |

## Pictures

One per benchmarked part (its slab-cutter case `#box`) plus the forum rebuilds and part pairs. Top row ours, bottom row
OCCT; columns operands A (grey) and B (tan), then A∩B, A∪B, A−B, B−A, A⊕B; red squares are vertices, black lines edges;
counts under each panel, red where ours and OCCT differ; a failed boolean or load is an empty panel with its error.

| case | part | ours (repaired input) | OCCT | image |
|---|---|---|---|---|
| `forum123416#mesh_cone` | t/123416 closed solid of 80 mesh triangles minus a cone | ok 5 | ok 5 | [cmp_forum123416_mesh_cone.png](images/cmp_forum123416_mesh_cone.png) |
| `forum163125#box_cone_base` | t/163125 box minus cone, base coplanar with the bottom face | ok 5 | ok 5 | [cmp_forum163125_box_cone_base.png](images/cmp_forum163125_box_cone_base.png) |
| `forum163125#box_cyl_inside` | t/163125 box minus cylinder fully inside, caps coplanar with top and bottom | ok 5 | ok 5 | [cmp_forum163125_box_cyl_inside.png](images/cmp_forum163125_box_cyl_inside.png) |
| `forum163125#box_cyl_side` | t/163125 box minus cylinder through a side face, caps coplanar | ok 5 | ok 5 | [cmp_forum163125_box_cyl_side.png](images/cmp_forum163125_box_cyl_side.png) |
| `forum213347#lining_brace` | t/213347 wall lining minus diagonal brace of the same thickness, front and back coplanar | ok 5 | ok 5 | [cmp_forum213347_lining_brace.png](images/cmp_forum213347_lining_brace.png) |
| `forum213347#lining_frame` | t/213347 wall lining minus frame stud, top and bottom coplanar | ok 5 | ok 5 | [cmp_forum213347_lining_frame.png](images/cmp_forum213347_lining_frame.png) |
| `forum216730#rod_thread` | t/216730 rod minus helical thread cutter (pipe shell along a helix) | FAIL 5 | ok 5 | [cmp_forum216730_rod_thread.png](images/cmp_forum216730_rod_thread.png) |
| `github_misc__as1-ac-214#box` | github_misc/as1-ac-214.stp | FAIL 5 | ok 5 | [cmp_github_misc__as1-ac-214_box.png](images/cmp_github_misc__as1-ac-214_box.png) |
| `github_misc__nema-17-bracket#box` | github_misc/nema-17-bracket.step | FAIL 5 | ok 5 | [cmp_github_misc__nema-17-bracket_box.png](images/cmp_github_misc__nema-17-bracket_box.png) |
| `hf_brepground__00015160_chamfer_12#box` | hf_brepground/00015160_chamfer_12.step | FAIL 5 | ok 5 | [cmp_hf_brepground__00015160_chamfer_12_box.png](images/cmp_hf_brepground__00015160_chamfer_12_box.png) |
| `hf_brepground__00019536_chamfer_10#box` | hf_brepground/00019536_chamfer_10.step | FAIL 5 | ok 5 | [cmp_hf_brepground__00019536_chamfer_10_box.png](images/cmp_hf_brepground__00019536_chamfer_10_box.png) |
| `hf_brepground__00042148_fillet_11#box` | hf_brepground/00042148_fillet_11.step | FAIL 5 | ok 5 | [cmp_hf_brepground__00042148_fillet_11_box.png](images/cmp_hf_brepground__00042148_fillet_11_box.png) |
| `hf_brepground__00071814_fillet_15#box` | hf_brepground/00071814_fillet_15.step | FAIL 5 | ok 5 | [cmp_hf_brepground__00071814_fillet_15_box.png](images/cmp_hf_brepground__00071814_fillet_15_box.png) |
| `hf_brepground__00089757_fillet_16#box` | hf_brepground/00089757_fillet_16.step | FAIL 5 | ok 5 | [cmp_hf_brepground__00089757_fillet_16_box.png](images/cmp_hf_brepground__00089757_fillet_16_box.png) |
| `hf_brepground__00161395_chamfer_16#box` | hf_brepground/00161395_chamfer_16.step | FAIL 5 | ok 5 | [cmp_hf_brepground__00161395_chamfer_16_box.png](images/cmp_hf_brepground__00161395_chamfer_16_box.png) |
| `hf_brepground__00170968_fillet_10#box` | hf_brepground/00170968_fillet_10.step | FAIL 5 | ok 5 | [cmp_hf_brepground__00170968_fillet_10_box.png](images/cmp_hf_brepground__00170968_fillet_10_box.png) |
| `hf_brepground__00171214_fillet_11#box` | hf_brepground/00171214_fillet_11.step | FAIL 5 | ok 5 | [cmp_hf_brepground__00171214_fillet_11_box.png](images/cmp_hf_brepground__00171214_fillet_11_box.png) |
| `hf_brepground__00275424_fillet_17#box` | hf_brepground/00275424_fillet_17.step | FAIL 5 | ok 5 | [cmp_hf_brepground__00275424_fillet_17_box.png](images/cmp_hf_brepground__00275424_fillet_17_box.png) |
| `hf_brepground__00290572_chamfer_12#box` | hf_brepground/00290572_chamfer_12.step | FAIL 5 | ok 5 | [cmp_hf_brepground__00290572_chamfer_12_box.png](images/cmp_hf_brepground__00290572_chamfer_12_box.png) |
| `hf_brepmfr__0m-3623639#box` | hf_brepmfr/0m-3623639.stp | FAIL 5 | ok 5 | [cmp_hf_brepmfr__0m-3623639_box.png](images/cmp_hf_brepmfr__0m-3623639_box.png) |
| `hf_brepmfr__107050503-m8u-8700-a267#box` | hf_brepmfr/107050503-m8u-8700-a267.stp | FAIL 5 | ok 5 | [cmp_hf_brepmfr__107050503-m8u-8700-a267_box.png](images/cmp_hf_brepmfr__107050503-m8u-8700-a267_box.png) |
| `hf_brepmfr__16P-03303#box` | hf_brepmfr/16P-03303.step | FAIL 5 | ok 5 | [cmp_hf_brepmfr__16P-03303_box.png](images/cmp_hf_brepmfr__16P-03303_box.png) |
| `hf_brepmfr__sample_round_1#box` | hf_brepmfr/sample_round_1.stp | FAIL 5 | ok 5 | [cmp_hf_brepmfr__sample_round_1_box.png](images/cmp_hf_brepmfr__sample_round_1_box.png) |
| `hf_brepmfr__sample_round_2#box` | hf_brepmfr/sample_round_2.stp | FAIL 5 | ok 5 | [cmp_hf_brepmfr__sample_round_2_box.png](images/cmp_hf_brepmfr__sample_round_2_box.png) |
| `hf_brepmfr__sample_round#box` | hf_brepmfr/sample_round.stp | FAIL 5 | ok 5 | [cmp_hf_brepmfr__sample_round_box.png](images/cmp_hf_brepmfr__sample_round_box.png) |
| `hf_brepmfr__zip_chainlinkouter00#box` | hf_brepmfr/zip_chainlinkouter00.stp | FAIL 5 | ok 5 | [cmp_hf_brepmfr__zip_chainlinkouter00_box.png](images/cmp_hf_brepmfr__zip_chainlinkouter00_box.png) |
| `hf_brepmfr__zip_cylinder400bore000#box` | hf_brepmfr/zip_cylinder400bore000.stp | FAIL 5 | ok 5 | [cmp_hf_brepmfr__zip_cylinder400bore000_box.png](images/cmp_hf_brepmfr__zip_cylinder400bore000_box.png) |
| `hf_brepmfr__zip_cylinder600bore000#box` | hf_brepmfr/zip_cylinder600bore000.stp | FAIL 5 | ok 5 | [cmp_hf_brepmfr__zip_cylinder600bore000_box.png](images/cmp_hf_brepmfr__zip_cylinder600bore000_box.png) |
| `hf_brepmfr__zip_defaultamacchina000#box` | hf_brepmfr/zip_defaultamacchina000.stp | FAIL 5 | ok 5 | [cmp_hf_brepmfr__zip_defaultamacchina000_box.png](images/cmp_hf_brepmfr__zip_defaultamacchina000_box.png) |
| `hf_brepmfr__zip_dfautbrutdusinage0001#box` | hf_brepmfr/zip_dfautbrutdusinage0001.stp | FAIL 3, ok 2 | ok 5 | [cmp_hf_brepmfr__zip_dfautbrutdusinage0001_box.png](images/cmp_hf_brepmfr__zip_dfautbrutdusinage0001_box.png) |
| `hf_brepmfr__zip_doorlatchvonduprin0001#box` | hf_brepmfr/zip_doorlatchvonduprin0001.stp | FAIL 5 | ok 5 | [cmp_hf_brepmfr__zip_doorlatchvonduprin0001_box.png](images/cmp_hf_brepmfr__zip_doorlatchvonduprin0001_box.png) |
| `hf_brepmfr__zip_dripmanifold0#box` | hf_brepmfr/zip_dripmanifold0.stp | FAIL 5 | ok 5 | [cmp_hf_brepmfr__zip_dripmanifold0_box.png](images/cmp_hf_brepmfr__zip_dripmanifold0_box.png) |
| `hf_brepmfr__zip_ea0000006992revit#box` | hf_brepmfr/zip_ea0000006992revit.stp | FAIL 5 | ok 5 | [cmp_hf_brepmfr__zip_ea0000006992revit_box.png](images/cmp_hf_brepmfr__zip_ea0000006992revit_box.png) |
| `hf_brepmfr__zip_ea0000006997revit#box` | hf_brepmfr/zip_ea0000006997revit.stp | FAIL 5 | ok 5 | [cmp_hf_brepmfr__zip_ea0000006997revit_box.png](images/cmp_hf_brepmfr__zip_ea0000006997revit_box.png) |
| `hf_brepmfr__zip_ea0000007008revit#box` | hf_brepmfr/zip_ea0000007008revit.stp | FAIL 5 | ok 5 | [cmp_hf_brepmfr__zip_ea0000007008revit_box.png](images/cmp_hf_brepmfr__zip_ea0000007008revit_box.png) |
| `hf_zero_to_cad__13e02b4d-d613-422b-6a17-390f6402693a#box` | hf_zero_to_cad/13e02b4d-d613-422b-6a17-390f6402693a.step | FAIL 5 | ok 5 | [cmp_hf_zero_to_cad__13e02b4d-d613-422b-6a17-390f6402693a_box.png](images/cmp_hf_zero_to_cad__13e02b4d-d613-422b-6a17-390f6402693a_box.png) |
| `hf_zero_to_cad__3692c35e-1985-41b6-b45d-edc922a59854#box` | hf_zero_to_cad/3692c35e-1985-41b6-b45d-edc922a59854.step | FAIL 5 | ok 5 | [cmp_hf_zero_to_cad__3692c35e-1985-41b6-b45d-edc922a59854_box.png](images/cmp_hf_zero_to_cad__3692c35e-1985-41b6-b45d-edc922a59854_box.png) |
| `hf_zero_to_cad__3bbf8b2b-5a16-b6b4-0c60-4df743e5e0bc#box` | hf_zero_to_cad/3bbf8b2b-5a16-b6b4-0c60-4df743e5e0bc.step | FAIL 5 | ok 5 | [cmp_hf_zero_to_cad__3bbf8b2b-5a16-b6b4-0c60-4df743e5e0bc_box.png](images/cmp_hf_zero_to_cad__3bbf8b2b-5a16-b6b4-0c60-4df743e5e0bc_box.png) |
| `hf_zero_to_cad__45278456-3334-0c11-81a7-458fce65d6d7#box` | hf_zero_to_cad/45278456-3334-0c11-81a7-458fce65d6d7.step | FAIL 5 | ok 5 | [cmp_hf_zero_to_cad__45278456-3334-0c11-81a7-458fce65d6d7_box.png](images/cmp_hf_zero_to_cad__45278456-3334-0c11-81a7-458fce65d6d7_box.png) |
| `hf_zero_to_cad__4b3aaa7b-f278-fc6a-8f9f-28fd4893be76#box` | hf_zero_to_cad/4b3aaa7b-f278-fc6a-8f9f-28fd4893be76.step | FAIL 5 | ok 5 | [cmp_hf_zero_to_cad__4b3aaa7b-f278-fc6a-8f9f-28fd4893be76_box.png](images/cmp_hf_zero_to_cad__4b3aaa7b-f278-fc6a-8f9f-28fd4893be76_box.png) |
| `hf_zero_to_cad__56155734-8313-cde8-e96a-dbb3bbe3ba2f#box` | hf_zero_to_cad/56155734-8313-cde8-e96a-dbb3bbe3ba2f.step | FAIL 5 | ok 5 | [cmp_hf_zero_to_cad__56155734-8313-cde8-e96a-dbb3bbe3ba2f_box.png](images/cmp_hf_zero_to_cad__56155734-8313-cde8-e96a-dbb3bbe3ba2f_box.png) |
| `hf_zero_to_cad__5c6512ae-9182-fc5e-05b1-b23c3735d060#box` | hf_zero_to_cad/5c6512ae-9182-fc5e-05b1-b23c3735d060.step | FAIL 5 | ok 5 | [cmp_hf_zero_to_cad__5c6512ae-9182-fc5e-05b1-b23c3735d060_box.png](images/cmp_hf_zero_to_cad__5c6512ae-9182-fc5e-05b1-b23c3735d060_box.png) |
| `hf_zero_to_cad__89ded05a-e2be-350b-db33-e42eb475ce39#box` | hf_zero_to_cad/89ded05a-e2be-350b-db33-e42eb475ce39.step | FAIL 5 | ok 5 | [cmp_hf_zero_to_cad__89ded05a-e2be-350b-db33-e42eb475ce39_box.png](images/cmp_hf_zero_to_cad__89ded05a-e2be-350b-db33-e42eb475ce39_box.png) |
| `hf_zero_to_cad__8bccb9ee-085e-5ce4-75ab-15c7ee2cab24#box` | hf_zero_to_cad/8bccb9ee-085e-5ce4-75ab-15c7ee2cab24.step | FAIL 5 | ok 5 | [cmp_hf_zero_to_cad__8bccb9ee-085e-5ce4-75ab-15c7ee2cab24_box.png](images/cmp_hf_zero_to_cad__8bccb9ee-085e-5ce4-75ab-15c7ee2cab24_box.png) |
| `hf_zero_to_cad__916572bc-ac4f-03d6-fc3d-1670590c4ce4#box` | hf_zero_to_cad/916572bc-ac4f-03d6-fc3d-1670590c4ce4.step | FAIL 5 | ok 5 | [cmp_hf_zero_to_cad__916572bc-ac4f-03d6-fc3d-1670590c4ce4_box.png](images/cmp_hf_zero_to_cad__916572bc-ac4f-03d6-fc3d-1670590c4ce4_box.png) |
| `mcneel_rebuilt__mesh_blob_80#box` | mcneel_rebuilt/mesh_blob_80.step | ok 5 | ok 5 | [cmp_mcneel_rebuilt__mesh_blob_80_box.png](images/cmp_mcneel_rebuilt__mesh_blob_80_box.png) |
| `mcneel_rebuilt__mesh_blob_80#rot5z` | mcneel_rebuilt/mesh_blob_80.step | ok 5 | ok 5 | [cmp_mcneel_rebuilt__mesh_blob_80_rot5z.png](images/cmp_mcneel_rebuilt__mesh_blob_80_rot5z.png) |
| `mcneel_rebuilt__threaded_rod_cutter#box` | mcneel_rebuilt/threaded_rod_cutter.step | FAIL 5 | ok 5 | [cmp_mcneel_rebuilt__threaded_rod_cutter_box.png](images/cmp_mcneel_rebuilt__threaded_rod_cutter_box.png) |
| `nist_edm__260012#box` | nist_edm/260012.stp | FAIL 5 | ok 5 | [cmp_nist_edm__260012_box.png](images/cmp_nist_edm__260012_box.png) |
| `nist_edm__DoubleCam1#box` | nist_edm/DoubleCam1.stp | FAIL 5 | ok 5 | [cmp_nist_edm__DoubleCam1_box.png](images/cmp_nist_edm__DoubleCam1_box.png) |
| `nist_edm__KnurledKnob10#box` | nist_edm/KnurledKnob10.stp | FAIL 5 | ok 5 | [cmp_nist_edm__KnurledKnob10_box.png](images/cmp_nist_edm__KnurledKnob10_box.png) |
| `nist_edm__NC_DRIVE#box` | nist_edm/NC_DRIVE.stp | FAIL 5 | ok 5 | [cmp_nist_edm__NC_DRIVE_box.png](images/cmp_nist_edm__NC_DRIVE_box.png) |
| `nist_edm__RestButton1#box` | nist_edm/RestButton1.stp | FAIL 5 | ok 5 | [cmp_nist_edm__RestButton1_box.png](images/cmp_nist_edm__RestButton1_box.png) |
| `nist_edm__anc101_a#box` | nist_edm/anc101_a.stp | FAIL 5 | ok 5 | [cmp_nist_edm__anc101_a_box.png](images/cmp_nist_edm__anc101_a_box.png) |
| `nist_edm__bellow#box` | nist_edm/bellow.stp | FAIL 5 | ok 5 | [cmp_nist_edm__bellow_box.png](images/cmp_nist_edm__bellow_box.png) |
| `nist_edm__bellow#cyl` | nist_edm/bellow.stp | FAIL 3, ok 2 | ok 5 | [cmp_nist_edm__bellow_cyl.png](images/cmp_nist_edm__bellow_cyl.png) |
| `nist_edm__bolt#box` | nist_edm/bolt.stp | FAIL 5 | ok 5 | [cmp_nist_edm__bolt_box.png](images/cmp_nist_edm__bolt_box.png) |
| `nist_edm__chamber#box` | nist_edm/chamber.stp | FAIL 5 | ok 5 | [cmp_nist_edm__chamber_box.png](images/cmp_nist_edm__chamber_box.png) |
| `nist_edm__clevis21#box` | nist_edm/clevis21.stp | FAIL 5 | ok 5 | [cmp_nist_edm__clevis21_box.png](images/cmp_nist_edm__clevis21_box.png) |
| `nist_edm__flange#box` | nist_edm/flange.stp | FAIL 5 | ok 5 | [cmp_nist_edm__flange_box.png](images/cmp_nist_edm__flange_box.png) |
| `nist_edm__fork#box` | nist_edm/fork.stp | FAIL 5 | ok 5 | [cmp_nist_edm__fork_box.png](images/cmp_nist_edm__fork_box.png) |
| `nist_edm__gear_40#box` | nist_edm/gear_40.stp | FAIL 5 | ok 5 | [cmp_nist_edm__gear_40_box.png](images/cmp_nist_edm__gear_40_box.png) |
| `nist_edm__interactingPockets#box` | nist_edm/interactingPockets.stp | FAIL 5 | ok 5 | [cmp_nist_edm__interactingPockets_box.png](images/cmp_nist_edm__interactingPockets_box.png) |
| `nist_edm__main_block#box` | nist_edm/main_block.stp | FAIL 5 | ok 5 | [cmp_nist_edm__main_block_box.png](images/cmp_nist_edm__main_block_box.png) |
| `nist_edm__moon_buggy#box` | nist_edm/moon_buggy.stp | FAIL 5 | ok 5 | [cmp_nist_edm__moon_buggy_box.png](images/cmp_nist_edm__moon_buggy_box.png) |
| `nist_edm__mt_jaw_half_finish-mach-bup#box` | nist_edm/mt_jaw_half_finish-mach-bup.stp | FAIL 5 | ok 5 | [cmp_nist_edm__mt_jaw_half_finish-mach-bup_box.png](images/cmp_nist_edm__mt_jaw_half_finish-mach-bup_box.png) |
| `nist_edm__needle-nose-inch#box` | nist_edm/needle-nose-inch.stp | FAIL 5 | ok 5 | [cmp_nist_edm__needle-nose-inch_box.png](images/cmp_nist_edm__needle-nose-inch_box.png) |
| `nist_edm__screw_driver1#box` | nist_edm/screw_driver1.stp | FAIL 5 | ok 5 | [cmp_nist_edm__screw_driver1_box.png](images/cmp_nist_edm__screw_driver1_box.png) |
| `nist_edm__sh-r44356-000-u#box` | nist_edm/sh-r44356-000-u.stp | FAIL 5 | ok 5 | [cmp_nist_edm__sh-r44356-000-u_box.png](images/cmp_nist_edm__sh-r44356-000-u_box.png) |
| `nist_edm__sh-r44363-000-u-compressed#box` | nist_edm/sh-r44363-000-u-compressed.stp | FAIL 5 | ok 5 | [cmp_nist_edm__sh-r44363-000-u-compressed_box.png](images/cmp_nist_edm__sh-r44363-000-u-compressed_box.png) |
| `nist_edm__stock#box` | nist_edm/stock.stp | FAIL 5 | ok 5 | [cmp_nist_edm__stock_box.png](images/cmp_nist_edm__stock_box.png) |
| `occt_booltest__bottle#box` | occt_booltest/bottle.step | FAIL 5 | ok 5 | [cmp_occt_booltest__bottle_box.png](images/cmp_occt_booltest__bottle_box.png) |
| `occt_data__Bottom_from_brep#box` | occt_data/Bottom_from_brep.step | FAIL 5 | ok 5 | [cmp_occt_data__Bottom_from_brep_box.png](images/cmp_occt_data__Bottom_from_brep_box.png) |
| `occt_data__CrankArm_from_brep#box` | occt_data/CrankArm_from_brep.step | FAIL 5 | ok 5 | [cmp_occt_data__CrankArm_from_brep_box.png](images/cmp_occt_data__CrankArm_from_brep_box.png) |
| `occt_data__MODERN_MVCooker_1_from_brep#box` | occt_data/MODERN_MVCooker_1_from_brep.step | FAIL 5 | ok 5 | [cmp_occt_data__MODERN_MVCooker_1_from_brep_box.png](images/cmp_occt_data__MODERN_MVCooker_1_from_brep_box.png) |
| `occt_data__MODERN_Table_1_from_brep#box` | occt_data/MODERN_Table_1_from_brep.step | FAIL 5 | ok 5 | [cmp_occt_data__MODERN_Table_1_from_brep_box.png](images/cmp_occt_data__MODERN_Table_1_from_brep_box.png) |
| `occt_data__Pump_Nut_from_brep#box` | occt_data/Pump_Nut_from_brep.step | FAIL 5 | ok 5 | [cmp_occt_data__Pump_Nut_from_brep_box.png](images/cmp_occt_data__Pump_Nut_from_brep_box.png) |
| `occt_data__Pump_TopCover_from_brep#box` | occt_data/Pump_TopCover_from_brep.step | FAIL 5 | ok 5 | [cmp_occt_data__Pump_TopCover_from_brep_box.png](images/cmp_occt_data__Pump_TopCover_from_brep_box.png) |
| `occt_data__bottle_from_brep#box` | occt_data/bottle_from_brep.step | FAIL 5 | ok 5 | [cmp_occt_data__bottle_from_brep_box.png](images/cmp_occt_data__bottle_from_brep_box.png) |
| `occt_data__linkrods#box` | occt_data/linkrods.step | LOADFAIL 5 | ok 5 | [cmp_occt_data__linkrods_box.png](images/cmp_occt_data__linkrods_box.png) |
| `occt_data__screw#box` | occt_data/screw.step | LOADFAIL 5 | ok 5 | [cmp_occt_data__screw_box.png](images/cmp_occt_data__screw_box.png) |
| `pair#bolt_vs_clevis21` | two NIST parts overlapping at their placed positions | FAIL 5 | ok 5 | [cmp_pair_bolt_vs_clevis21.png](images/cmp_pair_bolt_vs_clevis21.png) |
| `pair#sample_round_vs_1` | two revisions of the same rounded part, mostly coincident faces | FAIL 5 | ok 5 | [cmp_pair_sample_round_vs_1.png](images/cmp_pair_sample_round_vs_1.png) |
| `pair#sample_round_vs_2` | two revisions of the same rounded part, mostly coincident faces | FAIL 5 | ok 5 | [cmp_pair_sample_round_vs_2.png](images/cmp_pair_sample_round_vs_2.png) |

