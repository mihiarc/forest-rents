"""USDA Forest Service Pacific Northwest Research Station data downloader.

Downloads production, prices, employment, and trade data for Northwest
forest industries from 1958-2023.

Data source: https://research.fs.usda.gov/pnw/products/dataandtools/
             production-prices-employment-and-trade-northwest-forest-industries-1958
"""

import zipfile
from pathlib import Path

import pandas as pd
from rich.console import Console
from rich.table import Table

from forest_rents.downloaders.base import BaseDownloader

console = Console()

# Base URL for USFS PNW data
BASE_URL = "https://research.fs.usda.gov/sites/default/files/2025-07"

# ZIP archive containing all tables
ARCHIVE_URL = f"{BASE_URL}/pnw-ppet-tables-1958-2023-excel-latest-version.zip"

# Key stumpage price tables (file names as they appear in the ZIP archive)
STUMPAGE_TABLES = {
    # Public lands stumpage prices (includes state, county, and federal lands)
    "table76": {
        "description": "Stumpage prices on publicly managed lands, Montana and Idaho",
        "states": ["MT", "ID"],
        "file": "PPET-Table76.xlsx",
    },
    "table84": {
        "description": "Stumpage prices on publicly managed lands, California",
        "states": ["CA"],
        "file": "PPET-Table84.xlsx",
    },
    "table90": {
        "description": "Stumpage prices on publicly managed lands, Washington and Oregon",
        "states": ["WA", "OR"],
        "file": "PPET-Table90.xlsx",
    },
    "table96": {
        "description": "Stumpage prices on publicly managed lands, Alaska",
        "states": ["AK"],
        "file": "PPET-Table96.xlsx",
    },
    # National Forest stumpage prices by species
    "table78": {
        "description": "NF stumpage prices by species, Northern Region (MT/ID)",
        "states": ["MT", "ID"],
        "file": "PPET-Table78.xlsx",
    },
    "table81": {
        "description": "NF stumpage prices by species, Intermountain Region",
        "states": ["NV", "UT", "WY", "CO", "ID"],
        "file": "PPET-Table81.xlsx",
    },
    "table86": {
        "description": "NF stumpage prices by species, Pacific Southwest (CA)",
        "states": ["CA"],
        "file": "PPET-Table86.xlsx",
    },
    "table92": {
        "description": "NF stumpage prices by species, Pacific Northwest (WA/OR)",
        "states": ["WA", "OR"],
        "file": "PPET-Table92.xlsx",
    },
}


class USFSPNWDownloader(BaseDownloader):
    """Download stumpage data from USFS Pacific Northwest Research Station."""

    @property
    def source_name(self) -> str:
        return "USDA Forest Service Pacific Northwest Research Station"

    @property
    def source_id(self) -> str:
        return "usfs_pnw"

    def download(self) -> list[Path]:
        """Download the PPET Excel archive and extract stumpage tables.

        Returns:
            List of paths to extracted Excel files
        """
        console.print(f"\n[bold blue]{'='*60}[/bold blue]")
        console.print(f"[bold]{self.source_name}[/bold]")
        console.print(f"[dim]Stumpage prices 1958-2023 for Pacific Northwest region[/dim]")
        console.print(f"[bold blue]{'='*60}[/bold blue]\n")

        # Download the ZIP archive
        zip_path = self.download_file(ARCHIVE_URL, "ppet-tables-excel.zip")

        # Extract stumpage price tables
        extracted_files = []
        with zipfile.ZipFile(zip_path, "r") as zf:
            all_files = zf.namelist()
            console.print(f"[dim]Archive contains {len(all_files)} files[/dim]")

            # Extract only stumpage-related tables
            for table_id, table_info in STUMPAGE_TABLES.items():
                target_file = table_info["file"]
                matching = [f for f in all_files if f.endswith(target_file)]

                if matching:
                    source_path = matching[0]
                    dest_path = self.download_dir / target_file

                    with zf.open(source_path) as src, open(dest_path, "wb") as dst:
                        dst.write(src.read())

                    extracted_files.append(dest_path)
                    console.print(
                        f"[green]Extracted:[/green] {target_file} "
                        f"[dim]({table_info['description']})[/dim]"
                    )
                else:
                    console.print(f"[yellow]Not found:[/yellow] {target_file}")

        console.print(f"\n[bold green]Extracted {len(extracted_files)} stumpage tables[/bold green]")
        return extracted_files

    def parse(self) -> dict[str, pd.DataFrame]:
        """Parse extracted Excel files into DataFrames.

        Returns:
            Dictionary mapping table IDs to DataFrames
        """
        console.print("\n[bold]Parsing stumpage price tables...[/bold]\n")

        results = {}
        for table_id, table_info in STUMPAGE_TABLES.items():
            file_path = self.download_dir / table_info["file"]

            if not file_path.exists():
                console.print(f"[yellow]Skipping {table_id}: file not found[/yellow]")
                continue

            try:
                # Read the Excel file - may need to skip header rows
                df = pd.read_excel(file_path, header=None)

                # Store raw data for now - specific parsing logic will vary by table
                results[table_id] = {
                    "raw_df": df,
                    "file": file_path,
                    "states": table_info["states"],
                    "description": table_info["description"],
                }

                console.print(
                    f"[green]Parsed:[/green] {table_id} - "
                    f"{df.shape[0]} rows x {df.shape[1]} cols"
                )

            except Exception as e:
                console.print(f"[red]Error parsing {table_id}:[/red] {e}")

        return results

    def get_summary(self) -> None:
        """Print a summary of available stumpage data."""
        table = Table(title="USFS PNW Stumpage Price Tables")
        table.add_column("Table", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("States", style="green")
        table.add_column("Status", style="yellow")

        for table_id, table_info in STUMPAGE_TABLES.items():
            file_path = self.download_dir / table_info["file"]
            status = "[green]Downloaded[/green]" if file_path.exists() else "[dim]Not downloaded[/dim]"

            table.add_row(
                table_id,
                table_info["description"],
                ", ".join(table_info["states"]),
                status,
            )

        console.print(table)


if __name__ == "__main__":
    with USFSPNWDownloader() as downloader:
        files = downloader.download()
        downloader.get_summary()
