"""Integrate California CDTFA harvest values into the unified dataset.

The California Department of Tax and Fee Administration (CDTFA) publishes
semi-annual harvest values schedules used for timber yield tax assessment.
These serve as proxy stumpage values for California timber.

Data sources:
- ca_stumpage_parsed.csv from parse_ca_cdtfa.py

Output: Appends to data/processed/stumpage_unified.csv
"""

import pandas as pd
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

# Paths
RAW_DIR = Path("data/raw/ca_cdtfa")
UNIFIED_PATH = Path("data/processed/stumpage_unified.csv")

# Species standardization
SPECIES_MAP = {
    "Ponderosa Pine": "ponderosa_pine",
    "Douglas Fir": "douglas_fir",
    "Hemlock-Fir": "hemlock_fir",
    "Incense Cedar": "incense_cedar",
    "Redwood": "redwood",
    "Port Orford Cedar": "port_orford_cedar",
}

# Timber value areas to region descriptions
TVA_REGIONS = {
    1: "North Coast (Del Norte, Humboldt)",
    2: "Mendocino Coast",
    3: "Santa Cruz Mountains",
    4: "North Interior (Trinity, Shasta West)",
    5: "Northeast (Modoc, Lassen, Siskiyou East)",
    6: "Sacramento Valley",
    7: "Sierra Nevada North",
    8: "Sierra Nevada Central",
    9: "Southern California",
}

# MBF to tons conversion
MBF_TO_TONS = 4.0


def load_parsed_data() -> pd.DataFrame:
    """Load the parsed California CDTFA data."""
    path = RAW_DIR / "ca_stumpage_parsed.csv"
    df = pd.read_csv(path)
    console.print(f"[blue]Loaded parsed data:[/blue] {len(df)} rows")
    return df


def transform_to_unified(df: pd.DataFrame) -> pd.DataFrame:
    """Transform parsed California data to unified schema."""
    rows = []

    for _, row in df.iterrows():
        price_mbf = row['price_mbf']
        if pd.isna(price_mbf):
            continue

        # Calculate price per ton
        price_per_ton = float(price_mbf) / MBF_TO_TONS

        # Map species to standardized name
        species_std = SPECIES_MAP.get(row['species'], row['species'].lower().replace(' ', '_').replace('-', '_'))

        # Get timber value area
        tva = int(row['timber_value_area'])
        region_desc = TVA_REGIONS.get(tva, f"TVA {tva}")

        # Determine product type (green vs salvage)
        timber_type = row.get('timber_type', 'green')
        product_type = f"sawtimber_{timber_type}"

        rows.append({
            'source': 'CA',
            'year': int(row['year']),
            'quarter': None,  # Semi-annual data
            'period_type': 'semi-annual',
            'region': f"TVA_{tva}",
            'county': region_desc,
            'species': species_std,
            'product_type': product_type,
            'price_avg': float(price_mbf),
            'price_low': None,
            'price_high': None,
            'unit': '$/MBF',
            'price_per_ton': round(price_per_ton, 2),
            'conversion_factor': MBF_TO_TONS,
            'sample_size': None,
            'notes': f"CDTFA harvest values {row['year']} H{row['half']}. Size: {row['size_code']}. Tax assessment, not market.",
        })

    return pd.DataFrame(rows)


def show_summary(df: pd.DataFrame, title: str):
    """Display summary statistics."""
    table = Table(title=title)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total rows", str(len(df)))
    table.add_row("Year range", f"{df['year'].min()} - {df['year'].max()}")
    table.add_row("Regions", str(df['region'].nunique()))
    table.add_row("Species", str(df['species'].nunique()))

    console.print(table)


def main():
    console.print("[bold]Integrating California CDTFA harvest values[/bold]\n")

    # Load parsed data
    parsed_df = load_parsed_data()

    # Transform to unified schema
    console.print("\n[yellow]Transforming data...[/yellow]")
    ca_unified = transform_to_unified(parsed_df)

    # Remove duplicates
    ca_unified = ca_unified.drop_duplicates(
        subset=['source', 'year', 'species', 'region', 'product_type', 'notes'],
        keep='last'
    )

    show_summary(ca_unified, "California CDTFA Data Transformed")

    # Load existing unified dataset
    console.print("\n[yellow]Loading existing unified dataset...[/yellow]")
    existing_df = pd.read_csv(UNIFIED_PATH)
    console.print(f"[blue]Existing rows:[/blue] {len(existing_df)}")

    # Check for existing CA CDTFA data
    existing_ca = existing_df[existing_df['notes'].str.contains('CDTFA', na=False)]
    if len(existing_ca) > 0:
        console.print(f"[yellow]Found {len(existing_ca)} existing CA CDTFA rows - removing to avoid duplicates[/yellow]")
        existing_df = existing_df[~existing_df['notes'].str.contains('CDTFA', na=False)]

    # Append new data
    unified_df = pd.concat([existing_df, ca_unified], ignore_index=True)

    # Sort by source, year
    unified_df = unified_df.sort_values(['source', 'year', 'quarter'], na_position='last')

    # Save
    unified_df.to_csv(UNIFIED_PATH, index=False)
    console.print(f"\n[green]Saved unified dataset:[/green] {len(unified_df)} total rows")

    # Show final summary
    console.print("\n[bold]Integration complete![/bold]")
    console.print(f"  Added: {len(ca_unified)} California CDTFA rows")
    console.print(f"  Total: {len(unified_df)} rows in unified dataset")

    # Show California coverage
    console.print("\n[bold]California CDTFA Coverage:[/bold]")
    year_summary = ca_unified.groupby('year').agg({
        'species': 'nunique',
        'region': 'nunique',
        'price_avg': 'mean'
    }).round(0)
    year_summary.columns = ['species', 'regions', 'avg_price_mbf']
    console.print(year_summary.to_string())

    # Show species coverage
    console.print("\n[bold]Species Coverage:[/bold]")
    species_summary = ca_unified.groupby('species').agg({
        'year': ['min', 'max', 'count'],
        'price_avg': 'mean'
    }).round(0)
    species_summary.columns = ['first_year', 'last_year', 'rows', 'avg_price']
    console.print(species_summary.to_string())


if __name__ == "__main__":
    main()
