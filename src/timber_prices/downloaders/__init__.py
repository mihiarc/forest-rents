"""Data downloaders for stumpage price sources."""

from timber_prices.downloaders.base import BaseDownloader
from timber_prices.downloaders.usfs_pnw import USFSPNWDownloader
from timber_prices.downloaders.nc_state import NCStateDownloader
from timber_prices.downloaders.texas_am import TexasAMDownloader
from timber_prices.downloaders.lake_states import (
    MichiganDNRDownloader,
    MinnesotaDNRDownloader,
    WisconsinDNRDownloader,
    LakeStatesDownloader,
)
from timber_prices.downloaders.northeast import (
    NewYorkDECDownloader,
    PennsylvaniaExtensionDownloader,
    VermontFPRDownloader,
    NortheastDownloader,
)
from timber_prices.downloaders.maine import MaineForestServiceDownloader
from timber_prices.downloaders.arkansas import ArkansasExtensionDownloader
from timber_prices.downloaders.mississippi import MississippiExtensionDownloader
from timber_prices.downloaders.louisiana import LouisianaForestryDownloader
from timber_prices.downloaders.alabama import AlabamaForestryDownloader
from timber_prices.downloaders.georgia import (
    GeorgiaDORDownloader,
    UGAExtensionDownloader,
    GeorgiaDownloader,
)
from timber_prices.downloaders.florida import FloridaIFASDownloader
from timber_prices.downloaders.south_carolina import SouthCarolinaForestryDownloader
from timber_prices.downloaders.west_virginia import WestVirginiaForestryDownloader

__all__ = [
    "BaseDownloader",
    # Pacific Northwest
    "USFSPNWDownloader",
    # South
    "NCStateDownloader",
    "TexasAMDownloader",
    "ArkansasExtensionDownloader",
    "MississippiExtensionDownloader",
    "LouisianaForestryDownloader",
    "AlabamaForestryDownloader",
    "GeorgiaDORDownloader",
    "UGAExtensionDownloader",
    "GeorgiaDownloader",
    "FloridaIFASDownloader",
    "SouthCarolinaForestryDownloader",
    "WestVirginiaForestryDownloader",
    # Lake States
    "MichiganDNRDownloader",
    "MinnesotaDNRDownloader",
    "WisconsinDNRDownloader",
    "LakeStatesDownloader",
    # Northeast
    "NewYorkDECDownloader",
    "PennsylvaniaExtensionDownloader",
    "VermontFPRDownloader",
    "NortheastDownloader",
    "MaineForestServiceDownloader",
]
