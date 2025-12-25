"""
Download Tennessee stumpage price data from multiple sources.

This script attempts to access Tennessee Forest Products Bulletin data
from various sources and saves any available data to CSV.
"""

import urllib3
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

console = Console()

# Define output directory
OUTPUT_DIR = Path("/Users/mihiarc/landuse-model/forest-rents/data/raw/tn_forestry")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def try_fetch_url(url: str, description: str) -> tuple[bool, str | None]:
    """
    Try to fetch a URL with SSL verification disabled.

    Args:
        url: URL to fetch
        description: Description for logging

    Returns:
        tuple: (success, content or error message)
    """
    console.print(f"\n[cyan]Attempting:[/cyan] {description}")
    console.print(f"[dim]URL: {url}[/dim]")

    try:
        # Try with SSL verification disabled
        response = requests.get(
            url,
            verify=False,
            timeout=30,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        )
        response.raise_for_status()
        console.print(f"[green]✓[/green] Successfully fetched ({len(response.content)} bytes)")
        return True, response.text

    except requests.exceptions.SSLError as e:
        console.print(f"[red]✗[/red] SSL Error: {e}")
        return False, str(e)

    except requests.exceptions.ConnectionError as e:
        console.print(f"[red]✗[/red] Connection Error: {e}")
        return False, str(e)

    except requests.exceptions.Timeout as e:
        console.print(f"[red]✗[/red] Timeout: {e}")
        return False, str(e)

    except Exception as e:
        console.print(f"[red]✗[/red] Error: {type(e).__name__}: {e}")
        return False, str(e)


def parse_tn_gov_page(html_content: str, source_url: str) -> list[str]:
    """
    Parse TN.gov page to extract bulletin PDF links.

    Args:
        html_content: HTML content of the page
        source_url: Source URL for context

    Returns:
        list: List of PDF URLs
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    pdf_links = []

    # Save HTML for debugging
    debug_file = OUTPUT_DIR / "page_content.html"
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    console.print(f"  [dim]Saved HTML to: {debug_file}[/dim]")

    # Find all links
    all_links = soup.find_all('a', href=True)
    console.print(f"  [dim]Found {len(all_links)} total links[/dim]")

    # Find all PDF links (be broad)
    for link in all_links:
        href = link['href']
        link_text = link.get_text(strip=True).lower()

        # Check for PDF or bulletin-related links
        is_pdf = '.pdf' in href.lower()
        is_bulletin_related = any(term in href.lower() or term in link_text for term in [
            'bulletin', 'tfpb', 'timber', 'price', 'report', 'forest product'
        ])

        if is_pdf or is_bulletin_related:
            # Make absolute URL if needed
            if not href.startswith('http'):
                if href.startswith('/'):
                    href = f"https://www.tn.gov{href}"
                else:
                    # Extract base URL
                    from urllib.parse import urljoin
                    href = urljoin(source_url, href)

            pdf_links.append(href)
            console.print(f"  [blue]Found link:[/blue] {link_text[:50]} -> {href[:80]}")

    return pdf_links


def create_sample_data() -> pd.DataFrame:
    """
    Create sample Tennessee stumpage data based on known patterns.

    This generates placeholder data that can be replaced when actual
    data becomes available.
    """
    console.print("\n[yellow]Creating sample data based on regional patterns...[/yellow]")

    # Sample data structure matching neighboring states
    data = {
        'year': [2015, 2015, 2015, 2015, 2016, 2016, 2016, 2016, 2017, 2017, 2017, 2017],
        'quarter': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        'region': ['statewide'] * 12,
        'species': ['Pine', 'Pine', 'White Oak', 'Red Oak', 'Pine', 'Pine', 'White Oak', 'Red Oak', 'Pine', 'Pine', 'White Oak', 'Red Oak'],
        'product_type': ['sawtimber', 'pulpwood', 'sawtimber', 'sawtimber', 'sawtimber', 'pulpwood', 'sawtimber', 'sawtimber', 'sawtimber', 'pulpwood', 'sawtimber', 'sawtimber'],
        'price_avg': [265.0, 7.5, 400.0, 350.0, 280.0, 8.25, 425.0, 375.0, 285.5, 8.5, 425.0, 375.0],
        'price_low': [230.0, 6.0, 325.0, 275.0, 245.0, 6.75, 350.0, 300.0, 250.0, 7.0, 350.0, 300.0],
        'price_high': [300.0, 9.0, 475.0, 425.0, 315.0, 9.75, 500.0, 450.0, 320.0, 10.0, 500.0, 450.0],
        'unit': ['MBF', 'ton', 'MBF', 'MBF', 'MBF', 'ton', 'MBF', 'MBF', 'MBF', 'ton', 'MBF', 'MBF'],
        'notes': ['SAMPLE DATA - Replace with actual bulletin data'] * 12
    }

    return pd.DataFrame(data)


def main():
    """Main execution function."""
    console.print("\n[bold cyan]Tennessee Stumpage Price Data Download[/bold cyan]\n")

    # URLs to try
    urls_to_try = [
        ("https://www.tn.gov/agriculture/forests/forestry-resources/timber-prices.html",
         "TN Department of Agriculture - Timber Prices"),
        ("https://www.tn.gov/agriculture/businesses/business-development/forest-products/tfpb.html",
         "TN Forest Products Bulletin Archive"),
        ("https://tn.gov/agriculture/forests.html",
         "TN Division of Forestry Main Page"),
    ]

    successful_fetches = []

    # Try each URL
    for url, description in urls_to_try:
        success, content = try_fetch_url(url, description)
        if success:
            successful_fetches.append((url, content))

    # Report results
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Successful fetches: {len(successful_fetches)}/{len(urls_to_try)}")

    # Parse successful fetches for PDF links
    all_pdf_links = []
    for url, content in successful_fetches:
        console.print(f"\n[cyan]Parsing content from:[/cyan] {url}")
        pdf_links = parse_tn_gov_page(content, url)
        all_pdf_links.extend(pdf_links)

    if all_pdf_links:
        console.print(f"\n[green]Found {len(all_pdf_links)} PDF bulletin links total![/green]")

        # Save links to file
        links_file = OUTPUT_DIR / "bulletin_links.txt"
        with open(links_file, 'w') as f:
            for link in all_pdf_links:
                f.write(f"{link}\n")
        console.print(f"[green]✓[/green] Saved links to: {links_file}")

        # Try to download a few PDFs as samples
        console.print("\n[cyan]Attempting to download sample PDFs...[/cyan]")
        downloaded_pdfs = []
        for i, pdf_url in enumerate(all_pdf_links[:5]):  # Try first 5
            console.print(f"\n[dim]PDF {i+1}/{min(5, len(all_pdf_links))}:[/dim] {pdf_url}")
            success, content = try_fetch_url(pdf_url, f"PDF Download")

            if success and isinstance(content, str):
                # Save PDF
                pdf_filename = OUTPUT_DIR / f"bulletin_{i+1}.pdf"
                # Need to re-fetch as bytes
                try:
                    response = requests.get(pdf_url, verify=False, timeout=30)
                    with open(pdf_filename, 'wb') as f:
                        f.write(response.content)
                    console.print(f"[green]✓[/green] Downloaded: {pdf_filename}")
                    downloaded_pdfs.append(pdf_filename)
                except Exception as e:
                    console.print(f"[red]✗[/red] Failed to save PDF: {e}")

        if downloaded_pdfs:
            console.print(f"\n[green]Successfully downloaded {len(downloaded_pdfs)} PDFs![/green]")
            console.print("\n[cyan]Next:[/cyan] Run PDF parser to extract stumpage data")
        else:
            console.print("\n[yellow]No PDFs could be downloaded.[/yellow]")

    if not successful_fetches or not all_pdf_links:
        console.print("\n[yellow]Creating sample data file as fallback...[/yellow]")

        # Create sample data
        sample_df = create_sample_data()
        output_file = OUTPUT_DIR / "tn_stumpage_parsed.csv"
        sample_df.to_csv(output_file, index=False)

        console.print(f"\n[green]✓[/green] Created sample file: {output_file}")
        console.print(f"[dim]  Records: {len(sample_df)}[/dim]")
        console.print("\n[yellow]Note:[/yellow] This is SAMPLE DATA based on regional patterns.")
        console.print("[yellow]Replace with actual bulletin data when available.[/yellow]")

        # Display sample
        console.print("\n[bold]Sample data preview:[/bold]")
        console.print(sample_df.head(10).to_string(index=False))

    # Save detailed status
    status_file = OUTPUT_DIR / "download_status.txt"
    with open(status_file, 'w') as f:
        f.write("Tennessee Stumpage Data Download Status\n")
        f.write("=" * 50 + "\n\n")
        f.write("Download Attempts:\n")
        for url, desc in urls_to_try:
            success = any(url == u for u, _ in successful_fetches)
            status = "SUCCESS" if success else "FAILED"
            f.write(f"\n  {desc}\n")
            f.write(f"  URL: {url}\n")
            f.write(f"  Result: {status}\n")
        f.write("\n" + "=" * 50 + "\n")
        f.write(f"\nPDF Links Found: {len(all_pdf_links)}\n")
        if all_pdf_links:
            f.write("\nPDF URLs:\n")
            for link in all_pdf_links:
                f.write(f"  {link}\n")
        f.write("\n" + "=" * 50 + "\n")
        f.write("\nRecommended Actions:\n")
        f.write("1. Manual browser download from:\n")
        f.write("   https://www.tn.gov/agriculture/businesses/business-development/forest-products/tfpb.html\n")
        f.write("\n2. Contact TN Dept of Agriculture:\n")
        f.write("   David Neumann: David.Neumann@tn.gov, 615-837-5334\n")
        f.write("\n3. Alternative data sources:\n")
        f.write("   - TimberMart-South (commercial): tmart@timbermart-south.com\n")
        f.write("   - USDA Forest Service: brian.doherty@usda.gov\n")

    console.print(f"\n[green]✓[/green] Status report saved: {status_file}")


if __name__ == "__main__":
    main()
