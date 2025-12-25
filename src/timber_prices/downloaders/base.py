"""Base downloader class for stumpage price data sources."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn

from timber_prices.config import get_settings

console = Console()


class BaseDownloader(ABC):
    """Abstract base class for data downloaders."""

    def __init__(self):
        self.settings = get_settings()
        self.client = httpx.Client(
            timeout=60.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (timber-prices research project)"
            },
        )

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable name of the data source."""
        pass

    @property
    @abstractmethod
    def source_id(self) -> str:
        """Short identifier for the data source (used in directory names)."""
        pass

    @property
    def download_dir(self) -> Path:
        """Directory for this source's downloaded files."""
        path = self.settings.raw_dir / self.source_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def download_file(self, url: str, filename: str | None = None) -> Path:
        """Download a file from URL to the source's download directory.

        Args:
            url: URL to download from
            filename: Optional filename override. If None, extracted from URL.

        Returns:
            Path to the downloaded file
        """
        if filename is None:
            filename = url.split("/")[-1].split("?")[0]

        dest_path = self.download_dir / filename

        console.print(f"[blue]Downloading:[/blue] {filename}")

        with self.client.stream("GET", url) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length", 0))

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(f"[cyan]{filename}", total=total)

                with open(dest_path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))

        console.print(f"[green]Saved:[/green] {dest_path}")
        return dest_path

    @abstractmethod
    def download(self) -> list[Path]:
        """Download all data files from this source.

        Returns:
            List of paths to downloaded files
        """
        pass

    @abstractmethod
    def parse(self) -> Any:
        """Parse downloaded files into structured data.

        Returns:
            Parsed data (format depends on source)
        """
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
