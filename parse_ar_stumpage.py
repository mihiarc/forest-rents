"""
Parse Arkansas Extension stumpage price data from PDF files.

This script handles two different PDF formats:
1. Old format (2005-2014): Two-page PDFs with tables on page 2 showing North/South Arkansas regions
2. New format (2015-2025): One-page PDFs with statewide averages extracted from text

Output: CSV file with columns:
- year, quarter, region, species, product_type, price_avg, price_low, price_high, unit
"""

import re
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd
import pdfplumber
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table as RichTable

console = Console()


def extract_year_quarter_from_filename(filename: str) -> tuple[int, int]:
    """
    Extract year and quarter from filename.
    Example: ar_timber_2005_q1.pdf -> (2005, 1)
    """
    parts = filename.split("_")
    year = int(parts[2])
    quarter = int(parts[3].replace("q", "").replace(".pdf", ""))
    return year, quarter


def parse_old_format_table(table_data: list, year: int, quarter: int, region: str) -> List[Dict]:
    """
    Parse old format tables (2005-2014) with separate North/South Arkansas tables.

    Expected structure:
    Row 0-3: Header rows
    Row 4: Column headers (Product, Price, DBH, Price Change, Percent Change)
    Row 5+: Data rows
    """
    records = []

    if not table_data or len(table_data) < 5:
        return records

    # Find the header row with "Product"
    header_row_idx = None
    for idx, row in enumerate(table_data):
        if row and any("Product" in str(cell) for cell in row if cell):
            header_row_idx = idx
            break

    if header_row_idx is None:
        return records

    # Parse data rows starting after header
    for row in table_data[header_row_idx + 1:]:
        if not row or len(row) < 2:
            continue

        product = str(row[0]).strip() if row[0] else ""

        # Skip empty rows or rows without product names
        if not product or product == "":
            continue

        # Extract price (column 1)
        price_str = str(row[1]).strip() if len(row) > 1 and row[1] else ""
        price = None

        if price_str:
            # Remove $ and convert to float
            price_clean = price_str.replace("$", "").replace(",", "").strip()
            try:
                price = float(price_clean)
            except (ValueError, AttributeError):
                continue

        if price is None:
            continue

        # Parse product name to extract species and product type
        product_lower = product.lower()

        if "pine" in product_lower:
            species = "Pine"
        elif "hardwood" in product_lower:
            species = "Hardwood"
        else:
            species = "Unknown"

        if "pulpwood" in product_lower:
            product_type = "Pulpwood"
        elif "chip-n-saw" in product_lower or "chip n saw" in product_lower or "cns" in product_lower:
            product_type = "Chip-n-Saw"
        elif "sawtimber" in product_lower:
            product_type = "Sawtimber"
        else:
            product_type = "Unknown"

        records.append({
            "year": year,
            "quarter": quarter,
            "region": region,
            "species": species,
            "product_type": product_type,
            "price_avg": price,
            "price_low": None,
            "price_high": None,
            "unit": "$/ton"
        })

    return records


def parse_old_format_pdf(pdf_path: Path, year: int, quarter: int) -> List[Dict]:
    """
    Parse old format PDFs (2005-2014) with regional tables.
    """
    records = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) < 2:
                return records

            # Page 2 (index 1) has the price tables
            page = pdf.pages[1]
            tables = page.extract_tables()

            for table_data in tables:
                if not table_data or len(table_data) < 5:
                    continue

                # Check if this is a North Arkansas or South Arkansas table
                table_str = " ".join([str(cell) for row in table_data[:4] for cell in row if cell])

                if "North Arkansas" in table_str:
                    region = "North Arkansas"
                    records.extend(parse_old_format_table(table_data, year, quarter, region))
                elif "South Arkansas" in table_str:
                    region = "South Arkansas"
                    records.extend(parse_old_format_table(table_data, year, quarter, region))

    except Exception as e:
        console.print(f"[red]Error parsing {pdf_path.name}: {e}[/red]")

    return records


def parse_new_format_pdf(pdf_path: Path, year: int, quarter: int) -> List[Dict]:
    """
    Parse new format PDFs (2015-2025) with statewide averages in text.

    Expected text format:
    Product Price Change
    Pine Sawtimber $ 24.00 -4.2%
    Oak Sawtimber $ 51.00 -2.7%
    etc.

    Or for 2025+ format:
    PRODUCT State Average ...
    PINE SAWTIMBER $23.60 ...
    PINE CHIP-N-SAW $13.74 ...
    etc.
    """
    records = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) < 1:
                return records

            # Extract text from first page
            text = pdf.pages[0].extract_text()

            if not text:
                return records

            # Look for price table in text
            lines = text.split("\n")

            # Find the section with prices
            in_price_section = False
            pending_product = None  # For handling multi-line product names

            for idx, line in enumerate(lines):
                line = line.strip()

                # Detect start of price section (handles both formats)
                if ("Stumpage Prices" in line and "$/ton" in line) or "PRODUCT State Average" in line:
                    in_price_section = True
                    continue

                # Detect end of price section
                if in_price_section and ("Time Series" in line or "Trends:" in line or "Figure" in line or "Average Q" in line or "Timber Specifications" in line):
                    break

                if in_price_section and line:
                    # Skip header-like lines
                    if "Product Price" in line or "Current Quarter" in line or "Quarter" in line:
                        continue

                    # Check if this line is just a product type continuation (e.g., "SAWTIMBER" on its own)
                    if pending_product and line.upper() in ["SAWTIMBER", "PULPWOOD", "CHIP-N-SAW", "CHIP N SAW"]:
                        # This is a continuation line - look for the price in the next line
                        continue

                    # Parse product line - handle both formats
                    # Format 1: Product $ Price Change%
                    # e.g., "Pine Sawtimber $ 24.00 -4.2%"
                    # Format 2: PRODUCT $Price ...
                    # e.g., "PINE SAWTIMBER $23.60 $25.23 ($1.63) $23.01 $0.59"
                    # Format 3: Multi-line - "MIXED HARDWOOD $40.93 ..." on line 1, "SAWTIMBER" on line 2

                    # Try to extract product and price
                    match = re.match(r'([A-Z\s]+?)\s+\$\s*(\d+\.?\d*)', line, re.IGNORECASE)

                    if match:
                        product = match.group(1).strip()
                        price = float(match.group(2))

                        # Check if next line might be a continuation (product type)
                        product_type_from_next_line = None
                        if idx + 1 < len(lines):
                            next_line = lines[idx + 1].strip().upper()
                            if next_line in ["SAWTIMBER", "PULPWOOD", "CHIP-N-SAW", "CHIP N SAW"]:
                                product_type_from_next_line = next_line

                        # Parse product name - check product type first, then species
                        product_lower = product.lower()

                        # Determine product type
                        if "pulpwood" in product_lower:
                            product_type = "Pulpwood"
                        elif "chip-n-saw" in product_lower or "chip n saw" in product_lower or "chip n-saw" in product_lower:
                            product_type = "Chip-n-Saw"
                        elif "sawtimber" in product_lower:
                            product_type = "Sawtimber"
                        elif product_type_from_next_line:
                            # Use the next line as product type
                            if "SAWTIMBER" in product_type_from_next_line:
                                product_type = "Sawtimber"
                            elif "PULPWOOD" in product_type_from_next_line:
                                product_type = "Pulpwood"
                            elif "CHIP" in product_type_from_next_line:
                                product_type = "Chip-n-Saw"
                            else:
                                product_type = "Unknown"
                            pending_product = product
                        else:
                            product_type = "Unknown"

                        # Determine species (check for specific patterns)
                        if "mixed hardwood" in product_lower or "mixed hdwd" in product_lower:
                            species = "Mixed Hardwood"
                        elif "oak" in product_lower:
                            species = "Oak"
                        elif "hardwood" in product_lower or "hdwd" in product_lower:
                            species = "Hardwood"
                        elif "pine" in product_lower:
                            species = "Pine"
                        else:
                            species = "Unknown"

                        records.append({
                            "year": year,
                            "quarter": quarter,
                            "region": "Statewide",
                            "species": species,
                            "product_type": product_type,
                            "price_avg": price,
                            "price_low": None,
                            "price_high": None,
                            "unit": "$/ton"
                        })

    except Exception as e:
        console.print(f"[red]Error parsing {pdf_path.name}: {e}[/red]")

    return records


def parse_all_pdfs(pdf_dir: Path) -> pd.DataFrame:
    """
    Parse all PDF files and return a DataFrame.
    """
    all_records = []
    pdf_files = sorted(pdf_dir.glob("ar_timber_*.pdf"))

    console.print(f"\n[bold blue]Parsing {len(pdf_files)} PDF files...[/bold blue]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Processing PDFs...", total=len(pdf_files))

        for pdf_path in pdf_files:
            year, quarter = extract_year_quarter_from_filename(pdf_path.name)

            progress.update(task, description=f"Processing {pdf_path.name}")

            # Determine format based on year
            if year <= 2014:
                # Old format with regional tables
                records = parse_old_format_pdf(pdf_path, year, quarter)
            else:
                # New format with statewide text
                records = parse_new_format_pdf(pdf_path, year, quarter)

            if records:
                all_records.extend(records)
                console.print(f"[green]✓[/green] {pdf_path.name}: {len(records)} records")
            else:
                console.print(f"[yellow]⚠[/yellow] {pdf_path.name}: No data extracted")

            progress.advance(task)

    # Create DataFrame
    df = pd.DataFrame(all_records)

    return df


def main():
    """Main execution function."""
    pdf_dir = Path("/Users/mihiarc/landuse-model/forest-rents/data/raw/ar_extension/")
    output_path = pdf_dir / "ar_stumpage_parsed.csv"

    console.print("\n[bold cyan]Arkansas Extension Stumpage Price Parser[/bold cyan]")
    console.print(f"[dim]Input directory: {pdf_dir}[/dim]")
    console.print(f"[dim]Output file: {output_path}[/dim]\n")

    # Parse all PDFs
    df = parse_all_pdfs(pdf_dir)

    if df.empty:
        console.print("\n[red]No data extracted from PDFs![/red]")
        return

    # Save to CSV
    df.to_csv(output_path, index=False)
    console.print(f"\n[bold green]✓ Data saved to:[/bold green] {output_path}")

    # Display summary
    console.print(f"\n[bold yellow]Summary:[/bold yellow]")
    console.print(f"Total records: {len(df)}")
    console.print(f"Years: {df['year'].min()} - {df['year'].max()}")
    console.print(f"Quarters: {sorted(df['quarter'].unique())}")
    console.print(f"Regions: {sorted(df['region'].unique())}")
    console.print(f"Species: {sorted(df['species'].unique())}")
    console.print(f"Product types: {sorted(df['product_type'].unique())}")

    # Display sample data
    console.print(f"\n[bold yellow]Sample data (first 10 records):[/bold yellow]")

    sample_df = df.head(10)
    table = RichTable(show_header=True, header_style="bold cyan")

    for col in df.columns:
        table.add_column(col)

    for _, row in sample_df.iterrows():
        table.add_row(*[str(val) for val in row])

    console.print(table)

    # Display last 10 records
    console.print(f"\n[bold yellow]Sample data (last 10 records):[/bold yellow]")

    sample_df = df.tail(10)
    table = RichTable(show_header=True, header_style="bold cyan")

    for col in df.columns:
        table.add_column(col)

    for _, row in sample_df.iterrows():
        table.add_row(*[str(val) for val in row])

    console.print(table)


if __name__ == "__main__":
    main()
