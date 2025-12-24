"""Texas A&M Forest Service timber price data downloader.

Downloads timber price trends from Texas A&M Forest Service.
Data available from 1984-present for East Texas timber market.

Data source: https://tfsweb.tamu.edu/timberpricetrends/

Note: This site uses Cloudflare protection, so we use curl for downloads.
"""

import subprocess
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table

from forest_rents.downloaders.base import BaseDownloader

console = Console()

# Base URL
BASE_URL = "https://tfsweb.tamu.edu"
TIMBER_TRENDS_URL = f"{BASE_URL}/timberpricetrends/"

# Known direct PDF URLs (discovered from website)
ANNUAL_REPORTS = {
    2024: "https://tfsweb.tamu.edu/wp-content/uploads/2025/03/Annual-Price-Report-2024.pdf",
    2023: "https://tfsweb.tamu.edu/wp-content/uploads/2025/01/Annual-Price-Report-2023.pdf",
    2022: "https://tfsweb.tamu.edu/wp-content/uploads/2024/05/Annual-Price-Report-2022.pdf",
    2021: "https://tfsweb.tamu.edu/wp-content/uploads/2024/05/Annual-Price-Report-2021.pdf",
    2020: "https://tfsweb.tamu.edu/wp-content/uploads/2024/05/Annual-Price-Report-2020.pdf",
    2019: "https://tfsweb.tamu.edu/wp-content/uploads/2024/05/Annual-Price-Report-2019.pdf",
    2018: "https://tfsweb.tamu.edu/wp-content/uploads/2024/05/Annual-Price-Report-2018.pdf",
    2017: "https://tfsweb.tamu.edu/wp-content/uploads/2024/05/Annual-Price-Report-2017.pdf",
    2016: "https://tfsweb.tamu.edu/wp-content/uploads/2024/05/Annual-Price-Report-2016.pdf",
    2015: "https://tfsweb.tamu.edu/wp-content/uploads/2024/05/Annual-Price-Report-2015.pdf",
}

FIVE_YEAR_REPORTS = {
    "2019-2023": "https://tfsweb.tamu.edu/wp-content/uploads/2025/01/5-Year-Stumpage-Prices-2019-2023.pdf",
    "2017-2021": "https://tfsweb.tamu.edu/wp-content/uploads/2024/05/Prices202017-2021.pdf",
    "2015-2019": "https://tfsweb.tamu.edu/wp-content/uploads/2024/05/Prices2015-2019.pdf",
    "2013-2017": "https://tfsweb.tamu.edu/wp-content/uploads/2024/05/Prices2013-2017.pdf",
    "2011-2015": "https://tfsweb.tamu.edu/wp-content/uploads/2024/05/Prices2011-2015.pdf",
    "2009-2013": "https://tfsweb.tamu.edu/wp-content/uploads/2024/05/Prices2009-2013.pdf",
    "2007-2011": "https://tfsweb.tamu.edu/wp-content/uploads/2024/05/Prices2007-2011.pdf",
    "2005-2009": "https://tfsweb.tamu.edu/wp-content/uploads/2024/05/Prices2005-2009.pdf",
}


class TexasAMDownloader(BaseDownloader):
    """Download timber price data from Texas A&M Forest Service.

    Note: This site uses Cloudflare protection, so we use curl for downloads
    instead of the httpx client.
    """

    @property
    def source_name(self) -> str:
        return "Texas A&M Forest Service Timber Price Trends"

    @property
    def source_id(self) -> str:
        return "texas_am"

    def _curl_download(self, url: str, dest_path: Path) -> bool:
        """Download a file using curl to bypass Cloudflare.

        Args:
            url: URL to download
            dest_path: Destination file path

        Returns:
            True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                [
                    "curl", "-sL",
                    "-A", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "-o", str(dest_path),
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Check if file was created and has content
            if dest_path.exists() and dest_path.stat().st_size > 0:
                return True

            return False

        except subprocess.TimeoutExpired:
            console.print(f"[yellow]Timeout downloading {url}[/yellow]")
            return False
        except Exception as e:
            console.print(f"[yellow]Error: {e}[/yellow]")
            return False

    def download(self) -> list[Path]:
        """Download Texas A&M timber price reports.

        Downloads annual summary reports, 5-year consolidated reports,
        and bi-monthly reports by discovering URLs from the main page.
        Uses curl to bypass Cloudflare protection.

        Returns:
            List of paths to downloaded PDF files
        """
        console.print(f"\n[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold]{self.source_name}[/bold]")
        console.print(f"[dim]East Texas stumpage prices (1984-present)[/dim]")
        console.print(f"[dim]Using curl to bypass Cloudflare protection[/dim]")
        console.print(f"[bold blue]{'='*60}[/bold blue]\n")

        downloaded = []

        # First, save the main page for reference
        console.print("[dim]Fetching main timber trends page...[/dim]")
        main_page = self.download_dir / "timber_trends_main.html"
        if not self._curl_download(TIMBER_TRENDS_URL, main_page):
            console.print("[red]Could not fetch main page - cannot continue[/red]")
            return downloaded

        downloaded.append(main_page)
        console.print(f"[green]Saved:[/green] {main_page}")

        # Parse the page for PDF links
        html_content = main_page.read_text(encoding="utf-8", errors="ignore")
        pdf_urls = self._discover_pdf_links(html_content)

        # Download annual reports
        if pdf_urls["annual"]:
            console.print(f"\n[bold]Downloading Annual Reports ({len(pdf_urls['annual'])} found)...[/bold]")
            for url in pdf_urls["annual"]:
                filename = url.split("/")[-1]
                pdf_path = self.download_dir / f"annual_{filename}"
                console.print(f"[blue]Downloading:[/blue] {filename}")

                if self._curl_download(url, pdf_path):
                    size_kb = pdf_path.stat().st_size / 1024
                    if size_kb > 1:  # Skip tiny error files
                        downloaded.append(pdf_path)
                        console.print(f"[green]Saved:[/green] {pdf_path.name} ({size_kb:.1f} KB)")
                    else:
                        pdf_path.unlink()  # Remove error files
                        console.print(f"[yellow]Skipped (invalid):[/yellow] {filename}")

        # Download 5-year reports
        if pdf_urls["five_year"]:
            console.print(f"\n[bold]Downloading 5-Year Reports ({len(pdf_urls['five_year'])} found)...[/bold]")
            for url in pdf_urls["five_year"]:
                filename = url.split("/")[-1]
                pdf_path = self.download_dir / f"5year_{filename}"
                console.print(f"[blue]Downloading:[/blue] {filename}")

                if self._curl_download(url, pdf_path):
                    size_kb = pdf_path.stat().st_size / 1024
                    if size_kb > 1:
                        downloaded.append(pdf_path)
                        console.print(f"[green]Saved:[/green] {pdf_path.name} ({size_kb:.1f} KB)")
                    else:
                        pdf_path.unlink()
                        console.print(f"[yellow]Skipped (invalid):[/yellow] {filename}")

        # Download bi-monthly reports (sample)
        if pdf_urls["bimonthly"]:
            console.print(f"\n[bold]Downloading Bi-Monthly Reports ({len(pdf_urls['bimonthly'])} found, downloading first 6)...[/bold]")
            for url in pdf_urls["bimonthly"][:6]:  # Limit to recent reports
                filename = url.split("/")[-1]
                pdf_path = self.download_dir / f"bimonthly_{filename}"
                console.print(f"[blue]Downloading:[/blue] {filename}")

                if self._curl_download(url, pdf_path):
                    size_kb = pdf_path.stat().st_size / 1024
                    if size_kb > 1:
                        downloaded.append(pdf_path)
                        console.print(f"[green]Saved:[/green] {pdf_path.name} ({size_kb:.1f} KB)")
                    else:
                        pdf_path.unlink()
                        console.print(f"[yellow]Skipped (invalid):[/yellow] {filename}")

        console.print(f"\n[bold green]Downloaded {len(downloaded)} files[/bold green]")
        return downloaded

    def _discover_pdf_links(self, html_content: str) -> dict[str, list[str]]:
        """Discover PDF links from the main page.

        Args:
            html_content: HTML content of the main page

        Returns:
            Dictionary with categorized PDF URLs
        """
        soup = BeautifulSoup(html_content, "lxml")

        categories = {
            "annual": [],
            "five_year": [],
            "bimonthly": [],
            "other": [],
        }

        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if ".pdf" not in href.lower():
                continue

            full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
            text = link.get_text(strip=True).lower()

            if "annual" in text or "annual" in href.lower():
                categories["annual"].append(full_url)
            elif "5-year" in text or "year" in href.lower() or "prices20" in href.lower():
                categories["five_year"].append(full_url)
            elif "ttpt" in href.lower() or any(m in text for m in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
                categories["bimonthly"].append(full_url)
            else:
                categories["other"].append(full_url)

        total = sum(len(v) for v in categories.values())
        console.print(f"[dim]Discovered {total} PDF links on main page[/dim]")
        return categories

    def download_bimonthly(self, years: list[int] | None = None) -> list[Path]:
        """Download bi-monthly reports for specified years.

        Args:
            years: List of years to download. Defaults to recent 5 years.

        Returns:
            List of paths to downloaded files
        """
        if years is None:
            years = [2024, 2023, 2022, 2021, 2020]

        console.print("\n[bold]Downloading Bi-Monthly Reports...[/bold]")

        periods = [
            ("January", "February", "JanFeb"),
            ("March", "April", "MarApr"),
            ("May", "June", "MayJun"),
            ("July", "August", "JulAug"),
            ("September", "October", "SepOct"),
            ("November", "December", "NovDec"),
        ]

        downloaded = []

        for year in years:
            for month1, month2, abbrev in periods:
                # Try different URL patterns
                url_patterns = [
                    f"https://tfsweb.tamu.edu/wp-content/uploads/{year}/TTPT_{year}_{month1}_{month2}.pdf",
                    f"https://tfsweb.tamu.edu/wp-content/uploads/{year + 1}/01/TTPT_{year}_{month1}_{month2}.pdf",
                    f"https://tfsweb.tamu.edu/wp-content/uploads/{year}/05/{abbrev}{year}.pdf",
                ]

                for url in url_patterns:
                    try:
                        pdf_path = self.download_file(
                            url, f"tx_bimonthly_{year}_{abbrev}.pdf"
                        )
                        downloaded.append(pdf_path)
                        break
                    except Exception:
                        continue

        return downloaded

    def parse(self) -> dict[str, Any]:
        """Parse Texas A&M PDF reports.

        Note: PDF parsing requires additional tools.

        Returns:
            Dictionary with file metadata
        """
        console.print("\n[bold]Texas A&M reports are PDFs.[/bold]")
        console.print("[dim]PDF parsing requires pdfplumber or similar tools.[/dim]\n")

        results = {
            "annual_reports": {},
            "five_year_reports": {},
        }

        # Catalog annual reports
        for year in ANNUAL_REPORTS:
            pdf_path = self.download_dir / f"tx_annual_{year}.pdf"
            if pdf_path.exists():
                results["annual_reports"][year] = {
                    "file": str(pdf_path),
                    "status": "downloaded",
                    "format": "PDF",
                }

        # Catalog 5-year reports
        for period in FIVE_YEAR_REPORTS:
            safe_period = period.replace("-", "_")
            pdf_path = self.download_dir / f"tx_5year_{safe_period}.pdf"
            if pdf_path.exists():
                results["five_year_reports"][period] = {
                    "file": str(pdf_path),
                    "status": "downloaded",
                    "format": "PDF",
                }

        return results

    def get_summary(self) -> None:
        """Print summary of Texas A&M downloaded data."""
        table = Table(title="Texas A&M Forest Service Downloaded Files")
        table.add_column("Category", style="cyan")
        table.add_column("File", style="white")
        table.add_column("Size", style="green")

        # Find all downloaded PDFs
        pdf_files = sorted(self.download_dir.glob("*.pdf"))

        if not pdf_files:
            table.add_row("None", "No files downloaded", "-")
        else:
            for pdf in pdf_files:
                size_kb = pdf.stat().st_size / 1024
                if pdf.name.startswith("annual_"):
                    category = "Annual"
                elif pdf.name.startswith("5year_"):
                    category = "5-Year"
                elif pdf.name.startswith("bimonthly_"):
                    category = "Bi-Monthly"
                else:
                    category = "Other"
                table.add_row(category, pdf.name, f"{size_kb:.1f} KB")

        console.print(table)


if __name__ == "__main__":
    with TexasAMDownloader() as downloader:
        files = downloader.download()
        downloader.get_summary()
