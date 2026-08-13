#!/usr/bin/env bash
# Re-import the demo sheets from their source PDFs into the viewer's assets tree.
#   ./import_drawings.sh            all of them
#   ./import_drawings.sh draw_pf_he only that one
#
# Everything the viewer can load lives under session_viewer/assets - PDFs in, .pb and extracted
# font programs out. All Rust: session_rust's pdf_import bin (--features pdf) reads the PDF with MuPDF
# (the engine PyMuPDF wraps),
# triangulates fills with earcut in parallel and writes the .pb. ~2s per sheet.
set -u
A=../session_viewer/assets
RUST=../session_rust

declare -A SHEET=(
  [30700_querschnitt_gg]="$A/pdf/Projekt-I/30700 Querschnitt G-G.pdf"
  [draw_pb_haus25]="$A/pdf/Projekt-B/Ansicht Haus 25 TH Schnitt a-a b-b.pdf"
  [draw_pc_gru_og2]="$A/pdf/Projekt-C/GRU_02 1149whz_ARC_AP_GRU_OG2_2.Obergeschoss.pdf"
  [draw_pd_treppenhaus04]="$A/pdf/Projekt-D/KAB_41_ARC_B2_MG_DE_5002_B2 Treppenhaus 04_F.pdf"
  [draw_pe_schalungsbild]="$A/pdf/Projekt-E/2508_W-700.1 Schalungsbild TRH West.pdf"
  [draw_pf_he]="$A/pdf/Projekt-F/HE.pdf"
  [draw_pi_laengsschnitt]="$A/pdf/Projekt-I/30300 Längsschnitt C-C.pdf"
  [draw_pj_grundriss_og2]="$A/pdf/Projekt-J/1606.51.4054 Grundriss 2. Obergeschoss.pdf"
  [draw_pj_treppenhaus_a]="$A/pdf/Projekt-J/1606.41.3201 Treppenhaus A.pdf"
)

# mupdf-sys needs clang's builtin headers; this box has libclang but not its resource dir, so
# point bindgen at gcc's instead of requiring a system package.
export BINDGEN_EXTRA_CLANG_ARGS="${BINDGEN_EXTRA_CLANG_ARGS:--I/usr/lib/gcc/x86_64-linux-gnu/15/include}"
cargo build --release --features pdf --bin pdf_import --manifest-path "$RUST/Cargo.toml" -q || exit 1
BIN="$RUST/target/release/pdf_import"

mkdir -p "$A/pb" "$A/fonts"
for stem in "${@:-${!SHEET[@]}}"; do
  pdf="${SHEET[$stem]}"
  [ -f "$pdf" ] || { echo "MISSING PDF: $pdf"; continue; }
  echo "=== $stem"
  "$BIN" "$pdf" "$A/pb/$stem" 0 || continue
done
