"""Florida timber price data downloader.

Downloads quarterly timber price updates from University of Florida IFAS
Extension (Florida Land Steward publication). Data available from Q2 2022
through present.

Data source: https://programs.ifas.ufl.edu/florida-land-steward/
"""

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from timber_prices.downloaders.base import BaseDownloader

console = Console()

# UF IFAS Florida Land Steward timber price update PDFs
BASE_URL = "https://programs.ifas.ufl.edu/media/programsifasufledu/florida-land-steward/events-calendar"

# Map quarter number to ordinal format used in URLs
QUARTER_NAMES = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}

# Available quarterly reports (verified as of December 2025)
# Format: {year: [list of available quarters]}
QUARTERLY_REPORTS = {
    2025: [1, 2, 3],
    2024: [1, 3, 4],  # Q2 2024 not available
    2023: [1, 2, 3, 4],
    2022: [2, 3, 4],  # Q1 2022 not available
}


class FloridaIFASDownloader(BaseDownloader):
    """Download timber price data from UF IFAS Florida Land Steward.

    The University of Florida IFAS Extension publishes quarterly timber
    price updates in the Florida Land Steward newsletter. Reports contain:
    - Florida stumpage price trends
    - Pine sawtimber prices
    - Pine chip-n-saw prices
    - Pine pulpwood prices
    - Hardwood prices
    - Market commentary

    Data coverage:
    - Geographic: Statewide Florida
    - Temporal: Quarterly (Q2 2022 - present)
    - Products: Pine and hardwood sawtimber, pulpwood, chip-n-saw
    """

    @property
    def source_name(self) -> str:
        return "UF IFAS Florida Land Steward Timber Prices"

    @property
    def source_id(self) -> str:
        return "fl_ifas"

    def _get_url(self, year: int, quarter: int) -> str:
        """Generate the URL for a quarterly report.

        Args:
            year: Year of the report
            quarter: Quarter number (1-4)

        Returns:
            Full URL for the PDF
        """
        qtr_name = QUARTER_NAMES[quarter]
        return f"{BASE_URL}/Timber-Price-Update,-{qtr_name}-Qtr-{year}.pdf"

    def download(self, years: list[int] | None = None) -> list[Path]:
        """Download Florida timber price reports.

        Args:
            years: Optional list of years to download. Defaults to all available.

        Returns:
            List of paths to downloaded PDF files
        """
        console.print(f"\n[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold]{self.source_name}[/bold]")
        console.print(f"[dim]Quarterly timber price updates (2022-2025)[/dim]")
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
            for quarter in quarters:
                url = self._get_url(year, quarter)
                local_filename = f"fl_timber_{year}_q{quarter}.pdf"

                try:
                    pdf_path = self.download_file(url, local_filename)

                    # Verify it's a valid PDF
                    size_kb = pdf_path.stat().st_size / 1024

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
        """Parse Florida timber price PDF reports.

        Note: PDF parsing requires pdfplumber or similar tools.

        Returns:
            Dictionary with file metadata
        """
        console.print("\n[bold]Florida reports are PDFs.[/bold]")
        console.print("[dim]PDF parsing requires pdfplumber or similar tools.[/dim]")
        console.print("[dim]Data contains quarterly statewide timber prices.[/dim]\n")

        results = {}
        for year in QUARTERLY_REPORTS:
            year_data = {}
            for quarter in QUARTERLY_REPORTS[year]:
                pdf_path = self.download_dir / f"fl_timber_{year}_q{quarter}.pdf"
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
        """Print summary of Florida data."""
        table = Table(title="UF IFAS Florida Land Steward Timber Prices")
        table.add_column("Year", style="cyan")
        table.add_column("Q1", style="white")
        table.add_column("Q2", style="white")
        table.add_column("Q3", style="white")
        table.add_column("Q4", style="white")

        for year in sorted(QUARTERLY_REPORTS.keys(), reverse=True):
            row = [str(year)]
            for quarter in [1, 2, 3, 4]:
                pdf_path = self.download_dir / f"fl_timber_{year}_q{quarter}.pdf"
                if pdf_path.exists():
                    row.append("[green]Yes[/green]")
                elif quarter in QUARTERLY_REPORTS.get(year, []):
                    row.append("[dim]No[/dim]")
                else:
                    row.append("[dim]-[/dim]")
            table.add_row(*row)

        console.print(table)

        # Count totals
        total_available = sum(len(q) for q in QUARTERLY_REPORTS.values())
        total_downloaded = len(list(self.download_dir.glob("fl_timber_*.pdf")))
        console.print(f"\n[dim]Total available: {total_available} reports ({len(QUARTERLY_REPORTS)} years)[/dim]")
        console.print(f"[dim]Downloaded: {total_downloaded} reports[/dim]")


if __name__ == "__main__":
    with FloridaIFASDownloader() as downloader:
        files = downloader.download()
        downloader.get_summary()
