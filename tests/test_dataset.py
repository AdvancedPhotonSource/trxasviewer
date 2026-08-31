# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import numpy as np
from trxasviewer.core.dataset import TrXASDataset


def test_subtract_groundstate_default_sync_type_is_bunch():
    """The default sync_value=1820 is a bunch index by convention (see
    examples/analyze_trxas.py and the GUI's spinBox_syncbunch_number default),
    so sync_type must default to "bunch" — defaulting to "time" would instead
    misinterpret 1820 as seconds."""
    dset = object.__new__(TrXASDataset)
    dset.xas_data_norm = np.arange(40.0).reshape(1, 40)
    dset.shape = (3, 1, 40)
    dset.delta_t_s = 2.0
    _, _, sync_index = dset.subtract_groundstate(
        sync_value=10, gs_value=3, gs_method="bunch-average"
    )
    assert sync_index == 10
