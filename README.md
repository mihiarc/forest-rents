# Timber Prices Dataset

Stumpage price data collection for US timberland across the contiguous United States.

## Overview

This project collects and standardizes timber stumpage price data from 18+ state and federal sources to build a unified national dataset for economic analysis.

### Theoretical Foundation

**Primary Reference:**
- Mihiar, C., and D.J. Lewis (2021). "Climate, adaptation, and the value of forestland: A national Ricardian analysis of the United States." Land Economics, 97(4): 911-932.

### Key Components

| Component | Description | Data Source |
|-----------|-------------|-------------|
| Timber stumpage prices | Regional timber prices by species | USFS Timber Product Output (TPO) |
| Harvest volumes | County-level harvest data | USFS Forest Inventory & Analysis (FIA) |
| Forest land values | Market values for timberland | USDA Land Values Survey |
| Climate variables | Temperature, precipitation | gridMET, PRISM |
| Site productivity | Forest site index | USFS FIA |

## Data Sources

1. **USFS Timber Product Output (TPO)** - Stumpage prices and harvest volumes
2. **USFS Forest Inventory & Analysis (FIA)** - Plot-level forest data
3. **USDA Land Values Survey** - Forest land market values
4. **gridMET/PRISM** - Climate data for Ricardian analysis
5. **Census TIGER/Line** - County boundaries

## Installation

```bash
# Clone repository
git clone <repository-url>
cd timber-prices

# Create virtual environment and install
uv venv
uv pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
```

## Usage

```bash
# Download data sources
uv run python scripts/download_data.py

# Process data and estimate rents
uv run python scripts/process_data.py

# Create visualizations
uv run python scripts/create_visualizations.py
```

## Output Files

### Primary Output: `data/output/county_timber_prices_panel.csv`

| Column | Description |
|--------|-------------|
| `state_fips` | 2-digit state FIPS code |
| `county_fips` | 5-digit county FIPS code |
| `county_name` | County name |
| `year` | Data year |
| `forest_rent` | Net return to forest land ($/acre) |
| `stumpage_value` | Timber stumpage value ($/acre) |
| `site_index` | Forest site productivity index |
| `data_source` | "observed" or "predicted" |

## Project Structure

```
timber-prices/
├── data/
│   ├── raw/                    # Downloaded source data
│   │   ├── tpo/                # Timber Product Output
│   │   ├── fia/                # Forest Inventory & Analysis
│   │   └── tiger/              # Census county boundaries
│   ├── processed/              # Cleaned intermediate data
│   └── output/                 # Final datasets
├── scripts/
│   ├── download_data.py        # Download all data sources
│   ├── process_data.py         # Process and estimate rents
│   └── create_visualizations.py # Generate maps and charts
├── src/timber_prices/           # Python package
│   ├── config.py               # Configuration settings
│   ├── tpo_client.py           # TPO data access
│   ├── fia_client.py           # FIA data access
│   └── ricardian.py            # Ricardian rent estimation
└── figures/                    # Generated visualizations
```

## Methodology

Forest net returns are estimated using the Ricardian approach:

1. **Timber revenue**: Stumpage prices × harvest probability × yield
2. **Climate adjustment**: Temperature and precipitation effects on productivity
3. **Site quality**: Adjustment for site index and species composition
4. **Non-timber values**: Recreation, carbon, water (where data available)

## License

MIT
