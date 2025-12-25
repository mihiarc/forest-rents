"""Integrate USFS PNW species-specific stumpage data into the unified dataset.

This adds detailed species data for Oregon and Washington from USFS PNW Table 92,
including Douglas-fir, Western hemlock, Sitka spruce, and other Pacific Northwest species.

Data source:
- usfs_pnw_table92_species.csv from parse_usfs_pnw_species.py

Output: Updates data/processed/stumpage_unified.csv
"""

import pandas as pd
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

# Paths
RAW_DIR = Path("data/raw/usfs_pnw")
UNIFIED_PATH = Path("data/processed/stumpage_unified.csv")

# Species name standardization
SPECIES_MAP = {
    'douglas_fir_west': 'douglas_fir',
    'douglas_fir_east': 'douglas_fir',
    'douglas_fir_total': 'douglas_fir',
    'ponderosa_jeffrey_pine': 'ponderosa_pine',
    'sugar_pine': 'sugar_pine',
    'white_pine': 'white_pine',
    'lodgepole_pine': 'lodgepole_pine',
    'engelmann_spruce': 'engelmann_spruce',
    'sitka_spruce': 'sitka_spruce',
    'western_hemlock': 'western_hemlock',
    'cedars': 'cedar',
    'larch': 'larch',
    'noble_shasta_fir': 'true_fir',
    'other_true_firs': 'true_fir',
    'all_species': 'all_species',
}

# Region descriptions
REGION_MAP = {
    'douglas_fir_west': 'Western OR/WA',
    'douglas_fir_east': 'Eastern OR/WA',
    'douglas_fir_total': 'Pacific Northwest OR/WA',
}

# MBF to tons conversion
MBF_TO_TONS = 4.0


def load_species_data() -> pd.DataFrame:
    """Load the parsed species data."""
    path = RAW_DIR / "usfs_pnw_table92_species.csv"
    df = pd.read_csv(path)
    console.print(f"[blue]Loaded species data:[/blue] {len(df)} rows ({df['year'].min()}-{df['year'].max()})")
    return df


def transform_to_unified(df: pd.DataFrame) -> pd.DataFrame:
    """Transform species data to unified schema."""
    rows = []

    for _, row in df.iterrows():
        price = row['price_per_mbf']
        if pd.isna(price) or price <= 0:
            continue

        year = int(row['year'])
        species_raw = row['species']

        # Standardize species name
        species = SPECIES_MAP.get(species_raw, species_raw)

        # Determine region based on species variant
        if species_raw in REGION_MAP:
            region = REGION_MAP[species_raw]
        else:
            region = 'Pacific Northwest OR/WA'

        # Calculate price per ton
        price_per_ton = float(price) / MBF_TO_TONS

        # Create note with detail
        if 'west' in species_raw:
            note_detail = "West side (coastal). "
        elif 'east' in species_raw:
            note_detail = "East side (interior). "
        else:
            note_detail = ""

        rows.append({
            'source': 'WA_OR',
            'year': year,
            'quarter': None,
            'period_type': 'annual',
            'region': region,
            'county': None,
            'species': species,
            'product_type': 'sawtimber',
            'price_avg': float(price),
            'price_low': None,
            'price_high': None,
            'unit': '$/MBF',
            'price_per_ton': round(price_per_ton, 2),
            'conversion_factor': MBF_TO_TONS,
            'sample_size': None,
            'notes': f"USFS PNW Table 92. {note_detail}National Forest stumpage, administered pricing.",
        })

    return pd.DataFrame(rows)


def show_summary(df: pd.DataFrame, title: str):
    """Display summary statistics."""
    table = Table(title=title)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total rows", str(len(df)))
    table.add_row("Year range", f"{df['year'].min()} - {df['year'].max()}")
    table.add_row("Species", str(df['species'].nunique()))
    table.add_row("Regions", str(df['region'].nunique()))

    console.print(table)


def main():
    console.print("[bold]Integrating USFS PNW species-specific stumpage data (OR/WA)[/bold]\n")

    # Load species data
    species_df = load_species_data()

    # Transform to unified schema
    console.print("\n[yellow]Transforming data...[/yellow]")
    wa_or_unified = transform_to_unified(species_df)

    # Remove duplicates (keep best record per year/species/region)
    wa_or_unified = wa_or_unified.drop_duplicates(
        subset=['source', 'year', 'species', 'region'],
        keep='last'
    )

    show_summary(wa_or_unified, "USFS PNW Species Data Transformed")

    # Load existing unified dataset
    console.print("\n[yellow]Loading existing unified dataset...[/yellow]")
    existing_df = pd.read_csv(UNIFIED_PATH)
    console.print(f"[blue]Existing rows:[/blue] {len(existing_df)}")

    # Remove existing WA_OR data (will be replaced with enhanced species data)
    existing_wa_or = existing_df[existing_df['source'] == 'WA_OR']
    console.print(f"[blue]Existing WA_OR rows:[/blue] {len(existing_wa_or)}")

    if len(existing_wa_or) > 0:
        console.print(f"[yellow]Removing existing WA_OR data to replace with species-detailed data[/yellow]")
        existing_df = existing_df[existing_df['source'] != 'WA_OR']

    # Append new data
    unified_df = pd.concat([existing_df, wa_or_unified], ignore_index=True)

    # Sort by source, year
    unified_df = unified_df.sort_values(['source', 'year', 'quarter'], na_position='last')

    # Save
    unified_df.to_csv(UNIFIED_PATH, index=False)
    console.print(f"\n[green]Saved unified dataset:[/green] {len(unified_df)} total rows")

    # Show final summary
    console.print("\n[bold]Integration complete![/bold]")

    # Count WA_OR rows in final dataset
    final_wa_or = unified_df[unified_df['source'] == 'WA_OR']
    console.print(f"  WA_OR total rows: {len(final_wa_or)}")
    console.print(f"  WA_OR year range: {final_wa_or['year'].min()}-{final_wa_or['year'].max()}")
    console.print(f"  Total unified: {len(unified_df)} rows")

    # Show species coverage
    console.print("\n[bold]OR/WA Species Coverage:[/bold]")
    species_summary = final_wa_or.groupby('species').agg({
        'year': ['min', 'max', 'count'],
        'price_avg': 'mean'
    }).round(2)
    species_summary.columns = ['first_year', 'last_year', 'records', 'avg_price']
    console.print(species_summary.to_string())

    # Highlight Douglas-fir
    console.print("\n[bold green]Douglas-fir Coverage (Primary Douglas-fir Market Species):[/bold green]")
    doug_fir = final_wa_or[final_wa_or['species'] == 'douglas_fir']
    console.print(f"  Records: {len(doug_fir)}")
    console.print(f"  Years: {doug_fir['year'].min()}-{doug_fir['year'].max()}")
    console.print(f"  Avg price: ${doug_fir['price_avg'].mean():.2f}/MBF")


if __name__ == "__main__":
    main()
