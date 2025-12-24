#!/usr/bin/env python
"""Download stumpage price data from all available sources.

This script downloads stumpage price data from multiple free sources:
- USFS Pacific Northwest Research Station (1958-2023)
- NC State Extension (1976-2024)
- Michigan DNR (quarterly indices)
- Minnesota DNR (annual reports 2007-2021)
- New York DEC (semi-annual 2021-2025)
- Pennsylvania Extension (quarterly reports)
- Vermont FPR (quarterly reports)

Usage:
    uv run python scripts/download_stumpage.py [--source SOURCE]

Options:
    --source SOURCE  Download only from specific source(s). Options:
                     usfs_pnw, nc_state, michigan, minnesota,
                     new_york, pennsylvania, vermont, all
                     Can specify multiple: --source usfs_pnw --source nc_state
"""

import argparse
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from forest_rents.downloaders import (
    USFSPNWDownloader,
    NCStateDownloader,
    TexasAMDownloader,
    ArkansasExtensionDownloader,
    MississippiExtensionDownloader,
    LouisianaForestryDownloader,
    AlabamaForestryDownloader,
    GeorgiaDownloader,
    FloridaIFASDownloader,
    SouthCarolinaForestryDownloader,
    WestVirginiaForestryDownloader,
    MichiganDNRDownloader,
    MinnesotaDNRDownloader,
    WisconsinDNRDownloader,
    NewYorkDECDownloader,
    PennsylvaniaExtensionDownloader,
    VermontFPRDownloader,
    MaineForestServiceDownloader,
)

console = Console()

# Map source names to downloader classes
SOURCES = {
    "usfs_pnw": {
        "class": USFSPNWDownloader,
        "description": "USFS Pacific Northwest (WA, OR, MT, ID, CA, AK)",
        "region": "Pacific Northwest",
    },
    "nc_state": {
        "class": NCStateDownloader,
        "description": "NC State Extension (NC + Southeast)",
        "region": "South",
    },
    "texas_am": {
        "class": TexasAMDownloader,
        "description": "Texas A&M Forest Service (TX)",
        "region": "South",
    },
    "arkansas": {
        "class": ArkansasExtensionDownloader,
        "description": "Arkansas Extension quarterly reports (2005-2025)",
        "region": "South",
    },
    "mississippi": {
        "class": MississippiExtensionDownloader,
        "description": "Mississippi State Extension quarterly reports (2013-2025)",
        "region": "South",
    },
    "louisiana": {
        "class": LouisianaForestryDownloader,
        "description": "Louisiana LDAF quarterly reports (2010-2025)",
        "region": "South",
    },
    "alabama": {
        "class": AlabamaForestryDownloader,
        "description": "Alabama AFC annual reports (2017-2024)",
        "region": "South",
    },
    "georgia": {
        "class": GeorgiaDownloader,
        "description": "Georgia DOR timber values & UGA Extension (2024-2025)",
        "region": "South",
    },
    "florida": {
        "class": FloridaIFASDownloader,
        "description": "UF IFAS Florida Land Steward quarterly reports (2022-2025)",
        "region": "South",
    },
    "south_carolina": {
        "class": SouthCarolinaForestryDownloader,
        "description": "SC Forestry Commission quarterly reports (2020-2025)",
        "region": "South",
    },
    "west_virginia": {
        "class": WestVirginiaForestryDownloader,
        "description": "WV Division of Forestry annual reports (2012-2023)",
        "region": "Appalachian",
    },
    "michigan": {
        "class": MichiganDNRDownloader,
        "description": "Michigan DNR price indices",
        "region": "Lake States",
    },
    "minnesota": {
        "class": MinnesotaDNRDownloader,
        "description": "Minnesota DNR annual reports",
        "region": "Lake States",
    },
    "wisconsin": {
        "class": WisconsinDNRDownloader,
        "description": "Wisconsin DNR FCL/MFL stumpage rates",
        "region": "Lake States",
    },
    "new_york": {
        "class": NewYorkDECDownloader,
        "description": "New York DEC semi-annual reports",
        "region": "Northeast",
    },
    "pennsylvania": {
        "class": PennsylvaniaExtensionDownloader,
        "description": "Penn State Extension quarterly reports",
        "region": "Northeast",
    },
    "vermont": {
        "class": VermontFPRDownloader,
        "description": "Vermont FPR quarterly reports",
        "region": "Northeast",
    },
    "maine": {
        "class": MaineForestServiceDownloader,
        "description": "Maine Forest Service annual reports (2000-2024)",
        "region": "Northeast",
    },
}


def download_source(source_name: str) -> dict:
    """Download data from a single source.

    Args:
        source_name: Name of the source to download

    Returns:
        Dictionary with download results
    """
    if source_name not in SOURCES:
        console.print(f"[red]Unknown source: {source_name}[/red]")
        return {"error": f"Unknown source: {source_name}"}

    source_info = SOURCES[source_name]
    downloader_class = source_info["class"]

    try:
        with downloader_class() as downloader:
            files = downloader.download()

            # Try to parse if the source supports it
            parsed = {}
            if hasattr(downloader, "parse"):
                try:
                    parsed = downloader.parse()
                except Exception as e:
                    console.print(f"[yellow]Parse warning:[/yellow] {e}")

            return {
                "source": source_name,
                "files_downloaded": len(files),
                "files": [str(f) for f in files],
                "parsed_tables": len(parsed) if parsed else 0,
            }

    except Exception as e:
        console.print(f"[red]Error downloading {source_name}:[/red] {e}")
        return {"source": source_name, "error": str(e)}


def print_summary(results: list[dict]) -> None:
    """Print a summary of all downloads."""
    console.print("\n")

    table = Table(title="Stumpage Data Download Summary")
    table.add_column("Source", style="cyan")
    table.add_column("Region", style="blue")
    table.add_column("Files", style="green")
    table.add_column("Parsed", style="yellow")
    table.add_column("Status", style="white")

    for result in results:
        source_name = result.get("source", "unknown")
        source_info = SOURCES.get(source_name, {})

        if "error" in result:
            status = f"[red]Error: {result['error'][:30]}...[/red]"
            files = "-"
            parsed = "-"
        else:
            status = "[green]Success[/green]"
            files = str(result.get("files_downloaded", 0))
            parsed = str(result.get("parsed_tables", 0))

        table.add_row(
            source_name,
            source_info.get("region", "Unknown"),
            files,
            parsed,
            status,
        )

    console.print(table)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download stumpage price data from free sources"
    )
    parser.add_argument(
        "--source",
        action="append",
        choices=list(SOURCES.keys()) + ["all"],
        help="Source(s) to download. Use 'all' for everything.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available sources and exit",
    )

    args = parser.parse_args()

    # List sources if requested
    if args.list:
        console.print(Panel.fit("Available Stumpage Data Sources", style="bold blue"))
        for name, info in SOURCES.items():
            console.print(f"  [cyan]{name:15}[/cyan] {info['description']}")
        return

    # Determine which sources to download
    if args.source is None or "all" in args.source:
        sources = list(SOURCES.keys())
    else:
        sources = args.source

    # Print header
    console.print(Panel.fit(
        "[bold]Stumpage Price Data Downloader[/bold]\n"
        f"Downloading from {len(sources)} source(s)",
        style="blue",
    ))

    # Download each source
    results = []
    for source_name in sources:
        result = download_source(source_name)
        results.append(result)

    # Print summary
    print_summary(results)

    # Save download manifest
    from forest_rents.config import get_settings
    import json
    from datetime import datetime

    settings = get_settings()
    manifest = {
        "download_date": datetime.now().isoformat(),
        "sources": results,
    }
    manifest_path = settings.raw_dir / "download_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    console.print(f"\n[dim]Manifest saved to: {manifest_path}[/dim]")


if __name__ == "__main__":
    main()
