#!/bin/bash
# Helper script to set up NH stumpage data

echo "================================"
echo "NH Stumpage Data Setup"
echo "================================"
echo ""
echo "The NH DRA website uses bot protection that blocks automated downloads."
echo "You must manually download the PDF files."
echo ""
echo "STEP 1: Open this URL in your web browser:"
echo "https://www.revenue.nh.gov/taxes-glance/timber-tax/average-stumpage-value-information"
echo ""
echo "STEP 2: Download the available PDF reports (look for files like 'avg-stump-val-XX-XX-XX-XX.pdf')"
echo ""
echo "STEP 3: Save the downloaded PDFs to this directory:"
echo "/Users/mihiarc/landuse-model/forest-rents/data/raw/nh_dra/pdfs/"
echo ""
echo "STEP 4: After downloading PDFs, run the parser:"
echo "uv run python scripts/parse_nh_stumpage.py"
echo ""
echo "Current status:"
PDF_COUNT=$(ls -1 /Users/mihiarc/landuse-model/forest-rents/data/raw/nh_dra/pdfs/*.pdf 2>/dev/null | wc -l | tr -d ' ')
echo "PDFs in directory: $PDF_COUNT"
echo ""
if [ "$PDF_COUNT" -gt 0 ]; then
    echo "Found PDFs:"
    ls -1 /Users/mihiarc/landuse-model/forest-rents/data/raw/nh_dra/pdfs/*.pdf
    echo ""
    echo "Ready to parse! Run: uv run python scripts/parse_nh_stumpage.py"
else
    echo "No PDFs found yet. Please download them manually from the website above."
fi
echo "================================"
