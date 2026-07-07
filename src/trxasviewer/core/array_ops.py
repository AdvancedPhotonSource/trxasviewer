import warnings
import logging

import numpy as np
from scipy.sparse import coo_array

from .utilities import remove_outlier


logger = logging.getLogger(__name__)


def construct_transform_mat(idx_mask, weights):
    num_ins = idx_mask.size
    num_outs = np.max(idx_mask) + 1  # idx = 0 is reserved for BAD data
    row = np.arange(num_ins)
    mat = coo_array((weights, (row, idx_mask)), shape=(num_ins, num_outs)).tocsr()
    return mat


def pad_last_dim(data, target_size):
    """Pad the last dimension of a 3D array with NaN to reach target_size."""
    if data.shape[2] >= target_size:
        return data
    padded = np.full((*data.shape[:2], target_size), np.nan, dtype=data.dtype)
    padded[:, :, : data.shape[2]] = data
    return padded


def normalize_by_orbitalmean_and_background(xas_data_3d, shape, num_rows):
    num_channel, num_orbital, num_bunch = shape
    shape_4d = (num_rows, num_channel, num_orbital, num_bunch)

    # pad with nan if needed, so that we can reshape to 4d for easier processing;
    xas_data_3d = pad_last_dim(xas_data_3d, num_orbital * num_bunch)

    xas_data_4d = xas_data_3d.reshape(shape_4d)

    # ch0 is background; ch1 and ch2 are signals
    orbital_mean_ch0 = np.nanmean(xas_data_4d[:, 0], axis=1)  # rows x [orbital] x bunch

    # it's (num_rows, total_bunches)
    # Suppress numpy RuntimeWarning: NaN-padded bunches from incomplete acquisitions
    # produce all-NaN slices, which nanmean handles correctly by returning NaN.
    signal_channels = xas_data_3d[:, 1:3]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        norm_data = np.nanmean(signal_channels, axis=(1,))
    cycle_indices = np.arange(norm_data.shape[1]) % num_bunch
    norm_data /= orbital_mean_ch0[:, cycle_indices]
    return norm_data


def preprocess_xas_data(xas_data_3d, shape, num_rows, **outlier_kwargs):
    """
    Preprocess XAS data by removing outliers and normalizing by bunch mean.

    Parameters
    ----------
    xas_data : ndarray
        Raw XAS data array of shape (num_energy, num_channel, num_bunches).
    shape : tuple
        Shape of the XAS data (num_channel, num_orbital, num_bunch).
    num_rows : int
        Number of rows in the dataset.
    outlier_kwargs : dict
        Additional keyword arguments for outlier removal.

    Returns
    -------
    norm_data : ndarray
        Preprocessed XAS data normalized by bunch mean and background.
    """
    xas_data_3d = remove_outlier(xas_data_3d, **outlier_kwargs)
    norm_data = normalize_by_orbitalmean_and_background(xas_data_3d, shape, num_rows)
    return xas_data_3d, norm_data
