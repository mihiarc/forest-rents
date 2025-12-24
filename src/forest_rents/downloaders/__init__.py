"""Data downloaders for stumpage price sources."""

from forest_rents.downloaders.base import BaseDownloader
from forest_rents.downloaders.usfs_pnw import USFSPNWDownloader
from forest_rents.downloaders.nc_state import NCStateDownloader
from forest_rents.downloaders.texas_am import TexasAMDownloader
from forest_rents.downloaders.lake_states import (
    MichiganDNRDownloader,
    MinnesotaDNRDownloader,
    WisconsinDNRDownloader,
    LakeStatesDownloader,
)
from forest_rents.downloaders.northeast import (
    NewYorkDECDownloader,
    PennsylvaniaExtensionDownloader,
    VermontFPRDownloader,
    NortheastDownloader,
)
from forest_rents.downloaders.maine import MaineForestServiceDownloader
from forest_rents.downloaders.arkansas import ArkansasExtensionDownloader
from forest_rents.downloaders.mississippi import MississippiExtensionDownloader
from forest_rents.downloaders.louisiana import LouisianaForestryDownloader
from forest_rents.downloaders.alabama import AlabamaForestryDownloader
from forest_rents.downloaders.georgia import (
    GeorgiaDORDownloader,
    UGAExtensionDownloader,
    GeorgiaDownloader,
)
from forest_rents.downloaders.florida import FloridaIFASDownloader
from forest_rents.downloaders.south_carolina import SouthCarolinaForestryDownloader
from forest_rents.downloaders.west_virginia import WestVirginiaForestryDownloader

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
