#!/usr/bin/env bash
# Re-import the demo sheets from their source PDFs into the viewer's assets tree.
#   ./import_drawings.sh            every sheet in SHEETS of session_rust/src/bin/pdf_import.rs
#
# Everything the viewer can load lives under session_viewer/assets - PDFs in, .pb and extracted
# font programs out. All Rust: session_rust's pdf_import bin (--features pdf) reads the PDF with MuPDF
# (the engine PyMuPDF wraps),
# triangulates fills with earcut in parallel and writes the .pb. ~2s per sheet.
set -u
RUST=../session_rust

# mupdf-sys needs clang's builtin headers; this box has libclang but not its resource dir, so
# point bindgen at gcc's instead of requiring a system package.
export BINDGEN_EXTRA_CLANG_ARGS="${BINDGEN_EXTRA_CLANG_ARGS:--I/usr/lib/gcc/x86_64-linux-gnu/15/include}"
cargo run --release --features pdf --bin pdf_import --manifest-path "$RUST/Cargo.toml" -q
