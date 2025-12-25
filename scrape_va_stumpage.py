"""
Scrape and parse Virginia stumpage price data from Virginia Tech.

This script fetches historical timber stumpage prices from Virginia Tech's
Forest Update website and saves the parsed data to a CSV file.
"""

import re
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table

console = Console()


def fetch_html(url: str) -> str:
    """Fetch HTML content from the given URL."""
    console.print(f"[cyan]Fetching data from:[/cyan] {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    console.print("[green]✓[/green] Successfully fetched HTML content")
    return response.text


def extract_product_info(header_text: str) -> tuple[str, str, str]:
    """
    Extract product type, species, and unit from table header.

    Returns:
        tuple: (species, product_type, unit)
    """
    header_lower = header_text.lower()

    # Determine product type first (order matters - chip-n-saw before sawtimber)
    if "chip-n-saw" in header_lower or "chip n saw" in header_lower:
        product_type = "Chip-n-saw"
        species = "Pine"  # Chip-n-saw is always pine
    elif "sawtimber" in header_lower:
        product_type = "Sawtimber"
        # Determine species for sawtimber
        if "pine" in header_lower:
            species = "Pine"
        elif "oak" in header_lower:
            species = "Oak"
        elif "hardwood" in header_lower or "mixed hardwood" in header_lower:
            species = "Mixed hardwood"
        else:
            species = "Unknown"
    elif "pulpwood" in header_lower:
        product_type = "Pulpwood"
        # Determine species for pulpwood
        if "pine" in header_lower:
            species = "Pine"
        elif "hardwood" in header_lower:
            species = "Hardwood"
        else:
            species = "Unknown"
    else:
        product_type = "Unknown"
        species = "Unknown"

    # Determine unit
    if "mbf" in header_lower or "thousand board feet" in header_lower:
        unit = "$/MBF"
    elif "ton" in header_lower:
        unit = "$/ton"
    else:
        unit = "$/unit"

    return species, product_type, unit


def parse_price_value(price_str: str) -> float | None:
    """Parse price string to float, handling 'Missing' and other formats."""
    if not price_str or price_str.strip().lower() in ["missing", "", "-"]:
        return None

    # Remove dollar signs, commas, and extra whitespace
    cleaned = re.sub(r"[$,\s]", "", price_str)

    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_stumpage_tables(html: str) -> pd.DataFrame:
    """Parse all stumpage price tables from the HTML."""
    soup = BeautifulSoup(html, "html.parser")
    all_data = []

    # Find all tables on the page
    tables = soup.find_all("table")
    console.print(f"[cyan]Found {len(tables)} tables on the page[/cyan]")

    for table_idx, table in enumerate(tables):
        # Find the preceding header to identify the product type
        header = None
        prev_element = table.find_previous(["h2", "h3", "h4", "p", "strong"])

        # Try to find a header that contains product information
        search_element = table.find_previous()
        attempts = 0
        while search_element and attempts < 20:
            text = search_element.get_text(strip=True)
            if any(keyword in text.lower() for keyword in
                   ["pine", "oak", "hardwood", "sawtimber", "pulpwood", "chip"]):
                header = text
                break
            search_element = search_element.find_previous()
            attempts += 1

        if not header:
            console.print(f"[yellow]⚠[/yellow] Skipping table {table_idx + 1} - no product header found")
            continue

        species, product_type, unit = extract_product_info(header)
        console.print(f"[green]✓[/green] Processing: {species} {product_type} ({unit})")

        # Parse table rows
        rows = table.find_all("tr")

        for row_idx, row in enumerate(rows):
            cells = row.find_all(["td", "th"])

            # Skip header rows
            if not cells or len(cells) < 3:
                continue

            cell_texts = [cell.get_text(strip=True) for cell in cells]

            # Skip if this looks like a header row
            if "year" in cell_texts[0].lower() or "quarter" in cell_texts[1].lower():
                continue

            # Parse year, quarter, and price
            try:
                year_str = cell_texts[0]
                quarter_str = cell_texts[1]
                price_str = cell_texts[2] if len(cell_texts) > 2 else ""

                # Parse year
                year_match = re.search(r"\d{4}", year_str)
                if not year_match:
                    continue
                year = int(year_match.group())

                # Parse quarter
                quarter_match = re.search(r"Q?(\d)", quarter_str, re.IGNORECASE)
                if not quarter_match:
                    continue
                quarter = f"Q{quarter_match.group(1)}"

                # Parse price
                price = parse_price_value(price_str)

                # Assume region is statewide (can be refined if regional data exists)
                region = "Statewide"

                all_data.append({
                    "year": year,
                    "quarter": quarter,
                    "region": region,
                    "species": species,
                    "product_type": product_type,
                    "price_avg": price,
                    "unit": unit,
                })

            except (ValueError, IndexError) as e:
                console.print(f"[yellow]⚠[/yellow] Skipping row {row_idx + 1} in table {table_idx + 1}: {e}")
                continue

    df = pd.DataFrame(all_data)
    console.print(f"[green]✓[/green] Extracted {len(df)} total records")

    return df


def save_to_csv(df: pd.DataFrame, output_path: Path) -> None:
    """Save the DataFrame to a CSV file."""
    # Create directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Sort by year, quarter, species, product_type
    df_sorted = df.sort_values(
        by=["year", "quarter", "species", "product_type"],
        ascending=[True, True, True, True]
    )

    # Save to CSV
    df_sorted.to_csv(output_path, index=False)
    console.print(f"[green]✓[/green] Data saved to: {output_path}")


def print_summary(df: pd.DataFrame) -> None:
    """Print a summary of the extracted data."""
    console.print("\n[bold cyan]Data Summary[/bold cyan]")
    console.print(f"Total records: {len(df)}")
    console.print(f"Year range: {df['year'].min()} - {df['year'].max()}")
    console.print(f"Products: {df.groupby(['species', 'product_type']).size().to_dict()}")

    # Show sample data
    console.print("\n[bold cyan]Sample Data (first 10 rows):[/bold cyan]")

    sample_df = df.head(10)

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Year", style="cyan")
    table.add_column("Quarter", style="cyan")
    table.add_column("Region", style="green")
    table.add_column("Species", style="yellow")
    table.add_column("Product", style="yellow")
    table.add_column("Price", style="blue")
    table.add_column("Unit", style="blue")

    for _, row in sample_df.iterrows():
        price_str = f"${row['price_avg']:.2f}" if pd.notna(row['price_avg']) else "Missing"
        table.add_row(
            str(row['year']),
            row['quarter'],
            row['region'],
            row['species'],
            row['product_type'],
            price_str,
            row['unit']
        )

    console.print(table)

    # Show statistics by product
    console.print("\n[bold cyan]Records by Product:[/bold cyan]")
    product_counts = df.groupby(['species', 'product_type']).size().reset_index(name='count')

    prod_table = Table(show_header=True, header_style="bold magenta")
    prod_table.add_column("Species", style="yellow")
    prod_table.add_column("Product Type", style="yellow")
    prod_table.add_column("Record Count", style="blue")

    for _, row in product_counts.iterrows():
        prod_table.add_row(
            row['species'],
            row['product_type'],
            str(row['count'])
        )

    console.print(prod_table)


def main():
    """Main execution function."""
    console.print("[bold green]Virginia Stumpage Price Scraper[/bold green]\n")

    # Configuration
    url = "https://forestupdate.frec.vt.edu/resources/HistoricVirginiaTimberStumpagePrices.html"
    output_path = Path("/Users/mihiarc/landuse-model/forest-rents/data/raw/va_tech/va_stumpage_parsed.csv")

    try:
        # Fetch and parse data
        html = fetch_html(url)
        df = parse_stumpage_tables(html)

        if df.empty:
            console.print("[red]✗[/red] No data extracted. Please check the page structure.")
            return

        # Save to CSV
        save_to_csv(df, output_path)

        # Print summary
        print_summary(df)

        console.print("\n[bold green]✓ Scraping completed successfully![/bold green]")

    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        raise


if __name__ == "__main__":
    main()
