"""Lake States (MN, MI, WI) stumpage price data downloaders.

Downloads stumpage price data from:
- Minnesota DNR: Public Stumpage Price Review (2003-2021)
- Michigan DNR: Stumpage Price Reports (1953-present)
- Wisconsin DNR: Forest Crop Law (FCL) and Managed Forest Law (MFL) Stumpage Rates

Data sources:
- https://www.dnr.state.mn.us/forestry/timbersales/stumpage.html
- https://www2.dnr.state.mi.us/ftp/forestry/tsreports/StumpagePriceReports/
- https://dnr.wisconsin.gov/topic/forestlandowners/taxrates
"""

from pathlib import Path
from typing import Any

import pandas as pd
from rich.console import Console
from rich.table import Table

from forest_rents.downloaders.base import BaseDownloader

console = Console()

# Michigan DNR URLs
MI_BASE_URL = "https://www2.dnr.state.mi.us/ftp/forestry/tsreports/StumpagePriceReports"
MI_EXCEL_FILE = "Majorspecies-productpriceindicestoPost.xlsx"

# Minnesota DNR URLs
MN_BASE_URL = "https://files.dnr.state.mn.us/forestry/timber_sales/stumpage"
MN_REPORTS = {
    2021: "stumpage-review-report-2021.pdf",
    2020: "stumpage-review-report-2020.pdf",
    2019: "stumpage-review-report-2019.pdf",
    2018: "stumpage-review-report-2018.pdf",
    2017: "stumpage-review-report-2017.pdf",
    2016: "stumpage-review-report-2016.pdf",
    2015: "stumpage-review-report-2015.pdf",
    2014: "stumpage-review-report-2014.pdf",
    2013: "stumpage-review-report-2013.pdf",
    2012: "stumpage-review-report-2012.pdf",
    2011: "stumpage-review-report-2011.pdf",
    2010: "stumpage-review-report-2010.pdf",
    2009: "stumpage-review-report-2009.pdf",
    2008: "stumpage-review-report-2008.pdf",
    2007: "stumpage-review-report-2007.pdf",
}

# Wisconsin DNR URLs
# FCL = Forest Crop Law, MFL = Managed Forest Law
# Rates are 3-year weighted averages, updated annually (effective Nov 1 - Oct 31)
WI_BASE_URL = "https://dnr.wisconsin.gov/sites/default/files/topic"
WI_STUMPAGE_FILES = {
    "fcl_mfl_combined": {
        "url": f"{WI_BASE_URL}/ForestLandowners/FCL_MFL_StumpageRates.pdf",
        "description": "Combined FCL/MFL stumpage rates (current year)",
    },
    "mfl_cords": {
        "url": f"{WI_BASE_URL}/ForestLandowners/MFL_Cords.pdf",
        "description": "MFL stumpage rates - cord products",
    },
    "mfl_logs": {
        "url": f"{WI_BASE_URL}/ForestLandowners/MFL_Logs.pdf",
        "description": "MFL stumpage rates - log products",
    },
    "fcl_logs": {
        "url": f"{WI_BASE_URL}/ForestLandowners/FCL_Logs.pdf",
        "description": "FCL stumpage rates - log products",
    },
    "state_lands_base": {
        "url": f"{WI_BASE_URL}/TimberSales/RecommendedBaseStumpageRates.pdf",
        "description": "State lands recommended base stumpage rates",
    },
}


class MichiganDNRDownloader(BaseDownloader):
    """Download stumpage data from Michigan DNR."""

    @property
    def source_name(self) -> str:
        return "Michigan DNR Stumpage Price Reports"

    @property
    def source_id(self) -> str:
        return "mi_dnr"

    def download(self) -> list[Path]:
        """Download Michigan DNR stumpage price data.

        Returns:
            List of paths to downloaded files
        """
        console.print(f"\n[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold]{self.source_name}[/bold]")
        console.print(f"[dim]Stumpage price indices - major species and products[/dim]")
        console.print(f"[bold blue]{'='*60}[/bold blue]\n")

        downloaded = []

        # Download the main Excel file with price indices
        excel_url = f"{MI_BASE_URL}/{MI_EXCEL_FILE}"
        try:
            excel_path = self.download_file(excel_url, "mi_stumpage_price_indices.xlsx")
            downloaded.append(excel_path)
        except Exception as e:
            console.print(f"[red]Error downloading Excel file:[/red] {e}")

        return downloaded

    def parse(self) -> dict[str, pd.DataFrame]:
        """Parse downloaded Michigan DNR Excel file.

        Returns:
            Dictionary with parsed DataFrames
        """
        console.print("\n[bold]Parsing Michigan DNR price data...[/bold]\n")

        excel_path = self.download_dir / "mi_stumpage_price_indices.xlsx"
        if not excel_path.exists():
            console.print("[red]Error: Excel file not found. Run download() first.[/red]")
            return {}

        results = {}

        try:
            # Read all sheets from the Excel file
            xlsx = pd.ExcelFile(excel_path)
            console.print(f"[dim]Found {len(xlsx.sheet_names)} sheets: {xlsx.sheet_names}[/dim]")

            for sheet_name in xlsx.sheet_names:
                df = pd.read_excel(xlsx, sheet_name=sheet_name)
                results[sheet_name] = df
                console.print(
                    f"[green]Parsed:[/green] {sheet_name} - "
                    f"{df.shape[0]} rows x {df.shape[1]} cols"
                )

                # Save each sheet as CSV
                csv_path = self.download_dir / f"mi_{sheet_name.lower().replace(' ', '_')}.csv"
                df.to_csv(csv_path, index=False)
                console.print(f"[dim]Saved: {csv_path.name}[/dim]")

        except Exception as e:
            console.print(f"[red]Error parsing Excel file:[/red] {e}")

        return results

    def get_summary(self) -> None:
        """Print summary of Michigan DNR data."""
        table = Table(title="Michigan DNR Stumpage Data")
        table.add_column("File", style="cyan")
        table.add_column("Status", style="yellow")

        excel_path = self.download_dir / "mi_stumpage_price_indices.xlsx"
        status = "[green]Downloaded[/green]" if excel_path.exists() else "[dim]Not downloaded[/dim]"
        table.add_row("Price Indices Excel", status)

        console.print(table)


class MinnesotaDNRDownloader(BaseDownloader):
    """Download stumpage data from Minnesota DNR."""

    @property
    def source_name(self) -> str:
        return "Minnesota DNR Stumpage Price Review"

    @property
    def source_id(self) -> str:
        return "mn_dnr"

    def download(self) -> list[Path]:
        """Download Minnesota DNR stumpage price reports.

        Returns:
            List of paths to downloaded PDF files
        """
        console.print(f"\n[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold]{self.source_name}[/bold]")
        console.print(f"[dim]Annual stumpage price reviews (2007-2021)[/dim]")
        console.print(f"[bold blue]{'='*60}[/bold blue]\n")

        downloaded = []

        for year, filename in MN_REPORTS.items():
            url = f"{MN_BASE_URL}/{filename}"
            try:
                pdf_path = self.download_file(url, f"mn_stumpage_{year}.pdf")
                downloaded.append(pdf_path)
            except Exception as e:
                console.print(f"[yellow]Could not download {year}:[/yellow] {e}")

        console.print(f"\n[bold green]Downloaded {len(downloaded)} annual reports[/bold green]")
        return downloaded

    def parse(self) -> dict[str, Any]:
        """Parse Minnesota DNR PDF reports.

        Note: PDF parsing requires additional tools. This method returns
        metadata about available files.

        Returns:
            Dictionary with file metadata
        """
        console.print("\n[bold]Minnesota DNR reports are PDFs.[/bold]")
        console.print("[dim]PDF parsing requires manual extraction or OCR tools.[/dim]\n")

        results = {}
        for year in MN_REPORTS:
            pdf_path = self.download_dir / f"mn_stumpage_{year}.pdf"
            if pdf_path.exists():
                results[year] = {
                    "file": pdf_path,
                    "status": "downloaded",
                    "format": "PDF",
                }

        return results

    def get_summary(self) -> None:
        """Print summary of Minnesota DNR data."""
        table = Table(title="Minnesota DNR Stumpage Reports")
        table.add_column("Year", style="cyan")
        table.add_column("Status", style="yellow")

        for year in sorted(MN_REPORTS.keys(), reverse=True):
            pdf_path = self.download_dir / f"mn_stumpage_{year}.pdf"
            status = "[green]Downloaded[/green]" if pdf_path.exists() else "[dim]Not downloaded[/dim]"
            table.add_row(str(year), status)

        console.print(table)


class WisconsinDNRDownloader(BaseDownloader):
    """Download stumpage data from Wisconsin DNR.

    Wisconsin DNR publishes stumpage rates for the Forest Crop Law (FCL) and
    Managed Forest Law (MFL) programs. Rates are 3-year weighted averages
    calculated from state and county timber sale data, updated annually.

    Data effective: November 1 - October 31 each year
    """

    @property
    def source_name(self) -> str:
        return "Wisconsin DNR Stumpage Rates"

    @property
    def source_id(self) -> str:
        return "wi_dnr"

    def download(self) -> list[Path]:
        """Download Wisconsin DNR stumpage rate PDFs.

        Downloads:
        - Combined FCL/MFL stumpage rates
        - MFL cord products rates
        - MFL log products rates
        - FCL log products rates
        - State lands recommended base rates

        Returns:
            List of paths to downloaded PDF files
        """
        console.print(f"\n[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold]{self.source_name}[/bold]")
        console.print(f"[dim]FCL/MFL 3-year weighted average stumpage rates[/dim]")
        console.print(f"[bold blue]{'='*60}[/bold blue]\n")

        downloaded = []

        for file_id, file_info in WI_STUMPAGE_FILES.items():
            url = file_info["url"]
            description = file_info["description"]

            try:
                pdf_path = self.download_file(url, f"wi_{file_id}.pdf")

                # Verify it's a valid PDF (not an error page)
                size_kb = pdf_path.stat().st_size / 1024
                if size_kb > 5:  # Valid PDFs should be > 5KB
                    downloaded.append(pdf_path)
                    console.print(f"[dim]{description}[/dim]")
                else:
                    console.print(f"[yellow]Invalid file for {file_id} (too small)[/yellow]")
                    pdf_path.unlink()

            except Exception as e:
                console.print(f"[yellow]Could not download {file_id}:[/yellow] {e}")

        console.print(f"\n[bold green]Downloaded {len(downloaded)} stumpage rate files[/bold green]")
        return downloaded

    def parse(self) -> dict[str, Any]:
        """Parse Wisconsin DNR PDF reports.

        Note: PDF parsing requires additional tools like pdfplumber.
        The PDFs contain tabular stumpage rates by species and product type.

        Returns:
            Dictionary with file metadata
        """
        console.print("\n[bold]Wisconsin DNR reports are PDFs.[/bold]")
        console.print("[dim]PDF parsing requires pdfplumber or similar tools.[/dim]")
        console.print("[dim]Data contains 3-year weighted averages by species/product.[/dim]\n")

        results = {}
        for file_id, file_info in WI_STUMPAGE_FILES.items():
            pdf_path = self.download_dir / f"wi_{file_id}.pdf"
            if pdf_path.exists():
                size_kb = pdf_path.stat().st_size / 1024
                results[file_id] = {
                    "file": str(pdf_path),
                    "description": file_info["description"],
                    "status": "downloaded",
                    "format": "PDF",
                    "size_kb": round(size_kb, 1),
                }

        return results

    def get_summary(self) -> None:
        """Print summary of Wisconsin DNR data."""
        table = Table(title="Wisconsin DNR Stumpage Rates")
        table.add_column("File", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Status", style="yellow")
        table.add_column("Size", style="green")

        for file_id, file_info in WI_STUMPAGE_FILES.items():
            pdf_path = self.download_dir / f"wi_{file_id}.pdf"
            if pdf_path.exists():
                size_kb = pdf_path.stat().st_size / 1024
                status = "[green]Downloaded[/green]"
                size = f"{size_kb:.1f} KB"
            else:
                status = "[dim]Not downloaded[/dim]"
                size = "-"

            table.add_row(
                file_id,
                file_info["description"][:40],
                status,
                size,
            )

        console.print(table)


class LakeStatesDownloader:
    """Combined downloader for all Lake States data."""

    def __init__(self):
        self.michigan = MichiganDNRDownloader()
        self.minnesota = MinnesotaDNRDownloader()
        self.wisconsin = WisconsinDNRDownloader()

    def download_all(self) -> dict[str, list[Path]]:
        """Download data from all Lake States sources.

        Returns:
            Dictionary mapping state to list of downloaded files
        """
        results = {}

        with self.michigan as mi:
            results["michigan"] = mi.download()
            mi.parse()

        with self.minnesota as mn:
            results["minnesota"] = mn.download()

        with self.wisconsin as wi:
            results["wisconsin"] = wi.download()

        return results

    def get_summary(self) -> None:
        """Print summary of all Lake States data."""
        self.michigan.get_summary()
        console.print()
        self.minnesota.get_summary()
        console.print()
        self.wisconsin.get_summary()


if __name__ == "__main__":
    downloader = LakeStatesDownloader()
    results = downloader.download_all()
    downloader.get_summary()
