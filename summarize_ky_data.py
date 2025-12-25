"""
Generate a comprehensive summary of the parsed Kentucky delivered log price data.
"""

import pandas as pd
from pathlib import Path
from rich.console import Console
from rich.table import Table as RichTable

console = Console()

# Read the parsed data
csv_path = Path("/Users/mihiarc/landuse-model/forest-rents/data/raw/ky_forestry/ky_stumpage_parsed.csv")
df = pd.read_csv(csv_path)

console.print("\n[bold cyan]Kentucky Delivered Log Price Data Summary[/bold cyan]\n")
console.print(f"[dim]Data file: {csv_path}[/dim]\n")

# Overall statistics
console.print("[bold]Dataset Overview:[/bold]\n")
overview = RichTable(show_header=True, header_style="bold magenta")
overview.add_column("Metric", style="cyan")
overview.add_column("Value", style="green")

overview.add_row("Total Records", f"{len(df):,}")
overview.add_row("File Size", f"{csv_path.stat().st_size / 1024:.1f} KB")
overview.add_row("Date Range", f"{df['year'].min()}-Q{df['quarter'].min()} to {df['year'].max()}-Q{df['quarter'].max()}")
overview.add_row("Unique Years", str(df['year'].nunique()))
overview.add_row("Unique Quarters", str(df['quarter'].nunique()))
overview.add_row("Unique Regions", str(df['region'].nunique()))
overview.add_row("Unique Species", str(df['species'].nunique()))
overview.add_row("Unique Product Types", str(df['product_type'].nunique()))
overview.add_row("Unique Grades", str(df['grade'].nunique()))

console.print(overview)
console.print()

# Year/Quarter breakdown
console.print("[bold]Records by Year/Quarter:[/bold]\n")
yq_table = RichTable(show_header=True, header_style="bold magenta")
yq_table.add_column("Year", style="cyan")
yq_table.add_column("Quarter", style="yellow")
yq_table.add_column("Records", justify="right", style="green")
yq_table.add_column("Regions", justify="right", style="blue")
yq_table.add_column("Species", justify="right", style="magenta")

for (year, quarter), group in df.groupby(['year', 'quarter']):
    yq_table.add_row(
        str(year),
        f"Q{quarter}",
        f"{len(group):,}",
        str(group['region'].nunique()),
        str(group['species'].nunique())
    )

console.print(yq_table)
console.print()

# Species list
console.print("[bold]All Species (sorted by record count):[/bold]\n")
species_table = RichTable(show_header=True, header_style="bold magenta")
species_table.add_column("Rank", justify="right", style="dim")
species_table.add_column("Species", style="cyan")
species_table.add_column("Records", justify="right", style="green")
species_table.add_column("Avg Price ($/MBF)", justify="right", style="yellow")
species_table.add_column("Max Price ($/MBF)", justify="right", style="red")

for rank, (species, count) in enumerate(df['species'].value_counts().items(), 1):
    species_df = df[df['species'] == species]
    avg_price = species_df['price_avg'].mean()
    max_price = species_df['price_avg'].max()
    species_table.add_row(
        str(rank),
        species,
        f"{count:,}",
        f"${avg_price:.0f}",
        f"${max_price:.0f}"
    )

console.print(species_table)
console.print()

# Product type and grade breakdown
console.print("[bold]Product Types and Grades:[/bold]\n")
product_table = RichTable(show_header=True, header_style="bold magenta")
product_table.add_column("Product Type", style="cyan")
product_table.add_column("Grade", style="yellow")
product_table.add_column("Records", justify="right", style="green")
product_table.add_column("Avg Price", justify="right", style="blue")
product_table.add_column("Price Range", style="magenta")

for (product, grade), group in df.groupby(['product_type', 'grade']):
    avg_price = group['price_avg'].mean()
    min_price = group['price_avg'].min()
    max_price = group['price_avg'].max()
    product_table.add_row(
        product,
        grade,
        f"{len(group):,}",
        f"${avg_price:.0f}",
        f"${min_price:.0f} - ${max_price:.0f}"
    )

console.print(product_table)
console.print()

# Regional comparison
console.print("[bold]Regional Price Comparison (Average across all species/products):[/bold]\n")
region_table = RichTable(show_header=True, header_style="bold magenta")
region_table.add_column("Region", style="cyan")
region_table.add_column("Records", justify="right", style="green")
region_table.add_column("Species Count", justify="right", style="yellow")
region_table.add_column("Avg Price ($/MBF)", justify="right", style="blue")
region_table.add_column("Price Range", style="magenta")

for region in sorted(df['region'].unique()):
    region_df = df[df['region'] == region]
    avg_price = region_df['price_avg'].mean()
    min_price = region_df['price_avg'].min()
    max_price = region_df['price_avg'].max()
    species_count = region_df['species'].nunique()
    region_table.add_row(
        region,
        f"{len(region_df):,}",
        str(species_count),
        f"${avg_price:.0f}",
        f"${min_price:.0f} - ${max_price:.0f}"
    )

console.print(region_table)
console.print()

# High-value species
console.print("[bold]Top 10 Highest Average Prices by Species/Product/Grade:[/bold]\n")
high_value = RichTable(show_header=True, header_style="bold magenta")
high_value.add_column("Species", style="cyan")
high_value.add_column("Product", style="yellow")
high_value.add_column("Grade", style="blue")
high_value.add_column("Avg Price", justify="right", style="green")
high_value.add_column("Region", style="magenta")
high_value.add_column("Unit", style="dim")

# Get top prices
top_prices = df.groupby(['species', 'product_type', 'grade', 'region', 'unit'])['price_avg'].mean()
top_prices = top_prices.sort_values(ascending=False).head(10)

for (species, product, grade, region, unit), price in top_prices.items():
    high_value.add_row(species, product, grade, f"${price:.0f}", region, unit)

console.print(high_value)
console.print()

# Sample data
console.print("[bold]Sample Data (first 10 rows):[/bold]\n")
sample = RichTable(show_header=True, header_style="bold magenta")
sample.add_column("Year", style="cyan", width=4)
sample.add_column("Q", style="yellow", width=2)
sample.add_column("Region", style="blue", width=8)
sample.add_column("Species", style="green", width=12)
sample.add_column("Product", style="magenta", width=10)
sample.add_column("Grade", style="cyan", width=6)
sample.add_column("Price", justify="right", style="green", width=8)
sample.add_column("Unit", style="dim", width=6)

for _, row in df.head(10).iterrows():
    sample.add_row(
        str(row['year']),
        f"Q{row['quarter']}",
        row['region'],
        row['species'],
        row['product_type'],
        row['grade'],
        f"${row['price_avg']:.0f}",
        row['unit']
    )

console.print(sample)
console.print()

console.print("[bold yellow]CRITICAL NOTES:[/bold yellow]")
console.print("[yellow]1. These are DELIVERED log prices, NOT stumpage prices[/yellow]")
console.print("[yellow]2. Delivered prices include harvesting and transportation costs[/yellow]")
console.print("[yellow]3. Stumpage prices are typically 30-50% LOWER than delivered prices[/yellow]")
console.print("[yellow]4. Use these prices with caution for stumpage estimation[/yellow]\n")

console.print("[bold green]Data extraction complete![/bold green]")
console.print(f"[green]Parsed data saved to: {csv_path}[/green]\n")
