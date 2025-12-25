#!/usr/bin/env python3
"""
Parse Mississippi Extension stumpage price data from quarterly PDF reports.

This script processes 45 quarterly PDF files (2013 Q1 - 2025 Q3) and extracts
stumpage prices for various timber products across different regions of Mississippi.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import pdfplumber
from rich.console import Console
from rich.progress import track

console = Console()


def extract_year_quarter(filename: str) -> tuple[int, int]:
    """
    Extract year and quarter from filename.

    Args:
        filename: Filename like 'ms_timber_2013_q1.pdf'

    Returns:
        Tuple of (year, quarter)
    """
    match = re.search(r'(\d{4})_q(\d)', filename)
    if match:
        year = int(match.group(1))
        quarter = int(match.group(2))
        return year, quarter
    raise ValueError(f"Could not extract year and quarter from {filename}")


def parse_early_format(text: str, year: int, quarter: int) -> List[Dict]:
    """
    Parse 2013-2014 format where prices are embedded in narrative text.

    Example text:
    "Pine Pulpwood increased $1.22/ton to end the quarter at $8.85/ton"
    """
    records = []

    # Patterns for different product types
    patterns = [
        # Pine Pulpwood increased $X/ton to end the quarter at $Y/ton
        (r'Pine Pulpwood.*?at \$(\d+\.?\d*)/ton', 'Pine', 'Pulpwood'),
        # Pine CNS ... at $Y/ton
        (r'Pine CNS.*?at \$(\d+\.?\d*)/ton', 'Pine', 'Chip-n-Saw'),
        # Pine Sawtimber ... at $Y/ton
        (r'Pine Sawtimber.*?at \$(\d+\.?\d*)/ton', 'Pine', 'Sawtimber'),
        # Hardwood Pulpwood ... at $Y/ton
        (r'Hardwood Pulpwood.*?at \$(\d+\.?\d*)/ton', 'Hardwood', 'Pulpwood'),
        # Low Grade Hardwood ... at $Y/ton
        (r'Low Grade Hardwood.*?at \$(\d+\.?\d*)/ton', 'Hardwood', 'Low Grade Sawtimber'),
        # High Grade Hardwood ... at $Y
        (r'High Grade Hardwood.*?at \$(\d+\.?\d*)', 'Hardwood', 'High Grade Sawtimber'),
        # Mixed Hardwood ... at $Y/ton
        (r'Mixed Hardwood.*?at \$(\d+\.?\d*)/ton', 'Hardwood', 'Mixed Sawtimber'),
    ]

    for pattern, species, product_type in patterns:
        match = re.search(pattern, text)
        if match:
            price = float(match.group(1))
            records.append({
                'year': year,
                'quarter': quarter,
                'region': 'Statewide',
                'species': species,
                'product_type': product_type,
                'price_avg': price,
                'price_low': None,
                'price_high': None,
                'unit': '$/ton'
            })

    return records


def parse_simple_format(text: str, year: int, quarter: int) -> List[Dict]:
    """
    Parse 2013-2019 format where prices are listed in simple lines.

    Example text:
    "Pine Sawtimber - $24, Pine Chip-N-Saw - $15, Pine Pulpwood - $8,"
    "Mixed Hardwood Sawtimber - $34, Hardwood Pulpwood - $12"
    """
    records = []

    # Pattern for product - price pairs (handles with or without dollar sign)
    pattern = r'(Pine|Mixed Hardwood|Hardwood|Oak)\s+(Sawtimber|Chip-N-Saw|Chip-n-Saw|Pulpwood|Poles|Plylogs)\s*-\s*\$?(\d+\.?\d*)'

    matches = re.finditer(pattern, text, re.IGNORECASE)

    for match in matches:
        species_raw = match.group(1)
        product_raw = match.group(2)
        price = float(match.group(3))

        # Normalize species
        if 'Pine' in species_raw:
            species = 'Pine'
        elif 'Mixed Hardwood' in species_raw:
            species = 'Hardwood'
            # Keep "Mixed Hardwood" in product name
            product_type = 'Mixed Hardwood ' + product_raw.replace('-N-', '-n-')
        elif 'Hardwood' in species_raw or 'Oak' in species_raw:
            species = 'Hardwood'
            # Normalize product type
            product_type = product_raw.replace('-N-', '-n-')
        else:
            species = species_raw
            product_type = product_raw.replace('-N-', '-n-')

        # For non-mixed hardwood, just use the product name
        if species == 'Pine':
            product_type = product_raw.replace('-N-', '-n-')
        elif 'Mixed' not in species_raw and species == 'Hardwood':
            product_type = product_raw.replace('-N-', '-n-')

        records.append({
            'year': year,
            'quarter': quarter,
            'region': 'Statewide',
            'species': species,
            'product_type': product_type,
            'price_avg': price,
            'price_low': None,
            'price_high': None,
            'unit': '$/ton'
        })

    return records


def parse_table_format(pdf, year: int, quarter: int) -> List[Dict]:
    """
    Parse 2020+ format with structured tables showing regional data.

    Tables have columns like:
    Region | Pine Poles | Pine Sawtimber | Pine Plylogs | Pine Chip-n-Saw | Pine Pulpwood | ...
    With rows for NW, NE, SW, SE showing Low/Average/High
    """
    records = []

    # Look for tables on page 2 (usually where price tables are)
    if len(pdf.pages) >= 2:
        page = pdf.pages[1]
        tables = page.extract_tables()

        if tables:
            # Process each table (Table 1 is usually Pine, Table 2 is Hardwood)
            for table in tables:
                if not table or len(table) < 2:
                    continue

                # Extract header row to identify columns
                # Headers might be split across multiple rows
                headers = []
                product_headers = []

                # Find product names in first few rows
                for row_idx in range(min(3, len(table))):
                    row = table[row_idx]
                    for cell in row:
                        if cell and any(prod in str(cell) for prod in ['Pine', 'Hardwood', 'Oak', 'Crossties']):
                            if 'Poles' in str(cell):
                                product_headers.append(('Pine', 'Poles'))
                            elif 'Sawtimber' in str(cell):
                                if 'Pine' in str(cell):
                                    product_headers.append(('Pine', 'Sawtimber'))
                                elif 'Oak' in str(cell):
                                    product_headers.append(('Hardwood', 'Oak Sawtimber'))
                                elif 'Mixed' in str(cell):
                                    product_headers.append(('Hardwood', 'Mixed Hardwood Sawtimber'))
                            elif 'Plylogs' in str(cell) or 'Plylog' in str(cell):
                                product_headers.append(('Pine', 'Plylogs'))
                            elif 'Chip-n-Saw' in str(cell) or 'Chip-\nn-Saw' in str(cell):
                                product_headers.append(('Pine', 'Chip-n-Saw'))
                            elif 'T-wood' in str(cell) or 'Twood' in str(cell):
                                product_headers.append(('Pine', 'T-wood'))
                            elif 'Topwood' in str(cell):
                                product_headers.append(('Pine', 'Topwood'))
                            elif 'Pulpwood' in str(cell):
                                if 'Pine' in str(cell):
                                    product_headers.append(('Pine', 'Pulpwood'))
                                elif 'Hardwood' in str(cell):
                                    product_headers.append(('Hardwood', 'Pulpwood'))
                            elif 'Crossties' in str(cell):
                                product_headers.append(('Hardwood', 'Crossties'))

                # Remove duplicates while preserving order
                seen = set()
                unique_headers = []
                for item in product_headers:
                    if item not in seen:
                        seen.add(item)
                        unique_headers.append(item)
                product_headers = unique_headers

                # Process data rows
                for row in table[2:]:  # Skip header rows
                    if not row or len(row) < 2:
                        continue

                    # Check if this is a region row (NW, NE, SW, SE, Statewide)
                    region = None
                    stat_type = None  # Low, Average, High

                    # Look for region in first few cells
                    for cell in row[:3]:
                        cell_str = str(cell).strip() if cell else ''
                        if cell_str in ['NW', 'NE', 'SW', 'SE', 'Statewide']:
                            region = cell_str
                        elif cell_str in ['Low', 'Average', 'High']:
                            stat_type = cell_str

                    if not region or not stat_type:
                        continue

                    # Extract prices from the row
                    # Price cells usually contain $ and numbers
                    price_cells = []
                    for cell in row:
                        cell_str = str(cell).strip() if cell else ''
                        if cell_str and ('$' in cell_str or cell_str.replace('.', '').isdigit()):
                            # Extract numeric value
                            price_match = re.search(r'\$?(\d+\.?\d*)', cell_str)
                            if price_match:
                                try:
                                    price_cells.append(float(price_match.group(1)))
                                except ValueError:
                                    price_cells.append(None)
                            else:
                                price_cells.append(None)
                        elif cell_str == 'IND' or cell_str == '':
                            price_cells.append(None)

                    # Match prices to products
                    # This is tricky because table structure varies
                    # We'll try to match based on position
                    for i, (species, product) in enumerate(product_headers):
                        # Try to find the price for this product
                        # Usually there are multiple columns per product (for different stats)
                        # We need to map column indices to products

                        # Simple heuristic: each product gets roughly equal column space
                        if i < len(price_cells):
                            price = price_cells[i]
                            if price is not None:
                                # Create record based on stat_type
                                key = (year, quarter, region, species, product)

                                # Find existing record or create new one
                                existing = None
                                for rec in records:
                                    if (rec['year'] == year and rec['quarter'] == quarter and
                                        rec['region'] == region and rec['species'] == species and
                                        rec['product_type'] == product):
                                        existing = rec
                                        break

                                if existing:
                                    if stat_type == 'Low':
                                        existing['price_low'] = price
                                    elif stat_type == 'Average':
                                        existing['price_avg'] = price
                                    elif stat_type == 'High':
                                        existing['price_high'] = price
                                else:
                                    new_rec = {
                                        'year': year,
                                        'quarter': quarter,
                                        'region': region,
                                        'species': species,
                                        'product_type': product,
                                        'price_avg': price if stat_type == 'Average' else None,
                                        'price_low': price if stat_type == 'Low' else None,
                                        'price_high': price if stat_type == 'High' else None,
                                        'unit': '$/ton'
                                    }
                                    records.append(new_rec)

    return records


def parse_table_format_v2(page_text: str, year: int, quarter: int) -> List[Dict]:
    """
    Alternative parser for 2018+ tables that extracts from text patterns.

    This looks for lines like:
    "NW Low IND $14.00 IND $6.00 IND $0.50 IND"
    "NW High IND $24.00 IND $14.00 $6.08"
    """
    records = []
    lines = page_text.split('\n')

    # Products in typical order for pine tables (2020+)
    pine_products_2020 = ['Poles', 'Sawtimber', 'Plylogs', 'Chip-n-Saw', 'T-wood', 'Pulpwood', 'Topwood']
    # Products for pine tables (2018-2019) - no T-wood, Topwood
    pine_products_2018 = ['Poles', 'Sawtimber', 'Plylogs', 'Chip-n-Saw', 'Pulpwood']
    # Products for hardwood tables
    hardwood_products = ['Oak Sawtimber', 'Mixed Hardwood Sawtimber', 'Pulpwood', 'Crossties']

    # Determine which product list to use based on year
    if year >= 2020:
        pine_products = pine_products_2020
    else:
        pine_products = pine_products_2018

    # Track which table we're in based on context
    current_table = None  # 'pine' or 'hardwood'

    for line in lines:
        # Detect table headers to know which species we're parsing
        if 'Table 1' in line or 'pine stumpage' in line.lower():
            current_table = 'pine'
        elif 'Table 2' in line or 'hardwood stumpage' in line.lower():
            current_table = 'hardwood'

        # Look for region patterns - handle multiple formats:
        # "NW Low IND $14.00 ..." or "NW Avg. IND $20.73 ..." or "Low $28.00 $8.00 ..."
        region_match = re.match(r'^\s*(NW|NE|SW|SE|Statewide)\s+(Low|Average|Avg\.|High)\s+(.+)$', line)
        if not region_match:
            # Try alternate pattern without region (statewide data only)
            region_match = re.match(r'^\s*(Low|Average|Avg\.|High)\s+(.+)$', line)
            if region_match:
                # This is a Low/Average/High line without region prefix - assume Statewide
                stat_type = region_match.group(1).replace('Avg.', 'Average')
                price_data = region_match.group(2)
                region = 'Statewide'
            else:
                continue
        else:
            region = region_match.group(1)
            stat_type = region_match.group(2).replace('Avg.', 'Average')
            price_data = region_match.group(3)

        # Extract all prices from the line
        prices = []
        tokens = price_data.split()
        for token in tokens:
            if token == 'IND' or token == '':
                prices.append(None)
            elif '$' in token:
                price_match = re.search(r'\$(\d+\.?\d*)', token)
                if price_match:
                    prices.append(float(price_match.group(1)))
            elif re.match(r'^\d+\.?\d*$', token):
                try:
                    prices.append(float(token))
                except ValueError:
                    pass

        # Determine species and products based on current_table or price count
        if current_table == 'pine':
            species = 'Pine'
            products = pine_products
        elif current_table == 'hardwood':
            species = 'Hardwood'
            products = hardwood_products
        elif len(prices) > 4:
            # Likely pine (more products)
            products = pine_products
            species = 'Pine'
        else:
            # Likely hardwood
            products = hardwood_products
            species = 'Hardwood'

        # Map prices to products
        for i, price in enumerate(prices):
            if i < len(products) and price is not None:
                product = products[i]

                # Find or create record
                key = (year, quarter, region, species, product)
                existing = None
                for rec in records:
                    if (rec['year'] == year and rec['quarter'] == quarter and
                        rec['region'] == region and rec['species'] == species and
                        rec['product_type'] == product):
                        existing = rec
                        break

                if existing:
                    if stat_type == 'Low':
                        existing['price_low'] = price
                    elif stat_type == 'Average':
                        existing['price_avg'] = price
                    elif stat_type == 'High':
                        existing['price_high'] = price
                else:
                    new_rec = {
                        'year': year,
                        'quarter': quarter,
                        'region': region,
                        'species': species,
                        'product_type': product,
                        'price_avg': price if stat_type == 'Average' else None,
                        'price_low': price if stat_type == 'Low' else None,
                        'price_high': price if stat_type == 'High' else None,
                        'unit': '$/ton'
                    }
                    records.append(new_rec)

    return records


def parse_pdf(pdf_path: Path) -> List[Dict]:
    """
    Parse a single PDF file and extract stumpage price data.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        List of dictionaries containing price records
    """
    year, quarter = extract_year_quarter(pdf_path.name)
    records = []

    with pdfplumber.open(pdf_path) as pdf:
        # Extract all text
        all_text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                all_text += page_text + "\n"

        # Determine format based on year
        if year <= 2014:
            # Try early narrative format first
            records = parse_early_format(all_text, year, quarter)
            # If that didn't work, try simple format (some 2013-2014 use this)
            if not records:
                records = parse_simple_format(all_text, year, quarter)
        elif year <= 2017:
            # Simple line format (2015-2017)
            records = parse_simple_format(all_text, year, quarter)
        else:
            # Table format (2018+)
            # Try text-based parser first
            records = parse_table_format_v2(all_text, year, quarter)

            # If we didn't get many records, try table parser
            if len(records) < 5:
                records = parse_table_format(pdf, year, quarter)

    return records


def main():
    """Main function to parse all Mississippi Extension PDFs."""
    console.print("\n[bold cyan]Mississippi Extension Stumpage Price Parser[/bold cyan]\n")

    # Setup paths
    data_dir = Path("/Users/mihiarc/landuse-model/forest-rents/data/raw/ms_extension")
    output_path = data_dir / "ms_stumpage_parsed.csv"

    # Find all PDF files
    pdf_files = sorted(data_dir.glob("ms_timber_*.pdf"))
    console.print(f"[bold]Found {len(pdf_files)} PDF files to process[/bold]\n")

    if not pdf_files:
        console.print("[red]No PDF files found![/red]")
        return

    # Parse all PDFs
    all_records = []
    errors = []

    for pdf_path in track(pdf_files, description="Parsing PDFs..."):
        try:
            records = parse_pdf(pdf_path)
            all_records.extend(records)
            if not records:
                errors.append(f"{pdf_path.name}: No records extracted")
        except Exception as e:
            errors.append(f"{pdf_path.name}: {str(e)}")
            console.print(f"[red]Error parsing {pdf_path.name}: {e}[/red]")

    # Create DataFrame
    df = pd.DataFrame(all_records)

    if df.empty:
        console.print("[red]No data extracted from any PDF![/red]")
        if errors:
            console.print("\n[yellow]Errors encountered:[/yellow]")
            for error in errors:
                console.print(f"  {error}")
        return

    # Sort by year, quarter, region, species, product
    df = df.sort_values(['year', 'quarter', 'region', 'species', 'product_type'])

    # Save to CSV
    df.to_csv(output_path, index=False)

    # Print summary
    console.print(f"\n[bold green]Successfully parsed {len(pdf_files)} PDFs[/bold green]")
    console.print(f"[bold]Total records extracted: {len(df)}[/bold]")
    console.print(f"[bold]Output saved to: {output_path}[/bold]\n")

    # Print statistics
    console.print("[bold cyan]Data Summary:[/bold cyan]")
    console.print(f"  Year range: {df['year'].min()} - {df['year'].max()}")
    console.print(f"  Regions: {', '.join(sorted(df['region'].unique()))}")
    console.print(f"  Species: {', '.join(sorted(df['species'].unique()))}")
    console.print(f"  Product types: {len(df['product_type'].unique())}")

    # Show product types
    console.print("\n[bold cyan]Product Types:[/bold cyan]")
    for species in sorted(df['species'].unique()):
        products = sorted(df[df['species'] == species]['product_type'].unique())
        console.print(f"  {species}: {', '.join(products)}")

    # Show sample data
    console.print("\n[bold cyan]Sample Data (first 10 rows):[/bold cyan]")
    console.print(df.head(10).to_string(index=False))

    console.print("\n[bold cyan]Sample Data (most recent quarter):[/bold cyan]")
    recent = df[(df['year'] == df['year'].max()) & (df['quarter'] == df['quarter'].max())]
    console.print(recent.to_string(index=False))

    # Show any errors
    if errors:
        console.print("\n[yellow]Files with issues:[/yellow]")
        for error in errors:
            console.print(f"  {error}")


if __name__ == "__main__":
    main()
