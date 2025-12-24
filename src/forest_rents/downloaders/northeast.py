"""Northeast states stumpage price data downloaders.

Downloads stumpage price data from:
- New York DEC: Semi-annual stumpage price reports
- Pennsylvania Extension: Quarterly timber market reports
- Vermont FPR: Quarterly stumpage reports

Data sources:
- https://dec.ny.gov/nature/forests-trees/forest-products-utilization/stumpage-price-reports
- https://extension.psu.edu/timber-market-report-archives
- https://fpr.vermont.gov/stumpage-price-reports
"""

from pathlib import Path
from typing import Any

import pandas as pd
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table

from forest_rents.downloaders.base import BaseDownloader

console = Console()

# New York DEC URLs
NY_BASE_URL = "https://dec.ny.gov"
NY_REPORTS = {
    "2025_winter": "/sites/default/files/2025-02/2025winterspr.pdf",
    "2024_summer": "/sites/default/files/2024-07/2024summerspr105.pdf",
    "2024_winter": "/sites/default/files/2024-02/2024winterspr104.pdf",
    "2023_summer": "/sites/default/files/2024-02/2023summerspr103.pdf",
    "2023_winter": "/sites/default/files/2024-02/2023winterspr102.pdf",
    "2022_summer": "/sites/default/files/2024-02/2022summerspr101.pdf",
    "2022_winter": "/sites/default/files/2024-02/2022winterspr100.pdf",
    "2021_summer": "/sites/default/files/2024-02/2021summerspr99.pdf",
    "2021_winter": "/sites/default/files/2024-02/2021winterspr98.pdf",
}

# Penn State Extension - we'll scrape their archives page for report URLs
PA_ARCHIVES_URL = "https://extension.psu.edu/timber-market-report-archives"

# Vermont FPR
VT_BASE_URL = "https://fpr.vermont.gov/stumpage-price-reports"


class NewYorkDECDownloader(BaseDownloader):
    """Download stumpage data from New York DEC."""

    @property
    def source_name(self) -> str:
        return "New York DEC Stumpage Price Reports"

    @property
    def source_id(self) -> str:
        return "ny_dec"

    def download(self) -> list[Path]:
        """Download New York DEC stumpage price reports.

        Returns:
            List of paths to downloaded PDF files
        """
        console.print(f"\n[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold]{self.source_name}[/bold]")
        console.print(f"[dim]Semi-annual reports by region (2021-2025)[/dim]")
        console.print(f"[bold blue]{'='*60}[/bold blue]\n")

        downloaded = []

        for report_id, path in NY_REPORTS.items():
            url = f"{NY_BASE_URL}{path}"
            try:
                pdf_path = self.download_file(url, f"ny_{report_id}.pdf")
                downloaded.append(pdf_path)
            except Exception as e:
                console.print(f"[yellow]Could not download {report_id}:[/yellow] {e}")

        console.print(f"\n[bold green]Downloaded {len(downloaded)} reports[/bold green]")
        return downloaded

    def parse(self) -> dict[str, Any]:
        """Parse New York DEC PDF reports.

        Note: PDF parsing requires additional tools.

        Returns:
            Dictionary with file metadata
        """
        console.print("\n[bold]New York DEC reports are PDFs.[/bold]")
        console.print("[dim]PDF parsing requires manual extraction or OCR tools.[/dim]\n")

        results = {}
        for report_id in NY_REPORTS:
            pdf_path = self.download_dir / f"ny_{report_id}.pdf"
            if pdf_path.exists():
                results[report_id] = {
                    "file": pdf_path,
                    "status": "downloaded",
                    "format": "PDF",
                }

        return results

    def get_summary(self) -> None:
        """Print summary of New York DEC data."""
        table = Table(title="New York DEC Stumpage Reports")
        table.add_column("Period", style="cyan")
        table.add_column("Status", style="yellow")

        for report_id in sorted(NY_REPORTS.keys(), reverse=True):
            pdf_path = self.download_dir / f"ny_{report_id}.pdf"
            status = "[green]Downloaded[/green]" if pdf_path.exists() else "[dim]Not downloaded[/dim]"
            table.add_row(report_id.replace("_", " ").title(), status)

        console.print(table)


class PennsylvaniaExtensionDownloader(BaseDownloader):
    """Download stumpage data from Penn State Extension.

    Penn State displays reports as HTML content. We scrape the quarterly
    reports from their archives page.
    """

    @property
    def source_name(self) -> str:
        return "Penn State Extension Timber Market Reports"

    @property
    def source_id(self) -> str:
        return "pa_extension"

    def download(self) -> list[Path]:
        """Download Pennsylvania Extension timber market reports.

        Scrapes report pages and saves as HTML for parsing.

        Returns:
            List of paths to downloaded HTML files
        """
        console.print(f"\n[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold]{self.source_name}[/bold]")
        console.print(f"[dim]Quarterly reports with regional stumpage prices[/dim]")
        console.print(f"[bold blue]{'='*60}[/bold blue]\n")

        # First, get the archives page to find report URLs
        console.print("[dim]Fetching report archive...[/dim]")
        response = self.client.get(PA_ARCHIVES_URL)
        response.raise_for_status()

        # Save archives page
        archives_path = self.download_dir / "archives.html"
        archives_path.write_text(response.text, encoding="utf-8")

        # Parse to find report links
        soup = BeautifulSoup(response.text, "lxml")
        report_links = []

        # Find all links to individual reports
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True).lower()
            if "timber-market-report" in href and "quarter" in text:
                full_url = href if href.startswith("http") else f"https://extension.psu.edu{href}"
                report_links.append((text, full_url))

        console.print(f"[dim]Found {len(report_links)} quarterly reports[/dim]")

        # Download a sample of recent reports (last 8 quarters = 2 years)
        downloaded = []
        for i, (title, url) in enumerate(report_links[:8]):
            try:
                response = self.client.get(url)
                response.raise_for_status()

                # Create filename from title
                safe_title = title.replace(" ", "_").replace(",", "")[:50]
                html_path = self.download_dir / f"pa_{safe_title}.html"
                html_path.write_text(response.text, encoding="utf-8")
                downloaded.append(html_path)
                console.print(f"[green]Downloaded:[/green] {title[:60]}...")

            except Exception as e:
                console.print(f"[yellow]Could not download {title[:40]}:[/yellow] {e}")

        return downloaded

    def parse(self) -> dict[str, pd.DataFrame]:
        """Parse Pennsylvania HTML reports into DataFrames.

        Returns:
            Dictionary mapping report names to DataFrames
        """
        console.print("\n[bold]Parsing Pennsylvania reports...[/bold]\n")

        results = {}
        html_files = list(self.download_dir.glob("pa_*.html"))

        for html_path in html_files:
            if html_path.name == "archives.html":
                continue

            try:
                html_content = html_path.read_text(encoding="utf-8")
                soup = BeautifulSoup(html_content, "lxml")

                # Find price tables in the HTML
                tables = soup.find_all("table")

                for i, table in enumerate(tables):
                    df = self._parse_price_table(table)
                    if df is not None and not df.empty:
                        key = f"{html_path.stem}_table{i}"
                        results[key] = df
                        console.print(f"[green]Parsed:[/green] {key}")

            except Exception as e:
                console.print(f"[yellow]Could not parse {html_path.name}:[/yellow] {e}")

        return results

    def _parse_price_table(self, table) -> pd.DataFrame | None:
        """Parse an HTML table into a DataFrame."""
        rows = table.find_all("tr")
        if len(rows) < 2:
            return None

        data = []
        headers = None

        for row in rows:
            cells = row.find_all(["th", "td"])
            cell_texts = [cell.get_text(strip=True) for cell in cells]

            if not any(cell_texts):
                continue

            if headers is None and any("price" in c.lower() or "species" in c.lower() for c in cell_texts):
                headers = cell_texts
                continue

            if headers and len(cell_texts) == len(headers):
                data.append(cell_texts)

        if not headers or not data:
            return None

        return pd.DataFrame(data, columns=headers)

    def get_summary(self) -> None:
        """Print summary of Pennsylvania data."""
        table = Table(title="Penn State Extension Reports")
        table.add_column("Report", style="cyan")
        table.add_column("Status", style="yellow")

        html_files = list(self.download_dir.glob("pa_*.html"))
        html_files = [f for f in html_files if f.name != "archives.html"]

        if html_files:
            for f in sorted(html_files)[:10]:
                table.add_row(f.stem, "[green]Downloaded[/green]")
        else:
            table.add_row("No reports", "[dim]Not downloaded[/dim]")

        console.print(table)


class VermontFPRDownloader(BaseDownloader):
    """Download stumpage data from Vermont Forests, Parks & Recreation."""

    @property
    def source_name(self) -> str:
        return "Vermont Stumpage Price Reports"

    @property
    def source_id(self) -> str:
        return "vt_fpr"

    def download(self) -> list[Path]:
        """Download Vermont FPR stumpage reports.

        Returns:
            List of paths to downloaded files
        """
        console.print(f"\n[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold]{self.source_name}[/bold]")
        console.print(f"[dim]Quarterly stumpage price reports (1981-present)[/dim]")
        console.print(f"[bold blue]{'='*60}[/bold blue]\n")

        # Fetch the main page to find report links
        response = self.client.get(VT_BASE_URL)
        response.raise_for_status()

        # Save main page
        main_path = self.download_dir / "vt_stumpage_main.html"
        main_path.write_text(response.text, encoding="utf-8")
        console.print(f"[green]Saved:[/green] {main_path}")

        # Parse for PDF links
        soup = BeautifulSoup(response.text, "lxml")
        downloaded = [main_path]

        pdf_links = []
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            if ".pdf" in href.lower():
                full_url = href if href.startswith("http") else f"https://fpr.vermont.gov{href}"
                pdf_links.append((link.get_text(strip=True), full_url))

        console.print(f"[dim]Found {len(pdf_links)} PDF links[/dim]")

        # Download PDFs (limit to recent ones)
        for title, url in pdf_links[:12]:  # Last 3 years of quarterly reports
            try:
                filename = url.split("/")[-1]
                pdf_path = self.download_file(url, f"vt_{filename}")
                downloaded.append(pdf_path)
            except Exception as e:
                console.print(f"[yellow]Could not download {title[:40]}:[/yellow] {e}")

        return downloaded

    def parse(self) -> dict[str, Any]:
        """Parse Vermont reports.

        Returns:
            Dictionary with file metadata
        """
        console.print("\n[bold]Vermont reports are PDFs.[/bold]")
        console.print("[dim]PDF parsing requires manual extraction.[/dim]\n")

        results = {}
        pdf_files = list(self.download_dir.glob("vt_*.pdf"))

        for pdf_path in pdf_files:
            results[pdf_path.stem] = {
                "file": pdf_path,
                "status": "downloaded",
                "format": "PDF",
            }

        return results

    def get_summary(self) -> None:
        """Print summary of Vermont data."""
        table = Table(title="Vermont Stumpage Reports")
        table.add_column("File", style="cyan")
        table.add_column("Status", style="yellow")

        pdf_files = list(self.download_dir.glob("vt_*.pdf"))

        if pdf_files:
            for f in sorted(pdf_files)[:10]:
                table.add_row(f.name, "[green]Downloaded[/green]")
            if len(pdf_files) > 10:
                table.add_row(f"... and {len(pdf_files) - 10} more", "")
        else:
            table.add_row("No reports", "[dim]Not downloaded[/dim]")

        console.print(table)


class NortheastDownloader:
    """Combined downloader for all Northeast states data."""

    def __init__(self):
        self.new_york = NewYorkDECDownloader()
        self.pennsylvania = PennsylvaniaExtensionDownloader()
        self.vermont = VermontFPRDownloader()

    def download_all(self) -> dict[str, list[Path]]:
        """Download data from all Northeast sources.

        Returns:
            Dictionary mapping state to list of downloaded files
        """
        results = {}

        with self.new_york as ny:
            results["new_york"] = ny.download()

        with self.pennsylvania as pa:
            results["pennsylvania"] = pa.download()

        with self.vermont as vt:
            results["vermont"] = vt.download()

        return results

    def get_summary(self) -> None:
        """Print summary of all Northeast data."""
        self.new_york.get_summary()
        console.print()
        self.pennsylvania.get_summary()
        console.print()
        self.vermont.get_summary()


if __name__ == "__main__":
    downloader = NortheastDownloader()
    results = downloader.download_all()
    downloader.get_summary()
