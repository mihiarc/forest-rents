# NH Stumpage Data Project Summary

## Overview

This project downloads and parses New Hampshire Department of Revenue Administration (DRA) stumpage price data from semi-annual PDF reports.

**Challenge**: The NH DRA website uses Akamai bot protection that blocks all automated downloads.

**Solution**: Manual download workflow + automated PDF parsing.

## What Was Created

### 1. Data Directory Structure

```
/Users/mihiarc/landuse-model/timber-prices/data/raw/nh_dra/
├── pdfs/                     # Directory for manually downloaded PDFs
├── README.md                 # Data source documentation
└── nh_stumpage_parsed.csv    # Output file (created after parsing)
```

### 2. Python Scripts

#### Main Workflow Script (Recommended)
- **`scripts/nh_stumpage_workflow.py`** - Interactive workflow guide
  - Shows current status (PDFs downloaded, directories created)
  - Provides step-by-step download instructions
  - Lists recommended PDFs to download (2021-2025)
  - Option to open download page in browser
  - Beautiful terminal UI with rich formatting

#### Parser (Core Functionality)
- **`scripts/parse_nh_stumpage.py`** - PDF parser
  - Finds all PDFs in the pdfs/ directory
  - Extracts period info from filenames
  - Parses tables using pdfplumber
  - Identifies regions (Northern, Central, Southern)
  - Cleans and validates price data
  - Outputs to CSV with standardized format
  - Displays summary statistics and sample data

#### Helper Scripts
- **`scripts/open_nh_download_page.py`** - Opens download page in browser
- **`scripts/setup_nh_data.sh`** - Bash script to check status

#### Download Attempts (For Reference)
- **`scripts/download_nh_stumpage.py`** - requests library (blocked)
- **`scripts/download_nh_pdfs_httpx.py`** - httpx library (blocked)
- **`scripts/download_nh_with_urllib.py`** - urllib library (blocked)

All download attempts were blocked by Akamai bot protection (403 Forbidden).

### 3. Documentation

- **`MANUAL_DOWNLOAD_GUIDE.md`** - Comprehensive guide covering:
  - Why automated download fails
  - Step-by-step manual download instructions
  - Parser usage
  - Output format description
  - Quick start commands
  - Troubleshooting
  - Alternative data sources

- **`data/raw/nh_dra/README.md`** - Data source documentation:
  - Source URL and description
  - Download instructions
  - Data format specification
  - Update frequency
  - Common units (MBF, Cord, Ton)

## How to Use

### Quick Start

```bash
# 1. Run the interactive workflow
uv run python scripts/nh_stumpage_workflow.py

# 2. Follow instructions to download PDFs manually

# 3. Run parser (after PDFs are downloaded)
uv run python scripts/parse_nh_stumpage.py
```

### Expected Workflow

1. **Setup**: Run workflow script to see what's needed
2. **Download**: Manually download PDFs from NH DRA website
3. **Parse**: Run parser to extract data from PDFs
4. **Analyze**: Use the CSV output for analysis

## Data Source Information

**Website**: https://www.revenue.nh.gov/taxes-glance/timber-tax/average-stumpage-value-information

**Update Schedule**: Semi-annual
- Spring: April - September (published in spring)
- Fall: October - March (published in fall)

**Geographic Coverage**: Three regions of New Hampshire
- Northern NH
- Central NH
- Southern NH

**Data Content**:
- Tree species (White Pine, Red Oak, Hemlock, etc.)
- Product types (Sawlogs, Pulpwood, etc.)
- Price ranges (LOW and HIGH values)
- Units (MBF, Cord, Ton)

## Output Format

The parser creates a CSV file with these columns:

| Column        | Description                           | Example        |
|---------------|---------------------------------------|----------------|
| year          | Primary year (start year)             | 2024           |
| period        | Season (Spring or Fall)               | Fall           |
| period_dates  | Full period coverage                  | 10/2024-03/2025|
| region        | NH region                             | Northern       |
| species       | Tree species                          | White Pine     |
| product_type  | Timber product type                   | Sawlogs        |
| price_low     | Low price ($/unit)                    | 250.00         |
| price_high    | High price ($/unit)                   | 350.00         |
| unit          | Measurement unit                      | MBF            |

## Technical Details

### Dependencies Used
- **pandas**: Data manipulation and CSV export
- **pdfplumber**: PDF text and table extraction
- **rich**: Terminal formatting and progress bars
- **requests/httpx**: HTTP requests (blocked by server)
- **pathlib**: File path handling
- **re**: Pattern matching for filename parsing

### Parser Features
- Flexible table structure detection
- Automatic period extraction from filenames
- Region identification from PDF content
- Price data cleaning and validation
- Comprehensive error handling
- Rich progress indicators
- Summary statistics display

## Known Issues & Limitations

1. **Automated Download Not Possible**: Akamai bot protection blocks all automated HTTP requests
2. **Manual Download Required**: User must download PDFs through a web browser
3. **Table Structure Variations**: PDFs may have varying table layouts (parser handles most cases)
4. **Region Detection**: Relies on text presence in PDF (may need manual verification)

## Files Created

```
timber-prices/
├── MANUAL_DOWNLOAD_GUIDE.md
├── NH_STUMPAGE_PROJECT_SUMMARY.md (this file)
├── data/raw/nh_dra/
│   ├── README.md
│   └── pdfs/
├── scripts/
│   ├── nh_stumpage_workflow.py       ⭐ Start here
│   ├── parse_nh_stumpage.py          ⭐ Main parser
│   ├── open_nh_download_page.py
│   ├── setup_nh_data.sh
│   ├── download_nh_stumpage.py       (reference only - blocked)
│   ├── download_nh_pdfs_httpx.py     (reference only - blocked)
│   └── download_nh_with_urllib.py    (reference only - blocked)
```

## Recommended PDFs to Download

For complete coverage from 2021-2025, download these 8 PDFs:

1. `avg-stump-val-10-24-03-25.pdf` - Oct 2024 - Mar 2025
2. `avg-stump-val-04-24-09-24.pdf` - Apr 2024 - Sep 2024
3. `avg-stump-val-10-23-03-24.pdf` - Oct 2023 - Mar 2024
4. `avg-stump-val-04-23-09-23.pdf` - Apr 2023 - Sep 2023
5. `avg-stump-val-10-22-03-23.pdf` - Oct 2022 - Mar 2023
6. `avg-stump-val-04-22-09-22.pdf` - Apr 2022 - Sep 2022
7. `avg-stump-val-10-21-03-22.pdf` - Oct 2021 - Mar 2022
8. `avg-stump-val-04-21-09-21.pdf` - Apr 2021 - Sep 2021

## Next Steps

After downloading and parsing the data, you can:

1. **Analyze trends**: Compare prices across years and regions
2. **Integrate with other data**: Combine with forest inventory data
3. **Visualize**: Create charts showing price trends
4. **Model**: Use for forest economics modeling
5. **Export**: Share parsed CSV with collaborators

## Support

For questions or issues:
- See `MANUAL_DOWNLOAD_GUIDE.md` for detailed instructions
- Check `data/raw/nh_dra/README.md` for data source info
- Run `scripts/nh_stumpage_workflow.py` for interactive help

---

**Created**: December 25, 2025
**Data Source**: NH Department of Revenue Administration
**Status**: Ready for manual download + parsing
