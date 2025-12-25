"""Parse Minnesota Forest Resources reports for stumpage price data.

The MN DNR publishes annual Forest Resources reports that contain
stumpage price tables by species for pulpwood, pulp/bolts, and sawtimber.

Data sources:
- mn_forest_resources_2023.pdf - Contains 2013-2023 price data

Output: data/raw/mn_dnr/mn_stumpage_forest_resources.csv
"""

import pandas as pd
from pathlib import Path
from rich.console import Console
from rich.table import Table
import pdfplumber
import re

console = Console()

# Paths
RAW_DIR = Path("data/raw/mn_dnr")

# Price tables from the 2023 Forest Resources Report (pages 92-94)
# Extracted manually from PDF text since table extraction is messy

# Table 6-1: Pulpwood prices ($ per cord)
PULPWOOD_DATA = """
Species,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023
Aspen,24.99,30.62,36.08,34.26,34.33,32.09,28.55,30.07,30.73,33.00,34.55
Balm,20.56,24.8,27.68,24.29,30.56,25.55,25.59,23.60,26.25,25.31,30.80
Birch,8.44,9.89,12.02,13.77,11.33,10.65,10.14,8.92,8.82,9.76,10.20
Ash,6.62,6.82,6,8.07,6.69,7.19,6.32,5.94,6.75,7.46,8.07
Oak,15.44,13.1,14.63,17,16.61,20.61,17.19,13.14,15.02,14.19,19.09
Basswood,9.16,8.82,12.51,8.26,8.49,7.87,8.17,7.34,7.67,10.57,10.67
Mixed/Other Hardwoods,10.59,12.44,11.45,8.06,14.38,6.8,8.9,11.05,8.90,12.84,5.48
Balsam Fir,9.86,10.62,14.18,14.76,16.71,14.64,13.28,9.90,6.68,9.34,6.83
W. Spruce,17.57,16.55,19.09,17.25,23,20.9,19.88,14.48,13.22,12.20,10.67
B. Spruce,19.22,16.8,22.63,24.87,24.9,23.11,23.55,20.84,17.38,19.99,14.05
Tamarack,5.05,5.4,7.81,6.26,7.81,5.45,5.35,5.53,5.94,5.34,6.08
W. Cedar,7.86,5.3,6.41,6.8,5.2,5.47,4.97,5.72,5.39,5.48,6.13
Jack Pine,13.5,13.41,15.66,14.2,16,15.02,19.32,17.82,7.51,14.88,2.89
Red Pine,15.5,12.44,18.59,11.84,12.3,10.87,6.85,10.00,9.52,18.13,5.61
White Pine,13.01,16.56,12.78,15.91,8.44,7.31,9.87,5.57,5.99,10.65,5.29
Maple,9.91,9.82,10.13,12.31,10.47,11.26,10.19,10.38,9.96,11.68,10.95
"""

# Table 6-2: Prices of pulp and bolts Combined ($ per cord)
PULP_BOLTS_DATA = """
Species,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023
Aspen,0,36.16,44.24,46.49,39.24,56.73,0,37.54,0,37.68,37.72
Balm,0,0,0,66.8,0,0,0,31.82,42.60,34.54,33.21
Birch,15.17,15.31,17.98,18.11,20.35,16.76,16.9,18.74,17.28,16.76,15.84
Ash,15.81,11.59,14.66,12.55,13.47,12.06,10.56,11.37,10.32,11.15,9.66
Oak,22.2,23.62,27.01,31.71,28.72,28.57,27.63,29.31,29.63,27.49,29.06
Basswood,13.78,12.03,14.52,16.62,15.91,13.56,11.84,13.05,12.89,16.56,13.82
Mixed/Other Hardwoods,14.32,16.02,15.67,17.15,16.77,16.57,14.38,12.37,16.13,10.92,30.20
Balsam Fir,16.65,17.93,23.97,24.73,21.7,24.03,21.19,18.46,12.03,9.86,11.30
W. Spruce,25.48,29.57,25.73,27.63,32.82,26.99,27.22,26.4,19.62,28.11,24.03
B. Spruce,24.65,27.9,30.48,41.36,27.87,27.1,27.82,0,28.23,32.19,25.77
Tamarack,12.75,15.54,13.87,0,15.31,9.82,7.9,10.4,7.27,10.03,9.54
W. Cedar,0,13.04,0,12.07,12.75,8.77,9.18,21.25,10.77,16.02,9.08
Jack Pine,27.31,32.06,30.88,34.03,32.19,28.63,27.73,25.61,24.78,30.30,28.96
Red Pine,40.48,43.09,43.78,37.71,39.73,40.3,38.64,36.93,39.81,46.97,46.08
White Pine,36.9,24.95,39.21,28.7,16.68,26.62,30.16,29.77,33.24,36.96,42.27
Maple,13.76,13.57,18.11,17.82,16.19,16.21,16.78,13.84,16.22,15.29,14.12
"""

# Table 6-3: Sawtimber prices ($ per thousand board feet)
SAWTIMBER_DATA = """
Species,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023
Aspen,53.12,0,0,0,0,0,72,0,0,0,33.60
Balm,0,0,0,0,0,0,0,0,0,0,0
Birch,36.97,47.04,42.84,45.24,0,61.23,53.33,51.69,80.54,97.38,53.44
Ash,34.06,73.41,54.17,97.67,72.2,196.37,149.81,61.14,89.96,31.32,55.03
Elm,41.41,42.19,42.5,42.54,39.77,54.75,54.07,72.91,43.99,54.38,29.05
Oak,274.5,411.3,265.5,299.03,195.16,194.63,213.2,161.13,108.64,209.85,145.48
Basswood,54.44,68.87,59.24,80.4,104.38,69.55,59.18,75.34,76.32,84.19,55.85
Mixed/Other Hardwoods,28.56,65.4,47.87,47.04,50.28,47.3,78.78,67.78,72.59,51.25,94.28
Balsam Fir,66.51,0,0,0,0,0,0,0,0,0,0
W. Spruce,87.57,61.12,74.68,73.59,67.58,76.14,83.77,82.53,96.89,59.63,25.32
B. Spruce,0,0,0,0,0,0,0,78.32,0,82.60,25.62
Tamarack,0,0,0,0,0,0,0,0,0,0,0
W. Cedar,0,0,0,0,0,0,0,0,0,0,0
Jack Pine,112,89.56,0,118.77,139.76,109.56,109.34,105.86,103.91,29.91,15.89
Red Pine,127.1,148.3,177.2,133.22,142.72,144.41,143.27,128.1,149.11,166.15,145.56
White Pine,112.8,121.3,88.92,117.5,82.28,127.44,100.32,109.9,109.09,104.12,94.18
Maple,70.92,406.7,126.7,168.5,153.04,95.21,0,94.29,110.28,93.32,76.02
"""


def parse_price_table(data: str, product_type: str, unit: str) -> pd.DataFrame:
    """Parse a price table from CSV-formatted string."""
    from io import StringIO

    df = pd.read_csv(StringIO(data.strip()))

    # Melt to long format
    years = [col for col in df.columns if col != 'Species']
    df_long = df.melt(
        id_vars=['Species'],
        value_vars=years,
        var_name='year',
        value_name='price'
    )

    # Clean up
    df_long['year'] = df_long['year'].astype(int)
    df_long['price'] = pd.to_numeric(df_long['price'], errors='coerce')

    # Remove zero/null prices
    df_long = df_long[df_long['price'] > 0]

    # Add metadata
    df_long['product_type'] = product_type
    df_long['unit'] = unit

    return df_long


def main():
    console.print("[bold]Parsing Minnesota Forest Resources stumpage price tables[/bold]\n")

    # Parse all three tables
    console.print("[blue]Parsing pulpwood prices...[/blue]")
    pulpwood = parse_price_table(PULPWOOD_DATA, 'pulpwood', '$/cord')
    console.print(f"  Extracted {len(pulpwood)} records")

    console.print("[blue]Parsing pulp and bolts prices...[/blue]")
    pulp_bolts = parse_price_table(PULP_BOLTS_DATA, 'pulp_bolts', '$/cord')
    console.print(f"  Extracted {len(pulp_bolts)} records")

    console.print("[blue]Parsing sawtimber prices...[/blue]")
    sawtimber = parse_price_table(SAWTIMBER_DATA, 'sawtimber', '$/MBF')
    console.print(f"  Extracted {len(sawtimber)} records")

    # Combine all data
    all_data = pd.concat([pulpwood, pulp_bolts, sawtimber], ignore_index=True)

    # Standardize species names
    species_map = {
        'Aspen': 'aspen',
        'Balm': 'balsam_poplar',
        'Birch': 'birch',
        'Ash': 'ash',
        'Oak': 'oak',
        'Basswood': 'basswood',
        'Mixed/Other Hardwoods': 'mixed_hardwood',
        'Balsam Fir': 'balsam_fir',
        'W. Spruce': 'white_spruce',
        'B. Spruce': 'black_spruce',
        'Tamarack': 'tamarack',
        'W. Cedar': 'white_cedar',
        'Jack Pine': 'jack_pine',
        'Red Pine': 'red_pine',
        'White Pine': 'white_pine',
        'Maple': 'maple',
        'Elm': 'elm',
    }
    all_data['species'] = all_data['Species'].map(species_map).fillna(all_data['Species'].str.lower())
    all_data = all_data.drop(columns=['Species'])

    # Reorder columns
    all_data = all_data[['year', 'species', 'product_type', 'price', 'unit']]

    # Sort
    all_data = all_data.sort_values(['year', 'species', 'product_type'])

    # Show summary
    table = Table(title="MN Forest Resources Price Data")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Total records", str(len(all_data)))
    table.add_row("Year range", f"{all_data['year'].min()} - {all_data['year'].max()}")
    table.add_row("Species", str(all_data['species'].nunique()))
    table.add_row("Product types", ", ".join(all_data['product_type'].unique()))
    console.print(table)

    # Save to CSV
    output_path = RAW_DIR / "mn_stumpage_forest_resources.csv"
    all_data.to_csv(output_path, index=False)
    console.print(f"\n[green]Saved to {output_path}[/green]")

    # Show year coverage
    console.print("\n[bold]Records by Year:[/bold]")
    year_counts = all_data.groupby('year').size()
    for year, count in year_counts.items():
        console.print(f"  {year}: {count} records")

    # Show new years (2022-2023) specifically
    console.print("\n[bold]New Data (2022-2023):[/bold]")
    new_data = all_data[all_data['year'] >= 2022]
    for year in [2022, 2023]:
        year_data = new_data[new_data['year'] == year]
        console.print(f"\n  {year}: {len(year_data)} records")
        for product in year_data['product_type'].unique():
            prod_data = year_data[year_data['product_type'] == product]
            avg_price = prod_data['price'].mean()
            console.print(f"    {product}: {len(prod_data)} species, avg ${avg_price:.2f}")


if __name__ == "__main__":
    main()
