"""South Carolina Forestry Commission timber price data downloader.

Downloads quarterly timber price reports from the SC Forestry Commission.
Data available from Q1 2020 through present as HTML pages with tables.

Data source: https://www.scfc.gov/resources/public-information/landowner-resources/timber-prices/
"""

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from timber_prices.downloaders.base import BaseDownloader

console = Console()

# SC Forestry Commission timber prices base URL
BASE_URL = "https://www.scfc.gov/resources/public-information/landowner-resources/timber-prices"

# Available quarterly reports (2020-2025)
# Note: Some URLs use abbreviated paths, so we define the full URL for each
QUARTERLY_REPORTS = {
    2025: {
        1: f"{BASE_URL}/timber-prices-2025-1st-quarter/",
        2: f"{BASE_URL}/timber-prices-2025-2nd-quarter/",
        # Q3 2025 available through acknowledgement page, not direct link
    },
    2024: {
        1: f"{BASE_URL}/timber-prices-2024-1st-quarter/",
        2: f"{BASE_URL}/timber-prices-2024-2nd-quarter/",
        3: f"{BASE_URL}/timber-prices-2024-3rd-quarter/",
        4: f"{BASE_URL}/timber-prices-2024-4th-quarter/",
    },
    2023: {
        1: f"{BASE_URL}/timber-prices-2023-1st-quarter/",
        2: f"{BASE_URL}/timber-prices-2023-2nd-quarter/",
        3: f"{BASE_URL}/timber-prices-2023-3rd-quarter/",
        4: f"{BASE_URL}/timber-prices-2023-4th-quarter/",
    },
    2022: {
        1: f"{BASE_URL}/timber-prices-2022-1st-quarter/",
        2: f"{BASE_URL}/timber-prices-2022-2nd-quarter/",
        3: f"{BASE_URL}/timber-prices-2022-3rd-quarter/",
        4: f"{BASE_URL}/timber-prices-2022-4th-quarter/",
    },
    2021: {
        1: f"{BASE_URL}/timber-prices-2021-1st-quarter/",
        2: f"{BASE_URL}/timber-prices-2021-2nd-quarter/",
        # Q3 2021 not available
        4: f"{BASE_URL}/timber-prices-2021-4th-quarter/",
    },
    2020: {
        1: f"{BASE_URL}/timber-prices-2020-1st-quarter/",
        2: f"{BASE_URL}/timber-prices-2020-2nd-quarter/",
        3: f"{BASE_URL}/timber-prices-2020-3rd-quarter/",
        4: f"{BASE_URL}/timber-prices-2020-4th-quarter/",
    },
}


class SouthCarolinaForestryDownloader(BaseDownloader):
    """Download timber price data from SC Forestry Commission.

    SC Forestry Commission publishes quarterly timber price reports
    in partnership with TimberMart-South. Reports are presented as
    HTML pages containing tables with:
    - Statewide average stumpage prices
    - 5-quarter price history
    - Year-over-year changes

    Products covered:
    - Pine pulpwood
    - Pine chip-n-saw
    - Pine sawtimber
    - Hardwood pulpwood
    - Hardwood sawtimber

    Data coverage:
    - Geographic: Statewide South Carolina
    - Temporal: Quarterly (Q1 2020 - present)
    """

    @property
    def source_name(self) -> str:
        return "South Carolina Forestry Commission Timber Prices"

    @property
    def source_id(self) -> str:
        return "sc_forestry"

    def download(self, years: list[int] | None = None) -> list[Path]:
        """Download SC Forestry Commission timber price pages.

        Args:
            years: Optional list of years to download. Defaults to all available.

        Returns:
            List of paths to downloaded HTML files
        """
        console.print(f"\n[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold]{self.source_name}[/bold]")
        console.print(f"[dim]Quarterly stumpage prices - HTML tables (2020-2025)[/dim]")
        console.print(f"[bold blue]{'='*60}[/bold blue]\n")

        # Determine which years to download
        if years is None:
            years = sorted(QUARTERLY_REPORTS.keys(), reverse=True)

        downloaded = []
        failed = []

        for year in years:
            if year not in QUARTERLY_REPORTS:
                console.print(f"[yellow]No reports available for {year}[/yellow]")
                continue

            quarters = QUARTERLY_REPORTS[year]
            for quarter, url in quarters.items():
                local_filename = f"sc_timber_{year}_q{quarter}.html"

                try:
                    # Download HTML page
                    html_path = self.download_file(url, local_filename)

                    # Verify it's valid HTML
                    size_kb = html_path.stat().st_size / 1024

                    with open(html_path, "r", encoding="utf-8") as f:
                        content = f.read(500)

                    if "<!DOCTYPE" in content or "<html" in content.lower():
                        downloaded.append(html_path)
                    else:
                        console.print(f"[yellow]Invalid file for {year} Q{quarter} (not HTML)[/yellow]")
                        html_path.unlink()
                        failed.append((year, quarter))

                except Exception as e:
                    console.print(f"[yellow]Could not download {year} Q{quarter}:[/yellow] {e}")
                    failed.append((year, quarter))

        console.print(f"\n[bold green]Downloaded {len(downloaded)} quarterly reports[/bold green]")
        if failed:
            console.print(f"[yellow]Failed: {len(failed)} reports[/yellow]")

        return downloaded

    def download_recent(self, num_years: int = 3) -> list[Path]:
        """Download the most recent N years of reports.

        Args:
            num_years: Number of recent years to download

        Returns:
            List of paths to downloaded files
        """
        recent_years = sorted(QUARTERLY_REPORTS.keys(), reverse=True)[:num_years]
        return self.download(years=recent_years)

    def parse(self) -> dict[str, Any]:
        """Parse SC Forestry Commission HTML pages.

        Note: Full HTML parsing requires BeautifulSoup.

        Returns:
            Dictionary with file metadata
        """
        console.print("\n[bold]SC Forestry reports are HTML pages.[/bold]")
        console.print("[dim]HTML parsing with BeautifulSoup can extract table data.[/dim]")
        console.print("[dim]Each page contains 5 quarters of stumpage prices.[/dim]\n")

        results = {}
        for year in QUARTERLY_REPORTS:
            year_data = {}
            for quarter in QUARTERLY_REPORTS[year]:
                html_path = self.download_dir / f"sc_timber_{year}_q{quarter}.html"
                if html_path.exists():
                    size_kb = html_path.stat().st_size / 1024
                    year_data[f"Q{quarter}"] = {
                        "file": str(html_path),
                        "status": "downloaded",
                        "format": "HTML",
                        "size_kb": round(size_kb, 1),
                    }
            if year_data:
                results[year] = year_data

        return results

    def get_summary(self) -> None:
        """Print summary of SC data."""
        table = Table(title="SC Forestry Commission Timber Prices")
        table.add_column("Year", style="cyan")
        table.add_column("Q1", style="white")
        table.add_column("Q2", style="white")
        table.add_column("Q3", style="white")
        table.add_column("Q4", style="white")

        for year in sorted(QUARTERLY_REPORTS.keys(), reverse=True):
            row = [str(year)]
            for quarter in [1, 2, 3, 4]:
                html_path = self.download_dir / f"sc_timber_{year}_q{quarter}.html"
                if html_path.exists():
                    row.append("[green]Yes[/green]")
                elif quarter in QUARTERLY_REPORTS.get(year, {}):
                    row.append("[dim]No[/dim]")
                else:
                    row.append("[dim]-[/dim]")
            table.add_row(*row)

        console.print(table)

        # Count totals
        total_available = sum(len(q) for q in QUARTERLY_REPORTS.values())
        total_downloaded = len(list(self.download_dir.glob("sc_timber_*.html")))
        console.print(f"\n[dim]Total available: {total_available} reports ({len(QUARTERLY_REPORTS)} years)[/dim]")
        console.print(f"[dim]Downloaded: {total_downloaded} reports[/dim]")


if __name__ == "__main__":
    with SouthCarolinaForestryDownloader() as downloader:
        files = downloader.download()
        downloader.get_summary()
