"""Arkansas Extension timber price data downloader.

Downloads quarterly timber price reports from University of Arkansas
Division of Agriculture Cooperative Extension Service.
Data available from 2005-present with statewide stumpage averages.

Data source: https://www.uaex.uada.edu/environment-nature/forestry/timber-price-report.aspx
"""

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from timber_prices.downloaders.base import BaseDownloader

console = Console()

# Base URL for Arkansas Extension
BASE_URL = "https://www.uaex.uada.edu/environment-nature/forestry"

# Quarterly reports by year - URL patterns vary by year
# Format: {year: {quarter: relative_url}}
QUARTERLY_REPORTS = {
    2025: {
        1: "1st-quarter-25-timber-price-report.pdf",
        2: "Q2-2025.pdf",
        3: "q3-2025.pdf",
    },
    2024: {
        1: "1st-quarter-24-timber-price-report.pdf",
        3: "3rd-quarter-24-Timber-price-report.pdf",
        4: "4th-quarter-24.pdf",
    },
    2023: {
        1: "1st%20Quarter%2023%20Timber%20price%20report.pdf",
        2: "2nd-quarter-23-timber-price-report.pdf",
        3: "3rd-quarter-23-timber-price-report.pdf",
        4: "4th-quarter-23-timber-price-report.pdf",
    },
    2022: {
        1: "1st%20Quarter%2022%20Timber%20price%20report.pdf",
        2: "2nd%20Quarter%2022%20Timber%20price%20report.pdf",
        3: "3rd%20Quarter%2022%20Timber%20price%20report.pdf",
        4: "4th%20Quarter%2022%20Timber%20price%20report.pdf",
    },
    2021: {
        1: "1st%20Q%202021.pdf",
        2: "2nd%20Q%202021.pdf",
        3: "3rd%20Q%202021.pdf",
        4: "4th%20qtr%202021%20Timber%20price%20report.pdf",
    },
    2020: {
        1: "TPR%201Q%202020.pdf",
        2: "TPR%202Q%202020.pdf",
        3: "TPR%203rd%20Q%202020.pdf",
        4: "TPR%204th%20Q%202020.pdf",
    },
    2019: {
        1: "TPR%20Q1%202019.pdf",
        2: "TPR%20Q2%202019.pdf",
        3: "TPR%20Q3%202019.pdf",
        4: "TPR%20Q4%202019.pdf",
    },
    2018: {
        1: "TPR%201st%20Q%202018.pdf",
        2: "TPR%202nd%20Q%202018.pdf",
        3: "TPR%203rd%20Q%202018%20.pdf",
        4: "TPR%204th%20Q%202018.pdf",
    },
    2017: {
        1: "TPR%201st%20Q%202017.pdf",
        2: "TPR%202nd%20Q%202017.pdf",
        3: "TPR%203rd%20Q%202017.pdf",
        4: "TPR%204th%20Q%202017.pdf",
    },
    2016: {
        1: "TPR%201st%20Q%202016.pdf",
        2: "TPR%202nd%20Q%202016.pdf",
        3: "TPR%203rd%20Q%202016.pdf",
        4: "TPR%204th%20Q%202016.pdf",
    },
    2015: {
        2: "TPR%202nd%20Q%202015.pdf",
        3: "TPR%203rd%20Q%202015.pdf",
        4: "TPR%204th%20Q%202015.pdf",
    },
    2014: {
        1: "docs/AR%20Price%20Report%201Q2014.pdf",
        2: "docs/AR%20Price%20Report%202Q2014.pdf",
        3: "AR%20Price%20Report%203Q2014.pdf",
        4: "AR%20Price%20Report%204Q2014.pdf",
    },
    2013: {
        1: "docs/AR%20Price%20Report%201Q2013.pdf",
        2: "docs/AR%20Price%20Report%202Q2013.pdf",
        3: "docs/AR%20Price%20Report%203Q2013.pdf",
        4: "AR%20Price%20Report%204Q2013.pdf",
    },
    2012: {
        1: "docs/AR%20Price%20Report%201Q2012.pdf",
        2: "docs/AR%20Price%20Report%202Q2012.pdf",
        3: "docs/AR%20Price%20Report%203Q2012.pdf",
        4: "docs/AR%20Price%20Report%204Q2012.pdf",
    },
    2011: {
        1: "docs/AR%20Price%20Report%201Q2011.pdf",
        2: "docs/AR%20Price%20Report%202Q2011.pdf",
        3: "docs/AR%20Price%20Report%203Q2011.pdf",
        4: "docs/AR%20Price%20Report%204Q2011.pdf",
    },
    2010: {
        1: "docs/AR%20Price%20Report%201Q2010.pdf",
        2: "docs/AR%20Price%20Report%202Q2010.pdf",
        3: "docs/AR%20Price%20Report%203Q2010.pdf",
        4: "docs/AR%20Price%20Report%204Q2010.pdf",
    },
    2009: {
        1: "docs/AR%20Price%20Report%201Q2009.pdf",
        2: "docs/AR%20Price%20Report%202Q2009.pdf",
        3: "docs/AR%20Price%20Report%203Q2009.pdf",
        4: "docs/AR%20Price%20Report%204Q2009.pdf",
    },
    2008: {
        1: "docs/AR%20Price%20Report%201Q2008.pdf",
        2: "docs/AR%20Price%20Report%202Q2008.pdf",
        3: "docs/AR%20Price%20Report%203Q2008.pdf",
        4: "docs/AR%20Price%20Report%204Q2008.pdf",
    },
    2007: {
        1: "docs/AR%20Price%20Report%201Q2007.pdf",
        2: "docs/AR%20Price%20Report%202Q2007.pdf",
        3: "docs/AR%20Price%20Report%203Q2007.pdf",
        4: "docs/AR%20Price%20Report%204Q2007.pdf",
    },
    2006: {
        1: "docs/AR%20Price%20Report%2006-1.pdf",
        2: "docs/AR%20Price%20Report%2006-2.pdf",
        3: "docs/AR%20Price%20Report%2006-3.pdf",
        4: "docs/AR%20Price%20Report%204Q2006.pdf",
    },
    2005: {
        1: "docs/AR%20Price%20Report%2005-1.pdf",
        2: "docs/AR%20Price%20Report%2005-2.pdf",
        3: "docs/AR%20Price%20Report%2005-3.pdf",
        4: "docs/AR%20Price%20Report%2005-4.pdf",
    },
}


class ArkansasExtensionDownloader(BaseDownloader):
    """Download timber price data from University of Arkansas Extension.

    Arkansas publishes quarterly timber price reports with statewide
    stumpage averages for pine and hardwood products. Data sourced
    from TimberMart-South.

    Products covered:
    - Pine pulpwood
    - Pine chip-n-saw
    - Pine sawtimber
    - Hardwood pulpwood
    - Mixed hardwood sawtimber
    - Oak sawtimber
    """

    @property
    def source_name(self) -> str:
        return "Arkansas Extension Timber Price Reports"

    @property
    def source_id(self) -> str:
        return "ar_extension"

    def download(self, years: list[int] | None = None) -> list[Path]:
        """Download Arkansas timber price reports.

        Args:
            years: Optional list of years to download. Defaults to all available.

        Returns:
            List of paths to downloaded PDF files
        """
        console.print(f"\n[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold]{self.source_name}[/bold]")
        console.print(f"[dim]Quarterly stumpage prices - pine & hardwood (2005-2025)[/dim]")
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
            for quarter, filename in quarters.items():
                url = f"{BASE_URL}/{filename}"
                local_filename = f"ar_timber_{year}_q{quarter}.pdf"

                try:
                    pdf_path = self.download_file(url, local_filename)

                    # Verify it's a valid PDF (not an error page)
                    size_kb = pdf_path.stat().st_size / 1024
                    if size_kb > 5:  # Valid PDFs should be > 5KB
                        downloaded.append(pdf_path)
                    else:
                        console.print(f"[yellow]Invalid file for {year} Q{quarter} (too small)[/yellow]")
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
        """Parse Arkansas timber price PDF reports.

        Note: PDF parsing requires additional tools like pdfplumber.

        Returns:
            Dictionary with file metadata
        """
        console.print("\n[bold]Arkansas reports are PDFs.[/bold]")
        console.print("[dim]PDF parsing requires pdfplumber or similar tools.[/dim]")
        console.print("[dim]Data contains statewide stumpage averages by product.[/dim]\n")

        results = {}
        for year in QUARTERLY_REPORTS:
            year_data = {}
            for quarter in QUARTERLY_REPORTS[year]:
                pdf_path = self.download_dir / f"ar_timber_{year}_q{quarter}.pdf"
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
        """Print summary of Arkansas data."""
        table = Table(title="Arkansas Extension Timber Price Reports")
        table.add_column("Year", style="cyan")
        table.add_column("Q1", style="white")
        table.add_column("Q2", style="white")
        table.add_column("Q3", style="white")
        table.add_column("Q4", style="white")

        for year in sorted(QUARTERLY_REPORTS.keys(), reverse=True)[:10]:
            row = [str(year)]
            for quarter in [1, 2, 3, 4]:
                pdf_path = self.download_dir / f"ar_timber_{year}_q{quarter}.pdf"
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
        total_downloaded = len(list(self.download_dir.glob("ar_timber_*.pdf")))
        console.print(f"\n[dim]Total available: {total_available} reports ({len(QUARTERLY_REPORTS)} years)[/dim]")
        console.print(f"[dim]Downloaded: {total_downloaded} reports[/dim]")


if __name__ == "__main__":
    with ArkansasExtensionDownloader() as downloader:
        # Download recent 5 years by default
        files = downloader.download_recent(5)
        downloader.get_summary()
