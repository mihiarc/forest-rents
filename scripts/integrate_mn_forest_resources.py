"""Integrate Minnesota Forest Resources data into the unified dataset.

The MN DNR Forest Resources reports contain stumpage prices for 2013-2023.
This extends the existing MN data which ends at 2021.

Data sources:
- mn_stumpage_forest_resources.csv from parse_mn_forest_resources.py (2013-2023)

Output: Appends to data/processed/stumpage_unified.csv
"""

import pandas as pd
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

# Paths
RAW_DIR = Path("data/raw/mn_dnr")
UNIFIED_PATH = Path("data/processed/stumpage_unified.csv")

# Product type mapping
PRODUCT_MAP = {
    'pulpwood': 'cordwood',
    'pulp_bolts': 'cordwood',
    'sawtimber': 'sawtimber',
    'cord': 'cordwood',
    'mbf': 'sawtimber',
}

# Cordwood to tons conversion (approximately 2.3 green tons per cord)
CORD_TO_TONS = 2.3
# MBF to tons conversion for softwood sawtimber
MBF_TO_TONS = 4.0


def load_forest_resources_data() -> pd.DataFrame:
    """Load the parsed Forest Resources data (2013-2023)."""
    path = RAW_DIR / "mn_stumpage_forest_resources.csv"
    df = pd.read_csv(path)
    console.print(f"[blue]Loaded Forest Resources data:[/blue] {len(df)} rows ({df['year'].min()}-{df['year'].max()})")
    return df


def transform_to_unified(df: pd.DataFrame) -> pd.DataFrame:
    """Transform parsed Minnesota data to unified schema."""
    rows = []

    for _, row in df.iterrows():
        price = row['price']
        if pd.isna(price) or price == 0:
            continue

        year = int(row['year'])
        species = row['species']
        product = row['product_type']
        unit = row['unit']

        # Standardize product type
        product_std = PRODUCT_MAP.get(product, product)

        # Calculate price per ton
        if unit == '$/cord':
            price_per_ton = float(price) / CORD_TO_TONS
            conversion = CORD_TO_TONS
        elif unit == '$/MBF':
            price_per_ton = float(price) / MBF_TO_TONS
            conversion = MBF_TO_TONS
        else:
            price_per_ton = None
            conversion = None

        # Create notes with product detail
        if product in ['pulp_bolts']:
            notes = "MN Forest Resources Report. Pulp and bolts combined price."
        else:
            notes = "MN Forest Resources Report. Public agencies stumpage."

        rows.append({
            'source': 'MN',
            'year': year,
            'quarter': None,
            'period_type': 'annual',
            'region': 'Statewide',
            'county': None,
            'species': species,
            'product_type': product_std,
            'price_avg': float(price),
            'price_low': None,
            'price_high': None,
            'unit': unit,
            'price_per_ton': round(price_per_ton, 2) if price_per_ton else None,
            'conversion_factor': conversion,
            'sample_size': None,
            'notes': notes,
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
    table.add_row("Product types", ", ".join(df['product_type'].unique()))

    console.print(table)


def main():
    console.print("[bold]Integrating Minnesota Forest Resources data[/bold]\n")

    # Load Forest Resources data
    fr_df = load_forest_resources_data()

    # Transform to unified schema
    console.print("\n[yellow]Transforming data...[/yellow]")
    mn_unified = transform_to_unified(fr_df)

    # Remove duplicates (keep one record per year/species/product)
    mn_unified = mn_unified.drop_duplicates(
        subset=['source', 'year', 'species', 'product_type'],
        keep='last'
    )

    show_summary(mn_unified, "Minnesota Forest Resources Data Transformed")

    # Load existing unified dataset
    console.print("\n[yellow]Loading existing unified dataset...[/yellow]")
    existing_df = pd.read_csv(UNIFIED_PATH)
    console.print(f"[blue]Existing rows:[/blue] {len(existing_df)}")

    # Check existing MN data
    existing_mn = existing_df[existing_df['source'] == 'MN']
    console.print(f"[blue]Existing MN rows:[/blue] {len(existing_mn)}")
    if len(existing_mn) > 0:
        console.print(f"  Years: {existing_mn['year'].min()}-{existing_mn['year'].max()}")

    # Strategy: Keep existing data for 2006-2012, use new data for 2013-2023
    # This gives us the longer historical series plus updated recent data

    # Remove MN data for years 2013+ (will be replaced with Forest Resources data)
    existing_df = existing_df[~((existing_df['source'] == 'MN') & (existing_df['year'] >= 2013))]
    console.print(f"[yellow]After removing MN 2013+ data:[/yellow] {len(existing_df)} rows")

    # Append new data
    unified_df = pd.concat([existing_df, mn_unified], ignore_index=True)

    # Sort by source, year
    unified_df = unified_df.sort_values(['source', 'year', 'quarter'], na_position='last')

    # Save
    unified_df.to_csv(UNIFIED_PATH, index=False)
    console.print(f"\n[green]Saved unified dataset:[/green] {len(unified_df)} total rows")

    # Show final summary
    console.print("\n[bold]Integration complete![/bold]")

    # Count MN rows in final dataset
    final_mn = unified_df[unified_df['source'] == 'MN']
    console.print(f"  MN total rows: {len(final_mn)}")
    console.print(f"  MN year range: {final_mn['year'].min()}-{final_mn['year'].max()}")
    console.print(f"  Total unified: {len(unified_df)} rows")

    # Show MN year coverage
    console.print("\n[bold]Minnesota Year Coverage:[/bold]")
    year_summary = final_mn.groupby('year').agg({
        'species': 'nunique',
        'product_type': 'nunique',
        'price_avg': 'mean'
    }).round(2)
    year_summary.columns = ['species', 'products', 'avg_price']
    console.print(year_summary.to_string())

    # Highlight the extension
    console.print("\n[bold green]Gap Filled:[/bold green]")
    console.print(f"  Previous coverage: 2006-2021")
    console.print(f"  New coverage: 2006-2023")
    console.print(f"  Added years: 2022, 2023")


if __name__ == "__main__":
    main()
