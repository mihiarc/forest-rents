"""
Parse Tennessee Forest Products Bulletin PDFs to extract price data.

This script extracts timber price data from TN Forest Products Bulletins
and saves it to CSV format matching other state data.

Note: TN bulletins report DELIVERED prices, not stumpage prices.
Stumpage = Delivered - Harvest Cost - Haul Cost - Buyer Profit
"""

import re
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import pdfplumber
from rich.console import Console
from rich.progress import track
from rich.table import Table

console = Console()

# Define output directory
DATA_DIR = Path("/Users/mihiarc/landuse-model/forest-rents/data/raw/tn_forestry")
OUTPUT_FILE = DATA_DIR / "tn_stumpage_parsed.csv"


def extract_year_quarter(filename: str) -> tuple[int | None, int | None]:
    """
    Extract year and quarter from filename like '2017-1.pdf'.

    Args:
        filename: PDF filename

    Returns:
        tuple: (year, quarter) or (None, None) if not found
    """
    match = re.search(r'(\d{4})-(\d)', filename)
    if match:
        year = int(match.group(1))
        quarter = int(match.group(2))
        return year, quarter
    return None, None


def extract_price_from_text(text: str) -> float | None:
    """
    Extract numeric price from text like '$250/MBF' or '$8.5/ton'.

    Args:
        text: Text containing price

    Returns:
        float: Extracted price or None if not found
    """
    if not text:
        return None

    # Remove commas and extra spaces
    text = text.replace(',', '').strip()

    # Try to find dollar amount
    match = re.search(r'\$\s*(\d+\.?\d*)', text)
    if match:
        return float(match.group(1))

    return None


def parse_hardwood_table(page_text: str, year: int, quarter: int) -> List[Dict[str, Any]]:
    """
    Parse hardwood sawlog prices from bulletin page.

    Args:
        page_text: Text content of page
        year: Year of bulletin
        quarter: Quarter of bulletin

    Returns:
        list: List of price records
    """
    records = []

    # Look for regional hardwood pricing patterns
    # Example: "Red Oak Grade 1: $431 Grade 2: $334"

    # Define species to look for
    species_list = [
        'Red Oak', 'White Oak', 'Ash', 'Yellow Poplar',
        'Walnut', 'Cherry', 'Hard Maple', 'Hickory'
    ]

    # Define regions
    regions = ['Region I', 'Region II', 'Region III']

    for species in species_list:
        for region_idx, region in enumerate(regions, 1):
            # Try to find species and region combination
            pattern = f"{species}.*?{region}.*?Grade 1.*?\\$(\\d+\\.?\\d*)"
            match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)

            if match:
                price = float(match.group(1))
                records.append({
                    'year': year,
                    'quarter': quarter,
                    'region': region.lower().replace(' ', '_'),
                    'species': species,
                    'product_type': 'sawtimber',
                    'price_avg': price,
                    'price_low': None,
                    'price_high': None,
                    'unit': 'MBF',
                    'notes': 'Delivered price, Grade 1'
                })

    return records


def parse_pine_prices(page_text: str, year: int, quarter: int) -> List[Dict[str, Any]]:
    """
    Parse pine prices from bulletin page.

    Args:
        page_text: Text content of page
        year: Year of bulletin
        quarter: Quarter of bulletin

    Returns:
        list: List of price records
    """
    records = []

    # Look for pine sawtimber
    pine_saw_match = re.search(r'SY Pine.*?\$(\d+)/MBF', page_text, re.IGNORECASE)
    if pine_saw_match:
        records.append({
            'year': year,
            'quarter': quarter,
            'region': 'statewide',
            'species': 'Pine',
            'product_type': 'sawtimber',
            'price_avg': float(pine_saw_match.group(1)),
            'price_low': None,
            'price_high': None,
            'unit': 'MBF',
            'notes': 'Delivered price, Southern Yellow Pine'
        })

    # Look for pine pulpwood
    pine_pulp_match = re.search(r'Pine Pulpwood.*?\$(\d+\.?\d*)/ton', page_text, re.IGNORECASE | re.DOTALL)
    if pine_pulp_match:
        records.append({
            'year': year,
            'quarter': quarter,
            'region': 'statewide',
            'species': 'Pine',
            'product_type': 'pulpwood',
            'price_avg': float(pine_pulp_match.group(1)),
            'price_low': None,
            'price_high': None,
            'unit': 'ton',
            'notes': 'Delivered price'
        })

    # Look for chip-n-saw
    cns_match = re.search(r'CNS.*?\$(\d+\.?\d*)/ton', page_text, re.IGNORECASE)
    if cns_match:
        records.append({
            'year': year,
            'quarter': quarter,
            'region': 'statewide',
            'species': 'Pine',
            'product_type': 'chip-n-saw',
            'price_avg': float(cns_match.group(1)),
            'price_low': None,
            'price_high': None,
            'unit': 'ton',
            'notes': 'Delivered price'
        })

    return records


def parse_bulletin_pdf(pdf_path: Path) -> List[Dict[str, Any]]:
    """
    Parse a single bulletin PDF to extract price data.

    Args:
        pdf_path: Path to PDF file

    Returns:
        list: List of price records
    """
    filename = pdf_path.name
    year, quarter = extract_year_quarter(filename)

    if year is None or quarter is None:
        console.print(f"[yellow]Skipping {filename} - cannot parse date[/yellow]")
        return []

    all_records = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Concatenate all pages that might have price data
            price_pages_text = ""
            for page in pdf.pages:
                text = page.extract_text() or ""
                if any(keyword in text.lower() for keyword in ['price', 'delivered', 'sawlog', 'pulpwood']):
                    price_pages_text += "\n" + text

            # Parse hardwood prices
            hardwood_records = parse_hardwood_table(price_pages_text, year, quarter)
            all_records.extend(hardwood_records)

            # Parse pine prices
            pine_records = parse_pine_prices(price_pages_text, year, quarter)
            all_records.extend(pine_records)

    except Exception as e:
        console.print(f"[red]Error parsing {filename}:[/red] {e}")
        return []

    if all_records:
        console.print(f"[green]✓[/green] {filename}: {len(all_records)} records")
    else:
        console.print(f"[dim]{filename}: No price data found[/dim]")

    return all_records


def main():
    """Main execution function."""
    console.print("\n[bold cyan]Tennessee Forest Products Bulletin Parser[/bold cyan]\n")

    # Find all PDF files
    pdf_files = sorted([
        p for p in DATA_DIR.glob("*.pdf")
        if re.match(r'\d{4}-\d\.pdf', p.name)
    ])

    if not pdf_files:
        console.print("[red]No bulletin PDFs found in {DATA_DIR}[/red]")
        return

    console.print(f"[cyan]Found {len(pdf_files)} bulletin PDFs to parse[/cyan]\n")

    # Parse all PDFs
    all_records = []
    for pdf_path in track(pdf_files, description="Parsing bulletins..."):
        records = parse_bulletin_pdf(pdf_path)
        all_records.extend(records)

    if not all_records:
        console.print("\n[red]No price data extracted from bulletins[/red]")
        return

    # Create DataFrame
    df = pd.DataFrame(all_records)

    # Sort by year, quarter, region, species
    df = df.sort_values(['year', 'quarter', 'region', 'species', 'product_type'])

    # Save to CSV
    df.to_csv(OUTPUT_FILE, index=False)

    # Display summary
    console.print(f"\n[green]✓ Successfully parsed price data![/green]")
    console.print(f"[green]✓ Saved to:[/green] {OUTPUT_FILE}")
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Total records: {len(df)}")
    console.print(f"  Years: {df['year'].min()} - {df['year'].max()}")
    console.print(f"  Species: {', '.join(df['species'].unique())}")
    console.print(f"  Product types: {', '.join(df['product_type'].unique())}")

    # Show sample data
    console.print("\n[bold]Sample data (first 20 rows):[/bold]")
    table = Table(show_header=True)
    for col in df.columns:
        table.add_column(col)

    for _, row in df.head(20).iterrows():
        table.add_row(*[str(v) for v in row])

    console.print(table)

    # Show data by year
    console.print("\n[bold]Records by year:[/bold]")
    year_counts = df.groupby('year').size()
    for year, count in year_counts.items():
        console.print(f"  {year}: {count} records")

    console.print(f"\n[yellow]Note:[/yellow] Tennessee bulletins report DELIVERED prices, not stumpage.")
    console.print("[yellow]Stumpage = Delivered - Harvest Cost - Haul Cost - Buyer Profit[/yellow]")


if __name__ == "__main__":
    main()
