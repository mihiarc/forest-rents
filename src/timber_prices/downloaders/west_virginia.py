"""West Virginia Division of Forestry timber price data downloader.

Downloads annual timber stumpage price reports from WV Division of Forestry.
Data available from 2012-2023 with annual statewide stumpage averages by
tax region and species.

Data source: https://wvforestry.com/
"""

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from timber_prices.downloaders.base import BaseDownloader

console = Console()

# West Virginia Division of Forestry stumpage reports
# Note: URL patterns are inconsistent across years
ANNUAL_REPORTS = {
    2023: "https://wvforestry.com/wp-content/uploads/2024/01/Timber-Stumpage-report-2023.pdf",
    2020: "https://wvforestry.com/pdf/2020TPR_FINAL_5-11-20.pdf",
    2019: "https://wvforestry.com/pdf/STUMPAGE%20REPORT%202019.pdf",
    2018: "https://wvforestry.com/pdf/STUMPAGE%20REPORT%202018.pdf",
    2017: "https://wvforestry.com/pdf/STUMPAGE%20REPORT%202017.pdf",
    2016: "https://wvforestry.com/pdf/STUMPAGE%20REPORT%202016.pdf",
    2015: "https://wvforestry.com/pdf/STUMPAGE%20REPORT%202015.pdf",
    2014: "https://wvforestry.com/pdf/STUMPAGE%20REPORT%202014.pdf",
    2013: "https://wvforestry.com/pdf/STUMPAGE%20REPORT%202013.pdf",
    2012: "https://wvforestry.com/pdf/STUMPAGE%20REPORT%202012.pdf",
}


class WestVirginiaForestryDownloader(BaseDownloader):
    """Download timber price data from WV Division of Forestry.

    West Virginia Division of Forestry publishes annual timber stumpage
    price reports containing:
    - Average stumpage prices by tax region
    - Prices for hardwood and softwood species
    - Year-over-year price changes
    - All prices based on Doyle Log Scale

    Tax regions covered:
    - Region 1: Eastern Panhandle
    - Region 2: Northwestern
    - Region 3: Southwestern
    - Region 4: Southern
    - Region 5: Northeastern

    Data coverage:
    - Geographic: Statewide by tax region
    - Temporal: Annual (2012-2023)
    - Products: Hardwood and softwood by species
    """

    @property
    def source_name(self) -> str:
        return "West Virginia Division of Forestry Timber Price Reports"

    @property
    def source_id(self) -> str:
        return "wv_forestry"

    def download(self, years: list[int] | None = None) -> list[Path]:
        """Download WV Forestry timber price reports.

        Args:
            years: Optional list of years to download. Defaults to all available.

        Returns:
            List of paths to downloaded PDF files
        """
        console.print(f"\n[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold]{self.source_name}[/bold]")
        console.print(f"[dim]Annual stumpage prices by tax region (2012-2023)[/dim]")
        console.print(f"[bold blue]{'='*60}[/bold blue]\n")

        # Determine which years to download
        if years is None:
            years = sorted(ANNUAL_REPORTS.keys(), reverse=True)

        downloaded = []
        failed = []

        for year in years:
            if year not in ANNUAL_REPORTS:
                console.print(f"[yellow]No report available for {year}[/yellow]")
                continue

            url = ANNUAL_REPORTS[year]
            local_filename = f"wv_timber_{year}.pdf"

            try:
                pdf_path = self.download_file(url, local_filename)

                # Verify it's a valid PDF
                size_kb = pdf_path.stat().st_size / 1024

                with open(pdf_path, "rb") as f:
                    header = f.read(4)

                if header == b"%PDF" and size_kb > 5:
                    downloaded.append(pdf_path)
                else:
                    console.print(f"[yellow]Invalid file for {year} (not a PDF)[/yellow]")
                    pdf_path.unlink()
                    failed.append(year)

            except Exception as e:
                console.print(f"[yellow]Could not download {year}:[/yellow] {e}")
                failed.append(year)

        console.print(f"\n[bold green]Downloaded {len(downloaded)} annual reports[/bold green]")
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
        recent_years = sorted(ANNUAL_REPORTS.keys(), reverse=True)[:num_years]
        return self.download(years=recent_years)

    def parse(self) -> dict[str, Any]:
        """Parse WV timber price PDF reports.

        Note: PDF parsing requires pdfplumber or similar tools.

        Returns:
            Dictionary with file metadata
        """
        console.print("\n[bold]West Virginia reports are PDFs.[/bold]")
        console.print("[dim]PDF parsing requires pdfplumber or similar tools.[/dim]")
        console.print("[dim]Data contains annual stumpage prices by tax region.[/dim]\n")

        results = {}
        for year in ANNUAL_REPORTS:
            pdf_path = self.download_dir / f"wv_timber_{year}.pdf"
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
        """Print summary of WV data."""
        table = Table(title="WV Division of Forestry Timber Price Reports")
        table.add_column("Year", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Size", style="green")

        for year in sorted(ANNUAL_REPORTS.keys(), reverse=True):
            pdf_path = self.download_dir / f"wv_timber_{year}.pdf"
            if pdf_path.exists():
                size_kb = pdf_path.stat().st_size / 1024
                status = "[green]Downloaded[/green]"
                size = f"{size_kb:.1f} KB"
            else:
                status = "[dim]Not downloaded[/dim]"
                size = "-"
            table.add_row(str(year), status, size)

        console.print(table)

        # Count totals
        total_available = len(ANNUAL_REPORTS)
        total_downloaded = len(list(self.download_dir.glob("wv_timber_*.pdf")))
        console.print(f"\n[dim]Total available: {total_available} annual reports[/dim]")
        console.print(f"[dim]Downloaded: {total_downloaded} reports[/dim]")


if __name__ == "__main__":
    with WestVirginiaForestryDownloader() as downloader:
        files = downloader.download()
        downloader.get_summary()
