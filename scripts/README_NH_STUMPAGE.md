# NH Stumpage Data Scripts

This directory contains scripts for downloading and parsing NH DRA stumpage price data.

## Quick Start

```bash
# Run the interactive workflow (RECOMMENDED)
uv run python nh_stumpage_workflow.py
```

This will guide you through the entire process.

## Available Scripts

### 1. nh_stumpage_workflow.py ⭐ START HERE
**Purpose**: Interactive workflow guide with status checking

**What it does**:
- Checks if data directory exists
- Counts PDFs already downloaded
- Shows step-by-step download instructions
- Lists recommended PDFs (2021-2025)
- Optionally opens download page in browser
- Explains expected output format

**Usage**:
```bash
uv run python nh_stumpage_workflow.py
```

### 2. parse_nh_stumpage.py ⭐ MAIN PARSER
**Purpose**: Parse downloaded PDFs into CSV format

**What it does**:
- Scans `data/raw/nh_dra/pdfs/` for PDF files
- Extracts period info from filenames
- Parses tables from each PDF
- Identifies regions (Northern, Central, Southern)
- Cleans price data
- Creates CSV: `data/raw/nh_dra/nh_stumpage_parsed.csv`
- Shows summary statistics

**Usage**:
```bash
uv run python parse_nh_stumpage.py
```

**Requirements**:
- PDFs must be in `data/raw/nh_dra/pdfs/`
- PDFs should follow naming pattern: `avg-stump-val-MM-YY-MM-YY.pdf`

**Output CSV columns**:
- year, period, period_dates, region, species, product_type, price_low, price_high, unit

### 3. open_nh_download_page.py
**Purpose**: Open the NH DRA download page in your browser

**Usage**:
```bash
uv run python open_nh_download_page.py
```

Opens: https://www.revenue.nh.gov/taxes-glance/timber-tax/average-stumpage-value-information

### 4. setup_nh_data.sh
**Purpose**: Bash script to check download status

**Usage**:
```bash
bash setup_nh_data.sh
```

Shows:
- Current PDF count
- List of downloaded PDFs
- Next steps

## Download Scripts (Reference Only - Blocked by Server)

These scripts attempted automated download but are blocked by Akamai bot protection:

### download_nh_stumpage.py
Attempted using `requests` library - **Blocked (403 Forbidden)**

### download_nh_pdfs_httpx.py
Attempted using `httpx` with HTTP/2 - **Blocked (403 Forbidden)**

### download_nh_with_urllib.py
Attempted using `urllib` with custom SSL - **Blocked (403 Forbidden)**

**Conclusion**: Automated download is not possible. PDFs must be downloaded manually through a web browser.

## Typical Workflow

1. **Check Status**
   ```bash
   uv run python nh_stumpage_workflow.py
   ```

2. **Download PDFs Manually**
   - Visit: https://www.revenue.nh.gov/taxes-glance/timber-tax/average-stumpage-value-information
   - Download desired PDF reports
   - Save to: `data/raw/nh_dra/pdfs/`

3. **Verify Downloads**
   ```bash
   bash setup_nh_data.sh
   ```

4. **Parse PDFs**
   ```bash
   uv run python parse_nh_stumpage.py
   ```

5. **Check Output**
   ```bash
   cat ../data/raw/nh_dra/nh_stumpage_parsed.csv | head -20
   ```

## PDFs to Download (2021-2025)

Download these 8 files for complete coverage:

| Period | Filename |
|--------|----------|
| Oct 2024 - Mar 2025 | avg-stump-val-10-24-03-25.pdf |
| Apr 2024 - Sep 2024 | avg-stump-val-04-24-09-24.pdf |
| Oct 2023 - Mar 2024 | avg-stump-val-10-23-03-24.pdf |
| Apr 2023 - Sep 2023 | avg-stump-val-04-23-09-23.pdf |
| Oct 2022 - Mar 2023 | avg-stump-val-10-22-03-23.pdf |
| Apr 2022 - Sep 2022 | avg-stump-val-04-22-09-22.pdf |
| Oct 2021 - Mar 2022 | avg-stump-val-10-21-03-22.pdf |
| Apr 2021 - Sep 2021 | avg-stump-val-04-21-09-21.pdf |

## Dependencies

These scripts require:
- Python 3.11+
- pandas
- pdfplumber
- rich
- requests (for reference scripts)
- httpx (for reference scripts)

All dependencies are already in `pyproject.toml`.

## Troubleshooting

**Q: Parser finds no PDFs**
- Check PDFs are in `data/raw/nh_dra/pdfs/`
- Ensure PDFs have `.pdf` extension
- Run `bash setup_nh_data.sh` to verify

**Q: Parser extracts no records**
- Verify PDFs are from NH DRA (not corrupted)
- Check PDF contains tables with price data
- PDF naming should match pattern: `avg-stump-val-MM-YY-MM-YY.pdf`

**Q: Can't download PDFs automatically**
- This is expected - NH DRA uses Akamai bot protection
- Must download manually through web browser
- See `MANUAL_DOWNLOAD_GUIDE.md` for details

## Additional Documentation

- **`../MANUAL_DOWNLOAD_GUIDE.md`**: Complete guide with troubleshooting
- **`../NH_STUMPAGE_PROJECT_SUMMARY.md`**: Project overview
- **`../data/raw/nh_dra/README.md`**: Data source documentation

## Example Output

After parsing, you'll see:

```
Summary Statistics
Total records: 156
Year range: 2024 - 2024
Periods: Fall
Regions: Central, Northern, Southern
Unique species: 15

Sample Data (first 10 records):
┌──────┬────────┬────────┬──────────────┬──────────┬──────┬──────┬──────┐
│ Year │ Period │ Region │ Species      │ Product  │ Low  │ High │ Unit │
├──────┼────────┼────────┼──────────────┼──────────┼──────┼──────┼──────┤
│ 2024 │ Fall   │ Northern│ White Pine   │ Sawlogs  │$250  │$350  │ MBF  │
│ ...  │ ...    │ ...    │ ...          │ ...      │ ...  │ ...  │ ...  │
└──────┴────────┴────────┴──────────────┴──────────┴──────┴──────┴──────┘
```

---

**For help**: Run `uv run python nh_stumpage_workflow.py`
