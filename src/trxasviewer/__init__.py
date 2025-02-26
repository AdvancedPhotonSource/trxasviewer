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

from .trxasviewer import main_gui

__all__ = ['main_gui']