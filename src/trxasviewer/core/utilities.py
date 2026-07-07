import json
from functools import lru_cache

import numpy as np
from scipy.sparse import coo_array
from scipy.stats import median_abs_deviation
import logging


logger = logging.getLogger(__name__)


def construct_transform_mat(idx_mask, weights):
    num_ins = idx_mask.size
    num_outs = np.max(idx_mask) + 1  # idx = 0 is reserved for BAD data
    row = np.arange(num_ins)
    mat = coo_array((weights, (row, idx_mask)), shape=(num_ins, num_outs)).tocsr()
    return mat


@lru_cache(maxsize=1024)
def prepare_binning_matrix(
    size,
    sync_index,
    method="Linear",
    lin_num=5,
    log_num=None,
    anchors=None,
    lengths=None,
    fraction=0.25,
):
    """Build a binning index map that converts raw bunch indices to time bins.

    Args:
        size: Total number of bunch indices in the data.
        sync_index: Bunch index at which the laser fires (0-based).
        method: Binning strategy. One of ``"Linear"``, ``"Log"``, or ``"Manual"``.
        lin_num: Bunches per bin for linear binning.
        log_num: Logarithmic base for log binning (e.g. 1.2 means each bin is
            1.2× wider than the previous).
        anchors: Tuple of 5 anchor bunch indices for manual binning levels.
        lengths: Tuple of 5 bin counts per manual level (−1 disables that level
            and beyond; 0 = no binning of laser-adjacent bunches).
        fraction: Fraction of the post-laser range used for log binning.

    Returns:
        Tuple of (idx_mask, nobin_laserd_idx) where idx_mask is a 1-D integer array
        mapping each bunch index to a bin (0 = excluded), and nobin_laserd_idx is a
        list of bunch indices in the un-binned single-bunch region.
    """
    assert method in ("Manual", "Linear", "Log")
    begin = (sync_index + lin_num - 1) // lin_num * lin_num - sync_index
    idx_mask = np.arange(begin, begin + size)
    idx_mask = idx_mask // lin_num + 1  # idx = 0 is reserved for BAD data
    nobin_laserd_idx = []

    if method == "Log":
        index_start = idx_mask[sync_index]
        start = sync_index
        power = 0
        while True:
            end = min(size, start + int(log_num**power))
            idx_mask[start:end] = power + index_start
            power += 1
            start = end  # Removed redundant else statement
            if start == size:
                break
    elif method == "Manual":
        start = sync_index
        idx_offset = idx_mask[sync_index]
        for n, length in enumerate(lengths):
            flag_append_nobin = False
            if length == -1:
                idx_mask[start:] = 0  # mark the rest as BAD
                break
            elif length == 0:  # length = 0 means do not bin lasered
                flag_append_nobin = True
                length = 1
            end = min(size, sync_index + anchors[n])
            if n == len(anchors) - 1:  # last level
                end = size
            temp = np.arange(end - start) // length + idx_offset
            idx_mask[start:end] = temp
            if flag_append_nobin:
                nobin_laserd_idx.extend(temp.tolist())
            start = end
            idx_offset = temp[-1] + 1  # number of unique values in temp
            if start == size:
                break
        bunch_start = 0  # pre-trigger bunches always start from 0
        cutoff = idx_mask[bunch_start]
        idx_mask[idx_mask < cutoff] = cutoff
        idx_mask -= cutoff  # offset everything to start from 0, which means BAD
        nobin_laserd_idx = [x - cutoff for x in nobin_laserd_idx]

    counts = np.bincount(idx_mask)
    weights = np.reciprocal(counts[idx_mask], dtype=float)
    mat = construct_transform_mat(idx_mask, weights)
    nobin_laserd_idx = [x - 1 for x in nobin_laserd_idx]  # convert to 0-based
    return mat, nobin_laserd_idx


def format_time(input_time, as_string=True):
    """
    Convert time in seconds to a human-readable string or its components.

    If as_string is True, it returns a formatted string.
    If as_string is False, it returns the value, unit, and the numeric scale.

    Args:
        input_time (float or None): Time in seconds (can be negative).
        as_string (bool): If True, return a formatted string. If False,
                          return a tuple of (value, unit, scale).

    Returns:
        str or tuple: Formatted time string (e.g., "130.000 ns"),
                      a tuple (value, unit, scale) (e.g., (130.0, 'ns', 1e-9)),
                      or "invalid" if input is None.
    """
    # Handle invalid input as described in the original docstring
    if input_time is None:
        # For the tuple return case, returning (None, None, None) is consistent
        return "invalid" if as_string else (None, None, None)

    # Handle zero case for a clean output
    if input_time == 0:
        if as_string:
            return "0.000 s"
        else:
            return 0.0, "s", 1.0

    units = [(1e-12, "ps"), (1e-9, "ns"), (1e-6, "µs"), (1e-3, "ms"), (1, "s")]
    abs_time = abs(input_time)

    for scale, unit in units:
        # Find the first unit where the absolute time is less than 1000 of that unit
        if abs_time < scale * 1000:
            value = input_time / scale
            if as_string:
                return f"{value:.3f} {unit}"
            else:
                # Return the value, unit, and the requested scale
                return value, unit, scale

    # Default to seconds for large values
    scale = 1.0
    if as_string:
        return f"{input_time:.3f} s"
    else:
        # Return the value, unit, and the requested scale
        return input_time, "s", scale


def remove_outlier(xas_data_3d_input, outlier_method="MedianAbsoluteDeviation", outlier_threshold=1):
    """Remove outlier shots from the background channel (ch0) of XAS data.

    Identifies rows where the background signal deviates beyond the threshold and
    replaces them with NaN across all channels.

    Args:
        xas_data_3d_input: Shape ``(num_rows, num_channel, total_bunches)`` float32 array.
        outlier_method: Detection algorithm. One of ``"MedianAbsoluteDeviation"`` or
            ``"StandardDeviation"``.
        outlier_threshold: Rejection threshold in units of MAD or σ. Default 1.

    Returns:
        Copy of xas_data_3d_input with outlier rows set to NaN.
    """
    if outlier_method is None:
        return xas_data_3d_input

    xas_data_3d = np.copy(xas_data_3d_input)

    background = xas_data_3d[:, 0, :]  # ch0 is background, now has shape (num_rows, num_bunches)
    # Detect outliers using background channel (channel 0)
    if outlier_method == "MedianAbsoluteDeviation":
        mad_threshold = median_abs_deviation(background, axis=1, keepdims=True)
        outlier_mask = (
            np.abs(background - np.median(background, axis=1, keepdims=True))
            > outlier_threshold * mad_threshold
        )
    elif outlier_method == "StandardDeviation":
        std_threshold = np.std(background, axis=1, keepdims=True)
        outlier_mask = (
            np.abs(background - np.median(background, axis=1, keepdims=True))
            > outlier_threshold * std_threshold
        )
    else:
        raise ValueError(f"Unsupported outlier detection method: {outlier_method}")

    # Replace outliers with average of neighbors in all channels
    # usually only one bunch is missing, so we can use the average of neighbors
    for channel in range(xas_data_3d.shape[1]):    # go through each channel
        neighbor_up = np.roll(xas_data_3d[:, channel, :], 1, axis=1)
        neighbor_dn = np.roll(xas_data_3d[:, channel, :], -1, axis=1)
        xas_data_3d[:, channel, :][outlier_mask] = 0.5 * (
            neighbor_up[outlier_mask] + neighbor_dn[outlier_mask]
        )

    return xas_data_3d


class NumpyEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for NumPy types.
    Converts np.ndarray to list, and other np types to native Python types.
    """

    def default(self, obj):
        """Serialize NumPy scalar and array types to JSON-compatible Python types."""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            # Convert NaN to None (which becomes null in JSON)
            return float(obj) if not np.isnan(obj) else None
        if isinstance(obj, np.bool_):
            return bool(obj)
        # Let the base class default method raise the TypeError
        return super(NumpyEncoder, self).default(obj)
