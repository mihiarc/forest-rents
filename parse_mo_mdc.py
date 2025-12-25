"""Parse Missouri MDC stumpage price data into unified schema."""

import pandas as pd
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

# Define paths
data_dir = Path("/Users/mihiarc/landuse-model/forest-rents/data/raw/mo_mdc")
input_file = data_dir / "qryPastPricesForResearchWeb20251002.csv"
output_file = data_dir / "mo_stumpage_parsed.csv"

# Read the raw CSV
console.print(f"[blue]Reading data from {input_file}[/blue]")
raw_data = pd.read_csv(input_file)

console.print(f"[green]Successfully loaded {len(raw_data)} records[/green]")
console.print(f"[yellow]Columns: {list(raw_data.columns)}[/yellow]")

# Function to clean price values
def clean_price(price_str):
    """Remove dollar signs and convert to float."""
    if pd.isna(price_str):
        return None
    if isinstance(price_str, (int, float)):
        return float(price_str)
    # Remove dollar sign and commas, then convert to float
    cleaned = str(price_str).replace('$', '').replace(',', '')
    try:
        return float(cleaned)
    except ValueError:
        return None

# Parse data into unified schema
parsed_records = []

for _, row in raw_data.iterrows():
    record = {
        'year': int(row['Year']),
        'quarter': int(row['Quarter']),
        'region': row['Region'],
        'species': row['Species'],
        'product_type': row['Product'],
        'price_avg': clean_price(row['Avg Price']),
        'price_low': clean_price(row['Min Price']),
        'price_high': clean_price(row['Max Price']),
        'unit': row['Units']
    }
    parsed_records.append(record)

# Create DataFrame from parsed records
parsed_df = pd.DataFrame(parsed_records)

# Save to CSV
console.print(f"[blue]Saving parsed data to {output_file}[/blue]")
parsed_df.to_csv(output_file, index=False)

# Generate summary statistics
console.print("\n[bold green]Summary Statistics[/bold green]")
console.print(f"Total records extracted: {len(parsed_df)}")
console.print(f"Year range: {parsed_df['year'].min()} - {parsed_df['year'].max()}")
console.print(f"Unique regions: {parsed_df['region'].nunique()}")
console.print(f"Unique species: {parsed_df['species'].nunique()}")
console.print(f"Unique product types: {parsed_df['product_type'].nunique()}")

# Display value counts for key columns
console.print("\n[bold cyan]Product Types:[/bold cyan]")
for product, count in parsed_df['product_type'].value_counts().items():
    console.print(f"  {product}: {count}")

console.print("\n[bold cyan]Top 10 Species by Record Count:[/bold cyan]")
for species, count in parsed_df['species'].value_counts().head(10).items():
    console.print(f"  {species}: {count}")

# Display sample data
console.print("\n[bold magenta]Sample Data (First 10 Records):[/bold magenta]")
table = Table(show_header=True, header_style="bold")
table.add_column("Year", style="cyan")
table.add_column("Q", style="cyan")
table.add_column("Region", style="yellow")
table.add_column("Species", style="green")
table.add_column("Product", style="blue")
table.add_column("Avg Price", style="magenta")
table.add_column("Unit", style="white")

for _, row in parsed_df.head(10).iterrows():
    table.add_row(
        str(row['year']),
        str(row['quarter']),
        str(row['region'])[:15],
        str(row['species'])[:20],
        str(row['product_type'])[:15],
        f"${row['price_avg']:.2f}",
        str(row['unit'])
    )

console.print(table)

# Display price statistics
console.print("\n[bold yellow]Price Statistics:[/bold yellow]")
console.print(f"  Average price (mean): ${parsed_df['price_avg'].mean():.2f}")
console.print(f"  Average price (median): ${parsed_df['price_avg'].median():.2f}")
console.print(f"  Minimum average price: ${parsed_df['price_avg'].min():.2f}")
console.print(f"  Maximum average price: ${parsed_df['price_avg'].max():.2f}")

console.print("\n[bold green]Parsing complete! ✓[/bold green]")
