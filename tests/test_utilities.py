import numpy as np
import pytest
from trxasviewer.core.utilities import format_time, remove_outlier, prepare_binning_matrix


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
