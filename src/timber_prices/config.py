"""Configuration settings for forest-rents package."""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Base paths
    project_root: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent
    )

    @property
    def data_dir(self) -> Path:
        """Base data directory."""
        return self.project_root / "data"

    @property
    def raw_dir(self) -> Path:
        """Raw downloaded data."""
        path = self.data_dir / "raw"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def processed_dir(self) -> Path:
        """Processed intermediate data."""
        path = self.data_dir / "processed"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def output_dir(self) -> Path:
        """Final output data."""
        path = self.data_dir / "output"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def figures_dir(self) -> Path:
        """Generated figures."""
        path = self.project_root / "figures"
        path.mkdir(parents=True, exist_ok=True)
        return path


# Stumpage data source URLs
STUMPAGE_SOURCES = {
    # Federal sources
    "usfs_pnw": {
        "name": "USFS Pacific Northwest Research Station",
        "description": "Production, prices, employment, and trade 1958-2023",
        "url": "https://research.fs.usda.gov/pnw/products/dataandtools/production-prices-employment-and-trade-northwest-forest-industries-1958",
        "states": ["WA", "OR", "MT", "ID", "AK", "CA"],
        "years": "1958-2023",
        "format": "Excel",
        "cost": "free",
    },
    # Southern states
    "nc_state_extension": {
        "name": "NC State Extension Historic Prices",
        "description": "Historic NC timber stumpage prices 1976-2024",
        "url": "https://content.ces.ncsu.edu/historic-north-carolina-timber-stumpage-prices-1976-2014",
        "data_url": "https://forestry.ces.ncsu.edu/forestry-price-data/",
        "states": ["NC"],
        "years": "1976-2024",
        "format": "PDF/Excel",
        "cost": "free",
    },
    "texas_am": {
        "name": "Texas A&M Forest Service Timber Price Trends",
        "description": "Bimonthly timber price reports",
        "url": "https://tfsweb.tamu.edu/timberpricetrends/",
        "states": ["TX"],
        "years": "1984-present",
        "format": "PDF",
        "cost": "free",
    },
    # Lake States
    "mn_dnr": {
        "name": "Minnesota DNR Stumpage Price Review",
        "description": "Annual public stumpage price reports",
        "url": "https://www.dnr.state.mn.us/forestry/timbersales/stumpage.html",
        "states": ["MN"],
        "years": "2017-present",
        "format": "PDF",
        "cost": "free",
    },
    "mi_dnr": {
        "name": "Michigan DNR Stumpage Price Reports",
        "description": "Quarterly stumpage price reports",
        "url": "https://www2.dnr.state.mi.us/ftp/forestry/tsreports/StumpagePriceReports/",
        "states": ["MI"],
        "years": "varies",
        "format": "PDF",
        "cost": "free",
    },
    # Northeast
    "pa_extension": {
        "name": "Penn State Extension Timber Market Report",
        "description": "Quarterly timber market reports",
        "url": "https://extension.psu.edu/forests-and-wildlife/forestry-business-and-economics/timber-market-report",
        "states": ["PA"],
        "years": "1992-present",
        "format": "PDF",
        "cost": "free",
    },
    "ny_dec": {
        "name": "New York DEC Stumpage Price Reports",
        "description": "Quarterly stumpage reports by region",
        "url": "https://dec.ny.gov/nature/forests-trees/forest-products-utilization/stumpage-price-reports",
        "states": ["NY"],
        "years": "varies",
        "format": "PDF",
        "cost": "free",
    },
    "vt_fpr": {
        "name": "Vermont Stumpage Price Reports",
        "description": "Quarterly stumpage reports",
        "url": "https://fpr.vermont.gov/stumpage-price-reports",
        "states": ["VT"],
        "years": "1981-present",
        "format": "PDF",
        "cost": "free",
    },
    "me_forest_service": {
        "name": "Maine Forest Service Stumpage Reports",
        "description": "Annual stumpage price reports",
        "url": "https://www.maine.gov/dacf/mfs/publications/annual_reports.html",
        "states": ["ME"],
        "years": "1960s-present",
        "format": "PDF",
        "cost": "free",
    },
    # Pacific Northwest state sources
    "wa_dor": {
        "name": "Washington Dept of Revenue Stumpage Values",
        "description": "Stumpage value determination tables",
        "url": "https://dor.wa.gov/taxes-rates/other-taxes/forest-tax/stumpage-value-determination-tables",
        "states": ["WA"],
        "years": "2000-present",
        "format": "PDF/Web",
        "cost": "free",
    },
}


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()
