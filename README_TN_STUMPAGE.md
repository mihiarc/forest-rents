# Tennessee Forest Stumpage Price Data Extraction

## Project Overview

This project extracts historical stumpage price data from the Tennessee Forest Products Bulletin archive (1977-2017). The data includes quarterly prices for various timber species and product types across Tennessee regions.

## Directory Structure

```
/Users/mihiarc/landuse-model/timber-prices/
├── data/raw/tn_forestry/
│   ├── *.pdf                        # Downloaded bulletin PDFs (to be added)
│   ├── tn_stumpage_SAMPLE.csv      # Sample output showing format
│   └── tn_stumpage_parsed.csv      # Final parsed data (generated)
├── src/
│   ├── download_tn_bulletins.py    # PDF download script
│   ├── parse_tn_bulletins.py       # PDF parsing script
│   └── test_parser_demo.py         # Demo showing expected output
└── docs/
    └── TN_BULLETIN_DOWNLOAD_GUIDE.md  # Download instructions
```

## Quick Start

### 1. Download PDFs

**Option A: Manual Download**
Visit the archive and download PDFs manually:
- https://www.tn.gov/agriculture/businesses/business-development/forest-products/tfpb.html

Save PDFs to: `/Users/mihiarc/landuse-model/timber-prices/data/raw/tn_forestry/`

**Option B: Automated Download** (if website is accessible)
```bash
uv run python src/download_tn_bulletins.py
```

### 2. Parse PDFs

Once PDFs are downloaded, extract stumpage price data:
```bash
uv run python src/parse_tn_bulletins.py
```

This will create: `/Users/mihiarc/landuse-model/timber-prices/data/raw/tn_forestry/tn_stumpage_parsed.csv`

### 3. View Sample Output

To see expected output format without downloading PDFs:
```bash
uv run python src/test_parser_demo.py
```

## Data Format

### Output CSV Columns

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `year` | int | Year of report | 2017 |
| `quarter` | int | Quarter (1-4) | 1 |
| `region` | str | Geographic region | statewide, east, west, middle |
| `species` | str | Timber species | Pine, White Oak, Yellow Poplar |
| `product_type` | str | Product category | sawtimber, pulpwood, chip-n-saw |
| `price_avg` | float | Average price | 285.50 |
| `price_low` | float | Low end of price range | 250.00 |
| `price_high` | float | High end of price range | 320.00 |
| `unit` | str | Price unit | MBF, ton, cord |

### Units Explained

- **MBF**: Thousand Board Feet (for sawtimber)
- **ton**: Short ton (2,000 lbs, typically for pulpwood)
- **cord**: Cord (128 cubic feet of stacked wood)

### Example Data

```csv
year,quarter,region,species,product_type,price_avg,price_low,price_high,unit
2017,1,statewide,Pine,sawtimber,285.5,250.0,320.0,MBF
2017,1,statewide,Pine,pulpwood,8.5,7.0,10.0,ton
2017,1,statewide,White Oak,sawtimber,425.0,350.0,500.0,MBF
2017,1,east,Pine,sawtimber,295.0,270.0,320.0,MBF
```

## Data Coverage

### Expected Coverage
- **Time Period**: 1977-2017 (41 years)
- **Frequency**: Quarterly (Q1, Q2, Q3, Q4)
- **Total Bulletins**: ~160 PDFs
- **Regions**: Statewide, East TN, Middle TN, West TN

### Species Typically Covered
- **Softwoods**: Pine (Loblolly, Shortleaf, Virginia)
- **Hardwoods**:
  - Oak (White Oak, Red Oak Group)
  - Yellow Poplar
  - Ash
  - Hickory
  - Mixed Hardwoods

### Product Types
- **Sawtimber**: Logs suitable for lumber production
- **Pulpwood**: Wood for paper/pulp manufacturing
- **Chip-n-Saw**: Small sawtimber/large pulpwood
- **Veneer**: High-quality logs for veneer production

## Technical Details

### Dependencies
```bash
# Installed with uv
requests        # HTTP downloads
beautifulsoup4  # HTML parsing
pdfplumber      # PDF text/table extraction
pandas          # Data manipulation
rich            # Terminal output
```

### Parser Features

The `parse_tn_bulletins.py` script includes:

1. **Automatic date extraction** from filenames or PDF content
2. **Table detection** using keyword matching
3. **Flexible parsing** handling multiple table formats
4. **Species extraction** with product type inference
5. **Regional data** extraction when available
6. **Price normalization** handling various formats
7. **Unit detection** (MBF, ton, cord)

### Parser Robustness

The parser handles:
- Multiple table formats across years
- Different naming conventions
- Missing or incomplete data
- Regional vs. statewide data
- Various unit representations

## Troubleshooting

### Website Connection Issues

If `download_tn_bulletins.py` fails with connection errors:
1. Try manual download via browser
2. Check internet connection
3. Contact TN Department of Agriculture for direct data access
4. Consider alternative sources (see guide)

### No Tables Found

If parser reports no tables found:
1. Verify PDFs are valid (not scanned images)
2. Check console warnings for specific issues
3. Review PDF manually to understand format
4. May need to adjust parser table detection logic

### Unexpected Values

If parsed prices seem unreasonable:
1. Check units ($/MBF vs $/ton are very different)
2. Verify year/quarter assignment is correct
3. Compare with known market data
4. Review specific PDF manually

## Data Quality Checks

After parsing, verify:

```python
import pandas as pd

df = pd.read_csv('data/raw/tn_forestry/tn_stumpage_parsed.csv')

# Check coverage
print(f"Years: {df['year'].min()} - {df['year'].max()}")
print(f"Total records: {len(df)}")
print(f"Records per year: {len(df) / (df['year'].max() - df['year'].min() + 1):.1f}")

# Check for gaps
years_quarters = df.groupby(['year', 'quarter']).size()
print(f"Quarters covered: {len(years_quarters)}")
print(f"Expected: {(df['year'].max() - df['year'].min() + 1) * 4}")

# Price ranges
print("\nPrice ranges by product type:")
print(df.groupby(['product_type', 'unit'])['price_avg'].describe())
```

## Alternative Data Sources

If PDFs are unavailable or incomplete:

1. **TimberMart-South** (https://timbermart-south.com/)
   - Commercial service with historical data
   - Contact: tmart@timbermart-south.com

2. **USDA Forest Service**
   - Contact: brian.doherty@usda.gov
   - May have compiled datasets

3. **University of Tennessee Extension**
   - May have archived data or alternative sources

## Next Steps After Extraction

1. **Data Validation**
   - Check for outliers
   - Verify units are consistent
   - Compare with external sources

2. **Analysis**
   - Time series analysis of price trends
   - Regional price comparisons
   - Species-specific trends
   - Inflation adjustment

3. **Integration**
   - Merge with land use model
   - Calculate forest rents
   - Estimate opportunity costs

## Support and Resources

- **Tennessee Dept of Agriculture**: https://www.tn.gov/agriculture/forests.html
- **USDA Forest Service SRS**: https://www.srs.fs.usda.gov/econ/
- **TimberMart-South**: https://timbermart-south.com/

## License and Citation

If using this data in publications, cite:
- Tennessee Department of Agriculture, Division of Forestry. Tennessee Forest Products Bulletin (1977-2017). Quarterly reports.

## Contact

For questions about the parser or data extraction, contact the project maintainer.
