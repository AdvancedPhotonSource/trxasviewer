# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import numpy as np
import pytest

EXAFS_S_LINE = "#S 1 exafs_scan Energy 7000 8000 200\n"
LASERD_S_LINE = "#S 2 rscan laserd 0 100 100\n"
DUTD_S_LINE = "#S 3 tscan dutd 0 100 100\n"
INVALID_S_LINE = "# This is a comment line\n"

@pytest.fixture
def synthetic_xas_3d():
    """Shape: (num_rows=10, num_channel=3, total_bunches=48)"""
    rng = np.random.default_rng(42)
    return rng.random((10, 3, 48)).astype(np.float32)

@pytest.fixture
def synthetic_shape():
    return np.array([3, 2, 24])  # 3 channels, 2 orbitals, 24 bunches
