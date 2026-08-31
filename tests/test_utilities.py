# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import numpy as np
import pytest
from trxasviewer.core.utilities import (
    format_time,
    remove_outlier,
    prepare_binning_matrix,
    compute_sync_max_bounds,
    bunch_index_to_sync_time_us,
    sync_time_us_to_bunch_index,
)


def test_format_time_nanoseconds():
    result = format_time(1e-9)
    assert "ns" in result or "1" in result


def test_format_time_microseconds():
    result = format_time(1e-6)
    assert "µs" in result or "us" in result or "1" in result


def test_format_time_milliseconds():
    result = format_time(1e-3)
    assert "ms" in result or "1" in result


def test_format_time_seconds():
    result = format_time(1.5)
    assert "1" in result or "s" in result


def test_format_time_as_string_false():
    value, unit, scale = format_time(1e-6, as_string=False)
    assert isinstance(value, float)
    assert isinstance(unit, str)
    assert isinstance(scale, float)


def test_remove_outlier_mad_removes_spike():
    rng = np.random.default_rng(0)
    data = rng.normal(0, 1, (20, 3, 48)).astype(np.float32)
    # Spike a single bunch in row 10's background channel so MAD detects it
    data[10, 0, 5] = 1e6
    result = remove_outlier(data, "MedianAbsoluteDeviation", 5.0)
    # The spiked bunch should be replaced with neighbor average (not 1e6)
    assert abs(result[10, 0, 5]) < 1e5


def test_prepare_binning_linear_shape():
    size = 200
    sync_index = 50
    mat, nobin_idx = prepare_binning_matrix(size, sync_index, method="Linear", lin_num=5)
    assert mat is not None


def test_compute_sync_max_bounds_matches_total_bunch_count():
    # 1296-bunch mode, single orbital: total_bunches == num_bunches, matching the
    # "index 99999 is out of bounds for axis 0 with size 1296" GUI bug report.
    shape = (3, 1, 1296)
    delta_t_s = 1 / (352055282.0 / 1296) / 1296
    max_bunch_index, max_time_us = compute_sync_max_bounds(shape, delta_t_s)
    assert max_bunch_index == 1295
    assert max_time_us == pytest.approx(1295 * delta_t_s * 1e6)


def test_compute_sync_max_bounds_scales_with_orbitals():
    shape = (3, 4, 1296)
    delta_t_s = 1 / (352055282.0 / 1296) / 1296
    max_bunch_index, _ = compute_sync_max_bounds(shape, delta_t_s)
    assert max_bunch_index == 4 * 1296 - 1


def test_bunch_index_to_sync_time_us_roundtrip():
    delta_t_s = 1 / (352055282.0 / 1296) / 1296
    bunch_index = 1820
    time_us = bunch_index_to_sync_time_us(bunch_index, delta_t_s)
    assert time_us == pytest.approx(bunch_index * delta_t_s * 1e6)
    assert sync_time_us_to_bunch_index(time_us, delta_t_s) == bunch_index


def test_sync_time_us_to_bunch_index_matches_dataset_truncation():
    # Must match TrXASDataset.subtract_groundstate's int(sync_value_s / delta_t_s)
    # truncation, so the GUI's bunch display matches the index actually used.
    delta_t_s = 1 / (352055282.0 / 1296) / 1296
    time_us = 5171.999  # deliberately not an exact multiple of delta_t_s
    sync_value_s = time_us * 1e-6
    expected = int(sync_value_s / delta_t_s)
    assert sync_time_us_to_bunch_index(time_us, delta_t_s) == expected
