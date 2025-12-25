# Stumpage Price Data Gaps

This document tracks known data gaps and potential sources for expanding the unified stumpage price dataset.

## Summary by State

| State | Current Coverage | Gap | Solution | Priority |
|-------|-----------------|-----|----------|----------|
| **New Hampshire** | 1985-2011 | 2012-2024 | Manual download from NH DRA | High |
| **Tennessee** | 2003-2017 | 2018-present | TimberMart-South (paid) | High |
| **Kentucky** | 2024 Q3-Q4 only | Historical (pre-2024), OCR needed | OCR for PDFs, contact state | Medium |
| **California** | 2019-2025 | 2009-2018 | Contact CDTFA | Medium |
| **Georgia** | 2024-2025 | Historical | TimberMart-South or UGA | Low |

---

## New Hampshire

### Current Status
- **Coverage**: 1985-2011 (Figshare/NHTOA Timber Crier data)
- **Gap**: 2012-2024 (13 years)

### Issue
The NH Department of Revenue Administration (DRA) publishes semi-annual stumpage values, but their website has **Akamai bot protection** that blocks automated downloads. Data exists for 2021-2025 online but must be downloaded manually via browser.

### Potential Solutions

1. **Manual Download (2021-2025)** - IMMEDIATE
   - URL: https://www.revenue.nh.gov/taxes-glance/timber-tax/average-stumpage-value-information
   - Download all available PDFs via browser
   - Save to `data/raw/nh_dra/pdfs/`
   - Run parser: `uv run python scripts/parse_nh_dra_stumpage.py`

2. **Request Historical Data (2012-2020)**
   - Contact: NH DRA Property Appraisal Division
   - Phone: (603) 203-5950
   - Email: Forms@dra.nh.gov
   - Request: Archived Average Stumpage Value PDFs

3. **NHTOA Quarterly Survey**
   - Contact: cbirch@nhtoa.org
   - May have compiled data from their quarterly surveys

### Data Format (NH DRA PDFs)
- Semi-annual publication (Apr-Sep, Oct-Mar)
- Three regions: Northern, Central, Southern NH
- Low and high stumpage values by species
- Units: $/MBF, $/Cord, $/Ton

### References
- [NH DRA Stumpage Values](https://www.revenue.nh.gov/taxes-glance/timber-tax/average-stumpage-value-information)
- [USFS NH Timber Price Info](https://research.fs.usda.gov/srs/centers/fep/timbernh)

---

## Tennessee

### Current Status
- **Coverage**: 2003-2017 (Tennessee Forest Products Bulletin)
- **Gap**: 2018-present (7 years)

### Issue
The Tennessee Forest Products Bulletin **ceased publication in 2017**. This was the official quarterly stumpage price report from the Tennessee Department of Agriculture Division of Forestry.

### Potential Solutions

1. **TimberMart-South (Recommended)**
   - Commercial subscription service
   - Has quarterly data from 1976-present for Tennessee
   - Contact: tmart@timbermart-south.com, 706-247-7660
   - Cost: Custom quotes based on data needs

2. **Tennessee State Forest Timber Sales Archive**
   - URL: https://www.tn.gov/agriculture/forests/state-forests/timber-sale-archive.html
   - Limited to FY 2023-2025, individual sale records
   - Labor-intensive to aggregate

3. **Contact Tennessee Division of Forestry**
   - David Neumann: David.Neumann@tn.gov, 615-837-5334
   - May have unpublished internal data

### References
- Archive: https://www.tn.gov/agriculture/businesses/business-development/forest-products/tfpb.html
- USDA SRS: https://srs.fs.usda.gov/econ/timberprices/data.php?location=TN

---

## Kentucky

### Current Status
- **Coverage**: 2024 Q3-Q4 only (530 records)
- **Gap**: All other periods

### Issues
1. **Image-based PDFs**: Most Kentucky reports are scanned images, not text-extractable
2. **Delivered prices only**: Kentucky publishes delivered log prices, not stumpage
3. **Not in TimberMart-South**: Kentucky is outside the 11-state coverage area

### Potential Solutions

1. **OCR Implementation**
   - Use Tesseract or cloud OCR to parse image-based PDFs
   - PDFs available: 2020-2025

2. **Delivered-to-Stumpage Conversion**
   - Stumpage is typically 30-50% of delivered prices
   - Use 50% reduction as conservative estimate

3. **Contact Kentucky Division of Forestry**
   - Stewart M. West: (502) 782-7179
   - Request historical delivered log price reports

### Important Notes
- Kentucky data represents **delivered prices at mill**, not stumpage
- For stumpage estimation, apply 50% reduction factor
- Notes field should clearly indicate: "Estimated from delivered prices"

---

## California

### Current Status
- **Coverage**: 2019-2025 (1,890 records from CDTFA)
- **Gap**: 2009-2018 (10 years)

### Issue
CDTFA harvest values schedules from 2009-2018 are not publicly archived online. USFS PNW data ends at 2008 for California.

### Potential Solutions

1. **Contact CDTFA**
   - Phone: 916-309-8560
   - Request archived Harvest Values Schedules for 2009-2018

2. **California Board of Equalization Archives**
   - Historical stumpage reports used for yield tax
   - May have older data

3. **UC Cooperative Extension**
   - Historical analysis available through 2012
   - Contact for unpublished data

### Notes
- CDTFA values are tax assessment values, not market prices
- Apply adjustments for logging system, volume, etc.

---

## Georgia

### Current Status
- **Coverage**: 2024-2025 (2,862 records from GA DOR)
- **Gap**: Historical data

### Issue
Only 2 years of structured GA DOR data available in parsed form. UGA Extension outlook PDFs exist but contain narrative data (not tables).

### Potential Solutions

1. **TimberMart-South**
   - Has quarterly Georgia data from 1976-present
   - Commercial subscription required

2. **Parse UGA Extension PDFs**
   - `uga_timber_outlook_2024.pdf`, `uga_timber_outlook_2025.pdf`
   - Contains quarterly market analysis (narrative form)

3. **Contact GA DOR**
   - Request historical Owner Harvest Timber Value reports

---

## Priority Actions

### High Priority
1. **Tennessee**: Contact TimberMart-South for 2018-2024 data quote
2. **California**: Contact CDTFA for 2009-2018 archived schedules

### Medium Priority
3. **Kentucky**: Implement OCR pipeline for image-based PDFs
4. **Georgia**: Explore UGA Extension PDF parsing

### Low Priority
5. **All states**: Establish contacts with state forestry divisions for historical data
6. **Research**: Investigate USDA FIA stumpage price surveys

---

## Data Quality Notes

| Source Type | Reliability | Notes |
|-------------|-------------|-------|
| TimberMart-South | High | Industry standard, quarterly surveys |
| State forestry reports | High | Official data, varies by state |
| Tax assessment values | Medium | Proxy for stumpage, not market prices |
| Delivered log prices | Medium | Must adjust for harvest/transport costs |
| Extension estimates | Low | Estimates, not transaction data |

---

## Contact Information

| State | Contact | Role | Phone | Email |
|-------|---------|------|-------|-------|
| TN | David Neumann | TN Dept of Agriculture | 615-837-5334 | David.Neumann@tn.gov |
| KY | Stewart M. West | KY Division of Forestry | 502-782-7179 | - |
| CA | CDTFA Timber Tax | Tax Section | 916-309-8560 | - |
| GA | - | GA DOR | - | - |
| TMS | - | TimberMart-South | 706-247-7660 | tmart@timbermart-south.com |
