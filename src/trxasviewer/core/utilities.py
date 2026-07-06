import re
import warnings
from dataclasses import dataclass
from pathlib import Path
import time
from packaging.version import Version
from functools import lru_cache
import numpy as np
from scipy.sparse import coo_array
from scipy.stats import median_abs_deviation
import logging
import json


logger = logging.getLogger(__name__)


# @lru_cache(maxsize=1024)
def get_scan_type(fname):
    """
    Determines the scan type from a file's first 10 lines.

    - If a line starts with "#S XXX exafs_scan", returns "exafs".
    - If a line starts with "#S XXX rscan laserd", returns "laserd".
    - If the file has less than 12 lines, returns "invalid".
    - Otherwise, or on exception, returns "invalid".
    """
    fname = Path(fname)
    if fname.is_dir():
        return "directory"

    if len(str(fname.name)) < 10:
        return "invalid"
    elif is_recently_modified(fname):
        return "writing"

    try:
        pattern_exafs = re.compile(r"^#S\s+\d+\s+exafs_?scan")
        # pattern_laserd = re.compile(r"^#S\s+\d+\s+rscan\s+laserd")
        pattern_laserd = re.compile(r"^#S\s+\d+\s+\S*scan\S*\s+laserd")
        pattern_dutd = re.compile(r"^#S\s+\d+\s+\S*scan\S*\s+dutd")
        line_count = 0
        scan_type = "invalid"  # Move this outside the loop
        matched = False
        with open(fname, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line_count += 1
                if not matched:
                    if pattern_exafs.match(line):
                        scan_type = "exafs"
                        matched = True
                    elif pattern_laserd.match(line) or pattern_dutd.match(line):
                        scan_type = "laserd"
                        matched = True
                if line_count >= 12:  # Stop reading after 12 lines
                    break

        if scan_type == "invalid":
            logger.debug(f"Invalid scan type. {matched=}/{fname=}")
            return "invalid"
        if line_count >= 12:
            return scan_type
        if line_count < 12:
            logger.debug(f"Line count < 12 and writing done. {fname=}")
            return "invalid"
        return "writing"

    except Exception:  # Catch all exceptions
        return "invalid"


def is_recently_modified(fname, threshold=45):
    """
    Check if a file was modified within the last 'threshold' seconds.

    Returns True if the file exists and was created <= 'threshold' seconds ago.
    """
    file = Path(fname)

    if not file.exists():
        return False  # File doesn't exist yet

    try:
        created_time = file.stat().st_ctime  # Creation time on most OSes
        elapsed_time = time.time() - created_time
        return elapsed_time <= threshold
    except Exception:
        logger.debug(f"Error checking file modification time: {fname}")
        return False


def compare_versions(version1, version2):
    """
    Compares two version strings.
    Returns:
        -1 if version1 < version2
         0 if version1 == version2
         1 if version1 > version2
    """
    v1 = Version(str(version1))
    v2 = Version(str(version2))

    if v1 < v2:
        return False
    elif v1 >= v2:
        return True


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
        # index_end = idx_mask[-1]
        # # apply cutoff since log binning only have a few points after sync
        # cutoff = max(0, index_start - (index_end - index_start) * fraction)
        # cutoff = int(cutoff)
        # idx_mask[idx_mask < cutoff] = cutoff
        # idx_mask -= cutoff  # offset everything to start from 0, which means BAD

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
        # apply cutoff to reduce the pre-trigger bunches for better visualization
        # bunch_start = max(0, sync_index - int((end - sync_index) * fraction))
        bunch_start = 0
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
    """
    Remove outliers from XAS data using median absolute deviation.

    Outliers are detected in the background channel (channel 0) and replaced
    with the average of neighboring values in all channels.

    Parameters
    ----------
    xas_data : ndarray
        XAS data array of shape (num_energy, num_channel, num_bunches).
    method : str, default="MedianAbsoluteDeviation"
        Outlier detection method: "MedianAbsoluteDeviation" or "StandardDeviation".
    threshold : float, default=1
        Number of MAD/std units beyond which a point is considered an outlier.

    Returns
    -------
    xas_data : ndarray
        Corrected XAS data with outliers replaced.
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


class NumpyEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for NumPy types.
    Converts np.ndarray to list, and other np types to native Python types.
    """

    def default(self, obj):
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


# ---------------------------------------------------------------------------
# Folder scanning (replaces DataTypeCache)
# ---------------------------------------------------------------------------

@dataclass
class FolderIndex:
    folder: Path
    prefix_db: dict   # {prefix: {"exafs": [idx, ...], "laserd": [idx, ...]}}
    type_db: dict     # {str(filepath): scan_type}

    def get_experiment_types(self) -> list:
        combos = []
        for prefix, types in self.prefix_db.items():
            for scan_type in ("exafs", "laserd"):
                if types.get(scan_type):
                    combos.append(f"{prefix}@{scan_type}")
        return combos

    def get_index_range(self, prefix: str, scan_type: str) -> tuple:
        indices = self.prefix_db.get(prefix, {}).get(scan_type, [])
        return (min(indices), max(indices)) if indices else (0, 1)

    def get_valid_filepaths(self) -> list:
        return [p for p, t in self.type_db.items() if t in ("exafs", "laserd")]

    def get_valid_filepaths_with_condition(self, prefix, scan_type, idx_min, idx_max) -> list:
        valid = set(self.prefix_db.get(prefix, {}).get(scan_type, []))
        return [
            str(self.folder / f"{prefix}{idx:05d}")
            for idx in range(idx_min, idx_max + 1)
            if idx in valid
        ]


def scan_data_folder(folder: Path) -> FolderIndex:
    """Scan folder once and build in-memory type and prefix-index maps."""
    prefix_db: dict = {}
    type_db: dict = {}
    for entry in sorted(folder.iterdir(), key=lambda x: x.name):
        if entry.is_dir():
            continue
        if len(entry.name) < 10:
            continue
        scan_type = get_scan_type(entry)
        type_db[str(entry)] = scan_type
        if scan_type in ("exafs", "laserd"):
            try:
                index = int(entry.name[-5:])
                prefix = entry.name[:-5]
            except ValueError:
                continue
            if prefix not in prefix_db:
                prefix_db[prefix] = {"exafs": [], "laserd": []}
            prefix_db[prefix][scan_type].append(index)
    return FolderIndex(folder=folder, prefix_db=prefix_db, type_db=type_db)
