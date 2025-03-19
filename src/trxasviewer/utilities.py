import re
from pathlib import Path
import time
from packaging.version import Version
from functools import lru_cache


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
        if not is_writing_done(fname):
            return "writing"
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
