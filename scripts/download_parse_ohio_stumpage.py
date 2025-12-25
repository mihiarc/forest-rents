#!/usr/bin/env python3
"""
Download and parse Ohio stumpage price reports from OSU.

This script:
1. Downloads PDF reports from OSU woodlandstewards website
2. Parses stumpage price tables using pdfplumber
3. Extracts data for 10 hardwood species across 3 regions
4. Saves to CSV with standardized format

Data includes prices in $/MBF Doyle scale for:
- 10 hardwood species
- 3 regions (Northwest, Northeast, South)
- Multiple quarters/periods
"""

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import pandas as pd
import pdfplumber
import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()

# Base URLs
BASE_URL = "https://woodlandstewards.osu.edu"
ARCHIVE_URL = "https://ohiowood.osu.edu"

# PDF URLs organized by year and period
PDF_URLS = {
    # 2025
    "2025_Q3": f"{BASE_URL}/sites/woodlands/files/imce/TPR/July%202025%20Report.pdf",
    "2025_Q1": f"{BASE_URL}/sites/woodlands/files/imce/TPR/January%202025%20Report.pdf",

    # 2024
    "2024_Q3": f"{BASE_URL}/sites/woodlands/files/imce/TPR/July%202024%20Report.pdf",
    "2024_Q1": f"{BASE_URL}/sites/woodlands/files/imce/TPR/January%202024%20Report.pdf",

    # 2023
    "2023_Q3": f"{BASE_URL}/sites/woodlands/files/imce/TPR/July%202023%20Report.pdf",
    "2023_Q1": f"{BASE_URL}/sites/woodlands/files/imce/TPR/January-2023-TPR.pdf",

    # 2022
    "2022_Q3": f"{BASE_URL}/sites/woodlands/files/imce/Ohio%20Timber%20Price%20Report%20Fall%2021%20-%20Spring%2022.pdf",
    "2022_Q1": f"{BASE_URL}/sites/woodlands/files/imce/Ohio%20Timber%20Price%20Report.pdf",

    # 2021
    "2021_Q3": f"{BASE_URL}/sites/woodlands/files/imce/Ohio%20Timber%20Price%20Report_FINAL_JUL2021.pdf",
    "2021_Q1": f"{BASE_URL}/sites/woodlands/files/imce/Ohio%20Timber%20Price%20Report%201-21.pdf",

    # 2020
    "2020_Q3": f"{BASE_URL}/sites/woodlands/files/imce/Ohio%20Timber%20Price%20Report%207-20.pdf",
    "2020_Q1": f"{BASE_URL}/sites/woodlands/files/imce/January%202020%20TPR.pdf",

    # 2019
    "2019_Q3": f"{BASE_URL}/sites/woodlands/files/imce/July%202019%20Price%20Report.pdf",
    "2019_Q1": f"{BASE_URL}/sites/woodlands/files/imce/Ohio%20Timber%20Price%20Report%20Jan%202019.pdf",

    # 2018
    "2018_Q3": f"{BASE_URL}/sites/woodlands/files/imce/Ohio%202018%20Full%20Report.pdf",
    "2018_Q1": f"{BASE_URL}/sites/woodlands/files/imce/2017%20SPR%20to%202017%20FALL%20due%20JAN%202018%20%2800000002%29.pdf",

    # 2017
    "2017_Q3": f"{BASE_URL}/sites/woodlands/files/imce/JUL%202017%20Final_Oh%20TPR_TO%20MAIL.pdf",
    "2017_Q1": f"{BASE_URL}/sites/woodlands/files/imce/sawmill/January%202017%20REV%20TPR.pdf",

    # 2016
    "2016_Q3": f"{BASE_URL}/sites/woodlands/files/imce/sawmill/Ohio%20TPR_Spr2016%20FINAL.pdf",
    "2016_Q1": f"{BASE_URL}/sites/woodlands/files/imce/January%202016%20Posted%20TPR.pdf",

    # 2015
    "2015_Q3": f"{BASE_URL}/sites/woodlands/files/imce/July%202015%20Timber%20Price%20Report.pdf",
    "2015_Q1": f"{BASE_URL}/sites/woodlands/files/d6/files/pubfiles/Final_TPRspr2014%20to%20fall2014.pdf",

    # 2014
    "2014_Q3": f"{BASE_URL}/sites/woodlands/files/d6/files/pubfiles/July_31_2014_Final.pdf",
    "2014_Q1": f"{BASE_URL}/sites/woodlands/files/d6/files/pubfiles/OH_Final_TPR_JAN2014.pdf",

    # 2013
    "2013_Q3": f"{BASE_URL}/sites/woodlands/files/d6/files/pubfiles/July_2013_Timber%20Price%20Report.pdf",

    # 2012
    "2012_Q3": f"{BASE_URL}/sites/woodlands/files/d6/files/pubfiles/FALL%202011%20to%20SPRING%202012%20Ohio%20TPR_JULY2012.pdf",
    "2012_Q1": f"{BASE_URL}/sites/woodlands/files/d6/files/pubfiles/JAN2012.pdf",

    # 2011
    "2011_Q1": f"{BASE_URL}/sites/woodlands/files/d6/files/pubfiles/SPR2010%20to%20FAL2010%20Ohio%20TPR_JAN2011.pdf",

    # 2010
    "2010_Q3": f"{BASE_URL}/sites/woodlands/files/d6/files/pubfiles/FAL09_SPR2010%20Ohio%20TPR_JUL2010.pdf",
    "2010_Q1": f"{BASE_URL}/sites/woodlands/files/d6/files/pubfiles/SPR09_FAL09%20Ohio%20TPR_JAN2010_pdf.pdf",

    # Annual reports
    "2009": f"{BASE_URL}/sites/woodlands/files/imce/2009%20Timber%20Price%20Reports.pdf",
    "2008": f"{BASE_URL}/sites/woodlands/files/imce/2008%20Timber%20Price%20Reports.pdf",
    "2007": f"{BASE_URL}/sites/woodlands/files/imce/2007%20Timber%20Price%20Reports.pdf",
    "2006": f"{BASE_URL}/sites/woodlands/files/imce/2006%20Timber%20Price%20Reports.pdf",
    "2005": f"{BASE_URL}/sites/woodlands/files/imce/2005%20Timber%20Price%20Reports.pdf",
    "2004": f"{BASE_URL}/sites/woodlands/files/imce/2004%20Timber%20Price%20Reports.pdf",

    # Historical compilation
    "1971-2001": f"{BASE_URL}/sites/woodlands/files/imce/Historical%20Timber%20Price%20Reports%201971-2001.pdf",
}

# Standard species names
SPECIES_MAPPING = {
    "white oak": "White Oak",
    "red oak": "Red Oak",
    "ash": "Ash",
    "black cherry": "Black Cherry",
    "hard maple": "Hard Maple",
    "soft maple": "Soft Maple",
    "yellow-poplar": "Yellow-Poplar",
    "yellow poplar": "Yellow-Poplar",
    "walnut": "Walnut",
    "hickory": "Hickory",
    "beech": "Beech",
}

REGIONS = ["Northwest", "Northeast", "South"]


def download_pdf(url: str, output_path: Path) -> bool:
    """Download a PDF file from URL to output_path."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        output_path.write_bytes(response.content)
        return True
    except Exception as e:
        console.print(f"[red]Error downloading {url}: {e}[/red]")
        return False


def extract_period_from_filename(period_key: str) -> Tuple[int, str]:
    """Extract year and quarter from period key like '2024_Q3' or '2024'."""
    if "_Q" in period_key:
        year_str, quarter = period_key.split("_")
        year = int(year_str)
        return year, quarter
    elif "-" in period_key:
        # Historical range like "1971-2001"
        start_year = int(period_key.split("-")[0])
        return start_year, "ANNUAL"
    else:
        # Single year like "2009"
        year = int(period_key)
        return year, "ANNUAL"


def parse_price_value(value_str: str) -> Optional[float]:
    """Parse a price string like '$450', '450', or '450-500' to float."""
    if not value_str or value_str.strip() in ["", "-", "N/A", "NA"]:
        return None

    # Remove $ and commas
    cleaned = value_str.strip().replace("$", "").replace(",", "")

    # If it's a range, take the average
    if "-" in cleaned:
        parts = cleaned.split("-")
        try:
            low = float(parts[0].strip())
            high = float(parts[1].strip())
            return (low + high) / 2
        except ValueError:
            return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def extract_tables_from_pdf(pdf_path: Path, period_key: str) -> List[Dict]:
    """
    Extract stumpage price tables from a PDF file.

    Returns a list of dictionaries with keys:
    - year, quarter, region, species, product_type, price_avg, price_low, price_high, unit
    """
    records = []
    year, quarter = extract_period_from_filename(period_key)

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract text to identify regions and species
                text = page.extract_text()
                if not text:
                    continue

                # Extract tables
                tables = page.extract_tables()

                for table in tables:
                    if not table or len(table) < 2:
                        continue

                    # Try to identify if this is a stumpage price table
                    # Look for species names and price columns
                    records.extend(parse_stumpage_table(table, year, quarter, text))

    except Exception as e:
        console.print(f"[yellow]Warning: Error parsing {pdf_path.name}: {e}[/yellow]")

    return records


def parse_stumpage_table(table: List[List[str]], year: int, quarter: str, page_text: str) -> List[Dict]:
    """Parse a stumpage price table from extracted table data."""
    records = []

    # Check if this is a stumpage table (vs sawlog table)
    if "stumpage" not in page_text.lower():
        return records

    # Look for header row with "Species--Region" or similar
    header_row = None
    for i, row in enumerate(table):
        if not row:
            continue
        row_text = " ".join([str(cell).lower() for cell in row if cell])
        if "species" in row_text and "region" in row_text:
            header_row = i
            break

    if header_row is None:
        return records

    # Parse data rows - they come in groups by species
    current_species = None
    for i in range(header_row + 2, len(table)):  # Skip header and sub-header
        row = table[i]
        if not row or len(row) < 2:
            continue

        # First column contains either species name or region
        first_cell = str(row[0]).strip() if row[0] else ""

        if not first_cell:
            continue

        # Check if this is a species name (capitalized, not a region name)
        # Species names: Walnut, White Oak, Red Oak, Cherry, Hard Maple, Soft Maple, Ash, Yellow-Poplar, Hickory, Beech
        is_species = False
        for key, standard_name in SPECIES_MAPPING.items():
            if key.lower() in first_cell.lower() or standard_name.lower() == first_cell.lower():
                current_species = standard_name
                is_species = True
                break

        # Check for other species not in mapping
        if not is_species and first_cell[0].isupper() and first_cell.lower() not in ["west", "northeast", "southeast", "state"]:
            # Likely a species name
            current_species = first_cell.title()
            is_species = True

        if is_species:
            continue  # Species header row, no data

        # If we get here, this should be a region row
        if not current_species:
            continue

        # Identify region
        region = None
        region_cell_lower = first_cell.lower()
        if "west" in region_cell_lower and "north" not in region_cell_lower:
            region = "Northwest"  # Sometimes listed as just "West"
        elif "northeast" in region_cell_lower or "north east" in region_cell_lower:
            region = "Northeast"
        elif "southeast" in region_cell_lower or "south" in region_cell_lower:
            region = "South"
        elif "state" in region_cell_lower:
            region = "State"  # State-wide average
        else:
            continue

        # Extract prices
        # Table format: Species--Region, No. Rptg., Min-Max Range, MEAN (SPR 2023, FALL 2023), MEDIAN (SPR 2023, FALL 2023), % Change
        # We want the FALL 2023 MEAN and the min-max from range
        try:
            # Column indices (approximate):
            # 0: Species/Region
            # 1: No. Reporting
            # 2: Min-Max Range
            # 3: Mean SPR
            # 4: Mean FALL (most recent)
            # 5: Median SPR
            # 6: Median FALL (most recent)

            price_mean = None
            price_low = None
            price_high = None

            # Get min-max range
            if len(row) > 2 and row[2]:
                range_str = str(row[2])
                if "-" in range_str and range_str.lower() not in ["n/a", "na"]:
                    parts = range_str.split("-")
                    if len(parts) == 2:
                        price_low = parse_price_value(parts[0])
                        price_high = parse_price_value(parts[1])

            # Get mean price (use most recent, typically column 4)
            if len(row) > 4 and row[4]:
                price_mean = parse_price_value(str(row[4]))

            # If no mean in column 4, try column 3
            if price_mean is None and len(row) > 3 and row[3]:
                price_mean = parse_price_value(str(row[3]))

            if price_mean is None:
                continue

            record = {
                "year": year,
                "quarter": quarter,
                "region": region,
                "species": current_species,
                "product_type": "Stumpage",
                "price_avg": price_mean,
                "price_low": price_low,
                "price_high": price_high,
                "unit": "$/MBF",
            }

            records.append(record)

        except Exception as e:
            console.print(f"[yellow]Warning parsing row: {e}[/yellow]")
            continue

    return records


def main():
    """Main execution function."""
    console.print("[bold blue]Ohio Stumpage Price Data Downloader and Parser[/bold blue]")
    console.print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Setup directories
    data_dir = Path("/Users/mihiarc/landuse-model/forest-rents/data/raw/oh_osu")
    pdf_dir = data_dir / "pdfs"
    pdf_dir.mkdir(parents=True, exist_ok=True)

    all_records = []
    downloaded_count = 0
    parsed_count = 0

    # Download and parse PDFs
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:

        task = progress.add_task(
            f"Processing {len(PDF_URLS)} reports...",
            total=len(PDF_URLS)
        )

        for period_key, url in PDF_URLS.items():
            pdf_filename = f"{period_key}.pdf"
            pdf_path = pdf_dir / pdf_filename

            progress.update(task, description=f"Downloading {period_key}...")

            # Download if not already present
            if not pdf_path.exists():
                if download_pdf(url, pdf_path):
                    downloaded_count += 1
                else:
                    progress.advance(task)
                    continue

            # Parse PDF
            progress.update(task, description=f"Parsing {period_key}...")
            records = extract_tables_from_pdf(pdf_path, period_key)

            if records:
                all_records.extend(records)
                parsed_count += 1
                console.print(f"[green]✓[/green] {period_key}: {len(records)} records extracted")
            else:
                console.print(f"[yellow]⚠[/yellow] {period_key}: No data extracted")

            progress.advance(task)

    # Create DataFrame
    console.print(f"\n[bold]Creating final dataset...[/bold]")
    df = pd.DataFrame(all_records)

    if df.empty:
        console.print("[red]No data extracted from PDFs. Please check the PDF formats.[/red]")
        return 1

    # Sort by year, quarter, region, species
    df = df.sort_values(["year", "quarter", "region", "species"]).reset_index(drop=True)

    # Save to CSV
    output_path = data_dir / "oh_stumpage_parsed.csv"
    df.to_csv(output_path, index=False)

    # Print summary
    console.print(f"\n[bold green]✓ Processing Complete![/bold green]")
    console.print(f"Downloaded: {downloaded_count} new PDFs")
    console.print(f"Parsed: {parsed_count} PDFs")
    console.print(f"Total records: {len(df):,}")
    console.print(f"Output saved to: {output_path}")

    # Year range
    year_range = f"{df['year'].min()}-{df['year'].max()}"
    console.print(f"Year range: {year_range}")

    # Species coverage
    species_counts = df["species"].value_counts()
    console.print(f"\nSpecies found: {len(species_counts)}")

    # Region coverage
    region_counts = df["region"].value_counts()
    console.print(f"Regions found: {len(region_counts)}")

    # Sample data
    console.print("\n[bold]Sample data (first 10 rows):[/bold]")
    sample_table = Table(show_header=True, header_style="bold magenta")

    for col in df.columns:
        sample_table.add_column(col)

    for _, row in df.head(10).iterrows():
        sample_table.add_row(*[str(val) for val in row])

    console.print(sample_table)

    # Summary statistics
    console.print("\n[bold]Price Statistics ($/MBF):[/bold]")
    stats_table = Table(show_header=True, header_style="bold cyan")
    stats_table.add_column("Metric")
    stats_table.add_column("Value")

    stats_table.add_row("Mean", f"${df['price_avg'].mean():.2f}")
    stats_table.add_row("Median", f"${df['price_avg'].median():.2f}")
    stats_table.add_row("Min", f"${df['price_avg'].min():.2f}")
    stats_table.add_row("Max", f"${df['price_avg'].max():.2f}")

    console.print(stats_table)

    return 0


if __name__ == "__main__":
    sys.exit(main())
