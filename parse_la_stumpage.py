"""
Parse Louisiana Office of Forestry stumpage price data from PDF reports.

This script extracts stumpage price data from quarterly PDF reports published by
the Louisiana Department of Agriculture & Forestry, Office of Forestry.

The data includes:
- Sawtimber prices (Pine, Mixed Hardwood, Cypress) in $/MBF (thousand board feet)
- Poles prices in $/Ton
- Pulpwood prices (Pine, Mixed Hardwood, Cypress) in $/Standard Cord
- Chip-N-Saw prices in $/Standard Cord

Data is reported by region (Areas 1-5) and as state averages.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd
import pdfplumber
from rich.console import Console
from rich.progress import track
from rich.table import Table as RichTable

console = Console()


def extract_year_quarter(filename: str) -> tuple[int, int]:
    """Extract year and quarter from filename like 'la_forestry_2010_q1.pdf'."""
    match = re.search(r'(\d{4})_q(\d)', filename)
    if match:
        return int(match.group(1)), int(match.group(2))
    raise ValueError(f"Could not extract year/quarter from {filename}")


def clean_price(price_str: str) -> Optional[float]:
    """Clean price string and convert to float. Returns None for missing data."""
    if not price_str or price_str.strip() == '*' or price_str.strip() == '':
        return None
    # Remove dollar sign and commas
    cleaned = price_str.replace('$', '').replace(',', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_la_forestry_pdf(pdf_path: Path, year: int, quarter: int) -> List[Dict]:
    """
    Parse a Louisiana forestry PDF and extract stumpage price data.
    
    Returns a list of dictionaries containing:
    - year, quarter, region, species, product_type, price, unit
    """
    records = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Data is on page 2 (index 1)
            if len(pdf.pages) < 2:
                console.print(f"[yellow]Warning: {pdf_path.name} has only {len(pdf.pages)} page(s)[/yellow]")
                return records
            
            page = pdf.pages[1]
            tables = page.extract_tables()
            
            if not tables:
                console.print(f"[yellow]Warning: No tables found in {pdf_path.name}[/yellow]")
                return records
            
            table = tables[0]
            
            # Table structure:
            # Row 0: Headers (Products, Regional Values, ..., State Averages)
            # Row 1: Column headers (Area 1, Area 2, etc., Current Quarter, Previous Quarter, Year Ago)
            # Rows 2-10: Data rows
            
            # Expected row products (in order):
            # 2: Pine (sawtimber)
            # 3: Mixed Hardwood (sawtimber)
            # 4: Cypress (sawtimber)
            # 5: Poles
            # 6: Cordwood header row (skip)
            # 7: Pine Pulpwood
            # 8: Mixed Hardwood Pulpwood
            # 9: Cypress Pulpwood
            # 10: Chip-N-Saw
            
            # Define product mappings
            product_map = {
                2: ('Pine', 'Sawtimber', '$/MBF'),
                3: ('Mixed Hardwood', 'Sawtimber', '$/MBF'),
                4: ('Cypress', 'Sawtimber', '$/MBF'),
                5: ('Poles', 'Poles', '$/Ton'),
                7: ('Pine', 'Pulpwood', '$/Cord'),
                8: ('Mixed Hardwood', 'Pulpwood', '$/Cord'),
                9: ('Cypress', 'Pulpwood', '$/Cord'),
                10: ('Chip-N-Saw', 'Chip-N-Saw', '$/Cord'),
            }
            
            # Extract data for each product row
            for row_idx, (species, product_type, unit) in product_map.items():
                if row_idx >= len(table):
                    continue
                    
                row = table[row_idx]
                
                # Columns:
                # 0: Product name
                # 1-5: Area 1-5
                # 6: Current Quarter (state avg)
                # 7: Previous Quarter
                # 8: Year Ago
                
                # Extract regional prices (Areas 1-5)
                for area_idx in range(1, 6):
                    if area_idx < len(row):
                        price = clean_price(row[area_idx])
                        if price is not None:
                            records.append({
                                'year': year,
                                'quarter': quarter,
                                'region': f'Area {area_idx}',
                                'species': species,
                                'product_type': product_type,
                                'price': price,
                                'unit': unit,
                                'price_type': 'current',
                            })
                
                # Extract state average - current quarter (column 6)
                if len(row) > 6:
                    price = clean_price(row[6])
                    if price is not None:
                        records.append({
                            'year': year,
                            'quarter': quarter,
                            'region': 'State Average',
                            'species': species,
                            'product_type': product_type,
                            'price': price,
                            'unit': unit,
                            'price_type': 'current',
                        })
                
                # We could also extract previous quarter (column 7) and year ago (column 8)
                # but those are just historical comparisons already in our dataset
    
    except Exception as e:
        console.print(f"[red]Error parsing {pdf_path.name}: {e}[/red]")
    
    return records


def main():
    """Main function to parse all Louisiana forestry PDFs."""
    data_dir = Path("/Users/mihiarc/landuse-model/forest-rents/data/raw/la_forestry")
    output_path = data_dir / "la_stumpage_parsed.csv"
    
    console.print("\n[bold cyan]Louisiana Stumpage Price Parser[/bold cyan]\n")
    console.print(f"[dim]Data directory: {data_dir}[/dim]")
    console.print(f"[dim]Output file: {output_path}[/dim]\n")
    
    # Find all PDF files
    pdf_files = sorted(data_dir.glob("la_forestry_*.pdf"))
    console.print(f"[green]Found {len(pdf_files)} PDF files[/green]\n")
    
    # Parse all PDFs
    all_records = []
    
    for pdf_path in track(pdf_files, description="[cyan]Parsing PDFs...", console=console):
        try:
            year, quarter = extract_year_quarter(pdf_path.name)
            records = parse_la_forestry_pdf(pdf_path, year, quarter)
            all_records.extend(records)
        except Exception as e:
            console.print(f"[red]Error with {pdf_path.name}: {e}[/red]")
    
    # Convert to DataFrame
    df = pd.DataFrame(all_records)
    
    if df.empty:
        console.print("[red]No data extracted![/red]")
        return
    
    # Sort by year, quarter, region, species
    df = df.sort_values(['year', 'quarter', 'region', 'species', 'product_type'])
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    console.print(f"\n[bold green]Successfully saved {len(df)} records to {output_path}[/bold green]\n")
    
    # Print summary statistics
    console.print("[bold]Summary Statistics:[/bold]\n")
    
    summary_table = RichTable(title="Data Summary", show_header=True, header_style="bold magenta")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Total Records", f"{len(df):,}")
    summary_table.add_row("Date Range", f"{df['year'].min()}-Q{df['quarter'].min()} to {df['year'].max()}-Q{df['quarter'].max()}")
    summary_table.add_row("Unique Species", str(df['species'].nunique()))
    summary_table.add_row("Unique Product Types", str(df['product_type'].nunique()))
    summary_table.add_row("Regions", str(df['region'].nunique()))
    
    console.print(summary_table)
    console.print()
    
    # Show species breakdown
    species_table = RichTable(title="Records by Species", show_header=True, header_style="bold magenta")
    species_table.add_column("Species", style="cyan")
    species_table.add_column("Count", justify="right", style="green")
    
    for species, count in df['species'].value_counts().items():
        species_table.add_row(species, f"{count:,}")
    
    console.print(species_table)
    console.print()
    
    # Show product type breakdown
    product_table = RichTable(title="Records by Product Type", show_header=True, header_style="bold magenta")
    product_table.add_column("Product Type", style="cyan")
    product_table.add_column("Count", justify="right", style="green")
    
    for product, count in df['product_type'].value_counts().items():
        product_table.add_row(product, f"{count:,}")
    
    console.print(product_table)
    console.print()
    
    # Show sample data
    console.print("[bold]Sample Data (first 20 rows):[/bold]\n")
    sample_table = RichTable(show_header=True, header_style="bold magenta")
    
    for col in df.columns:
        sample_table.add_column(col, overflow="fold")
    
    for _, row in df.head(20).iterrows():
        sample_table.add_row(*[str(val) for val in row])
    
    console.print(sample_table)
    console.print()
    
    # Show some price statistics
    console.print("[bold]Price Statistics by Product Type:[/bold]\n")
    stats_table = RichTable(show_header=True, header_style="bold magenta")
    stats_table.add_column("Product Type", style="cyan")
    stats_table.add_column("Species", style="yellow")
    stats_table.add_column("Unit", style="dim")
    stats_table.add_column("Mean", justify="right", style="green")
    stats_table.add_column("Min", justify="right", style="blue")
    stats_table.add_column("Max", justify="right", style="red")
    stats_table.add_column("Count", justify="right", style="dim")
    
    for (product, species, unit), group in df.groupby(['product_type', 'species', 'unit']):
        stats = group['price'].describe()
        stats_table.add_row(
            product,
            species,
            unit,
            f"${stats['mean']:.2f}",
            f"${stats['min']:.2f}",
            f"${stats['max']:.2f}",
            f"{int(stats['count']):,}"
        )
    
    console.print(stats_table)
    console.print()


if __name__ == "__main__":
    main()
