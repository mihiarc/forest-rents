#!/usr/bin/env python3
"""
Parse Texas A&M Forest Service stumpage price data from multiple PDF formats.

This script extracts stumpage (standing timber) price data from Texas A&M Forest Service
reports covering 2017-2024. Data sources include:
- 5-year summary reports (statewide averages)
- Annual price reports (regional breakdowns)
- Bimonthly market reports (current prices)

Output: Standardized CSV with columns:
- year: Calendar year
- region: Geographic region (Northeast TX, Southeast TX, or Statewide)
- species: Tree species (Pine or Hardwood)
- product_type: Forest product category
- unit: Price unit ($/ton)
- price_avg: Combined average price
- price_unweighted_avg: Simple average price (when available)
- price_weighted_avg: Volume-weighted average price (when available)

Author: Claude Code
Date: 2025-12-25
"""

import pdfplumber
import re
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()


def clean_price(price_str: str) -> Optional[float]:
    """Clean and convert price string to float.

    Args:
        price_str: Price string potentially containing $, commas, or ** (missing data marker)

    Returns:
        Float price value or None if invalid/missing
    """
    if not price_str or price_str == '**':
        return None
    # Remove $ and commas
    cleaned = price_str.replace('$', '').replace(',', '').strip()
    try:
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def normalize_product_type(product: str, species: str) -> str:
    """Normalize product type names for consistency.

    Args:
        product: Original product type name
        species: Species (Pine or Hardwood)

    Returns:
        Normalized product type name
    """
    # Normalize sawtimber variations
    if 'Large Sawtimber' in product or (product == 'Sawlogs' and species == 'Pine'):
        return 'Pine Sawtimber (Large)'
    elif 'Small Sawtimber' in product or 'Chip-N-Saw' in product:
        return 'Pine Chip-N-Saw'
    elif 'Sawtimber' in product and species == 'Pine':
        return 'Pine Sawtimber'
    elif 'Mixed Sawtimber' in product or (product == 'Sawlogs' and species == 'Hardwood'):
        return 'Hardwood Sawtimber (Mixed)'
    elif 'Pulpwood' in product and species == 'Pine':
        return 'Pine Pulpwood'
    elif 'Pulpwood' in product and species == 'Hardwood':
        return 'Hardwood Pulpwood'
    else:
        return f"{species} {product}"


def parse_5year_report(pdf_path: Path) -> List[Dict]:
    """Parse 5-year summary reports (2017-2021 and 2019-2023).

    These reports contain statewide average prices across multiple years,
    with unweighted and weighted averages for different product categories.

    Args:
        pdf_path: Path to 5-year summary PDF

    Returns:
        List of price records
    """
    console.print(f"[cyan]Parsing 5-year report: {pdf_path.name}[/cyan]")
    records = []

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()

        # Extract all lines
        lines = text.split('\n')

        # Parse Large Pine Sawtimber section
        in_large_pine = False
        in_small_pine = False
        in_hardwood_saw = False
        in_pine_pulp = False
        in_hardwood_pulp = False

        for i, line in enumerate(lines):
            # Track sections
            if 'Large Pine Sawtimber' in line:
                in_large_pine = True
                continue
            elif 'Small Pine Sawtimber' in line:
                in_large_pine = False
                in_small_pine = True
                continue
            elif 'Hardwood Sawtimber' in line:
                in_small_pine = False
                in_hardwood_saw = True
                continue
            elif 'Pine Pulpwood' in line:
                in_hardwood_saw = False
                in_pine_pulp = True
                continue
            elif 'Hardwood Pulpwood' in line:
                in_pine_pulp = False
                in_hardwood_pulp = True
                continue

            # Parse data lines (year followed by prices)
            year_price_match = re.match(r'^(20\d{2})\s+\$', line)
            if year_price_match:
                year = int(year_price_match.group(1))
                # Extract all prices from the line
                prices = re.findall(r'\$[\d,]+\.[\d]{2}', line)

                if in_large_pine and len(prices) >= 3:
                    records.append({
                        'year': year,
                        'region': 'Statewide',
                        'species': 'Pine',
                        'product_type': 'Large Sawtimber',
                        'price_unweighted_avg': clean_price(prices[0]),
                        'price_weighted_avg': clean_price(prices[1]),
                        'price_avg': clean_price(prices[2]),
                        'unit': '$/ton'
                    })

                elif in_small_pine and len(prices) >= 3:
                    records.append({
                        'year': year,
                        'region': 'Statewide',
                        'species': 'Pine',
                        'product_type': 'Small Sawtimber (Chip-N-Saw)',
                        'price_unweighted_avg': clean_price(prices[0]),
                        'price_weighted_avg': clean_price(prices[1]),
                        'price_avg': clean_price(prices[2]),
                        'unit': '$/ton'
                    })

                elif in_hardwood_saw and len(prices) >= 3:
                    records.append({
                        'year': year,
                        'region': 'Statewide',
                        'species': 'Hardwood',
                        'product_type': 'Mixed Sawtimber',
                        'price_unweighted_avg': clean_price(prices[0]),
                        'price_weighted_avg': clean_price(prices[1]),
                        'price_avg': clean_price(prices[2]),
                        'unit': '$/ton'
                    })

                elif in_pine_pulp and len(prices) >= 3:
                    records.append({
                        'year': year,
                        'region': 'Statewide',
                        'species': 'Pine',
                        'product_type': 'Pulpwood',
                        'price_unweighted_avg': clean_price(prices[0]),
                        'price_weighted_avg': clean_price(prices[1]),
                        'price_avg': clean_price(prices[2]),
                        'unit': '$/ton'
                    })

                elif in_hardwood_pulp and len(prices) >= 3:
                    records.append({
                        'year': year,
                        'region': 'Statewide',
                        'species': 'Hardwood',
                        'product_type': 'Pulpwood',
                        'price_unweighted_avg': clean_price(prices[0]),
                        'price_weighted_avg': clean_price(prices[1]),
                        'price_avg': clean_price(prices[2]),
                        'unit': '$/ton'
                    })

    console.print(f"[green]Extracted {len(records)} records from 5-year report[/green]")
    return records


def parse_annual_report(pdf_path: Path) -> List[Dict]:
    """Parse annual price report (2023).

    Annual reports contain regional breakdowns (Northeast TX, Southeast TX, Statewide)
    with detailed price data for different product types.

    Args:
        pdf_path: Path to annual report PDF

    Returns:
        List of price records
    """
    console.print(f"[cyan]Parsing annual report: {pdf_path.name}[/cyan]")
    records = []

    # Extract year from filename
    year_match = re.search(r'(\d{4})', pdf_path.name)
    year = int(year_match.group(1)) if year_match else 2023

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()
        lines = text.split('\n')

        current_product = None
        current_species = None

        for line in lines:
            # Identify sections
            if line.strip() == 'PINE':
                current_species = 'Pine'
                continue
            elif line.strip() == 'HARDWOOD':
                current_species = 'Hardwood'
                continue

            # Identify product types
            if 'Sawlogs' in line and '$/Ton' in line:
                current_product = 'Sawlogs' if current_species == 'Pine' else 'Mixed Sawtimber'
                continue
            elif 'Pulpwood' in line and '$/Ton' in line:
                current_product = 'Pulpwood'
                continue
            elif 'Chip-N-Saw' in line and '$/Ton' in line:
                current_product = 'Chip-N-Saw'
                continue

            # Parse regional data lines
            region_match = re.match(r'^(Northeast TX|Southeast TX|Statewide)\s+', line)
            if region_match and current_species and current_product:
                region = region_match.group(1)

                # Extract prices - looking for $/Ton values
                price_parts = re.findall(r'([\d,]+\.[\d]{2})', line)

                # The pattern is: unweighted_ton, unweighted_other, weighted_ton, weighted_other, avg_ton, avg_other
                if len(price_parts) >= 5:
                    records.append({
                        'year': year,
                        'region': region,
                        'species': current_species,
                        'product_type': current_product,
                        'price_unweighted_avg': clean_price(price_parts[0]),
                        'price_weighted_avg': clean_price(price_parts[2]),
                        'price_avg': clean_price(price_parts[4]),
                        'unit': '$/ton'
                    })

    console.print(f"[green]Extracted {len(records)} records from annual report[/green]")
    return records


def parse_bimonthly_report(pdf_path: Path) -> List[Dict]:
    """Parse bimonthly reports (2004-2024).

    Bimonthly reports contain current market prices with regional breakdowns.
    Format varies by publication year.

    Args:
        pdf_path: Path to bimonthly report PDF

    Returns:
        List of price records
    """
    console.print(f"[cyan]Parsing bimonthly report: {pdf_path.name}[/cyan]")
    records = []

    # Extract year and months from filename or content
    year_match = re.search(r'(\d{4})', pdf_path.name)
    year = int(year_match.group(1)) if year_match else None

    with pdfplumber.open(pdf_path) as pdf:
        # Look for stumpage price table (usually page 2)
        for page_num in range(min(len(pdf.pages), 3)):
            page = pdf.pages[page_num]
            text = page.extract_text()

            if not text:
                continue

            # Find year from header if not in filename
            if not year:
                header_year = re.search(r'(20\d{2})', text[:500])
                if header_year:
                    year = int(header_year.group(1))

            # Look for "Stumpage Prices in Texas" table
            if 'Stumpage Prices' not in text:
                continue

            lines = text.split('\n')
            current_species = None
            current_product = None

            for i, line in enumerate(lines):
                # Identify sections
                if line.strip() == 'PINE':
                    current_species = 'Pine'
                    continue
                elif line.strip() == 'HARDWOOD':
                    current_species = 'Hardwood'
                    continue

                # Identify product types
                if 'Sawtimber' in line and '$/Ton' in line:
                    if current_species == 'Pine':
                        current_product = 'Sawtimber'
                    else:
                        current_product = 'Mixed Sawtimber'
                    continue
                elif 'Pulpwood' in line and '$/Ton' in line:
                    current_product = 'Pulpwood'
                    continue
                elif 'Chip-N-Saw' in line and '$/Ton' in line:
                    current_product = 'Chip-N-Saw'
                    continue

                # Parse data lines
                region_match = re.match(r'^(Northeast TX|Southeast TX|Statewide)\s+\$', line)
                if region_match and current_species and current_product and year:
                    region = region_match.group(1)

                    # Extract first price (average price in $/Ton)
                    price_match = re.search(r'\$([\d,]+\.[\d]{2})', line)
                    if price_match:
                        avg_price = clean_price(price_match.group(1))

                        records.append({
                            'year': year,
                            'region': region,
                            'species': current_species,
                            'product_type': current_product,
                            'price_avg': avg_price,
                            'unit': '$/ton'
                        })

    console.print(f"[green]Extracted {len(records)} records from bimonthly report[/green]")
    return records


def main():
    """Main function to parse all Texas A&M stumpage price data."""
    console.print("\n[bold blue]═══════════════════════════════════════════════════════════[/bold blue]")
    console.print("[bold blue]  Texas A&M Forest Service Stumpage Price Parser[/bold blue]")
    console.print("[bold blue]═══════════════════════════════════════════════════════════[/bold blue]\n")

    data_dir = Path("/Users/mihiarc/landuse-model/forest-rents/data/raw/texas_am")
    output_path = Path("/Users/mihiarc/landuse-model/forest-rents/data/raw/texas_am/tx_stumpage_parsed.csv")

    all_records = []

    # Parse 5-year reports
    console.print("\n[bold yellow]📊 Processing 5-Year Summary Reports[/bold yellow]")
    five_year_files = [
        "5year_5-Year-Stumpage-Prices-2019-2023.pdf",
        "5year_Prices202017-2021.pdf",
    ]
    for filename in five_year_files:
        pdf_path = data_dir / filename
        if pdf_path.exists():
            try:
                records = parse_5year_report(pdf_path)
                all_records.extend(records)
            except Exception as e:
                console.print(f"[red]Error parsing {filename}: {e}[/red]")

    # Parse annual report
    console.print("\n[bold yellow]📈 Processing Annual Reports[/bold yellow]")
    annual_files = list(data_dir.glob("annual_*.pdf"))
    for pdf_path in annual_files:
        try:
            records = parse_annual_report(pdf_path)
            all_records.extend(records)
        except Exception as e:
            console.print(f"[red]Error parsing {pdf_path.name}: {e}[/red]")

    # Parse bimonthly reports
    console.print("\n[bold yellow]📅 Processing Bimonthly Reports[/bold yellow]")
    bimonthly_files = sorted(data_dir.glob("bimonthly_*.pdf"))
    for pdf_path in track(bimonthly_files, description="Parsing bimonthly reports"):
        try:
            records = parse_bimonthly_report(pdf_path)
            all_records.extend(records)
        except Exception as e:
            console.print(f"[red]Error parsing {pdf_path.name}: {e}[/red]")

    # Convert to DataFrame
    console.print("\n[bold yellow]🔧 Creating DataFrame and cleaning data[/bold yellow]")
    df = pd.DataFrame(all_records)

    # Standardize columns
    df['year'] = df['year'].astype('Int64')

    # Normalize product types
    df['product_type_normalized'] = df.apply(
        lambda row: normalize_product_type(row['product_type'], row['species']),
        axis=1
    )

    # Create final output columns
    output_columns = ['year', 'region', 'species', 'product_type', 'product_type_normalized', 'unit']

    # Add price columns that exist
    price_cols = []
    if 'price_avg' in df.columns:
        price_cols.append('price_avg')
    if 'price_unweighted_avg' in df.columns:
        price_cols.append('price_unweighted_avg')
    if 'price_weighted_avg' in df.columns:
        price_cols.append('price_weighted_avg')

    output_columns.extend(price_cols)

    # Select and order columns
    df = df[output_columns].copy()

    # Sort by year, species, product_type, region
    df = df.sort_values(['year', 'species', 'product_type', 'region']).reset_index(drop=True)

    # Remove duplicates (prefer records with more price data)
    df['price_count'] = df[price_cols].notna().sum(axis=1)
    df = df.sort_values(['year', 'region', 'species', 'product_type', 'price_count'], ascending=[True, True, True, True, False])
    df = df.drop_duplicates(subset=['year', 'region', 'species', 'product_type'], keep='first')
    df = df.drop('price_count', axis=1)
    df = df.sort_values(['year', 'species', 'product_type', 'region']).reset_index(drop=True)

    # Save to CSV
    df.to_csv(output_path, index=False)
    console.print(f"\n[bold green]✓ Data saved to: {output_path}[/bold green]")

    # Print summary statistics
    console.print("\n[bold blue]═══════════════════════════════════════════════════════════[/bold blue]")
    console.print("[bold blue]  Summary Statistics[/bold blue]")
    console.print("[bold blue]═══════════════════════════════════════════════════════════[/bold blue]\n")

    console.print(f"[cyan]Total records:[/cyan] {len(df)}")
    console.print(f"[cyan]Years covered:[/cyan] {df['year'].min()} - {df['year'].max()}")
    console.print(f"[cyan]Regions:[/cyan] {df['region'].nunique()} ({', '.join(sorted(df['region'].unique()))})")
    console.print(f"[cyan]Species:[/cyan] {df['species'].nunique()} ({', '.join(sorted(df['species'].unique()))})")
    console.print(f"[cyan]Product types:[/cyan] {df['product_type'].nunique()}")

    # Show product types breakdown
    console.print("\n[bold blue]Product Types Breakdown:[/bold blue]")
    product_summary = df.groupby('product_type_normalized').size().reset_index(name='count')
    product_summary = product_summary.sort_values('count', ascending=False)

    product_table = Table(show_header=True, header_style="bold magenta")
    product_table.add_column("Product Type")
    product_table.add_column("Records", justify="right")

    for _, row in product_summary.iterrows():
        product_table.add_row(row['product_type_normalized'], str(row['count']))

    console.print(product_table)

    # Show sample data
    console.print("\n[bold blue]Sample Data (first 10 rows):[/bold blue]")
    sample_table = Table(show_header=True, header_style="bold magenta", show_lines=True)
    display_cols = ['year', 'region', 'species', 'product_type_normalized', 'price_avg']
    for col in display_cols:
        sample_table.add_column(col)

    for idx, row in df.head(10).iterrows():
        sample_table.add_row(*[str(row[col]) if pd.notna(row[col]) else '-' for col in display_cols])

    console.print(sample_table)

    # Show recent data (last 10 rows)
    console.print("\n[bold blue]Recent Data (last 10 rows):[/bold blue]")
    recent_table = Table(show_header=True, header_style="bold magenta", show_lines=True)
    for col in display_cols:
        recent_table.add_column(col)

    for idx, row in df.tail(10).iterrows():
        recent_table.add_row(*[str(row[col]) if pd.notna(row[col]) else '-' for col in display_cols])

    console.print(recent_table)

    # Summary by year
    console.print("\n[bold blue]Records per Year:[/bold blue]")
    year_counts = df.groupby('year').size().reset_index(name='count')
    year_table = Table(show_header=True, header_style="bold cyan")
    year_table.add_column("Year", justify="center")
    year_table.add_column("Records", justify="right")

    for _, row in year_counts.iterrows():
        year_table.add_row(str(row['year']), str(row['count']))

    console.print(year_table)

    # Price range summary
    console.print("\n[bold blue]Price Range Summary ($/ton):[/bold blue]")
    price_summary = df.groupby(['species', 'product_type_normalized'])['price_avg'].agg(['min', 'max', 'mean']).reset_index()
    price_summary = price_summary.dropna()
    price_summary = price_summary.sort_values(['species', 'mean'], ascending=[True, False])

    price_table = Table(show_header=True, header_style="bold yellow", show_lines=True)
    price_table.add_column("Species")
    price_table.add_column("Product Type")
    price_table.add_column("Min Price", justify="right")
    price_table.add_column("Max Price", justify="right")
    price_table.add_column("Avg Price", justify="right")

    for _, row in price_summary.iterrows():
        price_table.add_row(
            row['species'],
            row['product_type_normalized'],
            f"${row['min']:.2f}",
            f"${row['max']:.2f}",
            f"${row['mean']:.2f}"
        )

    console.print(price_table)

    console.print("\n[bold green]✓ Parsing complete![/bold green]\n")


if __name__ == "__main__":
    main()
