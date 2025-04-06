import re
from pathlib import Path
import time
from packaging.version import Version
from functools import lru_cache
import numpy as np
from scipy.sparse import coo_array
import logging


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
        pattern_laserd = re.compile(r"^#S\s+\d+\s+rscan\s+laserd")
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
                    elif pattern_laserd.match(line):
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
        index_end = idx_mask[-1]
        # apply cutoff since log binning only have a few points after sync
        cutoff = max(0, index_start - (index_end - index_start) * fraction)
        cutoff = int(cutoff)
        idx_mask[idx_mask < cutoff] = cutoff
        idx_mask -= cutoff  # offset everything to start from 0, which means BAD

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
            end = min(size, start + anchors[n])
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
        bunch_start = max(0, sync_index - int((end - sync_index) * fraction))
        cutoff = idx_mask[bunch_start]
        idx_mask[idx_mask < cutoff] = cutoff
        idx_mask -= cutoff  # offset everything to start from 0, which means BAD
        nobin_laserd_idx = [x - cutoff for x in nobin_laserd_idx]

    counts = np.bincount(idx_mask)
    weights = np.reciprocal(counts[idx_mask], dtype=float)
    mat = construct_transform_mat(idx_mask, weights)
    nobin_laserd_idx = [x - 1 for x in nobin_laserd_idx]  # convert to 0-based
    return mat, nobin_laserd_idx


def format_time(input_time):
    """
    Convert time in seconds to a human-readable string with appropriate time units,
    preserving the sign. Returns 'invalid' if input is None or zero.

    Args:
        input_time (float): Time in seconds (can be negative).

    Returns:
        str: Formatted time string like "130 ns", "-5 µs", or "invalid".
    """
    units = [(1e-12, "ps"), (1e-9, "ns"), (1e-6, "µs"), (1e-3, "ms"), (1, "s")]

    abs_time = abs(input_time)

    for scale, unit in units:
        if abs_time < scale * 1000:
            value = input_time / scale
            return f"{value:.0f} {unit}"

    return f"{input_time:.3f} s"
