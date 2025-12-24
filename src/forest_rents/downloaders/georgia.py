"""Georgia timber price data downloader.

Downloads timber price data from two Georgia sources:
1. Georgia Department of Revenue - Owner Harvest Timber Values (annual)
2. UGA Extension - Timber Situation and Outlook reports (annual)

Data source:
- https://dor.georgia.gov/local-government-services/digest-compliance/owner-harvest-timber-values
- https://fieldreport.caes.uga.edu/
"""

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from forest_rents.downloaders.base import BaseDownloader

console = Console()

# Georgia Department of Revenue Owner Harvest Timber Values
# Annual weighted average prices for tax assessment purposes
GA_DOR_BASE_URL = "https://dor.georgia.gov/document/document"

# Currently available years (DOR only keeps recent years online)
GA_DOR_REPORTS = {
    2025: f"{GA_DOR_BASE_URL}/2025-owner-harvest-timber-values/download",
    2024: f"{GA_DOR_BASE_URL}/2024-owner-harvest-timber-values/download",
}

# UGA Extension Timber Situation and Outlook reports
# Annual analysis of timber markets with price data
UGA_EXTENSION_BASE_URL = "https://fieldreport.caes.uga.edu/wp-content/uploads/generated-pub-pdfs"

# Publication numbers follow pattern: AP-130-{edition}-13.pdf
# Edition corresponds to Georgia Ag Forecast year (2=2024, 3=2025, etc.)
UGA_EXTENSION_REPORTS = {
    2025: {
        "url": f"{UGA_EXTENSION_BASE_URL}/AP-130-3-13.pdf",
        "title": "Timber Situation and 2025 Outlook",
        "publication_number": "AP130-3-13",
    },
    2024: {
        "url": f"{UGA_EXTENSION_BASE_URL}/AP-130-2-13.pdf",
        "title": "Timber Situation and 2024 Outlook",
        "publication_number": "AP130-2-13",
    },
}


class GeorgiaDORDownloader(BaseDownloader):
    """Download timber values from Georgia Department of Revenue.

    The Georgia DOR publishes annual tables of Owner Harvest Timber Values
    containing weighted average prices for:
    - Softwood and hardwood pulpwood
    - Chip-n-saw logs
    - Saw timber
    - Poles
    - Fuel wood

    These prices are used by tax assessors for timber harvested by owners.
    """

    @property
    def source_name(self) -> str:
        return "Georgia Department of Revenue Owner Harvest Timber Values"

    @property
    def source_id(self) -> str:
        return "ga_dor"

    def download(self, years: list[int] | None = None) -> list[Path]:
        """Download Georgia DOR timber value tables.

        Args:
            years: Optional list of years to download. Defaults to all available.

        Returns:
            List of paths to downloaded PDF files
        """
        console.print(f"\n[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold]{self.source_name}[/bold]")
        console.print(f"[dim]Annual weighted average timber values (2024-2025)[/dim]")
        console.print(f"[bold blue]{'='*60}[/bold blue]\n")

        # Determine which years to download
        if years is None:
            years = sorted(GA_DOR_REPORTS.keys(), reverse=True)

        downloaded = []

        for year in years:
            if year not in GA_DOR_REPORTS:
                console.print(f"[yellow]No report available for {year}[/yellow]")
                continue

            url = GA_DOR_REPORTS[year]
            local_filename = f"ga_dor_timber_values_{year}.pdf"

            try:
                pdf_path = self.download_file(url, local_filename)

                # Verify it's a valid PDF
                size_kb = pdf_path.stat().st_size / 1024
                with open(pdf_path, "rb") as f:
                    header = f.read(4)

                if header == b"%PDF" and size_kb > 5:
                    downloaded.append(pdf_path)
                    console.print(f"[green]Downloaded:[/green] {year} ({size_kb:.1f} KB)")
                else:
                    console.print(f"[yellow]Invalid file for {year} (not a PDF)[/yellow]")
                    pdf_path.unlink()

            except Exception as e:
                console.print(f"[yellow]Could not download {year}:[/yellow] {e}")

        console.print(f"\n[bold green]Downloaded {len(downloaded)} annual reports[/bold green]")
        return downloaded

    def parse(self) -> dict[str, Any]:
        """Parse Georgia DOR timber value PDF tables.

        Note: PDF parsing requires pdfplumber or similar tools.

        Returns:
            Dictionary with file metadata
        """
        console.print("\n[bold]Georgia DOR reports are PDFs.[/bold]")
        console.print("[dim]PDF parsing requires pdfplumber or similar tools.[/dim]")
        console.print("[dim]Data contains annual weighted averages by product type.[/dim]\n")

        results = {}
        for year in GA_DOR_REPORTS:
            pdf_path = self.download_dir / f"ga_dor_timber_values_{year}.pdf"
            if pdf_path.exists():
                size_kb = pdf_path.stat().st_size / 1024
                results[year] = {
                    "file": str(pdf_path),
                    "status": "downloaded",
                    "format": "PDF",
                    "size_kb": round(size_kb, 1),
                }

        return results


class UGAExtensionDownloader(BaseDownloader):
    """Download timber market reports from UGA Extension.

    UGA Extension publishes annual Timber Situation and Outlook reports
    containing market analysis and price data from TimberMart-South.

    Reports include:
    - Pine sawtimber prices by region (North/South Georgia)
    - Chip-n-saw prices
    - Pulpwood prices
    - Hardwood prices
    - Market trends and forecasts
    """

    @property
    def source_name(self) -> str:
        return "UGA Extension Timber Situation and Outlook"

    @property
    def source_id(self) -> str:
        return "uga_extension"

    def download(self, years: list[int] | None = None) -> list[Path]:
        """Download UGA Extension timber outlook reports.

        Args:
            years: Optional list of years to download. Defaults to all available.

        Returns:
            List of paths to downloaded PDF files
        """
        console.print(f"\n[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold]{self.source_name}[/bold]")
        console.print(f"[dim]Annual timber market analysis (2024-2025)[/dim]")
        console.print(f"[bold blue]{'='*60}[/bold blue]\n")

        # Determine which years to download
        if years is None:
            years = sorted(UGA_EXTENSION_REPORTS.keys(), reverse=True)

        downloaded = []

        for year in years:
            if year not in UGA_EXTENSION_REPORTS:
                console.print(f"[yellow]No report available for {year}[/yellow]")
                continue

            report = UGA_EXTENSION_REPORTS[year]
            url = report["url"]
            local_filename = f"uga_timber_outlook_{year}.pdf"

            try:
                pdf_path = self.download_file(url, local_filename)

                # Verify it's a valid PDF
                size_kb = pdf_path.stat().st_size / 1024
                with open(pdf_path, "rb") as f:
                    header = f.read(4)

                if header == b"%PDF" and size_kb > 5:
                    downloaded.append(pdf_path)
                    console.print(f"[green]Downloaded:[/green] {report['title']} ({size_kb:.1f} KB)")
                else:
                    console.print(f"[yellow]Invalid file for {year} (not a PDF)[/yellow]")
                    pdf_path.unlink()

            except Exception as e:
                console.print(f"[yellow]Could not download {year}:[/yellow] {e}")

        console.print(f"\n[bold green]Downloaded {len(downloaded)} outlook reports[/bold green]")
        return downloaded

    def parse(self) -> dict[str, Any]:
        """Parse UGA Extension outlook PDF reports.

        Note: PDF parsing requires pdfplumber or similar tools.

        Returns:
            Dictionary with file metadata
        """
        console.print("\n[bold]UGA Extension reports are PDFs.[/bold]")
        console.print("[dim]PDF parsing requires pdfplumber or similar tools.[/dim]")
        console.print("[dim]Reports contain market analysis with regional price data.[/dim]\n")

        results = {}
        for year, report in UGA_EXTENSION_REPORTS.items():
            pdf_path = self.download_dir / f"uga_timber_outlook_{year}.pdf"
            if pdf_path.exists():
                size_kb = pdf_path.stat().st_size / 1024
                results[year] = {
                    "file": str(pdf_path),
                    "title": report["title"],
                    "publication_number": report["publication_number"],
                    "status": "downloaded",
                    "format": "PDF",
                    "size_kb": round(size_kb, 1),
                }

        return results


class GeorgiaDownloader(BaseDownloader):
    """Combined downloader for all Georgia timber price sources.

    Downloads data from:
    1. Georgia Department of Revenue - Owner Harvest Timber Values
    2. UGA Extension - Timber Situation and Outlook reports

    Note: Detailed quarterly stumpage prices for Georgia are available
    through TimberMart-South (paid subscription).
    """

    @property
    def source_name(self) -> str:
        return "Georgia Timber Price Data"

    @property
    def source_id(self) -> str:
        return "georgia"

    def download(self, years: list[int] | None = None) -> list[Path]:
        """Download from all Georgia sources.

        Args:
            years: Optional list of years to download. Defaults to all available.

        Returns:
            List of paths to downloaded files
        """
        console.print(f"\n[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold]{self.source_name}[/bold]")
        console.print(f"[dim]Downloading from multiple Georgia sources[/dim]")
        console.print(f"[dim]Note: Quarterly prices via TimberMart-South (paid)[/dim]")
        console.print(f"[bold blue]{'='*60}[/bold blue]\n")

        all_downloaded = []

        # Download from Georgia DOR
        with GeorgiaDORDownloader() as dor:
            dor_files = dor.download(years=years)
            all_downloaded.extend(dor_files)

        # Download from UGA Extension
        with UGAExtensionDownloader() as uga:
            uga_files = uga.download(years=years)
            all_downloaded.extend(uga_files)

        console.print(f"\n[bold green]Total: {len(all_downloaded)} files downloaded[/bold green]")
        return all_downloaded

    def parse(self) -> dict[str, Any]:
        """Parse all Georgia data sources.

        Returns:
            Dictionary with metadata from all sources
        """
        results = {
            "ga_dor": {},
            "uga_extension": {},
        }

        # Check DOR files
        for year in GA_DOR_REPORTS:
            pdf_path = self.download_dir / f"ga_dor_timber_values_{year}.pdf"
            if pdf_path.exists():
                size_kb = pdf_path.stat().st_size / 1024
                results["ga_dor"][year] = {
                    "file": str(pdf_path),
                    "status": "downloaded",
                    "size_kb": round(size_kb, 1),
                }

        # Check UGA files
        for year, report in UGA_EXTENSION_REPORTS.items():
            pdf_path = self.download_dir / f"uga_timber_outlook_{year}.pdf"
            if pdf_path.exists():
                size_kb = pdf_path.stat().st_size / 1024
                results["uga_extension"][year] = {
                    "file": str(pdf_path),
                    "title": report["title"],
                    "status": "downloaded",
                    "size_kb": round(size_kb, 1),
                }

        return results

    def get_summary(self) -> None:
        """Print summary of Georgia data."""
        table = Table(title="Georgia Timber Price Data")
        table.add_column("Source", style="cyan")
        table.add_column("Year", style="white")
        table.add_column("Status", style="yellow")
        table.add_column("Size", style="green")

        # DOR files
        for year in sorted(GA_DOR_REPORTS.keys(), reverse=True):
            pdf_path = self.download_dir / f"ga_dor_timber_values_{year}.pdf"
            if pdf_path.exists():
                size_kb = pdf_path.stat().st_size / 1024
                status = "[green]Downloaded[/green]"
                size = f"{size_kb:.1f} KB"
            else:
                status = "[dim]Not downloaded[/dim]"
                size = "-"
            table.add_row("GA DOR", str(year), status, size)

        # UGA files
        for year in sorted(UGA_EXTENSION_REPORTS.keys(), reverse=True):
            pdf_path = self.download_dir / f"uga_timber_outlook_{year}.pdf"
            if pdf_path.exists():
                size_kb = pdf_path.stat().st_size / 1024
                status = "[green]Downloaded[/green]"
                size = f"{size_kb:.1f} KB"
            else:
                status = "[dim]Not downloaded[/dim]"
                size = "-"
            table.add_row("UGA Extension", str(year), status, size)

        console.print(table)


if __name__ == "__main__":
    with GeorgiaDownloader() as downloader:
        files = downloader.download()
        downloader.get_summary()
