"""Alabama Forestry Commission data downloader.

Downloads annual Forest Resource Reports from Alabama Forestry Commission.
Data available from 2017-present with forest product volumes and values.

Note: Alabama does not publish free quarterly stumpage price reports.
Detailed stumpage prices are available through TimberMart-South (paid).

Data source: https://www.forestry.alabama.gov/Pages/Management/Forest_Management.aspx
"""

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from forest_rents.downloaders.base import BaseDownloader

console = Console()

# Base URL for Alabama Forestry Commission
BASE_URL = "https://www.forestry.alabama.gov/Pages/Management/Forms"

# Annual Forest Resource Reports (available 2017-2024)
ANNUAL_REPORTS = {
    2024: f"{BASE_URL}/Forest_Resource_Report_2024.pdf",
    2023: f"{BASE_URL}/Forest_Resource_Report_2023.pdf",
    2022: f"{BASE_URL}/Forest_Resource_Report_2022.pdf",
    2021: f"{BASE_URL}/Forest_Resource_Report_2021.pdf",
    2020: f"{BASE_URL}/Forest_Resource_Report_2020.pdf",
    2019: f"{BASE_URL}/Forest_Resource_Report_2019.pdf",
    2018: f"{BASE_URL}/Forest_Resource_Report_2018.pdf",
    2017: f"{BASE_URL}/Forest_Resource_Report_2017.pdf",
}

# Additional resources
ADDITIONAL_REPORTS = {
    "economic_impact": f"{BASE_URL}/Economic_Impact.pdf",
    "forest_management_investments": "https://www.forestry.alabama.gov/Pages/Informational/Forms/Forest_Management_Investments.pdf",
}


class AlabamaForestryDownloader(BaseDownloader):
    """Download forest resource data from Alabama Forestry Commission.

    Alabama Forestry Commission publishes annual Forest Resource Reports
    containing data on:
    - Forest product harvest volumes by species and product type
    - Timber severance tax receipts
    - Mill capacity and production
    - Forest land area by ownership

    Note: Detailed stumpage price data is not freely available from Alabama.
    The state references TimberMart-South for current pricing data.
    """

    @property
    def source_name(self) -> str:
        return "Alabama Forestry Commission Forest Resource Reports"

    @property
    def source_id(self) -> str:
        return "al_forestry"

    def download(self, years: list[int] | None = None) -> list[Path]:
        """Download Alabama Forest Resource Reports.

        Args:
            years: Optional list of years to download. Defaults to all available.

        Returns:
            List of paths to downloaded PDF files
        """
        console.print(f"\n[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold]{self.source_name}[/bold]")
        console.print(f"[dim]Annual forest resource reports (2017-2024)[/dim]")
        console.print(f"[dim]Note: Stumpage prices not included (use TimberMart-South)[/dim]")
        console.print(f"[bold blue]{'='*60}[/bold blue]\n")

        # Determine which years to download
        if years is None:
            years = sorted(ANNUAL_REPORTS.keys(), reverse=True)

        downloaded = []

        for year in years:
            if year not in ANNUAL_REPORTS:
                console.print(f"[yellow]No report available for {year}[/yellow]")
                continue

            url = ANNUAL_REPORTS[year]
            local_filename = f"al_forest_resource_{year}.pdf"

            try:
                pdf_path = self.download_file(url, local_filename)

                # Verify it's a valid PDF
                size_kb = pdf_path.stat().st_size / 1024
                if size_kb > 10:  # These reports are typically large
                    downloaded.append(pdf_path)
                else:
                    console.print(f"[yellow]Invalid file for {year} (too small)[/yellow]")
                    pdf_path.unlink()

            except Exception as e:
                console.print(f"[yellow]Could not download {year}:[/yellow] {e}")

        console.print(f"\n[bold green]Downloaded {len(downloaded)} annual reports[/bold green]")
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

    def download_additional(self) -> list[Path]:
        """Download additional reports (economic impact, etc.).

        Returns:
            List of paths to downloaded files
        """
        console.print("\n[bold]Downloading additional reports...[/bold]")

        downloaded = []
        for report_name, url in ADDITIONAL_REPORTS.items():
            try:
                pdf_path = self.download_file(url, f"al_{report_name}.pdf")
                downloaded.append(pdf_path)
                console.print(f"[green]Downloaded:[/green] {report_name}")
            except Exception as e:
                console.print(f"[yellow]Could not download {report_name}:[/yellow] {e}")

        return downloaded

    def parse(self) -> dict[str, Any]:
        """Parse Alabama Forest Resource PDF reports.

        Note: PDF parsing requires additional tools like pdfplumber.

        Returns:
            Dictionary with file metadata
        """
        console.print("\n[bold]Alabama reports are PDFs.[/bold]")
        console.print("[dim]PDF parsing requires pdfplumber or similar tools.[/dim]")
        console.print("[dim]Reports contain harvest volumes, not detailed stumpage prices.[/dim]\n")

        results = {}
        for year in ANNUAL_REPORTS:
            pdf_path = self.download_dir / f"al_forest_resource_{year}.pdf"
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
        """Print summary of Alabama data."""
        table = Table(title="Alabama Forestry Commission Reports")
        table.add_column("Year", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Size", style="green")

        for year in sorted(ANNUAL_REPORTS.keys(), reverse=True):
            pdf_path = self.download_dir / f"al_forest_resource_{year}.pdf"
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
        total_downloaded = len(list(self.download_dir.glob("al_forest_resource_*.pdf")))
        console.print(f"\n[dim]Total available: {total_available} annual reports[/dim]")
        console.print(f"[dim]Downloaded: {total_downloaded} reports[/dim]")


if __name__ == "__main__":
    with AlabamaForestryDownloader() as downloader:
        files = downloader.download_recent(5)
        downloader.get_summary()
