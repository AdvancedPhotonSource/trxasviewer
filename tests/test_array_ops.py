import numpy as np
import pytest
from trxasviewer.core.array_ops import (
    pad_last_dim, construct_transform_mat,
    normalize_by_orbitalmean_and_background, preprocess_xas_data,
)


def test_pad_last_dim_already_correct_size():
    data = np.ones((5, 3, 10))
    result = pad_last_dim(data, 10)
    assert result.shape == (5, 3, 10)
    assert not np.any(np.isnan(result))


def test_pad_last_dim_pads_with_nan():
    data = np.ones((5, 3, 8))
    result = pad_last_dim(data, 10)
    assert result.shape == (5, 3, 10)
    assert np.all(np.isnan(result[:, :, 8:]))
    assert not np.any(np.isnan(result[:, :, :8]))


def test_construct_transform_mat_basic():
    idx_mask = np.array([1, 1, 2, 2, 3])
    weights = np.ones(5)
    mat = construct_transform_mat(idx_mask, weights)
    # mat shape is (num_ins=5, num_outs=max_idx+1=4)
    assert mat.shape[0] == 5  # rows = num inputs
    assert mat.shape[1] == 4  # cols = num outputs (max_idx + 1)


def test_preprocess_no_outlier(synthetic_xas_3d, synthetic_shape):
    xas, norm = preprocess_xas_data(synthetic_xas_3d, synthetic_shape, synthetic_xas_3d.shape[0], outlier_method=None)
    assert xas.shape == synthetic_xas_3d.shape
    assert norm.shape[0] == synthetic_xas_3d.shape[0]


def test_preprocess_with_outlier_mad(synthetic_xas_3d, synthetic_shape):
    # Inject a known outlier in ch0
    data = synthetic_xas_3d.copy()
    data[5, 0, :] = 1e6  # extreme outlier in background channel
    xas, norm = preprocess_xas_data(data, synthetic_shape, data.shape[0],
                                     outlier_method="MedianAbsoluteDeviation", outlier_threshold=5.0)
    assert xas.shape == data.shape
