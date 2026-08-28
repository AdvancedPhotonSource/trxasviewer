# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import numpy as np
import pytest
from trxasviewer.core.result import TrXASResult, get_levels, convert_npz_obj


def _make_synthetic_result_dict():
    """Minimal dict that TrXASResult can be constructed from."""
    n_energy = 20
    n_time = 30
    return {
        "target": "normalized-GS",
        "data": np.random.random((n_energy, n_time)).astype(np.float32),
        "diff": np.random.random((n_energy, n_time)).astype(np.float32),
        "t_axis": np.linspace(0, 1e-6, n_time),
        "x_axis": {"value": np.linspace(7000, 8000, n_energy), "label": "Energy", "unit": "keV"},
        "kinetics": {},
        "bunch_mode": 24,
        "delta_t_s": 1e-9,
        "shape": np.array([3, 2, 24]),
        "dset_type": "EXAFS",
        "flist": ["/fake/path/file001"],
        "label": "result_file001",
        "analysis_type": "normalized-GS",
        "analysis_kwargs": {},
        "created": "2026-07-06 00:00:00",
    }


def test_result_constructs_from_dict():
    d = _make_synthetic_result_dict()
    r = TrXASResult(d)
    assert r.dset_type == "EXAFS"
    assert r.diff.shape == (30, 20)  # transposed in __init__


def test_svd_is_lazy():
    d = _make_synthetic_result_dict()
    r = TrXASResult(d)
    assert r._svd is None  # not computed yet


def test_svd_computed_on_access():
    d = _make_synthetic_result_dict()
    r = TrXASResult(d)
    svd = r.svd  # access the property
    assert svd is not None
    assert r._svd is not None  # now cached


def test_svd_cached_second_access():
    d = _make_synthetic_result_dict()
    r = TrXASResult(d)
    svd1 = r.svd
    svd2 = r.svd
    assert svd1 is svd2  # same object, not recomputed


def test_get_levels_symmetric():
    data = np.linspace(-1, 1, 100)
    lo, hi = get_levels(data)
    assert lo < 0 < hi
    assert abs(abs(lo) - abs(hi)) < 0.1  # roughly symmetric
