"""NC State Extension timber price data downloader.

Downloads historical stumpage prices from NC State Extension.
Data available from 1976-2024 for North Carolina regions.

Data source: https://content.ces.ncsu.edu/historic-north-carolina-timber-stumpage-prices-1976-2014
"""

from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table

from forest_rents.downloaders.base import BaseDownloader

console = Console()

# URLs for NC State Extension data
HISTORIC_PRICES_URL = "https://content.ces.ncsu.edu/historic-north-carolina-timber-stumpage-prices-1976-2014"

# Expected products in the tables
PRODUCTS = [
    "pine_sawtimber",
    "pine_pulpwood",
    "hardwood_sawtimber",
    "hardwood_pulpwood",
]

PRODUCT_NAMES = {
    "pine_sawtimber": "Pine Sawtimber",
    "pine_pulpwood": "Pine Pulpwood",
    "hardwood_sawtimber": "Mixed Hardwood Sawtimber",
    "hardwood_pulpwood": "Hardwood Pulpwood",
}


class NCStateDownloader(BaseDownloader):
    """Download stumpage data from NC State Extension."""

    @property
    def source_name(self) -> str:
        return "NC State Extension Historic Timber Prices"

    @property
    def source_id(self) -> str:
        return "nc_state"

    def download(self) -> list[Path]:
        """Download and save the historic prices HTML page.

        Returns:
            List containing path to the saved HTML file
        """
        console.print(f"\n[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold]{self.source_name}[/bold]")
        console.print(f"[dim]Historic timber stumpage prices 1976-2024[/dim]")
        console.print(f"[bold blue]{'='*60}[/bold blue]\n")

        # Download the HTML page
        response = self.client.get(HISTORIC_PRICES_URL)
        response.raise_for_status()

        # Save the raw HTML
        html_path = self.download_dir / "historic_prices.html"
        html_path.write_text(response.text, encoding="utf-8")
        console.print(f"[green]Saved:[/green] {html_path}")

        return [html_path]

    def parse(self) -> dict[str, pd.DataFrame]:
        """Parse the HTML tables into DataFrames.

        Returns:
            Dictionary mapping product names to DataFrames with price data
        """
        console.print("\n[bold]Parsing NC State historic price tables...[/bold]\n")

        html_path = self.download_dir / "historic_prices.html"
        if not html_path.exists():
            console.print("[red]Error: HTML file not found. Run download() first.[/red]")
            return {}

        html_content = html_path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html_content, "lxml")

        # Find all tables in the page
        tables = soup.find_all("table")
        console.print(f"[dim]Found {len(tables)} tables in the HTML[/dim]")

        results = {}

        for i, table in enumerate(tables):
            try:
                # Parse table to DataFrame
                df = self._parse_table(table, i)
                if df is not None and not df.empty:
                    # Try to identify the product based on table content
                    product_key = self._identify_product(table, i)
                    results[product_key] = df
                    console.print(
                        f"[green]Parsed:[/green] {PRODUCT_NAMES.get(product_key, product_key)} - "
                        f"{len(df)} years of data"
                    )
            except Exception as e:
                console.print(f"[yellow]Warning: Could not parse table {i}: {e}[/yellow]")

        # Save parsed data to CSV
        if results:
            self._save_parsed_data(results)

        return results

    def _parse_table(self, table, table_index: int) -> pd.DataFrame | None:
        """Parse an HTML table element to DataFrame."""
        rows = table.find_all("tr")
        if len(rows) < 3:  # Need header + at least some data
            return None

        data = []
        headers = None

        for row in rows:
            cells = row.find_all(["th", "td"])
            cell_texts = [cell.get_text(strip=True) for cell in cells]

            # Skip empty rows
            if not any(cell_texts):
                continue

            # First row with data becomes headers
            if headers is None:
                headers = cell_texts
                continue

            # Data rows
            if len(cell_texts) == len(headers):
                data.append(cell_texts)

        if not headers or not data:
            return None

        df = pd.DataFrame(data, columns=headers)

        # Clean up the DataFrame
        df = self._clean_dataframe(df)

        return df

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean up parsed DataFrame."""
        # Standardize column names
        df.columns = [col.lower().strip().replace(" ", "_").replace("-", "_") for col in df.columns]

        # Rename common column variations
        rename_map = {
            "eastern_nc": "eastern_nc",
            "western_nc": "western_nc",
            "state_wide": "statewide",
            "statewide": "statewide",
            "southeast": "southeast",
            "se": "southeast",
        }

        df = df.rename(columns=rename_map)

        # Convert year column to integer if present
        if "year" in df.columns:
            df["year"] = pd.to_numeric(df["year"], errors="coerce")
            df = df.dropna(subset=["year"])
            df["year"] = df["year"].astype(int)

        # Convert price columns to numeric
        price_cols = [c for c in df.columns if c != "year"]
        for col in price_cols:
            # Remove dollar signs, commas, handle "--" as NaN
            df[col] = df[col].astype(str).str.replace(r"[$,]", "", regex=True)
            df[col] = df[col].replace(["--", "-", "n/a", "N/A", ""], pd.NA)
            df[col] = pd.to_numeric(df[col], errors="coerce")

        return df

    def _identify_product(self, table, index: int) -> str:
        """Try to identify which product this table represents."""
        # Look for identifying text in preceding elements or table caption
        table_text = table.get_text().lower()

        if "pine" in table_text and "sawtimber" in table_text and "pulp" not in table_text:
            return "pine_sawtimber"
        elif "pine" in table_text and "pulp" in table_text:
            return "pine_pulpwood"
        elif "hardwood" in table_text and "sawtimber" in table_text:
            return "hardwood_sawtimber"
        elif "hardwood" in table_text and "pulp" in table_text:
            return "hardwood_pulpwood"
        else:
            # Fall back to index-based naming matching expected order
            if index < len(PRODUCTS):
                return PRODUCTS[index]
            return f"table_{index}"

    def _save_parsed_data(self, results: dict[str, pd.DataFrame]) -> None:
        """Save parsed data to CSV files."""
        for product_key, df in results.items():
            csv_path = self.download_dir / f"{product_key}.csv"
            df.to_csv(csv_path, index=False)
            console.print(f"[green]Saved CSV:[/green] {csv_path}")

        # Also create a combined long-format file
        combined_data = []
        for product_key, df in results.items():
            df_long = df.melt(
                id_vars=["year"] if "year" in df.columns else [],
                var_name="region",
                value_name="price",
            )
            df_long["product"] = product_key
            combined_data.append(df_long)

        if combined_data:
            combined_df = pd.concat(combined_data, ignore_index=True)
            combined_path = self.download_dir / "nc_stumpage_prices_combined.csv"
            combined_df.to_csv(combined_path, index=False)
            console.print(f"[green]Saved combined CSV:[/green] {combined_path}")

    def get_summary(self) -> None:
        """Print a summary of available NC State data."""
        table = Table(title="NC State Extension Stumpage Price Data")
        table.add_column("Product", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Years", style="green")

        for product_key in PRODUCTS:
            csv_path = self.download_dir / f"{product_key}.csv"
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                years = f"{df['year'].min()}-{df['year'].max()}" if "year" in df.columns else "N/A"
                status = "[green]Downloaded[/green]"
            else:
                years = "N/A"
                status = "[dim]Not downloaded[/dim]"

            table.add_row(
                PRODUCT_NAMES.get(product_key, product_key),
                status,
                years,
            )

        console.print(table)


if __name__ == "__main__":
    with NCStateDownloader() as downloader:
        files = downloader.download()
        results = downloader.parse()
        downloader.get_summary()
