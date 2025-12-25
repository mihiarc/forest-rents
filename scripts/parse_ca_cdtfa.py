"""Parse California CDTFA Timber Harvest Values PDFs.

The California Department of Tax and Fee Administration (CDTFA) publishes
semi-annual harvest values schedules used for timber yield tax assessment.
These are proxy values for stumpage prices.

Data sources:
- Harvest Values Schedule PDFs (2019-present)
- Semi-annual publication (H1: Jan-Jun, H2: Jul-Dec)

Output: data/raw/ca_cdtfa/ca_stumpage_parsed.csv
"""

import re
import pandas as pd
from pathlib import Path
from rich.console import Console
from rich.table import Table as RichTable

console = Console()

# Paths
RAW_DIR = Path("data/raw/ca_cdtfa")

# Species mapping from CDTFA codes to standardized names
SPECIES_MAP = {
    "PPG": "ponderosa_pine",
    "PPS": "ponderosa_pine",
    "FG": "hemlock_fir",
    "FS": "hemlock_fir",
    "DFG": "douglas_fir",
    "DFS": "douglas_fir",
    "ICG": "incense_cedar",
    "ICS": "incense_cedar",
    "RG": "redwood",
    "RS": "redwood",
    "PCG": "port_orford_cedar",
    "PCS": "port_orford_cedar",
}

# Human-readable species names
SPECIES_NAMES = {
    "PPG": "Ponderosa Pine",
    "PPS": "Ponderosa Pine",
    "FG": "Hemlock-Fir",
    "FS": "Hemlock-Fir",
    "DFG": "Douglas Fir",
    "DFS": "Douglas Fir",
    "ICG": "Incense Cedar",
    "ICS": "Incense Cedar",
    "RG": "Redwood",
    "RS": "Redwood",
    "PCG": "Port Orford Cedar",
    "PCS": "Port Orford Cedar",
}

# Size code descriptions
SIZE_MAP = {
    "1": "over_300_mbf",
    "2": "150_300_mbf",
    "3": "under_150_mbf",
    "N/A": "all_sizes",
}

# Timber value areas (counties)
TVA_COUNTIES = {
    1: "Del Norte, Humboldt (coast)",
    2: "Mendocino, Sonoma (coast)",
    3: "Santa Cruz, Santa Clara, San Mateo",
    4: "Siskiyou (west), Shasta (west), Trinity, Humboldt (inland), Mendocino (inland)",
    5: "Siskiyou (east), Shasta (east), Modoc, Lassen",
    6: "Tehama (west), Glenn, Lake, Colusa, Yolo, Napa, Solano, Marin",
    7: "Tehama (east), Butte, Plumas, Sierra, Nevada, Placer, El Dorado, Amador, Calaveras",
    8: "Alpine, Tuolumne, Mariposa, Madera, Fresno",
    9: "Tulare, Kern, San Bernardino, Riverside, San Diego, Los Angeles, Ventura, Santa Barbara, San Luis Obispo, Monterey, Inyo",
}


def parse_table_from_extraction(table: list, table_type: str = "G") -> list[dict]:
    """Parse extracted table data from pdfplumber.

    Args:
        table: List of rows from pdfplumber extract_tables()
        table_type: 'G' for green timber, 'S' for salvage

    Returns:
        List of price records
    """
    rows = []
    current_species_code = None

    # Skip header rows
    data_started = False
    for row in table:
        # Skip empty rows
        if not row or all(cell is None or cell == '' for cell in row):
            continue

        # Detect start of data (look for species code in first column)
        first_cell = row[0] if row[0] else ''

        # Check if this row has a species code
        if first_cell in ['PPG', 'PPS', 'FG', 'FS', 'DFG', 'DFS', 'ICG', 'ICS', 'RG', 'RS', 'PCG', 'PCS']:
            current_species_code = first_cell
            data_started = True
        elif not data_started:
            continue

        # Skip header rows
        if 'SPECIES' in str(first_cell) or 'CODE' in str(first_cell):
            continue

        # Parse data row
        if data_started and current_species_code:
            try:
                # Row format: [species_code or None, volume_range, size_code, area1, area2, ..., area9]
                size_code = row[2] if len(row) > 2 and row[2] else 'N/A'

                # Extract values for areas 1-9 (columns 3-11)
                for area_idx in range(9):
                    col_idx = 3 + area_idx
                    if col_idx < len(row):
                        value = row[col_idx]
                        if value and value != 'N/A':
                            try:
                                price = float(value)
                                rows.append({
                                    'species_code': current_species_code,
                                    'species': SPECIES_NAMES.get(current_species_code, current_species_code),
                                    'size_code': str(size_code),
                                    'timber_value_area': area_idx + 1,
                                    'price_mbf': price,
                                    'timber_type': 'green' if table_type == 'G' else 'salvage',
                                })
                            except (ValueError, TypeError):
                                pass

                # Update species code if next row doesn't have one (continuation row)
                if row[0] and row[0] in ['PPG', 'PPS', 'FG', 'FS', 'DFG', 'DFS', 'ICG', 'ICS', 'RG', 'RS', 'PCG', 'PCS']:
                    current_species_code = row[0]

            except (IndexError, ValueError) as e:
                continue

    return rows


def parse_values(values_str: str) -> list:
    """Parse a string of space-separated values into a list."""
    values = []
    parts = values_str.strip().split()
    for part in parts:
        if part == 'N/A':
            values.append('N/A')
        else:
            try:
                values.append(float(part))
            except ValueError:
                values.append('N/A')
    return values


def parse_pdf_tables(pdf_path: Path) -> pd.DataFrame:
    """Parse Table G and Table S from a CDTFA harvest values PDF."""
    import pdfplumber

    all_rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if not text:
                continue

            # Detect table type from text
            table_type = None
            if 'TABLE G' in text or 'GREEN TIMBER' in text:
                table_type = 'G'
            elif 'TABLE S' in text or 'SALVAGE' in text:
                table_type = 'S'

            if table_type:
                # Extract tables using pdfplumber
                tables = page.extract_tables()
                for table in tables:
                    if table and len(table) > 2:  # Need at least header + data
                        rows = parse_table_from_extraction(table, table_type)
                        all_rows.extend(rows)

    return pd.DataFrame(all_rows)


def extract_date_from_filename(filename: str) -> tuple[int, int]:
    """Extract year and half from filename like ca_harvest_values_2024_h2.pdf"""
    match = re.search(r'(\d{4})_h(\d)', filename)
    if match:
        year = int(match.group(1))
        half = int(match.group(2))
        return year, half
    return None, None


def parse_all_pdfs() -> pd.DataFrame:
    """Parse all CDTFA harvest values PDFs in the raw directory."""
    all_records = []

    pdf_files = sorted(RAW_DIR.glob("ca_harvest_values_*.pdf"))
    console.print(f"[blue]Found {len(pdf_files)} PDF files[/blue]")

    for pdf_path in pdf_files:
        year, half = extract_date_from_filename(pdf_path.name)
        if year is None:
            console.print(f"[yellow]Skipping {pdf_path.name} - could not parse date[/yellow]")
            continue

        console.print(f"[blue]Parsing {pdf_path.name}...[/blue]")

        try:
            df = parse_pdf_tables(pdf_path)
            if len(df) > 0:
                df['year'] = year
                df['half'] = half
                # Convert half to quarter range
                df['quarter_start'] = 1 if half == 1 else 3
                df['quarter_end'] = 2 if half == 1 else 4
                all_records.append(df)
                console.print(f"  [green]Extracted {len(df)} records[/green]")
            else:
                console.print(f"  [yellow]No records extracted[/yellow]")
        except Exception as e:
            console.print(f"  [red]Error: {e}[/red]")

    if all_records:
        return pd.concat(all_records, ignore_index=True)
    return pd.DataFrame()


def transform_to_unified(df: pd.DataFrame) -> pd.DataFrame:
    """Transform parsed California data to unified schema."""
    # MBF to tons conversion (rough average for softwood sawtimber)
    MBF_TO_TONS = 4.0

    rows = []
    for _, row in df.iterrows():
        price_mbf = row['price_mbf']
        if pd.isna(price_mbf) or price_mbf == 'N/A':
            continue

        # Calculate price per ton
        price_per_ton = float(price_mbf) / MBF_TO_TONS

        # Map species code to standardized name
        species_std = SPECIES_MAP.get(row['species_code'], row['species'].lower().replace(' ', '_').replace('-', '_'))

        rows.append({
            'source': 'CA',
            'year': int(row['year']),
            'quarter': None,  # Semi-annual data
            'period_type': 'semi-annual',
            'region': f"TVA_{row['timber_value_area']}",
            'county': TVA_COUNTIES.get(row['timber_value_area'], ''),
            'species': species_std,
            'product_type': f"sawtimber_{row['timber_type']}",
            'price_avg': float(price_mbf),
            'price_low': None,
            'price_high': None,
            'unit': '$/MBF',
            'price_per_ton': round(price_per_ton, 2),
            'conversion_factor': MBF_TO_TONS,
            'sample_size': None,
            'notes': f"CDTFA harvest values {row['year']} H{row['half']}. Size: {row['size_code']}. Tax assessment values, not market.",
        })

    return pd.DataFrame(rows)


def show_summary(df: pd.DataFrame, title: str):
    """Display summary statistics."""
    table = RichTable(title=title)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total rows", str(len(df)))
    table.add_row("Year range", f"{df['year'].min()} - {df['year'].max()}")
    table.add_row("Species", str(df['species'].nunique()))
    table.add_row("Timber Value Areas", str(df['region'].nunique()))

    console.print(table)


def main():
    console.print("[bold]Parsing California CDTFA Harvest Values[/bold]\n")

    # Parse all PDFs
    df = parse_all_pdfs()

    if len(df) == 0:
        console.print("[red]No data extracted from PDFs[/red]")
        return

    console.print(f"\n[green]Total raw records: {len(df)}[/green]")

    # Save raw parsed data
    raw_output = RAW_DIR / "ca_stumpage_parsed.csv"
    df.to_csv(raw_output, index=False)
    console.print(f"[blue]Saved raw parsed data to {raw_output}[/blue]")

    # Transform to unified schema
    unified_df = transform_to_unified(df)

    show_summary(unified_df, "California CDTFA Data Transformed")

    # Show by year
    console.print("\n[bold]Records by Year:[/bold]")
    year_counts = unified_df.groupby('year').size()
    for year, count in year_counts.items():
        console.print(f"  {year}: {count} records")

    # Show by species
    console.print("\n[bold]Records by Species:[/bold]")
    species_counts = unified_df.groupby('species').size().sort_values(ascending=False)
    for species, count in species_counts.items():
        console.print(f"  {species}: {count}")

    return unified_df


if __name__ == "__main__":
    main()
