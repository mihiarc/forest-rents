"""Louisiana Department of Agriculture and Forestry stumpage data downloader.

Downloads quarterly forest products reports from Louisiana Office of Forestry.
Data available from 2010-present with stumpage prices by region and product.

Data source: https://www.ldaf.la.gov/land/forestry/forestry-reports
"""

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from timber_prices.downloaders.base import BaseDownloader

console = Console()

# Quarterly report URLs from LDAF (hosted on Contentful CDN)
# Format: {year: {quarter: url}}
QUARTERLY_REPORTS = {
    2025: {
        1: "https://assets.ctfassets.net/pc5e1rlgfrov/6HYnpFUgcxZ4Cx0FZrK5Ti/64678db035b31f17e8e895539af0e2f9/1ST_QTR_2025.pdf",
        2: "https://assets.ctfassets.net/pc5e1rlgfrov/3kCWE2SUJPcLLsPF0HIo23/e4cfedca2ba87f1c6db11d90fedca5a0/2ND_QTR_2025.pdf",
        3: "https://assets.ctfassets.net/pc5e1rlgfrov/15Rp15kXQOZHyzQqVxSdFl/cef99b1f9239a6f030aef7493309c782/3RD_QTR_2025.pdf",
    },
    2024: {
        1: "https://assets.ctfassets.net/pc5e1rlgfrov/2BPAjKpb5al6YSPxhfDCcl/5730bbac00ea10c75ac27c622b8494a4/1ST_QTR_2024_report.pdf",
        2: "https://assets.ctfassets.net/pc5e1rlgfrov/5as3lfrdQBUqFDM3rielMC/11db607683e90a8070b60f8103aa3c92/2nd_QTR_2024_Forestry_Report.pdf",
        3: "https://assets.ctfassets.net/pc5e1rlgfrov/6VIQMVI9DGPbfr3VFZ2ydz/d797e61a10b871df681bd550aa7c6bc4/3rd_QTR_2024_forest_report_of_products.pdf",
        4: "https://assets.ctfassets.net/pc5e1rlgfrov/014vX8zbsMDeBl7HnVhbId/1b5f1a6967fd07f70e0cce563a25bc1d/4TH_QTR_2024.pdf",
    },
    2023: {
        1: "https://assets.ctfassets.net/pc5e1rlgfrov/3D8vXW7fJNGwZZcwdhBpXW/53fce0da425180a5aad0781bbf2bc3cf/1stqtr2023_FORESTRY-REPORT.pdf",
        2: "https://assets.ctfassets.net/pc5e1rlgfrov/7M5LXcOpw1iwMKC79vomh4/13102fc6ec4fc062812e8cba0a680da5/2ndqtr2023.pdf",
        3: "https://assets.ctfassets.net/pc5e1rlgfrov/6O1YoVZ0oLE3zbtomf1ha1/845c8a28738fa69ff8b34d8d0be35bdb/3rdqtr2023.pdf",
        4: "https://assets.ctfassets.net/pc5e1rlgfrov/BldcEzrkKWBkVcfuxRCbC/500b8be983ac9e74ff20352222f08e75/4THqtr2023.pdf",
    },
    2022: {
        1: "https://assets.ctfassets.net/pc5e1rlgfrov/4S1TpIAJNv1sZAKnfdeaIT/2646d04bf4d91f5ba70c3f5aa9cae041/1stqtr2022_FORESTRY-REPORT.pdf",
        2: "https://assets.ctfassets.net/pc5e1rlgfrov/6M8HcmY4eE9OnI5PFkOdRE/fafc25262a7b4cf92d3dbb832902d833/2ndqtr2022_FORESTRY-REPORT.pdf",
        3: "https://assets.ctfassets.net/pc5e1rlgfrov/2EvziZhNFLbBnOxAE0wE11/e268a917a5f4b9ea1a1f5067807b1f9c/3rdqtr2022_FORESTRY-REPORT.pdf",
        4: "https://assets.ctfassets.net/pc5e1rlgfrov/5PKKEYOuxfvECa56dqg6Nu/1fcc324e3a75467446a1f2ed0dc88164/4THqtr2022.pdf",
    },
    2021: {
        1: "https://assets.ctfassets.net/pc5e1rlgfrov/24Kx4ZRXGVjCQH16ouWhh3/43383d142a9179bd857c7584caeb9934/1stqtr2021.pdf",
        2: "https://assets.ctfassets.net/pc5e1rlgfrov/3pKlooK09VQ9NeYAQMgjg2/1299afdba7ff91cbbe2536b54a8d847b/2ndqtr2021.pdf",
        3: "https://assets.ctfassets.net/pc5e1rlgfrov/6nn1AVdUHFPecyaitj7k8u/9e4f5531721adc9d0d6beee53ff783c9/3rdqtr2021.pdf",
        4: "https://assets.ctfassets.net/pc5e1rlgfrov/zm7USIso2sZPLjPhkeUF1/1a995f4bf1edec4db5a971ca4e4062f9/4thQtr2021.pdf",
    },
    2020: {
        1: "https://assets.ctfassets.net/pc5e1rlgfrov/1662x07tLwK6HUMh0HW7wE/0e0281c60bf1b77b69115c84df433b9a/1stqtr2020.pdf",
        2: "https://assets.ctfassets.net/pc5e1rlgfrov/4hFCusVDeBr18AWqbwXBTd/183d0f5a20e165ee43839666b3b4b0cf/2ND-QTR-RPT-2020.pdf",
        3: "https://assets.ctfassets.net/pc5e1rlgfrov/4eUIHV186sQHH4ygPfXIrC/0ea619d5386b4a3d9aab52910fe59f91/3rdqtr2020.pdf",
        4: "https://assets.ctfassets.net/pc5e1rlgfrov/5n7VODKXjmjMdKArGIBbcL/3fb26596d90707f83383ab538c1cfc85/4th-qtr-2020.pdf",
    },
    2019: {
        1: "https://assets.ctfassets.net/pc5e1rlgfrov/3I5vsieSeUnNo7P2qC8GLD/cdb28b534bfc062e86ebb627c2231aa1/1st-qtr-2019.pdf",
        2: "https://assets.ctfassets.net/pc5e1rlgfrov/6aux9wHHEDlpW0bjEAtSxV/b61757ba0d73d802f69042e46edd2bf2/2nd-qtr-2019.pdf",
        3: "https://assets.ctfassets.net/pc5e1rlgfrov/4p8aTyi4J3aDPRVUhlckKl/7b5e87eae2dede8887f5db911efd9385/3rd-qtr-2019.pdf",
        4: "https://assets.ctfassets.net/pc5e1rlgfrov/6DDXuphXyMbBF6ghsfwViy/8387a7340016ea66d7bb6f6a407c76c6/4th-qtr-2019.pdf",
    },
    2018: {
        1: "https://assets.ctfassets.net/pc5e1rlgfrov/5DL2rUIpCTMtuDF1ZDnYAU/1e02588222247d58cecbf5b584f1485e/1stqtr2018.pdf",
        2: "https://assets.ctfassets.net/pc5e1rlgfrov/3EK7JkGmtbFtdG2yyUuuDx/4773f16854d55e45bc8ed358ef5846d5/2ndqtr2018.pdf",
        3: "https://assets.ctfassets.net/pc5e1rlgfrov/6opjoZaekGwcnC5PLxmJSd/af3179418ccd82dee17ffc4b8742b078/3ndqtr2018.pdf",
        4: "https://assets.ctfassets.net/pc5e1rlgfrov/4WZRgf91KWLgOAE293euw9/eba4918010cb643e1996500fe47e8b39/4thqtr2018.pdf",
    },
    2017: {
        1: "https://assets.ctfassets.net/pc5e1rlgfrov/5M7dFeW95SCLUGKGzftXNq/2b6040c30a8541cf00605183b3a6b59b/1stqtr2017.pdf",
        2: "https://assets.ctfassets.net/pc5e1rlgfrov/1DJ0BczsSDFwzMBvUPiEgN/c48d525c4ef4919d9d207b3ef62ea2fc/2ndquarter2017.pdf",
        3: "https://assets.ctfassets.net/pc5e1rlgfrov/4smplXXblMOeRIsX4Ghf6H/27bfdf62c79c4a7c935bb4dd60f52b84/3rdqtr2017.pdf",
        4: "https://assets.ctfassets.net/pc5e1rlgfrov/1soLcUbx4pZ0UNQrTqxovD/88ae92a0133f29922d1d4f607503632c/4THQTR2017.pdf",
    },
    2016: {
        2: "https://assets.ctfassets.net/pc5e1rlgfrov/5XEEm3N4EPu2K82KMvqpnF/7215d1bed4638803ef359017b12d169d/2nrqtr2016.pdf",
        3: "https://assets.ctfassets.net/pc5e1rlgfrov/7j42GDIzXqlV9zm2lrak7b/603eba8027f8d2ab47cda9d03d51622d/3rdqtr2016.pdf",
        4: "https://assets.ctfassets.net/pc5e1rlgfrov/584g4JNKwPvBTGWSkEqNxD/f5e02be9290e36735f6b24002fcb8937/4thqtr2016.pdf",
    },
    2015: {
        1: "https://assets.ctfassets.net/pc5e1rlgfrov/5F1M3UFAQ3bADEkKDiYUbb/402d79a7d2303ae0ae1f6f99c1213235/1stqtr2015.pdf",
        2: "https://assets.ctfassets.net/pc5e1rlgfrov/7Jc3pwMGUkg2t59wyMdKX8/86111cc82e05b3a7fb6ce90fc0e2e67e/2ndqtr2015.pdf",
        3: "https://assets.ctfassets.net/pc5e1rlgfrov/2tCtn5oFUnpCjkPqNmPW0G/04df2695420e78dc89a9f88d17fe1278/3rdqtr2015.pdf",
        4: "https://assets.ctfassets.net/pc5e1rlgfrov/q8yR71lURB85Sl2TPIG86/353537a00e86df953b0db3afe7e669bf/4thqtr2015.pdf",
    },
    2014: {
        1: "https://assets.ctfassets.net/pc5e1rlgfrov/2i88WAbVmRPtKcgScD9XMy/10158718d68531218fca331726b24b2b/1stquarter2014.pdf",
        2: "https://assets.ctfassets.net/pc5e1rlgfrov/1A5C0SlgUAuOny7VQ1tiYW/1379e55529fa9d2773ae4dda8b22e7fc/2ndquarter2014.pdf",
        3: "https://assets.ctfassets.net/pc5e1rlgfrov/4K5vC7elBNYJcodtVucAre/41ce0f554089654b7723dcb88d60060f/3rdqtr2014.pdf",
        4: "https://assets.ctfassets.net/pc5e1rlgfrov/3siUY9egR2hCpaejjsYDsk/f429695362dba70f08d92e1306ea4a9e/4thqtr2014.pdf",
    },
    2013: {
        1: "https://assets.ctfassets.net/pc5e1rlgfrov/1fnE4kSNISOo19Uzqy8t97/5bdef3d4b251d382ecd5af2c77dfb1e4/1stquarterrpt2013.pdf",
        2: "https://assets.ctfassets.net/pc5e1rlgfrov/5h4DIfymNBM6pP0lZlLF4m/782ef220cb23091d77a0740508df14de/2ndquarterreport2013.pdf",
        3: "https://assets.ctfassets.net/pc5e1rlgfrov/3MbsSDdKJVj50cy2ph3ZtD/dc63b7dda14d6761df0767443d87223b/3qtrreport2013.pdf",
        4: "https://assets.ctfassets.net/pc5e1rlgfrov/2xYxuO91lTOHREkWUuOZcf/3901da08c8314123f552c8c132c6bb05/4thqtrreport2013.pdf",
    },
    2012: {
        1: "https://assets.ctfassets.net/pc5e1rlgfrov/42lsZbpr2IYdwdOnlR9OUW/3ce6a7d05a5d132e90ba8aab569af006/FOR_2012_Qtr1.pdf",
        2: "https://assets.ctfassets.net/pc5e1rlgfrov/1Dhq089pPm1rSA7F2tLg7V/da28c5f1dac866ea7de91707b8b9adf0/FOR_2012_Qtr2.pdf",
        3: "https://assets.ctfassets.net/pc5e1rlgfrov/71n5N5tki1gKnVGaopTavS/55609333917b99a6f988adc7371fd9ac/FOR_2012_Qtr3.pdf",
        4: "https://assets.ctfassets.net/pc5e1rlgfrov/Aaf2X7LD53IhLhe68pqga/f95a16d55bc5b869be34dcdab6254194/FOR_2012_Qtr4.pdf",
    },
    2011: {
        1: "https://assets.ctfassets.net/pc5e1rlgfrov/3NGlj0fXVakcwOB3JaWF1Q/ec9fee90932f542052cdf4d4f79f2070/FOR_2011_Qtr1.pdf",
        2: "https://assets.ctfassets.net/pc5e1rlgfrov/4OddK7Vu7tEzFFzvL0AWlk/268bb72b839ab47bb7cb4c14c0e1155d/FOR_2011_Qtr2.pdf",
        3: "https://assets.ctfassets.net/pc5e1rlgfrov/9Dur57w0Rie36Jytxc60R/66b80f46019556f5347f3542730e6a2e/FOR_2011_Qtr3.pdf",
        4: "https://assets.ctfassets.net/pc5e1rlgfrov/2hSdyYDUPngEMt3mfm48AQ/fcda502188556021523a5bc40f611514/FOR_2011_Qtr4.pdf",
    },
    2010: {
        1: "https://assets.ctfassets.net/pc5e1rlgfrov/1V1uNMayZEJHNxh0C97Fkh/09af64ab2064d7bc676548b562e610bc/FOR_2010_Qtr1.pdf",
        2: "https://assets.ctfassets.net/pc5e1rlgfrov/5gMIgisckgrINAfnHpgvxw/e9124f401185fbfb66a1f371b4733099/FOR_2010_Qtr2.pdf",
        3: "https://assets.ctfassets.net/pc5e1rlgfrov/7czeKXgX2snwvgspNBMtfe/3feff0afbb677d729427dbec351cb8b2/FOR_2010_Qtr3.pdf",
        4: "https://assets.ctfassets.net/pc5e1rlgfrov/3c5lSj0Zj7bRvRZNIqytZm/411ecd3c1c181153a9f52027debb77bd/FOR_2010_Qtr4.pdf",
    },
}

# Additional resources (annual reports, summaries)
ADDITIONAL_REPORTS = {
    "annual_harvest_summary": "https://assets.ctfassets.net/pc5e1rlgfrov/1uMisSNuuGVYHCogMAGEXb/e8ada678fb3b3fd768e92195c495b86c/ANNUAL_HARVEST_SUMMARY.pdf",
    "annual_income_summary": "https://assets.ctfassets.net/pc5e1rlgfrov/hnZWLYRzsRErnvTJhcmfH/97725571e9c119b202ce9d3020e0d6d0/ANNUAL_INCOME_SUMMARY.pdf",
    "timber_production_2020_present": "https://assets.ctfassets.net/pc5e1rlgfrov/68NVFhA7QWXGgYlk7RZoum/a9876e221206a21dd6a70b5cd4ce4053/timberProd_2020-present.pdf",
    "timber_production_2010_2019": "https://assets.ctfassets.net/pc5e1rlgfrov/78QUCEp0I8zML208rX0DbG/6d28aa6f563f42dad27e7ec8ec1fca47/timberProd_2010-2019.pdf",
    "timber_severance_2020_present": "https://assets.ctfassets.net/pc5e1rlgfrov/3w2IAhzXPe8AVoItdwZPEv/877bb7af07e1a3d30f393cff8d441cdf/timberSev_2020ToPresent.pdf",
    "2024_timber_pulpwood_report": "https://assets.ctfassets.net/pc5e1rlgfrov/38N7cC0aFnXKtZPSzIjist/b3562106311bed37b924c734a6b8f7ae/2024_tbr_pwp_report__002_.pdf",
}


class LouisianaForestryDownloader(BaseDownloader):
    """Download stumpage data from Louisiana Department of Agriculture and Forestry.

    LDAF Office of Forestry publishes quarterly reports of stumpage prices
    paid for raw forest products at the first point of sale.

    Products covered:
    - Pine sawtimber
    - Pine chip-n-saw
    - Pine pulpwood
    - Hardwood sawtimber
    - Hardwood pulpwood

    Regions covered:
    - North Louisiana
    - Central Louisiana
    - South Louisiana
    - Statewide averages
    """

    @property
    def source_name(self) -> str:
        return "Louisiana LDAF Forestry Reports"

    @property
    def source_id(self) -> str:
        return "la_forestry"

    def download(self, years: list[int] | None = None) -> list[Path]:
        """Download Louisiana forestry quarterly reports.

        Args:
            years: Optional list of years to download. Defaults to all available.

        Returns:
            List of paths to downloaded PDF files
        """
        console.print(f"\n[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold]{self.source_name}[/bold]")
        console.print(f"[dim]Quarterly stumpage prices by region (2010-2025)[/dim]")
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
            for quarter, url in quarters.items():
                local_filename = f"la_forestry_{year}_q{quarter}.pdf"

                try:
                    pdf_path = self.download_file(url, local_filename)

                    # Verify it's a valid PDF
                    size_kb = pdf_path.stat().st_size / 1024
                    if size_kb > 5:
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

    def download_additional(self) -> list[Path]:
        """Download additional reports (annual summaries, production reports).

        Returns:
            List of paths to downloaded files
        """
        console.print("\n[bold]Downloading additional reports...[/bold]")

        downloaded = []
        for report_name, url in ADDITIONAL_REPORTS.items():
            try:
                pdf_path = self.download_file(url, f"la_{report_name}.pdf")
                downloaded.append(pdf_path)
                console.print(f"[green]Downloaded:[/green] {report_name}")
            except Exception as e:
                console.print(f"[yellow]Could not download {report_name}:[/yellow] {e}")

        return downloaded

    def parse(self) -> dict[str, Any]:
        """Parse Louisiana forestry PDF reports.

        Note: PDF parsing requires additional tools like pdfplumber.

        Returns:
            Dictionary with file metadata
        """
        console.print("\n[bold]Louisiana reports are PDFs.[/bold]")
        console.print("[dim]PDF parsing requires pdfplumber or similar tools.[/dim]")
        console.print("[dim]Data contains regional and statewide stumpage averages.[/dim]\n")

        results = {}
        for year in QUARTERLY_REPORTS:
            year_data = {}
            for quarter in QUARTERLY_REPORTS[year]:
                pdf_path = self.download_dir / f"la_forestry_{year}_q{quarter}.pdf"
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
        """Print summary of Louisiana data."""
        table = Table(title="Louisiana LDAF Forestry Reports")
        table.add_column("Year", style="cyan")
        table.add_column("Q1", style="white")
        table.add_column("Q2", style="white")
        table.add_column("Q3", style="white")
        table.add_column("Q4", style="white")

        for year in sorted(QUARTERLY_REPORTS.keys(), reverse=True):
            row = [str(year)]
            for quarter in [1, 2, 3, 4]:
                pdf_path = self.download_dir / f"la_forestry_{year}_q{quarter}.pdf"
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
        total_downloaded = len(list(self.download_dir.glob("la_forestry_*_q*.pdf")))
        console.print(f"\n[dim]Total available: {total_available} quarterly reports ({len(QUARTERLY_REPORTS)} years)[/dim]")
        console.print(f"[dim]Downloaded: {total_downloaded} reports[/dim]")


if __name__ == "__main__":
    with LouisianaForestryDownloader() as downloader:
        # Download recent 5 years by default
        files = downloader.download_recent(5)
        downloader.get_summary()
