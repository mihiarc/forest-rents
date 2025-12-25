"""Parse USFS PNW Table 92 for species-specific stumpage prices.

Table 92 contains average stumpage prices for sawtimber sold on National Forests
by selected species for the Pacific Northwest Region (OR/WA), 1959-2022.

Data source:
- pnw-ppet-table92.xlsx from USFS PNW Research Station

Output: data/raw/usfs_pnw/usfs_pnw_table92_species.csv
"""

import pandas as pd
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

# Paths
RAW_DIR = Path("data/raw/usfs_pnw")

# Species columns in Table 92 (columns 1-15 after Year column)
SPECIES_COLUMNS = {
    1: 'douglas_fir_west',
    2: 'douglas_fir_east',
    3: 'douglas_fir_total',
    4: 'ponderosa_jeffrey_pine',
    5: 'sugar_pine',
    6: 'white_pine',
    7: 'lodgepole_pine',
    8: 'engelmann_spruce',
    9: 'sitka_spruce',
    10: 'western_hemlock',
    11: 'cedars',
    12: 'larch',
    13: 'noble_shasta_fir',
    14: 'other_true_firs',
    15: 'all_species',
}


def parse_table92() -> pd.DataFrame:
    """Parse Table 92 for species-specific stumpage prices."""
    filepath = RAW_DIR / "pnw-ppet-table92.xlsx"

    # Read raw Excel
    df = pd.read_excel(filepath, header=None)

    rows = []

    # Data starts at row 4 (0-indexed), Year is in column 0
    for i in range(4, len(df)):
        row = df.iloc[i]

        # Get year
        year_val = row[0]
        if pd.isna(year_val):
            continue

        try:
            year = int(float(year_val))
        except (ValueError, TypeError):
            continue

        if year < 1900 or year > 2100:
            continue

        # Extract each species price
        for col_idx, species in SPECIES_COLUMNS.items():
            price = row[col_idx]

            if pd.isna(price):
                continue

            # Handle "--" or other non-numeric values
            if isinstance(price, str):
                if price.strip() in ['--', '-', 'e', 'c', '']:
                    continue
                try:
                    price = float(price)
                except ValueError:
                    continue

            try:
                price_val = float(price)
                if price_val <= 0:
                    continue
            except (ValueError, TypeError):
                continue

            rows.append({
                'year': year,
                'species': species,
                'price_per_mbf': price_val,
            })

    return pd.DataFrame(rows)


def main():
    console.print("[bold]Parsing USFS PNW Table 92: Pacific Northwest Species Stumpage[/bold]\n")

    # Parse Table 92
    df = parse_table92()

    console.print(f"[blue]Extracted {len(df)} records[/blue]")
    console.print(f"[blue]Years: {df['year'].min()} - {df['year'].max()}[/blue]")
    console.print(f"[blue]Species: {df['species'].nunique()}[/blue]")

    # Show summary table
    table = Table(title="USFS PNW Table 92 Species Data")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Total records", str(len(df)))
    table.add_row("Year range", f"{df['year'].min()} - {df['year'].max()}")
    table.add_row("Species", str(df['species'].nunique()))
    console.print(table)

    # Save to CSV
    output_path = RAW_DIR / "usfs_pnw_table92_species.csv"
    df.to_csv(output_path, index=False)
    console.print(f"\n[green]Saved to {output_path}[/green]")

    # Show species coverage
    console.print("\n[bold]Species Coverage:[/bold]")
    species_summary = df.groupby('species').agg({
        'year': ['min', 'max', 'count'],
        'price_per_mbf': 'mean'
    }).round(2)
    species_summary.columns = ['first_year', 'last_year', 'records', 'avg_price']
    console.print(species_summary.to_string())

    # Show recent Douglas-fir prices
    console.print("\n[bold]Recent Douglas-fir Prices (2018-2022):[/bold]")
    doug_fir = df[df['species'].str.contains('douglas_fir')]
    recent = doug_fir[doug_fir['year'] >= 2018].pivot(
        index='year',
        columns='species',
        values='price_per_mbf'
    )
    console.print(recent.to_string())


if __name__ == "__main__":
    main()
