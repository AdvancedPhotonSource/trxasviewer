import re
from pathlib import Path
import time
from packaging.version import Version
from functools import lru_cache
import numpy as np
from scipy.sparse import coo_array


# @lru_cache(maxsize=1024)
def get_scan_type(fname):
    """
    Determines the scan type from a file's first 10 lines.
    
    - If a line starts with "#S XXX exafs_scan", returns "exafs".
    - If a line starts with "#S XXX rscan laserd", returns "laserd".
    - If the file has less than 12 lines, returns "invalid".
    - Otherwise, or on exception, returns "invalid".
    """
    if Path(fname).is_dir():
        return "directory"

    try:
        # if not is_writing_done(fname):
        #     return "writing"
        pattern_exafs = re.compile(r"^#S\s+\d+\s+exafs_scan")
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
        return scan_type if line_count >= 12 else "invalid"

    except Exception:  # Catch all exceptions
        return "invalid"


def is_writing_done(fname, threshold=60):
    """
    Check if a file has not been modified in the last 'threshold' seconds.
    
    Returns True if the last modification was more than 'threshold' seconds ago.
    """
    file = Path(fname)
    
    if not file.exists():
        return False  # File doesn't exist yet

    last_modified = file.stat().st_mtime  # Get last modified time
    elapsed_time = time.time() - last_modified  # Time since last modification

    return elapsed_time > threshold  # True if more than 'threshold' seconds


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
    num_outs = idx_mask[-1] + 1
    row = np.arange(num_ins)
    mat = coo_array((weights, (row, idx_mask)),
                     shape=(num_ins, num_outs)).tocsr()
    return mat
    

@lru_cache(maxsize=1024)
def prepare_binning_matrix(size, sync_index, method="Linear", lin_num=5, 
                           log_num=None, anchors=None, lengths=None,
                           fraction=0.25):
    assert method in ("Manual", "Linear", "Log")
    begin = (sync_index + lin_num - 1) // lin_num * lin_num - sync_index
    idx_mask = np.arange(begin, begin + size)
    idx_mask = idx_mask // lin_num

    if method == "Log":
        index_start = idx_mask[sync_index]
        start = sync_index
        power = 0
        while True:
            end = min(size, start + int(log_num ** power))
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
        idx_mask -= cutoff  # offset everything to start from 0

    elif method == "Manual":
        start = sync_index + 1
        idx_offset = idx_mask[sync_index] + 1
        for n, length in enumerate(lengths):
            if length == 0:
                break
            end = min(size, start + anchors[n])
            if n == len(anchors) - 1:
                end = size
            temp = np.arange(end - start) // length
            idx_mask[start:end] = temp + idx_offset
            start = end
            idx_offset += temp[-1] + 1
            if start == size:
                break

    counts = np.bincount(idx_mask)
    weights = np.reciprocal(counts[idx_mask], dtype=float)
    mat = construct_transform_mat(idx_mask, weights)
    return idx_mask, mat
