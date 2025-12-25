#!/usr/bin/env python3
"""
Parse Georgia DOR timber values from PDF files.

This script extracts timber stumpage prices by county, species, and product type
from Georgia Department of Revenue PDF reports.
"""

import re
from pathlib import Path
from typing import List, Dict, Any
import pdfplumber
import pandas as pd
from rich.console import Console
from rich.table import Table as RichTable
from rich import print as rprint

console = Console()


def parse_pdf_text(pdf_path: Path, year: int) -> List[Dict[str, Any]]:
    """
    Parse timber values from a GA DOR PDF using text extraction.

    Args:
        pdf_path: Path to the PDF file
        year: Year of the data

    Returns:
        List of dictionaries containing parsed timber values
    """
    records = []

    # Define product types in order they appear in the table
    product_types = [
        ("Softwood", "Pulpwood"),
        ("Softwood", "chip-n-saw"),
        ("Softwood", "Sawtimber"),
        ("Softwood", "Poles"),
        ("Softwood", "Posts"),
        ("Softwood", "Fuelchips"),
        ("Hardwood", "Pulpwood"),
        ("Hardwood", "Sawtimber"),
        ("Hardwood", "Firewood"),
    ]

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()

            if not text:
                continue

            # Split into lines
            lines = text.split("\n")

            for line in lines:
                line = line.strip()

                # Skip empty lines and header lines
                if not line or "County" in line or "Softwood" in line or "Hardwood" in line:
                    continue

                # Skip lines that are just the page header
                if "Georgia Department of Revenue" in line or "Frank M. O'Connell" in line:
                    continue

                if "State Revenue Commissioner" in line or "Director," in line:
                    continue

                if "Local Government Services Division" in line or "Table of Owner" in line:
                    continue

                if "Page" in line and line.split()[0] == "Page":
                    continue

                # Parse county data lines
                # Format: COUNTY_NAME value1 value2 value3 ... value9
                parts = line.split()

                if len(parts) < 2:
                    continue

                # First part should be the county name (all caps)
                county = parts[0]

                # Check if this looks like a county name (all uppercase letters)
                if not county.isupper() or len(county) < 3:
                    continue

                # Extract numeric values
                values = []
                for part in parts[1:]:
                    try:
                        # Try to convert to float
                        value = float(part)
                        values.append(value)
                    except ValueError:
                        # If it's not a number, it might be part of the county name
                        # (e.g., "BEN HILL" split into two parts)
                        if part.isupper() and len(values) == 0:
                            county = f"{county} {part}"
                        continue

                # We expect 9 values (6 softwood + 3 hardwood)
                if len(values) == 9:
                    for (species, product_type), price in zip(product_types, values):
                        records.append({
                            "year": year,
                            "county": county.title(),  # Convert to title case
                            "species": species,
                            "product_type": product_type,
                            "price_avg": price,
                            "unit": "$/ton"  # Based on GA DOR documentation
                        })

    return records


def parse_all_pdfs(data_dir: Path) -> pd.DataFrame:
    """
    Parse all GA DOR PDF files in the directory.

    Args:
        data_dir: Directory containing the PDF files

    Returns:
        DataFrame with all parsed timber values
    """
    all_records = []

    # Find all PDF files
    pdf_files = sorted(data_dir.glob("ga_dor_timber_values_*.pdf"))

    console.print(f"\n[bold cyan]Found {len(pdf_files)} PDF files to parse[/bold cyan]")

    for pdf_file in pdf_files:
        # Extract year from filename
        match = re.search(r"(\d{4})", pdf_file.name)
        if not match:
            console.print(f"[yellow]Warning: Could not extract year from {pdf_file.name}[/yellow]")
            continue

        year = int(match.group(1))
        console.print(f"\n[green]Parsing {pdf_file.name} (year: {year})...[/green]")

        records = parse_pdf_text(pdf_file, year)
        all_records.extend(records)

        console.print(f"  Extracted {len(records)} records")

    # Create DataFrame
    df = pd.DataFrame(all_records)

    return df


def display_summary(df: pd.DataFrame):
    """Display a summary of the parsed data."""

    console.print("\n[bold cyan]=" * 40)
    console.print("[bold cyan]DATA SUMMARY[/bold cyan]")
    console.print("[bold cyan]=" * 40)

    console.print(f"\n[bold]Total records:[/bold] {len(df):,}")
    console.print(f"[bold]Years:[/bold] {sorted(df['year'].unique())}")
    console.print(f"[bold]Counties:[/bold] {df['county'].nunique()}")
    console.print(f"[bold]Species:[/bold] {sorted(df['species'].unique())}")
    console.print(f"[bold]Product types:[/bold] {sorted(df['product_type'].unique())}")

    # Display sample data
    console.print("\n[bold green]Sample data (first 10 records):[/bold green]")

    table = RichTable(show_header=True, header_style="bold magenta")
    table.add_column("Year", style="cyan")
    table.add_column("County", style="green")
    table.add_column("Species", style="yellow")
    table.add_column("Product Type", style="blue")
    table.add_column("Price", justify="right", style="white")
    table.add_column("Unit", style="dim")

    for _, row in df.head(10).iterrows():
        table.add_row(
            str(row["year"]),
            row["county"],
            row["species"],
            row["product_type"],
            f"${row['price_avg']:.2f}",
            row["unit"]
        )

    console.print(table)

    # Display statistics by year and species
    console.print("\n[bold green]Average prices by year and species:[/bold green]")

    pivot_table = RichTable(show_header=True, header_style="bold magenta")
    pivot_table.add_column("Year", style="cyan")
    pivot_table.add_column("Species", style="yellow")
    pivot_table.add_column("Avg Price", justify="right", style="white")
    pivot_table.add_column("Min Price", justify="right", style="green")
    pivot_table.add_column("Max Price", justify="right", style="red")

    stats = df.groupby(["year", "species"])["price_avg"].agg(["mean", "min", "max"]).reset_index()

    for _, row in stats.iterrows():
        pivot_table.add_row(
            str(row["year"]),
            row["species"],
            f"${row['mean']:.2f}",
            f"${row['min']:.2f}",
            f"${row['max']:.2f}"
        )

    console.print(pivot_table)


def main():
    """Main function to parse GA DOR timber values."""

    # Define paths
    data_dir = Path("/Users/mihiarc/landuse-model/forest-rents/data/raw/ga_dor")
    output_path = data_dir / "ga_stumpage_parsed.csv"

    console.print("\n[bold cyan]Georgia DOR Timber Values Parser[/bold cyan]")
    console.print("=" * 80)

    # Parse all PDFs
    df = parse_all_pdfs(data_dir)

    if df.empty:
        console.print("[bold red]No data extracted![/bold red]")
        return

    # Sort by year, county, species, and product type
    df = df.sort_values(["year", "county", "species", "product_type"]).reset_index(drop=True)

    # Save to CSV
    console.print(f"\n[bold]Saving to:[/bold] {output_path}")
    df.to_csv(output_path, index=False)

    console.print("[bold green]✓ Data saved successfully![/bold green]")

    # Display summary
    display_summary(df)

    console.print("\n[bold cyan]=" * 40)
    console.print("[bold green]✓ Parsing complete![/bold green]")
    console.print("[bold cyan]=" * 40 + "\n")


if __name__ == "__main__":
    main()
