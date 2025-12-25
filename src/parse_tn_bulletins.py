"""
Parse Tennessee Forest Products Bulletin PDFs to extract stumpage price data.

This script uses pdfplumber to extract stumpage price tables from PDF bulletins
and converts them to a structured CSV format.
"""
import re
from pathlib import Path
from typing import List, Dict, Optional
import pdfplumber
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()


class TNBulletinParser:
    """Parser for Tennessee Forest Products Bulletin PDFs."""

    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self.year = None
        self.quarter = None
        self._extract_date_from_filename()

    def _extract_date_from_filename(self) -> None:
        """Extract year and quarter from filename."""
        filename = self.pdf_path.stem

        # Try various patterns
        patterns = [
            r'(?P<year>\d{4}).*?[Qq](?P<quarter>\d)',  # TFPB_2017_Q1
            r'(?P<year>\d{4}).*?(?P<quarter>[1-4])',   # TFPB_2017_1
            r'(?P<quarter>[1-4]).*?(?P<year>\d{4})',   # Q1_2017
        ]

        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                self.year = int(match.group('year'))
                self.quarter = int(match.group('quarter'))
                break

        if not self.year:
            console.print(f"[yellow]Warning: Could not extract date from {filename}[/yellow]")

    def parse(self) -> List[Dict]:
        """Parse the PDF and extract stumpage price data."""
        console.print(f"[cyan]Parsing {self.pdf_path.name}...[/cyan]")

        records = []

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract text and tables
                    text = page.extract_text()
                    tables = page.extract_tables()

                    # Try to extract year/quarter from text if not in filename
                    if not self.year:
                        self._extract_date_from_text(text)

                    # Process each table
                    for table_idx, table in enumerate(tables):
                        if self._is_stumpage_table(table):
                            table_records = self._parse_stumpage_table(table)
                            records.extend(table_records)

                            console.print(f"  [green]Found stumpage table on page {page_num} "
                                        f"(extracted {len(table_records)} records)[/green]")

        except Exception as e:
            console.print(f"[red]Error parsing {self.pdf_path.name}: {e}[/red]")

        return records

    def _extract_date_from_text(self, text: str) -> None:
        """Extract year and quarter from page text."""
        # Look for patterns like "First Quarter 2017", "Q1 2017", "January-March 2017"
        quarter_patterns = {
            r'(?:first|1st).*?quarter.*?(\d{4})': 1,
            r'(?:second|2nd).*?quarter.*?(\d{4})': 2,
            r'(?:third|3rd).*?quarter.*?(\d{4})': 3,
            r'(?:fourth|4th).*?quarter.*?(\d{4})': 4,
            r'[Qq]1.*?(\d{4})': 1,
            r'[Qq]2.*?(\d{4})': 2,
            r'[Qq]3.*?(\d{4})': 3,
            r'[Qq]4.*?(\d{4})': 4,
            r'january.*?march.*?(\d{4})': 1,
            r'april.*?june.*?(\d{4})': 2,
            r'july.*?september.*?(\d{4})': 3,
            r'october.*?december.*?(\d{4})': 4,
        }

        text_lower = text.lower()
        for pattern, quarter in quarter_patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                self.year = int(match.group(1))
                self.quarter = quarter
                break

    def _is_stumpage_table(self, table: List[List]) -> bool:
        """Check if a table contains stumpage price data."""
        if not table or len(table) < 2:
            return False

        # Convert to string for searching
        table_text = ' '.join([' '.join([str(cell) or '' for cell in row]) for row in table[:3]])
        table_text_lower = table_text.lower()

        # Look for stumpage-related keywords
        stumpage_keywords = [
            'stumpage', 'price', 'species', 'sawtimber', 'pulpwood',
            'pine', 'hardwood', 'oak', 'yellow poplar', 'average',
            'high', 'low', 'range', 'ton', 'mbf', 'cord'
        ]

        keyword_count = sum(1 for keyword in stumpage_keywords if keyword in table_text_lower)

        return keyword_count >= 3

    def _parse_stumpage_table(self, table: List[List]) -> List[Dict]:
        """Parse a stumpage price table into structured records."""
        records = []

        if not table:
            return records

        # Find header row (usually first non-empty row)
        header_row = None
        data_start = 1

        for idx, row in enumerate(table[:5]):
            row_text = ' '.join([str(cell) or '' for cell in row]).lower()
            if 'species' in row_text or 'product' in row_text:
                header_row = row
                data_start = idx + 1
                break

        # Process data rows
        for row in table[data_start:]:
            # Skip empty rows
            if not any(row):
                continue

            # Extract species/product name (usually first column)
            species = str(row[0]).strip() if row[0] else None
            if not species or species.lower() in ['', 'none', 'total']:
                continue

            # Try to extract price data
            record = self._extract_price_from_row(row, species)
            if record:
                records.append(record)

        return records

    def _extract_price_from_row(self, row: List, species: str) -> Optional[Dict]:
        """Extract price information from a table row."""
        # Convert row to strings and clean
        cleaned_row = []
        for cell in row:
            if cell is None:
                cleaned_row.append('')
            else:
                # Remove currency symbols, commas
                cell_str = str(cell).strip().replace('$', '').replace(',', '')
                cleaned_row.append(cell_str)

        # Extract numeric values (potential prices)
        numbers = []
        for cell in cleaned_row[1:]:  # Skip species column
            try:
                # Try to parse as float
                if cell and cell.replace('.', '').replace('-', '').isdigit():
                    numbers.append(float(cell))
            except:
                continue

        if not numbers:
            return None

        # Determine product type from species name
        species_lower = species.lower()
        product_type = 'unknown'

        if 'sawtimber' in species_lower or 'saw timber' in species_lower or 'sawlog' in species_lower:
            product_type = 'sawtimber'
        elif 'pulpwood' in species_lower or 'pulp wood' in species_lower:
            product_type = 'pulpwood'
        elif 'chip' in species_lower and 'saw' in species_lower or 'cns' in species_lower:
            product_type = 'chip-n-saw'
        elif 'veneer' in species_lower:
            product_type = 'veneer'

        # Extract region if mentioned
        region = 'statewide'
        region_keywords = {
            'east': 'east',
            'west': 'west',
            'middle': 'middle',
            'north': 'north',
            'south': 'south',
            'central': 'central',
        }

        for keyword, region_name in region_keywords.items():
            if keyword in species_lower:
                region = region_name
                # Clean species name
                species = re.sub(rf'\b{keyword}\b', '', species, flags=re.IGNORECASE).strip()
                break

        # Clean up species name
        species = re.sub(r'\s+', ' ', species).strip()

        # Determine price fields
        # Common patterns: [avg], [low, high], [avg, low, high]
        price_avg = None
        price_low = None
        price_high = None

        if len(numbers) == 1:
            price_avg = numbers[0]
        elif len(numbers) == 2:
            price_low = numbers[0]
            price_high = numbers[1]
            price_avg = (price_low + price_high) / 2
        elif len(numbers) >= 3:
            # Assume format: avg, low, high or low, avg, high
            # Use statistics to determine
            price_avg = numbers[0]
            price_low = min(numbers)
            price_high = max(numbers)

        # Determine unit
        unit = 'unknown'
        row_text = ' '.join(cleaned_row).lower()

        if 'mbf' in row_text or 'thousand board feet' in row_text or '1000 bd' in row_text:
            unit = 'MBF'
        elif 'ton' in row_text:
            unit = 'ton'
        elif 'cord' in row_text:
            unit = 'cord'
        elif '/m' in row_text:
            unit = 'per thousand'

        return {
            'year': self.year,
            'quarter': self.quarter,
            'region': region,
            'species': species,
            'product_type': product_type,
            'price_avg': round(price_avg, 2) if price_avg else None,
            'price_low': round(price_low, 2) if price_low else None,
            'price_high': round(price_high, 2) if price_high else None,
            'unit': unit,
        }


def parse_all_bulletins(pdf_dir: Path, output_csv: Path) -> None:
    """Parse all PDF bulletins in a directory and save to CSV."""
    console.print(f"\n[bold cyan]Tennessee Forest Products Bulletin Parser[/bold cyan]\n")

    pdf_dir = Path(pdf_dir)
    pdf_files = sorted(pdf_dir.glob('*.pdf'))

    if not pdf_files:
        console.print(f"[yellow]No PDF files found in {pdf_dir}[/yellow]")
        return

    console.print(f"Found {len(pdf_files)} PDF files to process\n")

    all_records = []

    for pdf_path in track(pdf_files, description="Processing PDFs..."):
        parser = TNBulletinParser(pdf_path)
        records = parser.parse()
        all_records.extend(records)

    if not all_records:
        console.print("[yellow]No stumpage data extracted from PDFs[/yellow]")
        return

    # Convert to DataFrame
    df = pd.DataFrame(all_records)

    # Sort by year, quarter, region, species
    df = df.sort_values(['year', 'quarter', 'region', 'species', 'product_type'])

    # Save to CSV
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)

    console.print(f"\n[bold green]Successfully parsed {len(df)} records![/bold green]")
    console.print(f"Output saved to: {output_csv}")

    # Display summary statistics
    summary_table = Table(title="\nSummary Statistics")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")

    summary_table.add_row("Total records", str(len(df)))
    summary_table.add_row("Years covered", f"{df['year'].min()}-{df['year'].max()}")
    summary_table.add_row("Unique species", str(df['species'].nunique()))
    summary_table.add_row("Unique regions", str(df['region'].nunique()))
    summary_table.add_row("Unique product types", str(df['product_type'].nunique()))

    console.print(summary_table)

    # Display sample data
    console.print("\n[bold]Sample data (first 10 rows):[/bold]")
    console.print(df.head(10).to_string())

    # Display species breakdown
    console.print("\n[bold]Species breakdown:[/bold]")
    species_counts = df['species'].value_counts().head(10)
    for species, count in species_counts.items():
        console.print(f"  {species}: {count} records")


if __name__ == "__main__":
    pdf_directory = Path("/Users/mihiarc/landuse-model/forest-rents/data/raw/tn_forestry")
    output_file = Path("/Users/mihiarc/landuse-model/forest-rents/data/raw/tn_forestry/tn_stumpage_parsed.csv")

    parse_all_bulletins(pdf_directory, output_file)
