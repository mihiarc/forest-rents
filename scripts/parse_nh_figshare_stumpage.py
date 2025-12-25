"""
Parse New Hampshire stumpage price data from Figshare Excel file.

This script reads the Excel file downloaded from Figshare and converts it
to the standard CSV format used for stumpage price data.
"""

from pathlib import Path
import pandas as pd
from rich.console import Console
from rich.table import Table

console = Console()


def parse_excel_file(excel_path: Path) -> pd.DataFrame:
    """
    Parse the NH stumpage price Excel file from Figshare.

    Args:
        excel_path: Path to the Excel file

    Returns:
        DataFrame with parsed stumpage price data in standard format
    """
    console.print(f"[cyan]Reading Excel file:[/cyan] {excel_path}")

    # Read the information sheet to get species mapping
    info_df = pd.read_excel(excel_path, sheet_name='Information')
    console.print(f"[green]Read information sheet[/green]")

    # Create species code mapping from the information sheet
    # Rows 5-9 contain species codes and names
    species_mapping = {
        'EWP': 'White Pine',
        'WP': 'White Pine',  # Alternative code
        'YB': 'Yellow Birch',
        'SM': 'Sugar Maple',
        'RM': 'Red Maple',
        'RO': 'Red Oak'
    }

    # Read the main data sheet
    data_df = pd.read_excel(excel_path, sheet_name='NH_Data')
    console.print(f"[green]Read data sheet with {len(data_df)} rows[/green]")

    # Convert to standard format
    records = []
    for _, row in data_df.iterrows():
        species_code = row['species']
        species_name = species_mapping.get(species_code, species_code)

        record = {
            'year': int(row['year']),
            'quarter': f"Q{int(row['quarter'])}",
            'region': 'Statewide',  # This is statewide average data
            'species': species_name,
            'product_type': 'Sawlogs',  # From the info sheet, these are all sawlogs
            'price_avg': float(row['price']) if pd.notna(row['price']) else None,
            'price_low': None,  # Not provided in this dataset
            'price_high': None,  # Not provided in this dataset
            'unit': 'MBF',  # mbf Intl-1/4" from the info sheet
            'notes': f"Nominal price, inflation-adjusted: ${row['real price']:.2f}" if pd.notna(row['real price']) else ''
        }
        records.append(record)

    result_df = pd.DataFrame(records)
    console.print(f"[green]Converted {len(result_df)} records to standard format[/green]")

    return result_df


def main():
    """Main execution function."""
    console.print("\n[bold blue]NH Stumpage Data Parser (Figshare)[/bold blue]\n")

    # Input file
    data_dir = Path("/Users/mihiarc/landuse-model/forest-rents/data/raw/nh_dra")
    excel_path = data_dir / "nh_stumpage_figshare.xls"

    if not excel_path.exists():
        console.print(f"[red]Error: File not found:[/red] {excel_path}")
        return

    # Parse the file
    df = parse_excel_file(excel_path)

    # Sort by year, quarter, species
    df = df.sort_values(['year', 'quarter', 'species'])

    # Save to CSV
    output_csv = data_dir / "nh_stumpage_parsed.csv"
    df.to_csv(output_csv, index=False)
    console.print(f"\n[bold green]Data saved to:[/bold green] {output_csv}")

    # Print summary statistics
    console.print("\n[bold]Summary Statistics[/bold]")
    console.print(f"Total records: {len(df)}")
    console.print(f"Year range: {df['year'].min()} - {df['year'].max()}")
    console.print(f"Quarters: {sorted(df['quarter'].unique())}")
    console.print(f"Species: {sorted(df['species'].unique())}")
    console.print(f"Regions: {sorted(df['region'].unique())}")

    # Display sample data
    console.print("\n[bold]Sample Data (first 15 records):[/bold]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Year")
    table.add_column("Quarter")
    table.add_column("Region")
    table.add_column("Species")
    table.add_column("Product")
    table.add_column("Price Avg")
    table.add_column("Unit")

    for _, row in df.head(15).iterrows():
        table.add_row(
            str(row['year']),
            row['quarter'],
            row['region'],
            row['species'],
            row['product_type'],
            f"${row['price_avg']:.2f}" if pd.notna(row['price_avg']) else '',
            row['unit']
        )

    console.print(table)

    # Show records by year
    console.print("\n[bold]Records by Year:[/bold]")
    year_counts = df.groupby('year').size().sort_index()
    # Show first 5 and last 5 years
    console.print("First 5 years:")
    for year, count in year_counts.head(5).items():
        console.print(f"  {year}: {count} records")
    console.print("...")
    console.print("Last 5 years:")
    for year, count in year_counts.tail(5).items():
        console.print(f"  {year}: {count} records")

    # Show average price trends for each species
    console.print("\n[bold]Average Price by Species (most recent year):[/bold]")
    latest_year = df['year'].max()
    latest_data = df[df['year'] == latest_year]
    species_avg = latest_data.groupby('species')['price_avg'].mean().sort_values(ascending=False)
    for species, avg_price in species_avg.items():
        console.print(f"  {species}: ${avg_price:.2f}/MBF")


if __name__ == "__main__":
    main()
