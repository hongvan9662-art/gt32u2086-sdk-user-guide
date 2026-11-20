#!/usr/bin/env bash
# Build the GT32U2086 SDK User Guide website + PDF
set -e
cd "$(dirname "$0")"
rm -rf build/html
mkdir -p build
doxygen Doxyfile
python3 tools/postprocess.py build/html
node tools/make_pdf.js
echo "Done: build/html/index.html and build/html/GT32U2086_SDK_User_Guide.pdf"
