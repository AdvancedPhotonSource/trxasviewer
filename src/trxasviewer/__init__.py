"""Top-level package for TrXASViewer."""

from importlib.metadata import version, PackageNotFoundError

# Metadata
__author__ = "Miaoqi Chu"
__email__ = "mqichu@anl.gov"

# Version handling
try:
    __version__ = version("trxasviewer")
except PackageNotFoundError:
    __version__ = "0.1.0"  # Fallback if package is not installed

from .trxasviewer_gui import main_gui
from .trxas_dataset import TrXASDataset

__all__ = ["main_gui", "TrXASDataset"]
