"""Parse South Carolina Forestry Commission stumpage price data from HTML files."""

import re
from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd
from rich.console import Console
from rich.table import Table

console = Console()


def extract_year_quarter_from_filename(filename: str) -> tuple[int, int]:
    """Extract year and quarter from filename like 'sc_timber_2020_q1.html'."""
    match = re.search(r"sc_timber_(\d{4})_q(\d)", filename)
    if match:
        year = int(match.group(1))
        quarter = int(match.group(2))
        return year, quarter
    raise ValueError(f"Could not extract year and quarter from filename: {filename}")


def parse_quarter_string(quarter_str: str) -> tuple[int, int]:
    """Parse quarter string like '20201st quarter' to (year, quarter)."""
    # Extract year (first 4 digits)
    year_match = re.search(r"(\d{4})", quarter_str)
    if not year_match:
        raise ValueError(f"Could not extract year from quarter string: {quarter_str}")

    year = int(year_match.group(1))

    # Extract quarter number (1st, 2nd, 3rd, 4th)
    if "1st" in quarter_str:
        quarter = 1
    elif "2nd" in quarter_str:
        quarter = 2
    elif "3rd" in quarter_str:
        quarter = 3
    elif "4th" in quarter_str:
        quarter = 4
    else:
        raise ValueError(f"Could not extract quarter from quarter string: {quarter_str}")

    return year, quarter


def clean_price(price_str: str) -> float | None:
    """Clean price string like '$11.49' or '+$0.84' to float."""
    if not price_str or price_str.strip() == "":
        return None

    # Remove dollar signs and plus signs
    cleaned = price_str.replace("$", "").replace("+", "").strip()

    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_product_name(product_str: str) -> tuple[str, str]:
    """Parse product name into species and product type."""
    product_str = product_str.strip()

    if "Pine" in product_str:
        species = "Pine"
        if "pulpwood" in product_str.lower():
            product_type = "pulpwood"
        elif "chip-n-saw" in product_str.lower():
            product_type = "chip-n-saw"
        elif "sawtimber" in product_str.lower():
            product_type = "sawtimber"
        else:
            product_type = product_str.replace("Pine", "").strip()
    elif "Hardwood" in product_str:
        species = "Hardwood"
        if "pulpwood" in product_str.lower():
            product_type = "pulpwood"
        elif "sawtimber" in product_str.lower():
            product_type = "sawtimber"
        else:
            product_type = product_str.replace("Hardwood", "").strip()
    else:
        species = "Unknown"
        product_type = product_str

    return species, product_type


def parse_html_file(html_file: Path) -> list[dict]:
    """Parse a single HTML file and extract stumpage prices."""
    records = []

    with open(html_file, "r", encoding="utf-8") as file:
        content = file.read()

    soup = BeautifulSoup(content, "html.parser")
    table = soup.find("table")

    if not table:
        console.print(f"[yellow]Warning: No table found in {html_file.name}[/yellow]")
        return records

    rows = table.find_all("tr")

    if len(rows) < 2:
        console.print(f"[yellow]Warning: Not enough rows in {html_file.name}[/yellow]")
        return records

    # Parse header row to get quarter information
    header_row = rows[0]
    header_cells = header_row.find_all(["td", "th"])
    header_text = [cell.get_text(strip=True) for cell in header_cells]

    # First column is "Product type", rest are quarters
    quarter_headers = header_text[1:]

    # Parse quarter information (skip the last column which is "1-year change")
    quarters_info = []
    for header in quarter_headers:
        if "change" not in header.lower():
            try:
                year, quarter = parse_quarter_string(header)
                quarters_info.append((year, quarter))
            except ValueError as e:
                console.print(f"[yellow]Warning: {e}[/yellow]")

    # Parse data rows
    for row in rows[1:]:
        cells = row.find_all(["td", "th"])
        if len(cells) < 2:
            continue

        cell_text = [cell.get_text(strip=True) for cell in cells]
        product_name = cell_text[0]
        prices = cell_text[1:]

        # Parse product name
        species, product_type = parse_product_name(product_name)

        # Extract prices for each quarter (skip the last column which is "1-year change")
        for idx, (year, quarter) in enumerate(quarters_info):
            if idx < len(prices):
                price = clean_price(prices[idx])

                if price is not None:
                    record = {
                        "year": year,
                        "quarter": quarter,
                        "region": "Statewide",  # SC data appears to be statewide
                        "species": species,
                        "product_type": product_type,
                        "price_avg": price,
                        "price_low": None,  # Not available in this dataset
                        "price_high": None,  # Not available in this dataset
                        "unit": "$/ton",  # Standard stumpage price unit
                    }
                    records.append(record)

    return records


def parse_all_files() -> pd.DataFrame:
    """Parse all HTML files and return a combined DataFrame."""
    data_dir = Path("/Users/mihiarc/landuse-model/forest-rents/data/raw/sc_forestry/")
    html_files = sorted(data_dir.glob("sc_timber_*.html"))

    console.print(f"[bold cyan]Found {len(html_files)} HTML files to parse[/bold cyan]\n")

    all_records = []
    for html_file in html_files:
        console.print(f"Parsing {html_file.name}...")
        records = parse_html_file(html_file)
        all_records.extend(records)

    # Convert to DataFrame
    dataframe = pd.DataFrame(all_records)

    # Remove duplicates (since files have overlapping quarters)
    if not dataframe.empty:
        dataframe = dataframe.drop_duplicates(
            subset=["year", "quarter", "species", "product_type"], keep="last"
        )

        # Sort by year, quarter, species, product_type
        dataframe = dataframe.sort_values(
            ["year", "quarter", "species", "product_type"]
        ).reset_index(drop=True)

    return dataframe


def main():
    """Main function to parse all files and save to CSV."""
    console.print("[bold green]South Carolina Stumpage Price Parser[/bold green]\n")

    # Parse all files
    dataframe = parse_all_files()

    if dataframe.empty:
        console.print("[bold red]Error: No data extracted![/bold red]")
        return

    # Save to CSV
    output_file = Path(
        "/Users/mihiarc/landuse-model/forest-rents/data/raw/sc_forestry/sc_stumpage_parsed.csv"
    )
    dataframe.to_csv(output_file, index=False)

    console.print(f"\n[bold green]Data saved to: {output_file}[/bold green]\n")

    # Print summary statistics
    console.print("[bold]Summary Statistics:[/bold]")
    console.print(f"  Total records extracted: {len(dataframe)}")
    console.print(f"  Year range: {dataframe['year'].min()} - {dataframe['year'].max()}")
    console.print(f"  Quarters covered: {dataframe['quarter'].min()} - {dataframe['quarter'].max()}")
    console.print(f"  Species: {', '.join(dataframe['species'].unique())}")
    console.print(f"  Product types: {', '.join(dataframe['product_type'].unique())}")

    # Show sample data
    console.print("\n[bold]Sample Data (first 10 rows):[/bold]")
    rich_table = Table(show_header=True, header_style="bold magenta")

    for col in dataframe.columns:
        rich_table.add_column(col)

    for _, row in dataframe.head(10).iterrows():
        rich_table.add_row(*[str(val) for val in row])

    console.print(rich_table)

    # Show summary by species and product type
    console.print("\n[bold]Price Summary by Product:[/bold]")
    summary = (
        dataframe.groupby(["species", "product_type"])["price_avg"]
        .agg(["count", "min", "max", "mean"])
        .round(2)
    )
    console.print(summary)


if __name__ == "__main__":
    main()
