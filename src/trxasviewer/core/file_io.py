import ctypes
import ctypes.util
import os
import re
import struct
import sys
import time
import logging
from dataclasses import dataclass
from pathlib import Path


logger = logging.getLogger(__name__)


def _classify_scan_header(line: str) -> str:
    """Pure: classify a #S header line."""
    if re.match(r"^#S\s+\d+\s+exafs_?scan", line):
        return "exafs"
    if re.match(r"^#S\s+\d+\s+\S*scan\S*\s+laserd", line) or \
       re.match(r"^#S\s+\d+\s+\S*scan\S*\s+dutd", line):
        return "laserd"
    return "invalid"


# @lru_cache(maxsize=1024)
def get_scan_type(fname):
    """
    Determines the scan type from a file's first 12 lines.

    Returns "exafs", "laserd", "directory", or "invalid".
    Returns "invalid" if the file has fewer than 12 lines (header not yet complete).
    """
    fname = Path(fname)
    if fname.is_dir():
        return "directory"
    if len(str(fname.name)) < 10:
        return "invalid"

    try:
        line_count = 0
        scan_type = "invalid"
        matched = False
        with open(fname, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line_count += 1
                if not matched:
                    classified = _classify_scan_header(line)
                    if classified != "invalid":
                        scan_type = classified
                        matched = True
                if line_count >= 12:
                    break

        if line_count < 12 or not matched:
            return "invalid"
        return scan_type

    except Exception:
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

    def add_entry(self, entry: Path, scan_type: str) -> None:
        """Register a newly discovered file incrementally (no full rescan)."""
        self.type_db[str(entry)] = scan_type
        if scan_type not in ("exafs", "laserd"):
            return
        try:
            index = int(entry.name[-5:])
            prefix = entry.name[:-5]
        except ValueError:
            return
        if prefix not in self.prefix_db:
            self.prefix_db[prefix] = {"exafs": [], "laserd": []}
        if index not in self.prefix_db[prefix][scan_type]:
            self.prefix_db[prefix][scan_type].append(index)


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


# ---------------------------------------------------------------------------
# NFS-safe stat helpers (bypass kernel attribute cache via AT_STATX_FORCE_SYNC)
# ---------------------------------------------------------------------------

_AT_FDCWD = -100
_AT_STATX_FORCE_SYNC = 0x2000
_STATX_SIZE = 0x00000200
_STATX_SIZE_OFFSET = 40          # byte offset of stx_size in struct statx

# Module-level cache: libc handle and reusable buffer (avoids per-call overhead)
_libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True) if sys.platform == "linux" else None
_statx_buf = (ctypes.c_char * 256)()


def _statx_get_size(path: str) -> int:
    """Return file size via statx(AT_STATX_FORCE_SYNC), bypassing the NFS
    attribute cache. Falls back to os.stat() on non-Linux or error."""
    if _libc is None:
        return os.stat(path).st_size
    try:
        ret = _libc.statx(
            ctypes.c_int(_AT_FDCWD),
            ctypes.c_char_p(path.encode()),
            ctypes.c_int(_AT_STATX_FORCE_SYNC),
            ctypes.c_uint(_STATX_SIZE),
            _statx_buf,
        )
        if ret != 0:
            errno = ctypes.get_errno()
            raise OSError(errno, os.strerror(errno), path)
        return struct.unpack_from("<Q", _statx_buf, _STATX_SIZE_OFFSET)[0]
    except Exception:
        return os.stat(path).st_size


def _statx_sync_dir(folder: Path) -> None:
    """Force the NFS client to fetch fresh directory attributes via
    statx(AT_STATX_FORCE_SYNC). If the directory mtime changed on the server,
    the kernel invalidates the dentry cache so iterdir() returns fresh entries.
    Falls back silently on non-Linux or error."""
    if _libc is None:
        return
    try:
        _libc.statx(
            ctypes.c_int(_AT_FDCWD),
            ctypes.c_char_p(str(folder).encode()),
            ctypes.c_int(_AT_STATX_FORCE_SYNC),
            ctypes.c_uint(0),
            _statx_buf,
        )
    except Exception:
        pass
