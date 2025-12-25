"""
Parse Kentucky delivered log price data from PDF reports.

This script downloads and extracts delivered log price data from quarterly PDF
reports published by the Kentucky Division of Forestry.

IMPORTANT: These are DELIVERED log prices, not stumpage prices. Delivered prices
include harvesting and transportation costs, and are therefore higher than
stumpage prices (what landowners receive).

The data includes:
- Delivered log prices for various species groups
- Prices by 4 regions (Northeast, Northwest, Southeast, Southwest)
- Product types and grades
- Quarterly data from 2020-2025

Source: https://eec.ky.gov/Natural-Resources/Forestry/resource-utilization-and-marketing/Pages/default.aspx
"""

import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

import pandas as pd
import pdfplumber
import requests
from rich.console import Console
from rich.progress import track
from rich.table import Table as RichTable

console = Console()


def download_pdf(url: str, output_path: Path) -> bool:
    """Download a PDF from URL to output_path."""
    try:
        console.print(f"[dim]Downloading: {url}[/dim]")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/pdf,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        output_path.write_bytes(response.content)
        console.print(f"[green]Downloaded: {output_path.name}[/green]")
        return True
    except Exception as e:
        console.print(f"[red]Failed to download {url}: {e}[/red]")
        return False


def find_available_pdfs() -> List[Dict[str, any]]:
    """
    Return list of known Kentucky delivered log pricing PDFs.
    These were discovered by scraping the Kentucky forestry website.
    """
    base_url = "https://eec.ky.gov/Natural-Resources/Forestry/resource-utilization-and-marketing/Documents/"

    pdfs = [
        {
            'year': 2025,
            'quarters': [1, 2],
            'url': base_url + "2025%20KENTUCKY%20DELIVERED%20LOG%20PRICING%201st%20%202nd%20QUARTER_.pdf",
            'filename': "ky_forestry_2025_q1_q2.pdf"
        },
        {
            'year': 2024,
            'quarters': [4],
            'url': base_url + "2024%20KENTUCKY%20DELIVERED%20LOG%20PRICING%204th%20QUARTER.pdf",
            'filename': "ky_forestry_2024_q4.pdf"
        },
        {
            'year': 2024,
            'quarters': [3],
            'url': base_url + "2024%20KENTUCKY%20DELIVERED%20LOG%20PRICING%203rd%20QUARTER.pdf",
            'filename': "ky_forestry_2024_q3.pdf"
        },
        {
            'year': 2024,
            'quarters': [1, 2],
            'url': base_url + "2024%20KENTUCKY%20DELIVERED%20LOG%20PRICING%201%262%20QUARTER%20.pdf",
            'filename': "ky_forestry_2024_q1_q2.pdf"
        },
    ]

    return pdfs


def reverse_text(text: str) -> str:
    """Reverse text that appears backwards in PDF."""
    return text[::-1] if text else text


def parse_ky_forestry_pdf(pdf_path: Path, year: int, quarters: List[int]) -> List[Dict]:
    """
    Parse a Kentucky forestry PDF and extract delivered log price data.

    The PDFs have data organized by region (1-4) with multiple species and product
    types. Headers are sometimes reversed in the PDF text.

    Returns a list of dictionaries containing:
    - year, quarter, region, species, product_type, grade, price_avg, price_low,
      price_high, unit, notes
    """
    records = []

    # Column mapping - based on inspection of PDFs
    # The headers are rotated/reversed in the PDF, so we need to map them
    column_headers = [
        ('MBF High', 'Sawtimber', 'High', '$/MBF'),
        ('MBF Medium', 'Sawtimber', 'Medium', '$/MBF'),
        ('MBF Low', 'Sawtimber', 'Low', '$/MBF'),
        ('1/4 MBF High', 'Quarter Sawn', 'High', '$/MBF'),
        ('1/4 MBF Medium', 'Quarter Sawn', 'Medium', '$/MBF'),
        ('1/4 MBF Low', 'Quarter Sawn', 'Low', '$/MBF'),
        ('Veneer Low MBF', 'Veneer', 'Low', '$/MBF'),
        ('Veneer High MBF', 'Veneer', 'High', '$/MBF'),
        ('Stave High MBF', 'Stave', 'High', '$/MBF'),
        ('Stave Low MBF', 'Stave', 'Low', '$/MBF'),
        ('Sawn High Qtr MBF', 'Sawn Quarter', 'High', '$/MBF'),
        ('Sawn Low MBF', 'Sawn', 'Low', '$/MBF'),
        ('Tie-HWD High MBF', 'Tie', 'High', '$/MBF'),
        ('Tie-HWD Low MBF', 'Tie', 'Low', '$/MBF'),
        ('TIE Ton', 'Tie', 'All', '$/Ton'),
        ('Pallet MBF', 'Pallet', 'All', '$/MBF'),
        ('Pallet Ton', 'Pallet', 'All', '$/Ton'),
        ('Mat MBF', 'Mat', 'All', '$/MBF'),
        ('Fencing MBF', 'Fencing', 'All', '$/MBF'),
        ('Handle MBF', 'Handle', 'All', '$/MBF'),
        ('HWD Pulp Ton', 'Pulpwood', 'Hardwood', '$/Ton'),
        ('PINE Pulp Ton', 'Pulpwood', 'Pine', '$/Ton'),
        ('Chip Log Per MBF', 'Chip Log', 'All', '$/MBF'),
        ('Chip Log Ton', 'Chip Log', 'All', '$/Ton'),
        ('Peelers MBF', 'Peelers', 'All', '$/MBF'),
        ('Peelers Ton', 'Peelers', 'All', '$/Ton'),
    ]

    try:
        with pdfplumber.open(pdf_path) as pdf:
            console.print(f"[dim]  Pages in PDF: {len(pdf.pages)}[/dim]")

            # Pages 2-3 contain the data tables (Region 1-2 on page 2, Region 3-4 on page 3)
            for page_num in [1, 2]:  # 0-indexed, so pages 2 and 3
                if page_num >= len(pdf.pages):
                    continue

                page = pdf.pages[page_num]
                text = page.extract_text()

                if not text:
                    continue

                # Parse text line by line to extract data
                lines = text.strip().split('\n')
                current_region = None

                for i, line in enumerate(lines):
                    line = line.strip()

                    # Detect region headers
                    if line.startswith('Region '):
                        try:
                            region_num = int(line.split()[1])
                            current_region = f"Region {region_num}"
                            console.print(f"[dim]    Processing {current_region}[/dim]")
                        except:
                            pass
                        continue

                    # Skip header rows and empty lines
                    if not line or line.startswith('Species') or line.startswith('2024') or line.startswith('3rd'):
                        continue

                    # Skip rotated header text (contains backwards 'FBM', 'noT', etc.)
                    if "'FBM" in line or "'noT" in line or "'fbM" in line:
                        continue

                    # This should be a species data row
                    # Split by whitespace
                    parts = line.split()

                    if len(parts) < 2 or not current_region:
                        continue

                    # First part(s) are species name
                    # Remaining parts are prices
                    # Need to identify where species name ends and prices begin
                    species_name = []
                    prices = []

                    for part in parts:
                        # If it's a number, it's a price
                        if part.replace('.', '').replace(',', '').isdigit():
                            prices.append(part)
                        else:
                            # If we haven't started collecting prices yet, it's part of species name
                            if not prices:
                                species_name.append(part)

                    if not species_name or not prices:
                        continue

                    species = ' '.join(species_name)

                    # Parse prices and match to column headers
                    for price_idx, price_str in enumerate(prices):
                        if price_idx >= len(column_headers):
                            break

                        price = clean_price(price_str)
                        if price is None:
                            continue

                        col_name, product_type, grade, unit = column_headers[price_idx]

                        # Create record for each quarter in this report
                        for quarter in quarters:
                            records.append({
                                'year': year,
                                'quarter': quarter,
                                'region': current_region,
                                'species': species,
                                'product_type': product_type,
                                'grade': grade,
                                'price_avg': price,
                                'price_low': None,
                                'price_high': None,
                                'unit': unit,
                                'notes': 'Delivered price (not stumpage)'
                            })

    except Exception as e:
        console.print(f"[red]Error parsing {pdf_path.name}: {e}[/red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")

    return records


def clean_price(price_str: str) -> Optional[float]:
    """Clean price string and convert to float. Returns None for missing data."""
    if not price_str or price_str.strip() in ['*', '', '-', 'N/A', 'n/a']:
        return None
    # Remove dollar sign, commas, and whitespace
    cleaned = price_str.replace('$', '').replace(',', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def main():
    """Main function to download and parse Kentucky forestry PDFs."""
    data_dir = Path("/Users/mihiarc/landuse-model/forest-rents/data/raw/ky_forestry")
    data_dir.mkdir(parents=True, exist_ok=True)
    output_path = data_dir / "ky_stumpage_parsed.csv"

    console.print("\n[bold cyan]Kentucky Delivered Log Price Parser[/bold cyan]\n")
    console.print(f"[dim]Data directory: {data_dir}[/dim]")
    console.print(f"[dim]Output file: {output_path}[/dim]\n")

    # Get list of PDFs to try downloading
    potential_pdfs = find_available_pdfs()
    console.print(f"[yellow]Attempting to download {len(potential_pdfs)} potential PDFs...[/yellow]\n")

    # Download PDFs
    downloaded_pdfs = []
    for pdf_info in track(potential_pdfs, description="[cyan]Downloading PDFs...", console=console):
        pdf_path = data_dir / pdf_info['filename']

        # Skip if already downloaded
        if pdf_path.exists():
            console.print(f"[dim]  Already exists: {pdf_path.name}[/dim]")
            downloaded_pdfs.append((pdf_path, pdf_info['year'], pdf_info['quarters']))
            continue

        if download_pdf(pdf_info['url'], pdf_path):
            downloaded_pdfs.append((pdf_path, pdf_info['year'], pdf_info['quarters']))

    console.print(f"\n[green]Successfully downloaded {len(downloaded_pdfs)} PDFs[/green]\n")

    if not downloaded_pdfs:
        console.print("[red]No PDFs downloaded. Cannot proceed.[/red]")
        return

    # Parse all downloaded PDFs
    console.print("[bold]Analyzing PDF structure...[/bold]\n")
    all_records = []

    for pdf_path, year, quarters in downloaded_pdfs:
        console.print(f"[cyan]Parsing: {pdf_path.name}[/cyan]")
        try:
            records = parse_ky_forestry_pdf(pdf_path, year, quarters)
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

    # Show records by year/quarter
    year_quarter_table = RichTable(title="Records by Year/Quarter", show_header=True, header_style="bold magenta")
    year_quarter_table.add_column("Year", style="cyan")
    year_quarter_table.add_column("Quarter", style="yellow")
    year_quarter_table.add_column("Count", justify="right", style="green")

    for (year, quarter), group in df.groupby(['year', 'quarter']):
        year_quarter_table.add_row(str(year), f"Q{quarter}", f"{len(group):,}")

    console.print(year_quarter_table)
    console.print()

    # Show species breakdown
    species_table = RichTable(title="Top 10 Species by Record Count", show_header=True, header_style="bold magenta")
    species_table.add_column("Species", style="cyan")
    species_table.add_column("Count", justify="right", style="green")

    for species, count in df['species'].value_counts().head(10).items():
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
    console.print("[bold]Sample Data (first 15 rows):[/bold]\n")
    sample_table = RichTable(show_header=True, header_style="bold magenta")

    for col in ['year', 'quarter', 'region', 'species', 'product_type', 'grade', 'price_avg', 'unit']:
        sample_table.add_column(col, overflow="fold")

    for _, row in df.head(15).iterrows():
        sample_table.add_row(*[str(row[col]) for col in ['year', 'quarter', 'region', 'species', 'product_type', 'grade', 'price_avg', 'unit']])

    console.print(sample_table)
    console.print()

    # Show some price statistics
    console.print("[bold]Price Statistics by Product Type (Top 10):[/bold]\n")
    stats_table = RichTable(show_header=True, header_style="bold magenta")
    stats_table.add_column("Product Type", style="cyan")
    stats_table.add_column("Grade", style="yellow")
    stats_table.add_column("Unit", style="dim")
    stats_table.add_column("Mean", justify="right", style="green")
    stats_table.add_column("Min", justify="right", style="blue")
    stats_table.add_column("Max", justify="right", style="red")
    stats_table.add_column("Count", justify="right", style="dim")

    count = 0
    for (product, grade, unit), group in df.groupby(['product_type', 'grade', 'unit']):
        if count >= 10:
            break
        stats = group['price_avg'].describe()
        stats_table.add_row(
            product,
            grade,
            unit,
            f"${stats['mean']:.2f}",
            f"${stats['min']:.2f}",
            f"${stats['max']:.2f}",
            f"{int(stats['count']):,}"
        )
        count += 1

    console.print(stats_table)
    console.print()

    console.print("[bold yellow]IMPORTANT NOTE:[/bold yellow]")
    console.print("[yellow]These are DELIVERED log prices, not stumpage prices.[/yellow]")
    console.print("[yellow]Delivered prices include harvesting and transportation costs.[/yellow]")
    console.print("[yellow]Stumpage prices (what landowners receive) are typically 30-50% lower.[/yellow]\n")


if __name__ == "__main__":
    main()
