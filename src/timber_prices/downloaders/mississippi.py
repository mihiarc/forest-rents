"""Mississippi State Extension timber price data downloader.

Downloads quarterly timber price reports from Mississippi State University
Extension Service. Data available from 2013-present with statewide stumpage
averages for pine and hardwood products.

Data source: https://extension.msstate.edu/natural-resources/forestry/forest-economics/timber-prices
"""

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from timber_prices.downloaders.base import BaseDownloader

console = Console()

# Base URL for Mississippi State Extension
BASE_URL = "https://extension.msstate.edu"

# Media IDs for quarterly reports by year
# Format: {year: {quarter: media_id or file_path}}
# Data extracted from the timber-prices-2013-present page
QUARTERLY_REPORTS = {
    2025: {
        1: {"type": "media", "id": 20712},
        2: {"type": "media", "id": 20713},
        3: {"type": "media", "id": 29140},
    },
    2024: {
        1: {"type": "media", "id": 20708},
        2: {"type": "media", "id": 20709},
        3: {"type": "media", "id": 20710},
        4: {"type": "media", "id": 20711},
    },
    # 2023: No reports available - referenced TimberMart-South
    2022: {
        1: {"type": "media", "id": 20704},
        2: {"type": "media", "id": 20705},
        3: {"type": "media", "id": 20706},
        4: {"type": "media", "id": 20707},
    },
    2021: {
        1: {"type": "media", "id": 20701},
        2: {"type": "media", "id": 20702},
        3: {"type": "media", "id": 20703},
        4: {"type": "media", "id": 20699},
    },
    2020: {
        1: {"type": "media", "id": 18758},
        2: {"type": "file", "path": "/sites/default/files/topic-files/timber-prices/timber-prices-2013-present/2Q%202020%20Price%20Report.pdf"},
        3: {"type": "media", "id": 18759},
        4: {"type": "media", "id": 18760},
    },
    2019: {
        1: {"type": "media", "id": 18754},
        2: {"type": "media", "id": 18755},
        3: {"type": "media", "id": 18756},
        4: {"type": "media", "id": 18757},
    },
    2018: {
        1: {"type": "file", "path": "/sites/default/files/topic-files/timber-prices/timber-prices-2013-present/Q1-2018-Price-Report.pdf"},
        2: {"type": "media", "id": 18752},
        3: {"type": "media", "id": 18753},
        4: {"type": "media", "id": 18735},
    },
    2017: {
        1: {"type": "media", "id": 29143},
        2: {"type": "media", "id": 29144},
        3: {"type": "media", "id": 18749},
        4: {"type": "media", "id": 18750},
    },
    2016: {
        1: {"type": "media", "id": 18748},
        2: {"type": "media", "id": 29145},
        3: {"type": "media", "id": 29146},
        4: {"type": "media", "id": 29147},
    },
    2015: {
        1: {"type": "media", "id": 18736},
        2: {"type": "media", "id": 18737},
        3: {"type": "media", "id": 18738},
        4: {"type": "media", "id": 18739},
    },
    2014: {
        1: {"type": "media", "id": 18740},
        2: {"type": "media", "id": 18741},
        3: {"type": "media", "id": 18742},
        4: {"type": "media", "id": 18743},
    },
    2013: {
        1: {"type": "media", "id": 18744},
        2: {"type": "media", "id": 18745},
        3: {"type": "media", "id": 18746},
        4: {"type": "media", "id": 18747},
    },
}


class MississippiExtensionDownloader(BaseDownloader):
    """Download timber price data from Mississippi State Extension.

    Mississippi publishes quarterly timber price reports with statewide
    stumpage averages. Data collected from timber sales across the state.

    Products covered:
    - Pine sawtimber
    - Pine chip-n-saw
    - Pine pulpwood
    - Oak sawtimber
    - Mixed hardwood sawtimber
    - Hardwood pulpwood
    """

    @property
    def source_name(self) -> str:
        return "Mississippi State Extension Timber Price Reports"

    @property
    def source_id(self) -> str:
        return "ms_extension"

    def _get_url(self, report_info: dict) -> str:
        """Get the download URL for a report.

        Args:
            report_info: Dictionary with 'type' and 'id' or 'path'

        Returns:
            Full URL for downloading the report
        """
        if report_info["type"] == "media":
            return f"{BASE_URL}/media/{report_info['id']}/download?inline="
        else:
            return f"{BASE_URL}{report_info['path']}"

    def download(self, years: list[int] | None = None) -> list[Path]:
        """Download Mississippi timber price reports.

        Args:
            years: Optional list of years to download. Defaults to all available.

        Returns:
            List of paths to downloaded PDF files
        """
        console.print(f"\n[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold]{self.source_name}[/bold]")
        console.print(f"[dim]Quarterly stumpage prices - pine & hardwood (2013-2025)[/dim]")
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
            for quarter, report_info in quarters.items():
                url = self._get_url(report_info)
                local_filename = f"ms_timber_{year}_q{quarter}.pdf"

                try:
                    pdf_path = self.download_file(url, local_filename)

                    # Verify it's a valid PDF (not an error page or image)
                    size_kb = pdf_path.stat().st_size / 1024

                    # Check if it's actually a PDF by reading first bytes
                    with open(pdf_path, "rb") as f:
                        header = f.read(4)

                    if header == b"%PDF" and size_kb > 5:
                        downloaded.append(pdf_path)
                    else:
                        console.print(f"[yellow]Invalid file for {year} Q{quarter} (not a PDF)[/yellow]")
                        pdf_path.unlink()
                        failed.append((year, quarter))

                except Exception as e:
                    console.print(f"[yellow]Could not download {year} Q{quarter}:[/yellow] {e}")
                    failed.append((year, quarter))

        console.print(f"\n[bold green]Downloaded {len(downloaded)} quarterly reports[/bold green]")
        if failed:
            console.print(f"[yellow]Failed: {len(failed)} reports[/yellow]")

        return downloaded

    def download_recent(self, num_years: int = 5) -> list[Path]:
        """Download the most recent N years of reports.

        Args:
            num_years: Number of recent years to download

        Returns:
            List of paths to downloaded files
        """
        recent_years = sorted(QUARTERLY_REPORTS.keys(), reverse=True)[:num_years]
        return self.download(years=recent_years)

    def parse(self) -> dict[str, Any]:
        """Parse Mississippi timber price PDF reports.

        Note: PDF parsing requires additional tools like pdfplumber.

        Returns:
            Dictionary with file metadata
        """
        console.print("\n[bold]Mississippi reports are PDFs.[/bold]")
        console.print("[dim]PDF parsing requires pdfplumber or similar tools.[/dim]")
        console.print("[dim]Data contains statewide stumpage averages by product.[/dim]\n")

        results = {}
        for year in QUARTERLY_REPORTS:
            year_data = {}
            for quarter in QUARTERLY_REPORTS[year]:
                pdf_path = self.download_dir / f"ms_timber_{year}_q{quarter}.pdf"
                if pdf_path.exists():
                    size_kb = pdf_path.stat().st_size / 1024
                    year_data[f"Q{quarter}"] = {
                        "file": str(pdf_path),
                        "status": "downloaded",
                        "format": "PDF",
                        "size_kb": round(size_kb, 1),
                    }
            if year_data:
                results[year] = year_data

        return results

    def get_summary(self) -> None:
        """Print summary of Mississippi data."""
        table = Table(title="Mississippi State Extension Timber Price Reports")
        table.add_column("Year", style="cyan")
        table.add_column("Q1", style="white")
        table.add_column("Q2", style="white")
        table.add_column("Q3", style="white")
        table.add_column("Q4", style="white")

        for year in sorted(QUARTERLY_REPORTS.keys(), reverse=True):
            row = [str(year)]
            for quarter in [1, 2, 3, 4]:
                pdf_path = self.download_dir / f"ms_timber_{year}_q{quarter}.pdf"
                if pdf_path.exists():
                    row.append("[green]Yes[/green]")
                elif quarter in QUARTERLY_REPORTS.get(year, {}):
                    row.append("[dim]No[/dim]")
                else:
                    row.append("[dim]-[/dim]")
            table.add_row(*row)

        console.print(table)

        # Count total available and downloaded
        total_available = sum(len(q) for q in QUARTERLY_REPORTS.values())
        total_downloaded = len(list(self.download_dir.glob("ms_timber_*.pdf")))
        console.print(f"\n[dim]Total available: {total_available} reports ({len(QUARTERLY_REPORTS)} years)[/dim]")
        console.print(f"[dim]Downloaded: {total_downloaded} reports[/dim]")


if __name__ == "__main__":
    with MississippiExtensionDownloader() as downloader:
        # Download recent 5 years by default
        files = downloader.download_recent(5)
        downloader.get_summary()
