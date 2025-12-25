"""
Download Tennessee Forest Products Bulletin PDFs from archive.
"""
import re
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Base URLs to try
BASE_URLS = [
    "https://www.tn.gov/agriculture/businesses/business-development/forest-products/tfpb.html",
    "https://www.srs.fs.usda.gov/econ/timberprices/data.php?location=TN"
]

OUTPUT_DIR = Path("/Users/mihiarc/landuse-model/forest-rents/data/raw/tn_forestry")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def fetch_pdf_links(url: str) -> list[dict]:
    """Fetch PDF links from the given URL."""
    console.print(f"[cyan]Fetching page: {url}[/cyan]")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all PDF links
        pdf_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.endswith('.pdf'):
                # Make absolute URL if relative
                if not href.startswith('http'):
                    if href.startswith('/'):
                        base = '/'.join(url.split('/')[:3])
                        href = base + href
                    else:
                        href = url.rsplit('/', 1)[0] + '/' + href

                # Extract text/title
                text = link.get_text(strip=True)

                pdf_links.append({
                    'url': href,
                    'title': text,
                    'filename': href.split('/')[-1]
                })

        console.print(f"[green]Found {len(pdf_links)} PDF links[/green]")
        return pdf_links

    except Exception as e:
        console.print(f"[red]Error fetching {url}: {e}[/red]")
        return []


def download_pdf(url: str, output_path: Path) -> bool:
    """Download a PDF file."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=60, stream=True)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return True

    except Exception as e:
        console.print(f"[red]Error downloading {url}: {e}[/red]")
        return False


def main():
    """Main function to download all bulletins."""
    console.print("[bold cyan]Tennessee Forest Products Bulletin Downloader[/bold cyan]\n")

    all_pdfs = []

    # Try each base URL
    for base_url in BASE_URLS:
        pdfs = fetch_pdf_links(base_url)
        all_pdfs.extend(pdfs)

    if not all_pdfs:
        console.print("[yellow]No PDFs found. Will try known archive patterns...[/yellow]")

        # Try common patterns for Tennessee bulletins (1977-2017, quarterly)
        # Common naming patterns: TFPB_YYYY_QN.pdf, tfpb-yyyy-qn.pdf, etc.
        test_urls = []

        for year in range(1977, 2018):
            for quarter in range(1, 5):
                patterns = [
                    f"https://www.tn.gov/content/dam/tn/agriculture/documents/forestry/TFPB_{year}_Q{quarter}.pdf",
                    f"https://www.tn.gov/content/dam/tn/agriculture/documents/forestry/tfpb_{year}_q{quarter}.pdf",
                    f"https://www.tn.gov/content/dam/tn/agriculture/documents/forestry/TFPB{year}Q{quarter}.pdf",
                    f"https://www.tn.gov/agriculture/forests/forest-products/tfpb/tfpb_{year}_q{quarter}.pdf",
                ]

                for pattern in patterns:
                    test_urls.append({
                        'url': pattern,
                        'title': f'TFPB {year} Q{quarter}',
                        'filename': f'TFPB_{year}_Q{quarter}.pdf'
                    })

        all_pdfs.extend(test_urls[:20])  # Start with first 20 to test

    console.print(f"\n[bold]Attempting to download {len(all_pdfs)} PDFs...[/bold]\n")

    successful = 0
    failed = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:

        for pdf_info in all_pdfs[:10]:  # Start with first 10 for testing
            task = progress.add_task(f"Downloading {pdf_info['filename']}...", total=None)

            output_path = OUTPUT_DIR / pdf_info['filename']

            if download_pdf(pdf_info['url'], output_path):
                successful += 1
                console.print(f"[green]✓[/green] {pdf_info['filename']} ({output_path.stat().st_size / 1024:.1f} KB)")
            else:
                failed += 1

            progress.remove_task(task)

    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Successful: {successful}")
    console.print(f"  Failed: {failed}")
    console.print(f"  Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
