"""Maine Forest Service stumpage price data downloader.

Downloads annual stumpage price reports from Maine Forest Service.
Data available from 2000-present by county, product, and species.

Data source: https://www.maine.gov/dacf/mfs/publications/annual_reports.html
"""

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from forest_rents.downloaders.base import BaseDownloader

console = Console()

# Base URL pattern for Maine attachments
BASE_URL = "https://www.maine.gov/tools/whatsnew/attach.php"

# Report IDs by year (discovered from the publications page)
REPORT_IDS = {
    2024: 13338663,
    2023: 13138879,
    2022: 12359545,
    2021: 11762628,
    2020: 6915492,
    2019: 4034732,
    2018: 1895130,
    2017: 810675,
    2016: 766046,
    2015: 723275,
    2014: 661708,
    2013: 626875,
    2012: 607752,
    2011: 526708,
    2010: 392084,
    2009: 263705,
    2008: 79762,
    2007: 392550,
    2006: 392551,
    2005: 392552,
    2004: 392553,
    2003: 392554,
    2002: 392555,
    2001: 392557,
    2000: 392559,
}


class MaineForestServiceDownloader(BaseDownloader):
    """Download stumpage data from Maine Forest Service."""

    @property
    def source_name(self) -> str:
        return "Maine Forest Service Stumpage Price Reports"

    @property
    def source_id(self) -> str:
        return "me_forest_service"

    def download(self, years: list[int] | None = None) -> list[Path]:
        """Download Maine stumpage price reports.

        Args:
            years: Optional list of years to download. Defaults to all available.

        Returns:
            List of paths to downloaded PDF files
        """
        console.print(f"\n[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold]{self.source_name}[/bold]")
        console.print(f"[dim]Annual stumpage by county, product, species (2000-2024)[/dim]")
        console.print(f"[bold blue]{'='*60}[/bold blue]\n")

        # Determine which years to download
        if years is None:
            years = sorted(REPORT_IDS.keys(), reverse=True)

        downloaded = []

        for year in years:
            if year not in REPORT_IDS:
                console.print(f"[yellow]No report available for {year}[/yellow]")
                continue

            report_id = REPORT_IDS[year]
            url = f"{BASE_URL}?id={report_id}&an=1"
            pdf_path = self.download_dir / f"me_stumpage_{year}.pdf"

            try:
                pdf_path_result = self.download_file(url, f"me_stumpage_{year}.pdf")

                # Verify it's a valid PDF (not an error page)
                size_kb = pdf_path_result.stat().st_size / 1024
                if size_kb > 5:  # Valid PDFs should be > 5KB
                    downloaded.append(pdf_path_result)
                else:
                    console.print(f"[yellow]Invalid file for {year} (too small)[/yellow]")
                    pdf_path_result.unlink()

            except Exception as e:
                console.print(f"[yellow]Could not download {year}:[/yellow] {e}")

        console.print(f"\n[bold green]Downloaded {len(downloaded)} annual reports[/bold green]")
        return downloaded

    def download_recent(self, num_years: int = 10) -> list[Path]:
        """Download the most recent N years of reports.

        Args:
            num_years: Number of recent years to download

        Returns:
            List of paths to downloaded files
        """
        recent_years = sorted(REPORT_IDS.keys(), reverse=True)[:num_years]
        return self.download(years=recent_years)

    def parse(self) -> dict[str, Any]:
        """Parse Maine stumpage PDF reports.

        Note: PDF parsing requires additional tools like pdfplumber.

        Returns:
            Dictionary with file metadata
        """
        console.print("\n[bold]Maine reports are PDFs.[/bold]")
        console.print("[dim]PDF parsing requires pdfplumber or similar tools.[/dim]\n")

        results = {}
        for year in REPORT_IDS:
            pdf_path = self.download_dir / f"me_stumpage_{year}.pdf"
            if pdf_path.exists():
                size_kb = pdf_path.stat().st_size / 1024
                results[year] = {
                    "file": str(pdf_path),
                    "status": "downloaded",
                    "format": "PDF",
                    "size_kb": round(size_kb, 1),
                }

        return results

    def get_summary(self) -> None:
        """Print summary of Maine data."""
        table = Table(title="Maine Forest Service Stumpage Reports")
        table.add_column("Year", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Size", style="green")

        for year in sorted(REPORT_IDS.keys(), reverse=True):
            pdf_path = self.download_dir / f"me_stumpage_{year}.pdf"
            if pdf_path.exists():
                size_kb = pdf_path.stat().st_size / 1024
                status = "[green]Downloaded[/green]"
                size = f"{size_kb:.1f} KB"
            else:
                status = "[dim]Not downloaded[/dim]"
                size = "-"
            table.add_row(str(year), status, size)

        console.print(table)


if __name__ == "__main__":
    with MaineForestServiceDownloader() as downloader:
        # Download recent 10 years by default
        files = downloader.download_recent(10)
        downloader.get_summary()
