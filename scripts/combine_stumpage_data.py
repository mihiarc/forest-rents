#!/usr/bin/env python3
"""
Combine all parsed stumpage price data into a unified dataset.

This script reads 16 state-level stumpage price CSV files and combines them
into a single unified dataset with a consistent schema.
"""

import pandas as pd
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()

# Base path for raw data
BASE_PATH = Path("/Users/mihiarc/landuse-model/forest-rents/data/raw")

# Unified schema columns
UNIFIED_COLUMNS = [
    'source',           # State abbreviation
    'year',             # Integer year
    'quarter',          # 1-4 or None for annual
    'period_type',      # quarterly, annual, semi-annual
    'region',           # State-specific geographic area
    'county',           # County name (GA only)
    'species',          # Species or species group
    'product_type',     # Standardized product type
    'price_avg',        # Average price
    'price_low',        # Low price range
    'price_high',       # High price range
    'unit',             # Price unit ($/ton, $/cord, $/mbf)
    'sample_size',      # Number of reports/samples
    'notes',            # Additional info (log_rule, program, etc.)
]


def standardize_product_type(product: str) -> str:
    """Standardize product type names across sources."""
    if pd.isna(product):
        return None

    product = str(product).lower().strip()

    # Sawtimber variants (check before generic 'log' check)
    if any(x in product for x in ['sawtimber', 'sawlog', 'saw log', 'sawlogs']):
        if 'large' in product:
            return 'sawtimber_large'
        elif 'small' in product:
            return 'sawtimber_small'
        return 'sawtimber'

    # Generic logs -> sawtimber
    if product in ['log', 'logs'] or 'hardwood_sawlog' in product or 'softwood_sawlog' in product:
        return 'sawtimber'

    # MBF products are sawtimber
    if product == 'mbf':
        return 'sawtimber'

    # Pulpwood
    if 'pulpwood' in product or 'pulp' in product:
        return 'pulpwood'

    # Chip-n-saw
    if 'chip' in product and 'saw' in product:
        return 'chip-n-saw'

    # Veneer
    if 'veneer' in product:
        return 'veneer'

    # Poles
    if 'pole' in product:
        return 'poles'

    # Firewood/Fuelwood
    if 'firewood' in product or 'fuelwood' in product or ('fuel' in product and 'chip' not in product):
        return 'firewood'

    # Fiber/Fuel combined
    if 'fiber' in product:
        return 'fiber_fuel'

    # Biomass
    if 'biomass' in product:
        return 'biomass'

    # Boltwood
    if 'bolt' in product:
        return 'boltwood'

    # Studwood
    if 'stud' in product:
        return 'studwood'

    # Cordwood
    if 'cordwood' in product or product == 'cord':
        return 'cordwood'

    # Posts
    if 'post' in product:
        return 'posts'

    # Crossties
    if 'crosstie' in product or 'tie' in product:
        return 'crossties'

    # Plylogs
    if 'plylog' in product:
        return 'plylogs'

    # T-wood/Topwood
    if 't-wood' in product or 'topwood' in product:
        return 'topwood'

    # Fuelchips
    if 'fuelchip' in product:
        return 'fuelchips'

    # Stumpage (generic)
    if 'stumpage' in product:
        return 'sawtimber'  # Assume stumpage without qualifier is sawtimber

    # Total/Index
    if 'total' in product or 'index' in product:
        return 'total_index'

    return product


def standardize_unit(unit: str) -> str:
    """Standardize unit names."""
    if pd.isna(unit):
        return None

    unit = str(unit).lower().strip()

    if 'mbf' in unit or 'thousand board' in unit:
        return '$/mbf'
    if 'cord' in unit:
        return '$/cord'
    if 'ton' in unit:
        return '$/ton'

    return unit


def load_michigan():
    """Load Michigan data - NOTE: This is price INDEX data, not actual prices."""
    path = BASE_PATH / "mi_dnr" / "mi_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    # Michigan has price indices, not actual prices
    return pd.DataFrame({
        'source': 'MI',
        'year': df['year'],
        'quarter': df['quarter'],
        'period_type': 'quarterly',
        'region': df['market_area'],
        'county': None,
        'species': df['species_group'],
        'product_type': df['product'].apply(lambda x: 'sawtimber' if x == 'SAW' else ('pulpwood' if x == 'PULP' else 'total_index')),
        'price_avg': df['avg_bid_index'],  # This is an index, not price
        'price_low': None,
        'price_high': None,
        'unit': 'index',  # Mark as index
        'sample_size': df['volume'],
        'notes': 'Price index (base=100), not actual price'
    })


def load_minnesota():
    """Load Minnesota data."""
    path = BASE_PATH / "mn_dnr" / "mn_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'MN',
        'year': df['year'],
        'quarter': None,
        'period_type': 'annual',
        'region': 'Statewide',
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price'],
        'price_low': None,
        'price_high': None,
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': None
    })


def load_wisconsin():
    """Load Wisconsin data."""
    path = BASE_PATH / "wi_dnr" / "wi_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'WI',
        'year': df['year'],
        'quarter': None,
        'period_type': 'annual',
        'region': df['zone'].apply(lambda x: f"Zone {x}" if str(x).isdigit() else x),
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price'],
        'price_low': None,
        'price_high': None,
        'unit': '$/cord',  # Wisconsin uses cords
        'sample_size': None,
        'notes': df['program'].apply(lambda x: f"Program: {x}")
    })


def load_new_york():
    """Load New York data."""
    path = BASE_PATH / "ny_dec" / "ny_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    # Map season to quarter
    season_to_quarter = {'winter': 1, 'spring': 2, 'summer': 3, 'fall': 4}

    return pd.DataFrame({
        'source': 'NY',
        'year': df['year'],
        'quarter': df['season'].apply(lambda x: season_to_quarter.get(str(x).lower())),
        'period_type': 'semi-annual',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg_median'],
        'price_low': df['price_low_median'],
        'price_high': df['price_high_median'],
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': df['log_rule'].apply(lambda x: f"Log rule: {x}" if pd.notna(x) else None)
    })


def load_pennsylvania():
    """Load Pennsylvania data."""
    path = BASE_PATH / "pa_extension" / "pa_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'PA',
        'year': df['year'],
        'quarter': df['quarter'],
        'period_type': 'quarterly',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': df['price_low'],
        'price_high': df['price_high'],
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': df['sample_size'],
        'notes': None
    })


def load_vermont():
    """Load Vermont data."""
    path = BASE_PATH / "vt_fpr" / "vt_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'VT',
        'year': df['year'],
        'quarter': df['quarter'],
        'period_type': 'quarterly',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price'],
        'price_low': None,
        'price_high': None,
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': df['sample_size'],
        'notes': None
    })


def load_maine():
    """Load Maine data."""
    path = BASE_PATH / "me_forest_service" / "me_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'ME',
        'year': df['year'],
        'quarter': None,
        'period_type': 'annual',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': df['price_min'],
        'price_high': df['price_max'],
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': df['num_reports'],
        'notes': None
    })


def load_alabama():
    """Load Alabama data."""
    path = BASE_PATH / "al_forestry" / "al_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'AL',
        'year': df['year'],
        'quarter': None,
        'period_type': 'annual',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': df.get('price_low'),
        'price_high': df.get('price_high'),
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': None
    })


def load_arkansas():
    """Load Arkansas data."""
    path = BASE_PATH / "ar_extension" / "ar_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'AR',
        'year': df['year'],
        'quarter': df['quarter'],
        'period_type': 'quarterly',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': df.get('price_low'),
        'price_high': df.get('price_high'),
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': None
    })


def load_florida():
    """Load Florida data."""
    path = BASE_PATH / "fl_ifas" / "fl_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'FL',
        'year': df['year'],
        'quarter': df['quarter'],
        'period_type': 'quarterly',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': df.get('price_low'),
        'price_high': df.get('price_high'),
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': None
    })


def load_georgia():
    """Load Georgia data - county-level data."""
    path = BASE_PATH / "ga_dor" / "ga_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'GA',
        'year': df['year'],
        'quarter': None,
        'period_type': 'annual',
        'region': 'Statewide',
        'county': df['county'],
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': None,
        'price_high': None,
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': 'County-level fair market values'
    })


def load_louisiana():
    """Load Louisiana data."""
    path = BASE_PATH / "la_forestry" / "la_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'LA',
        'year': df['year'],
        'quarter': df['quarter'],
        'period_type': 'quarterly',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price'],
        'price_low': None,
        'price_high': None,
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': None
    })


def load_mississippi():
    """Load Mississippi data."""
    path = BASE_PATH / "ms_extension" / "ms_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'MS',
        'year': df['year'],
        'quarter': df['quarter'],
        'period_type': 'quarterly',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': df.get('price_low'),
        'price_high': df.get('price_high'),
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': None
    })


def load_south_carolina():
    """Load South Carolina data."""
    path = BASE_PATH / "sc_forestry" / "sc_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'SC',
        'year': df['year'],
        'quarter': df['quarter'],
        'period_type': 'quarterly',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': df.get('price_low'),
        'price_high': df.get('price_high'),
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': None
    })


def load_texas():
    """Load Texas data."""
    path = BASE_PATH / "texas_am" / "tx_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'TX',
        'year': df['year'],
        'quarter': None,
        'period_type': 'annual',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type_normalized'].apply(standardize_product_type) if 'product_type_normalized' in df.columns else df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': None,
        'price_high': None,
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': None,
        'notes': None
    })


def load_west_virginia():
    """Load West Virginia data."""
    path = BASE_PATH / "wv_forestry" / "wv_stumpage_parsed.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)

    return pd.DataFrame({
        'source': 'WV',
        'year': df['year'],
        'quarter': None,
        'period_type': 'annual',
        'region': df['region'],
        'county': None,
        'species': df['species'],
        'product_type': df['product_type'].apply(standardize_product_type),
        'price_avg': df['price_avg'],
        'price_low': df.get('price_low'),
        'price_high': df.get('price_high'),
        'unit': df['unit'].apply(standardize_unit),
        'sample_size': df.get('num_reports'),
        'notes': None
    })


def main():
    console.print("[bold blue]Combining Stumpage Price Data from 16 States[/bold blue]\n")

    # Define all loaders
    loaders = [
        ('Michigan', load_michigan),
        ('Minnesota', load_minnesota),
        ('Wisconsin', load_wisconsin),
        ('New York', load_new_york),
        ('Pennsylvania', load_pennsylvania),
        ('Vermont', load_vermont),
        ('Maine', load_maine),
        ('Alabama', load_alabama),
        ('Arkansas', load_arkansas),
        ('Florida', load_florida),
        ('Georgia', load_georgia),
        ('Louisiana', load_louisiana),
        ('Mississippi', load_mississippi),
        ('South Carolina', load_south_carolina),
        ('Texas', load_texas),
        ('West Virginia', load_west_virginia),
    ]

    # Load all data
    all_data = []
    stats = []

    for name, loader in track(loaders, description="Loading state data..."):
        try:
            df = loader()
            if not df.empty:
                all_data.append(df)
                stats.append({
                    'State': name,
                    'Records': len(df),
                    'Years': f"{df['year'].min()}-{df['year'].max()}",
                    'Status': '[green]OK[/green]'
                })
            else:
                stats.append({
                    'State': name,
                    'Records': 0,
                    'Years': '-',
                    'Status': '[yellow]Empty[/yellow]'
                })
        except Exception as e:
            stats.append({
                'State': name,
                'Records': 0,
                'Years': '-',
                'Status': f'[red]Error: {str(e)[:30]}[/red]'
            })

    # Combine all dataframes
    console.print("\n[bold]Combining datasets...[/bold]")
    combined = pd.concat(all_data, ignore_index=True)

    # Ensure all columns exist
    for col in UNIFIED_COLUMNS:
        if col not in combined.columns:
            combined[col] = None

    # Reorder columns
    combined = combined[UNIFIED_COLUMNS]

    # Save combined dataset
    output_path = BASE_PATH.parent / "processed" / "stumpage_unified.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output_path, index=False)

    # Display loading stats
    table = Table(title="Data Loading Summary")
    table.add_column("State", style="cyan")
    table.add_column("Records", justify="right")
    table.add_column("Years", justify="center")
    table.add_column("Status")

    for s in stats:
        table.add_row(s['State'], str(s['Records']), s['Years'], s['Status'])

    console.print(table)

    # Display summary statistics
    console.print(f"\n[bold green]Combined Dataset Summary[/bold green]")
    console.print(f"Total records: {len(combined):,}")
    console.print(f"Output file: {output_path}")

    # Summary by state
    state_summary = combined.groupby('source').agg({
        'year': ['min', 'max', 'count']
    }).round(0)
    state_summary.columns = ['Year Min', 'Year Max', 'Records']

    console.print("\n[bold]Records by State:[/bold]")
    summary_table = Table()
    summary_table.add_column("State", style="cyan")
    summary_table.add_column("Records", justify="right")
    summary_table.add_column("Year Range", justify="center")

    for state in sorted(combined['source'].unique()):
        state_data = combined[combined['source'] == state]
        summary_table.add_row(
            state,
            f"{len(state_data):,}",
            f"{int(state_data['year'].min())}-{int(state_data['year'].max())}"
        )

    console.print(summary_table)

    # Summary by product type
    console.print("\n[bold]Records by Product Type:[/bold]")
    product_counts = combined['product_type'].value_counts()
    for product, count in product_counts.head(15).items():
        console.print(f"  {product}: {count:,}")

    # Summary by unit
    console.print("\n[bold]Records by Unit:[/bold]")
    unit_counts = combined['unit'].value_counts()
    for unit, count in unit_counts.items():
        console.print(f"  {unit}: {count:,}")

    # Year coverage
    console.print(f"\n[bold]Year Coverage:[/bold] {int(combined['year'].min())} - {int(combined['year'].max())}")

    return combined


if __name__ == "__main__":
    main()
