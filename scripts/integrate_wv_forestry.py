"""Integrate West Virginia Division of Forestry data into the unified dataset.

The WV Division of Forestry publishes annual timber price reports with
regional stumpage prices by species.

Data sources:
- wv_stumpage_parsed.csv from parse_wv_pdf.py (historical 2010-2020)
- wv_stumpage_parsed.csv from parse_wv_excel.py (2022-2023)

Output: Appends to data/processed/stumpage_unified.csv
"""

import pandas as pd
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

# Paths
RAW_DIR = Path("data/raw/wv_forestry")
UNIFIED_PATH = Path("data/processed/stumpage_unified.csv")

# Species standardization
SPECIES_MAP = {
    "Walnut": "black_walnut",
    "White Oak": "white_oak",
    "Red Oak": "red_oak",
    "Other Oak": "other_oak",
    "Cherry": "black_cherry",
    "Hard Maple": "hard_maple",
    "Soft Maple": "soft_maple",
    "Ash": "ash",
    "Yellow Poplar": "yellow_poplar",
    "Basswood": "basswood",
    "Hickory": "hickory",
    "White Pine": "white_pine",
    "Other Pine": "other_pine",
    "Other Hardwood": "other_hardwood",
    "Mixed": "mixed",
}

# Region standardization (old format to new)
REGION_MAP = {
    "Region 1": "Eastern Panhandle",
    "Region 2": "Northwestern",
    "Region 3": "Southwestern",
    "Region 4": "Southern",
    "Region 5": "Northeastern",
}

# MBF to tons conversion for hardwoods
MBF_TO_TONS = 5.0  # Hardwood conversion factor


def load_parsed_data() -> pd.DataFrame:
    """Load the parsed West Virginia data."""
    path = RAW_DIR / "wv_stumpage_parsed.csv"
    df = pd.read_csv(path)
    console.print(f"[blue]Loaded parsed data:[/blue] {len(df)} rows")
    return df


def transform_to_unified(df: pd.DataFrame) -> pd.DataFrame:
    """Transform parsed West Virginia data to unified schema."""
    rows = []

    for _, row in df.iterrows():
        price = row['price_avg']
        if pd.isna(price) or price == 0:
            continue

        # Standardize region name
        region = row['region']
        region_std = REGION_MAP.get(region, region)

        # Map species to standardized name
        species = row['species']
        species_std = SPECIES_MAP.get(species, species.lower().replace(' ', '_'))

        # Determine unit and conversion
        unit = row['unit']
        if unit == '$/MBF':
            price_per_ton = float(price) / MBF_TO_TONS
            conversion = MBF_TO_TONS
        elif unit == '$/Cord':
            # Cordwood - use cord as is, estimate ~2.5 tons per cord
            price_per_ton = float(price) / 2.5
            conversion = 2.5
        else:
            price_per_ton = None
            conversion = None

        # Product type mapping
        product = row['product_type']
        if product == 'Stumpage':
            product_type = 'sawtimber'
        elif product == 'Pulpwood':
            product_type = 'pulpwood'
        else:
            product_type = product.lower()

        rows.append({
            'source': 'WV',
            'year': int(row['year']),
            'quarter': None,  # Annual data
            'period_type': 'annual',
            'region': region_std,
            'county': None,
            'species': species_std,
            'product_type': product_type,
            'price_avg': float(price),
            'price_low': row.get('price_low'),
            'price_high': row.get('price_high'),
            'unit': unit,
            'price_per_ton': round(price_per_ton, 2) if price_per_ton else None,
            'conversion_factor': conversion,
            'sample_size': row.get('num_reports'),
            'notes': "WV Division of Forestry Timber Market Report",
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
    console.print("[bold]Integrating West Virginia Division of Forestry data[/bold]\n")

    # Load parsed data
    parsed_df = load_parsed_data()

    # Transform to unified schema
    console.print("\n[yellow]Transforming data...[/yellow]")
    wv_unified = transform_to_unified(parsed_df)

    # Remove duplicates
    wv_unified = wv_unified.drop_duplicates(
        subset=['source', 'year', 'species', 'region', 'product_type'],
        keep='last'
    )

    show_summary(wv_unified, "West Virginia Data Transformed")

    # Load existing unified dataset
    console.print("\n[yellow]Loading existing unified dataset...[/yellow]")
    existing_df = pd.read_csv(UNIFIED_PATH)
    console.print(f"[blue]Existing rows:[/blue] {len(existing_df)}")

    # Remove existing WV data to replace with fresh data
    existing_wv = existing_df[existing_df['source'] == 'WV']
    if len(existing_wv) > 0:
        console.print(f"[yellow]Found {len(existing_wv)} existing WV rows - removing to replace with updated data[/yellow]")
        existing_df = existing_df[existing_df['source'] != 'WV']

    # Append new data
    unified_df = pd.concat([existing_df, wv_unified], ignore_index=True)

    # Sort by source, year
    unified_df = unified_df.sort_values(['source', 'year', 'quarter'], na_position='last')

    # Save
    unified_df.to_csv(UNIFIED_PATH, index=False)
    console.print(f"\n[green]Saved unified dataset:[/green] {len(unified_df)} total rows")

    # Show final summary
    console.print("\n[bold]Integration complete![/bold]")
    console.print(f"  Added: {len(wv_unified)} West Virginia rows")
    console.print(f"  Total: {len(unified_df)} rows in unified dataset")

    # Show WV coverage
    console.print("\n[bold]West Virginia Year Coverage:[/bold]")
    year_summary = wv_unified.groupby('year').agg({
        'species': 'nunique',
        'region': 'nunique',
        'price_avg': 'mean'
    }).round(0)
    year_summary.columns = ['species', 'regions', 'avg_price_mbf']
    console.print(year_summary.to_string())

    # Show region coverage
    console.print("\n[bold]Region Coverage:[/bold]")
    region_summary = wv_unified.groupby('region').agg({
        'year': ['min', 'max', 'count'],
        'price_avg': 'mean'
    }).round(0)
    region_summary.columns = ['first_year', 'last_year', 'rows', 'avg_price']
    console.print(region_summary.to_string())


if __name__ == "__main__":
    main()
