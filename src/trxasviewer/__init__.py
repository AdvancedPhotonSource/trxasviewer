"""Top-level package for TrXASViewer."""

from importlib.metadata import version, PackageNotFoundError

__author__ = "Miaoqi Chu"
__email__ = "mqichu@anl.gov"

try:
    __version__ = version("trxasviewer")
except PackageNotFoundError:
    __version__ = "0.1.0"

# Core data class is always safe to expose — no Qt dependency
from .core.dataset import TrXASDataset

__all__ = ["TrXASDataset", "__version__", "main_gui", "main_modeling_gui"]


def __getattr__(name: str):
    """Lazy-load GUI entry points so bare ``import trxasviewer`` does not pull Qt."""
    if name == "main_gui":
        from .gui.view.viewer_view import main_gui
        return main_gui
    if name == "main_modeling_gui":
        from .modeling_gui.trxas_modeling import main_modeling_gui
        return main_modeling_gui
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
