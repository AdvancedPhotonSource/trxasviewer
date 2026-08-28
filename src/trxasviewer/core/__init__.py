# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""
trxasviewer.core — headless data-processing library for TrXAS datasets.

All public symbols are Qt-free and importable in scripts and Jupyter notebooks
without a display backend.

Typical usage::

    from trxasviewer.core import TrXASDataset, TrXASDatasetManager, TrXASResult
    from trxasviewer.core import save_results

"""

from .dataset import TrXASDataset, TrXASDatasetManager, create_trxas_dataset
from .result import TrXASResult
from .io import save_results, save_as_hdf5, save_as_origin_format, save_as_json
from .utilities import format_time, prepare_binning_matrix
from .fitting import (
    create_q_matrix,
    calculate_concentrations,
    global_fit_kinetic_model,
)
from .constants import TIME_SCALES

__all__ = [
    # Dataset loading
    "TrXASDataset",
    "TrXASDatasetManager",
    "create_trxas_dataset",
    # Results
    "TrXASResult",
    # Saving
    "save_results",
    "save_as_hdf5",
    "save_as_origin_format",
    "save_as_json",
    # Utilities
    "format_time",
    "prepare_binning_matrix",
    # Fitting
    "create_q_matrix",
    "calculate_concentrations",
    "global_fit_kinetic_model",
    # Constants
    "TIME_SCALES",
]
