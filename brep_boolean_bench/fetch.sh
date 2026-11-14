#!/usr/bin/env bash
# Re-download every STEP file of brep_boolean_bench from its source, pinned to the revisions fetched on 2026-11-14.
#   bash fetch.sh [target_dir]   (default: the directory of this script)
# Needs curl, python3; the occt_data/*_from_brep.step conversions and mcneel_rebuilt/ need the cadquery-ocp wheel
# (pip install cadquery-ocp==8.0.1.1.0) and are skipped when `python3 -c "import OCP"` fails.
set -euo pipefail
OUT=${1:-$(cd "$(dirname "$0")" && pwd)}
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
get() { mkdir -p "$(dirname "$2")"; curl -fsSL --retry 3 -o "$2" "$1"; }

# NIST Engineering Design Model Repository (public domain, NIST terms in its LICENSE.md)
NIST=https://raw.githubusercontent.com/usnistgov/engineering-design-models/dc4ed1c352bfa7fa0976c6abc6074a7a40aa1d5a
while read -r path name; do get "$NIST/$path" "$OUT/nist_edm/$name"; done <<'EOF'
models/ICEM-CDC/Fixture_Models/RestButton1/RestButton1.hh.sat.stp RestButton1.stp
models/ICEM-CDC/Fixture_Models/KnurledKnob10/KnurledKnob10.hh.sat.stp KnurledKnob10.stp
models/Sandia/Randy_Wilson/discriminator/sh-r44356-000-u/sh-r44356-000-u.hh.sat.stp sh-r44356-000-u.stp
models/Sandia/Randy_Wilson/discriminator/sh-r44363-000-u-compressed/sh-r44363-000-u-compressed.hh.sat.stp sh-r44363-000-u-compressed.stp
models/ICEM-CDC/Fixture_Models/DoubleCam1/DoubleCam1.hh.sat.stp DoubleCam1.stp
models/SDRC_I-DEAS/NC_DRIVE/NC_DRIVE.stp NC_DRIVE.stp
models/CMU/Tools/needle-nose-inch.hh.sat.stp needle-nose-inch.stp
models/PTC/V18/asmdes18/parts/bolt.prt.hh.sat.stp bolt.stp
models/VDS/chamber/chamber.stp chamber.stp
models/NIST/Manfred_Osti/spectrometer/bellow/bellow.prt.hh.sat.stp bellow.stp
models/Parasolid/NIST/Pete_Brown/flange/flange.step.hh.sat.stp flange.stp
models/VDS/fork/fork.stp fork.stp
models/CMU/Tools/screw_driver1.hh.sat.stp screw_driver1.stp
models/STEP/STI/moon_buggy/moon_buggy.hh.sat.stp moon_buggy.stp
models/Parasolid/NIST/Pete_Brown/260012/260012.step.hh.sat.stp 260012.stp
models/NIST/Manfred_Osti/spectrometer/main_block/main_block.hh.sat.stp main_block.stp
models/VDS/mt_jaw_half_finish-mach-bup/mt_jaw_half_finish-mach-bup.stp mt_jaw_half_finish-mach-bup.stp
models/Parasolid/NIST/Pete_Brown/Torpedo_Motor/stock/stock.hh.sat.stp stock.stp
models/STEP/STI/interactingPockets/interactingPockets.hh.sat.stp interactingPockets.stp
models/STEP/STI/clevis21/clevis21.hh.sat.stp clevis21.stp
models/UMD/swivel1-Part/swivel1-Part.step swivel1-Part.step
models/Parasolid/NIST/Bill_Regli/anc101_a/anc101_a.hh.sat.stp anc101_a.stp
models/PTC/Legos/stepmodels/gear_40.stp gear_40.stp
EOF

# Hugging Face Silly98/BrepMFR (dataset card: apache-2.0)
HF=https://huggingface.co/datasets/Silly98/BrepMFR/resolve/a32f70fd92513bf4b6514d54ed68a851c2c25b3c
for f in sample_round.stp sample_round_1.stp sample_round_2.stp 16P-03303.step 0m-3623639.stp 107050503-m8u-8700-a267.stp; do
    get "$HF/$f" "$OUT/hf_brepmfr/$f"
done
get "$HF/stp.zip" "$TMP/stp.zip"
mkdir -p "$TMP/stp" && python3 -I -m zipfile -e "$TMP/stp.zip" "$TMP/stp"
for f in "$TMP"/stp/stp/*.stp; do
    n=$(basename "$f" | sed 's/^.*_\([a-z0-9]*\)\.stp$/\1/'); cp "$f" "$OUT/hf_brepmfr/zip_$n.stp"
done

# Hugging Face jhlee11/BRepGround (CC BY 4.0, attribution in MANIFEST.md): ten solids of one test shard
get https://huggingface.co/datasets/jhlee11/BRepGround/resolve/3b963b0bac7fbdd54785a09f7f32405652c8e76a/assets/test-00001-of-00002.zip "$TMP/bg.zip"
mkdir -p "$TMP/bg" "$OUT/hf_brepground"
python3 -I -m zipfile -e "$TMP/bg.zip" "$TMP/bg"
for id in 00019536_chamfer_10 00171214_fillet_11 00275424_fillet_17 00089757_fillet_16 00170968_fillet_10 \
          00290572_chamfer_12 00015160_chamfer_12 00161395_chamfer_16 00071814_fillet_15 00042148_fillet_11; do
    cp "$(find "$TMP/bg" -name "$id.step" | head -1)" "$OUT/hf_brepground/"
done

# Hugging Face ADSKAILab/Zero-To-CAD-1m (apache-2.0): ten rows of the test split through the datasets-server rows API
curl -fsSL -o "$TMP/rows.json" "https://datasets-server.huggingface.co/rows?dataset=ADSKAILab/Zero-To-CAD-1m&config=default&split=test&offset=0&length=100"
mkdir -p "$OUT/hf_zero_to_cad"
python3 -I - "$TMP/rows.json" "$OUT/hf_zero_to_cad" <<'EOF'
import json, base64, sys
keep = {'4b3aaa7b-f278-fc6a-8f9f-28fd4893be76', '56155734-8313-cde8-e96a-dbb3bbe3ba2f', '45278456-3334-0c11-81a7-458fce65d6d7',
        '13e02b4d-d613-422b-6a17-390f6402693a', '916572bc-ac4f-03d6-fc3d-1670590c4ce4', '5c6512ae-9182-fc5e-05b1-b23c3735d060',
        '89ded05a-e2be-350b-db33-e42eb475ce39', '8bccb9ee-085e-5ce4-75ab-15c7ee2cab24', '3bbf8b2b-5a16-b6b4-0c60-4df743e5e0bc',
        '3692c35e-1985-41b6-b45d-edc922a59854'}
for r in json.load(open(sys.argv[1]))['rows']:
    row = r['row']
    if row['uuid'] in keep:
        open('%s/%s.step' % (sys.argv[2], row['uuid']), 'wb').write(base64.b64decode(row['step_file']))
        open('%s/%s.cadquery.py' % (sys.argv[2], row['uuid']), 'wb').write(base64.b64decode(row['cadquery_file']))
EOF

# Open CASCADE sample data (LGPL-2.1 with the OCCT exception), repository data/step and data/occ
OCCT=https://raw.githubusercontent.com/Open-Cascade-SAS/OCCT/4dbfdcc448c0b3e565488afcd626c84483172db9
get "$OCCT/data/step/screw.step" "$OUT/occt_data/screw.step"
get "$OCCT/data/step/linkrods.step" "$OUT/occt_data/linkrods.step"
if python3 -c "import OCP" 2>/dev/null; then
    for n in Pump_Nut Pump_TopCover CrankArm Bottom bottle MODERN_MVCooker_1 MODERN_Table_1; do
        get "$OCCT/data/occ/$n.brep" "$TMP/$n.brep"
        python3 "$(dirname "$0")/tools/brep2step.py" "$TMP/$n.brep" "$OUT/occt_data/${n}_from_brep.step"
    done
    python3 "$(dirname "$0")/tools/gen_forum.py" "$OUT/mcneel_rebuilt"
fi

# GitHub: build123d (Apache-2.0) and FreeCAD (LGPL-2.1+) test data
get https://raw.githubusercontent.com/gumyr/build123d/42ea4f7dcfc3d4aa6ee81b88e558197576ff6273/docs/topology_selection/examples/nema-17-bracket.step "$OUT/github_misc/nema-17-bracket.step"
get https://raw.githubusercontent.com/FreeCAD/FreeCAD/8280c2e41ab06f138fc35da83ab1b1fb9723714e/data/tests/Step/as1-ac-214.stp "$OUT/github_misc/as1-ac-214.stp"

# kaige/occt-booltest corpus index (corpus data CC-BY-4.0 per its README)
get https://raw.githubusercontent.com/kaige/occt-booltest/bb9b85a52dcf0e6ff421390371b27b741bb9b5fe/corpus-index/bottle.step "$OUT/occt_booltest/bottle.step"
echo "fetched into $OUT"
