"""Parse West Virginia timber price Excel files (2022-2024).

The WV Division of Forestry publishes annual timber price reports in Excel format
with regional stumpage prices by species.

Data sources:
- wv_timber_2022.xlsx: 2022 data
- wv_timber_2024.xls: 2022 and 2023 data

Output: Appends to data/raw/wv_forestry/wv_stumpage_parsed.csv
"""

import pandas as pd
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

# Paths
RAW_DIR = Path("data/raw/wv_forestry")

# Species columns in order (from Excel)
SPECIES_COLUMNS = [
    "Walnut", "White Oak", "Red Oak", "Other Oak", "Cherry",
    "Hard Maple", "Soft Maple", "Ash", "Yellow Poplar", "Basswood",
    "Hickory", "White Pine", "Other Pine", "Other Hardwood"
]

# Region mapping
REGION_MAP = {
    "REGION 1": "Eastern Panhandle",
    "REGION 2": "Northwestern",
    "REGION 3": "Southwestern",
    "REGION 4": "Southern",
    "REGION 5": "Northeastern",
}


def parse_2024_excel(filepath: Path) -> pd.DataFrame:
    """Parse the 2024 timber price report (contains 2022 and 2023 data)."""
    # Read raw Excel
    df = pd.read_excel(filepath, sheet_name=0, header=None)

    rows = []
    current_year = None

    # Process rows
    i = 0
    while i < len(df):
        row = df.iloc[i]

        # Check for year marker
        if pd.notna(row[0]) and isinstance(row[0], (int, float)):
            current_year = int(row[0])
            i += 1
            continue

        # Check for year in column 30 (2023 section)
        if pd.notna(row[30]) and isinstance(row[30], (int, float)):
            current_year = int(row[30])

        # Check for region marker in column 2 or 32
        region_col2 = str(row[2]) if pd.notna(row[2]) else ""
        region_col32 = str(row[32]) if pd.notna(row[32]) else ""

        if region_col2.startswith("REGION"):
            region = region_col2
            # Get prices from next row (column 3 = $/MBF indicator, columns 4-17 = species prices)
            if i + 1 < len(df):
                price_row = df.iloc[i + 1]
                if str(price_row[3]) == "$/MBF":
                    for j, species in enumerate(SPECIES_COLUMNS):
                        price = price_row[4 + j]
                        if pd.notna(price) and price != 0:
                            try:
                                price_val = float(price)
                                if price_val > 0:
                                    rows.append({
                                        'year': current_year or 2022,
                                        'region': REGION_MAP.get(region, region),
                                        'species': species,
                                        'product_type': 'Stumpage',
                                        'price_avg': price_val,
                                        'unit': '$/MBF',
                                    })
                            except (ValueError, TypeError):
                                pass
                    # Also get pulpwood price
                    pulp_price = price_row[23]  # Pulpwood column
                    if pd.notna(pulp_price) and pulp_price != 0:
                        try:
                            rows.append({
                                'year': current_year or 2022,
                                'region': REGION_MAP.get(region, region),
                                'species': 'Mixed',
                                'product_type': 'Pulpwood',
                                'price_avg': float(pulp_price),
                                'unit': '$/Cord',
                            })
                        except (ValueError, TypeError):
                            pass

        # Check 2023 section (columns 32+)
        if region_col32.startswith("REGION"):
            region = region_col32
            # Get prices from next row
            if i + 1 < len(df):
                price_row = df.iloc[i + 1]
                if str(price_row[33]) == "$/MBF":
                    for j, species in enumerate(SPECIES_COLUMNS):
                        price = price_row[34 + j]
                        if pd.notna(price) and price != 0:
                            try:
                                price_val = float(price)
                                if price_val > 0:
                                    rows.append({
                                        'year': 2023,
                                        'region': REGION_MAP.get(region, region),
                                        'species': species,
                                        'product_type': 'Stumpage',
                                        'price_avg': price_val,
                                        'unit': '$/MBF',
                                    })
                            except (ValueError, TypeError):
                                pass
                    # Pulpwood
                    pulp_price = price_row[53]
                    if pd.notna(pulp_price) and pulp_price != 0:
                        try:
                            rows.append({
                                'year': 2023,
                                'region': REGION_MAP.get(region, region),
                                'species': 'Mixed',
                                'product_type': 'Pulpwood',
                                'price_avg': float(pulp_price),
                                'unit': '$/Cord',
                            })
                        except (ValueError, TypeError):
                            pass

        i += 1

    return pd.DataFrame(rows)


def parse_2022_excel(filepath: Path) -> pd.DataFrame:
    """Parse the 2022 timber price report."""
    # Read raw Excel
    df = pd.read_excel(filepath, sheet_name=0, header=None)

    rows = []

    # Similar parsing logic but simpler (single year)
    i = 0
    while i < len(df):
        row = df.iloc[i]

        # Check for region marker
        region_col = str(row[2]) if pd.notna(row[2]) else ""

        if region_col.startswith("REGION"):
            region = region_col
            # Get prices from next row
            if i + 1 < len(df):
                price_row = df.iloc[i + 1]
                if str(price_row[3]) == "$/MBF":
                    for j, species in enumerate(SPECIES_COLUMNS):
                        if 4 + j < len(price_row):
                            price = price_row[4 + j]
                            if pd.notna(price) and price != 0:
                                try:
                                    price_val = float(price)
                                    if price_val > 0:
                                        rows.append({
                                            'year': 2022,
                                            'region': REGION_MAP.get(region, region),
                                            'species': species,
                                            'product_type': 'Stumpage',
                                            'price_avg': price_val,
                                            'unit': '$/MBF',
                                        })
                                except (ValueError, TypeError):
                                    pass
        i += 1

    return pd.DataFrame(rows)


def transform_to_standard(df: pd.DataFrame) -> pd.DataFrame:
    """Transform parsed data to standard format."""
    rows = []

    for _, row in df.iterrows():
        rows.append({
            'year': int(row['year']),
            'region': row['region'],
            'species': row['species'],
            'product_type': row['product_type'],
            'price_avg': row['price_avg'],
            'price_low': None,
            'price_high': None,
            'unit': row['unit'],
            'num_reports': None,
        })

    return pd.DataFrame(rows)


def main():
    console.print("[bold]Parsing West Virginia Excel timber price reports[/bold]\n")

    all_data = []

    # Parse 2024 Excel (contains 2022-2023 data)
    excel_2024 = RAW_DIR / "wv_timber_2024.xls"
    if excel_2024.exists():
        console.print(f"[blue]Parsing {excel_2024.name}...[/blue]")
        df_2024 = parse_2024_excel(excel_2024)
        console.print(f"  Extracted {len(df_2024)} records")
        all_data.append(df_2024)

    # Parse 2022 Excel
    excel_2022 = RAW_DIR / "wv_timber_2022.xlsx"
    if excel_2022.exists():
        console.print(f"[blue]Parsing {excel_2022.name}...[/blue]")
        df_2022 = parse_2022_excel(excel_2022)
        console.print(f"  Extracted {len(df_2022)} records")
        # Only add if we don't already have 2022 data
        if len(all_data) > 0:
            existing_years = pd.concat(all_data)['year'].unique()
            if 2022 not in existing_years:
                all_data.append(df_2022)
        else:
            all_data.append(df_2022)

    if not all_data:
        console.print("[red]No data extracted[/red]")
        return

    # Combine all data
    combined = pd.concat(all_data, ignore_index=True)

    # Remove duplicates
    combined = combined.drop_duplicates(
        subset=['year', 'region', 'species', 'product_type'],
        keep='first'
    )

    # Transform to standard format
    result = transform_to_standard(combined)

    # Show summary
    table = Table(title="WV Excel Data Extracted")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Total rows", str(len(result)))
    table.add_row("Years", ", ".join(map(str, sorted(result['year'].unique()))))
    table.add_row("Regions", str(result['region'].nunique()))
    table.add_row("Species", str(result['species'].nunique()))
    console.print(table)

    # Load existing parsed data
    existing_path = RAW_DIR / "wv_stumpage_parsed.csv"
    if existing_path.exists():
        existing = pd.read_csv(existing_path)
        console.print(f"\n[blue]Existing data:[/blue] {len(existing)} rows, years {existing['year'].min()}-{existing['year'].max()}")

        # Remove years we're adding to avoid duplicates
        new_years = result['year'].unique()
        existing = existing[~existing['year'].isin(new_years)]
        console.print(f"[yellow]After removing years {list(new_years)}:[/yellow] {len(existing)} rows")

        # Combine
        final = pd.concat([existing, result], ignore_index=True)
    else:
        final = result

    # Sort
    final = final.sort_values(['year', 'region', 'species'])

    # Save
    final.to_csv(existing_path, index=False)
    console.print(f"\n[green]Saved to {existing_path}:[/green] {len(final)} total rows")

    # Show year coverage
    console.print("\n[bold]Year Coverage:[/bold]")
    year_counts = final.groupby('year').size()
    for year, count in year_counts.items():
        console.print(f"  {year}: {count} records")


if __name__ == "__main__":
    main()
