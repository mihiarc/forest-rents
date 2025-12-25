# Tennessee Forest Products Bulletin Download Guide

## Overview
The Tennessee Forest Products Bulletin archive (1977-2017) contains quarterly reports with stumpage price data. Due to connection issues with the TN.gov website, this guide provides alternative methods to obtain the PDFs.

## Official Sources

### Primary Source
**Tennessee Department of Agriculture**
- URL: https://www.tn.gov/agriculture/businesses/business-development/forest-products/tfpb.html
- Archive: Quarterly bulletins from 1977-2017
- Status: No longer in production (ended 2017)

### Alternative Source
**USDA Forest Service Southern Research Station**
- URL: https://www.srs.fs.usda.gov/econ/timberprices/data.php?location=TN
- References the TN.gov archive

## Download Methods

### Method 1: Manual Browser Download
1. Visit: https://www.tn.gov/agriculture/businesses/business-development/forest-products/tfpb.html
2. Scroll to the archive section
3. Download individual PDFs (organized by year and quarter)
4. Save to: `/Users/mihiarc/landuse-model/timber-prices/data/raw/tn_forestry/`

### Method 2: Contact TN Department of Agriculture
If the website is inaccessible:
- **Contact**: Tennessee Department of Agriculture, Division of Forestry
- **Request**: Historical Tennessee Forest Products Bulletin PDFs (1977-2017)
- **Format**: Specify you need them in PDF format for data extraction

### Method 3: Alternative Data Sources
If PDFs are unavailable, consider these alternatives:

1. **TimberMart-South**
   - URL: https://timbermart-south.com/resources/state-stumpage-prices/tennessee/
   - Quarterly stumpage price data for Tennessee
   - Historical data available (paid service)
   - Contact: tmart@timbermart-south.com or 706-247-7660

2. **USDA Forest Service Research**
   - URL: https://www.srs.fs.usda.gov/econ/
   - Contact: brian.doherty@usda.gov
   - May have compiled data or alternative access methods

## Expected PDF File Naming Conventions

Based on typical naming patterns, PDFs may be named as:
- `TFPB_YYYY_QN.pdf` (e.g., TFPB_2017_Q1.pdf)
- `tfpb_YYYY_qN.pdf` (e.g., tfpb_2017_q1.pdf)
- `Tennessee_Forest_Products_Bulletin_YYYY_QN.pdf`

Where:
- `YYYY` = Year (1977-2017)
- `N` = Quarter (1-4)

## Processing Pipeline

Once PDFs are downloaded to `/Users/mihiarc/landuse-model/timber-prices/data/raw/tn_forestry/`:

1. Run the parser:
   ```bash
   uv run python src/parse_tn_bulletins.py
   ```

2. Output will be saved to:
   ```
   /Users/mihiarc/landuse-model/timber-prices/data/raw/tn_forestry/tn_stumpage_parsed.csv
   ```

3. Expected CSV columns:
   - year
   - quarter
   - region
   - species
   - product_type
   - price_avg
   - price_low
   - price_high
   - unit

## Data Coverage

- **Time Period**: 1977-2017 (41 years)
- **Frequency**: Quarterly (Q1-Q4)
- **Total Expected Bulletins**: ~160 PDFs
- **Product Types**: Sawtimber, Pulpwood, Chip-n-Saw, Veneer
- **Species**: Pine, Oak, Yellow Poplar, Hardwoods, etc.
- **Regions**: May include East TN, Middle TN, West TN, or statewide averages

## Troubleshooting

### Website Connection Issues
The TN.gov website may have SSL/connection issues. Try:
- Different browser
- Different network connection
- Contact TN Dept of Agriculture directly
- Use alternative data sources listed above

### PDF Format Variations
Bulletins from different years may have different table formats:
- The parser handles multiple table formats
- Check console output for warnings about unrecognized formats
- Manual review may be needed for edge cases

### Missing Data
If certain years/quarters are missing:
- Document gaps in coverage
- Consider interpolation for analysis
- Check alternative sources for missing periods

## Next Steps After Download

1. Verify PDF downloads are complete
2. Run parser script
3. Review output CSV for data quality
4. Check for missing quarters/years
5. Validate price ranges are reasonable
6. Compare with alternative data sources if available
