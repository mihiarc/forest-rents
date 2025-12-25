# NH Stumpage Data - Manual Download Guide

## Problem

The NH Department of Revenue Administration website uses Akamai bot protection that blocks automated downloads. All HTTP requests (requests, httpx, urllib, curl, wget) return `403 Forbidden` errors.

## Solution: Manual Download + Automated Parsing

### Step 1: Open Download Page

Run this command to open the download page in your browser:

```bash
uv run python scripts/open_nh_download_page.py
```

Or manually visit:
https://www.revenue.nh.gov/taxes-glance/timber-tax/average-stumpage-value-information

### Step 2: Download PDFs

On the page, you'll see links to PDF reports. Download the ones you need:

**Available Reports (as of December 2025):**
- October 2024 - March 2025: `avg-stump-val-10-24-03-25.pdf`
- April 2024 - September 2024: `avg-stump-val-04-24-09-24.pdf`
- October 2023 - March 2024: `avg-stump-val-10-23-03-24.pdf`
- April 2023 - September 2023: `avg-stump-val-04-23-09-23.pdf`
- And earlier periods back to 2021...

### Step 3: Save PDFs

Save all downloaded PDFs to:
```
/Users/mihiarc/landuse-model/timber-prices/data/raw/nh_dra/pdfs/
```

The directory has been created and is ready for your files.

### Step 4: Run the Parser

Once you have PDFs in the directory, run:

```bash
uv run python scripts/parse_nh_stumpage.py
```

This will:
1. Find all PDFs in the `pdfs/` directory
2. Parse each PDF using pdfplumber
3. Extract stumpage prices by region, species, and product type
4. Save to `data/raw/nh_dra/nh_stumpage_parsed.csv`
5. Display summary statistics and sample data

### Step 5: View Results

The parser creates a CSV file with columns:
- `year`: Primary year (2021-2025)
- `period`: Spring (April-Sept) or Fall (Oct-March)
- `period_dates`: Full coverage period
- `region`: Northern, Central, or Southern NH
- `species`: Tree species (White Pine, Red Oak, etc.)
- `product_type`: Sawlogs, Pulpwood, etc.
- `price_low`: Low end of price range ($/unit)
- `price_high`: High end of price range ($/unit)
- `unit`: MBF (thousand board feet), Cord, or Ton

## Quick Start Commands

```bash
# 1. Open browser to download page
uv run python scripts/open_nh_download_page.py

# 2. [Manually download PDFs and save to data/raw/nh_dra/pdfs/]

# 3. Check status
bash scripts/setup_nh_data.sh

# 4. Parse the PDFs
uv run python scripts/parse_nh_stumpage.py

# 5. View the results
cat data/raw/nh_dra/nh_stumpage_parsed.csv | head -20
```

## Data Usage

The parsed CSV can be used for:
- Forest economics analysis
- Timber valuation studies
- Regional price comparisons
- Time series analysis of stumpage values
- Integration with other forest inventory data

## Troubleshooting

**Q: Why can't we automate the download?**
A: The NH DRA website uses Akamai EdgeSuite bot protection. Even with browser headers, User-Agent spoofing, and SSL handling, all automated requests receive 403 Forbidden responses.

**Q: Can I use wget or curl?**
A: No, these will also be blocked by the same Akamai protection.

**Q: How often should I update?**
A: NH DRA publishes new reports twice per year (spring and fall). Check the website semi-annually for updates.

**Q: What if the parser fails?**
A: The parser is designed to handle various table structures in the PDFs. If it fails, please check:
- PDF is not corrupted
- PDF is from the NH DRA stumpage value series
- File is saved in the correct directory

## Technical Details

### Parser Features
- Automatic period extraction from filenames
- Flexible table structure detection
- Region identification from PDF text
- Price cleaning and validation
- Rich terminal output with progress bars
- Comprehensive error handling

### Dependencies
- pandas: Data manipulation
- pdfplumber: PDF text and table extraction
- rich: Terminal formatting
- requests/httpx: (Not used due to bot protection, but available)

## Alternative Data Sources

If you need automated access to timber pricing data, consider:
- USDA Forest Service Timber Product Output reports
- State-level forestry databases with API access
- Commercial timber market data services
- TimberMart-South (southern US)
- Oregon Department of Forestry stumpage reports
