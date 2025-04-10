import time
from pathlib import Path
import logging
import json
from .utilities import get_scan_type, compare_versions
from . import __version__
import atexit


logger = logging.getLogger(__name__)
CACHE_PATH = ".cache"


def is_valid_entry(entry: Path) -> bool:
    """Return True if the file should be considered in the cache."""
    if not entry.is_file():
        return False
    if entry.name.startswith("."):
        return False
    if entry.name == ".cache":
        return False
    return True


class DataTypeCache:
    def __init__(
        self, folder, min_version="0.3.0", flag_savecache=True, reset_cache=False
    ):
        self.folder = Path(folder)
        self.min_version = min_version
        self.cache_path = self.folder / CACHE_PATH
        self.cache_name = self.cache_path / "cache.json"
        self.time_now = time.strftime("%Y-%m-%d %H:%M:%S")
        self.db = self.initialize_cache(reset_cache)
        self.build_cache()
        if flag_savecache:
            atexit.register(self.save_dtype_cache)

    def initialize_cache(self, reset_cache=False):
        # either from file or create a empty template
        self.cache_path.mkdir(parents=True, exist_ok=True)
        db = {
            "version": __version__,
            "datetime": self.time_now,
            "prefix_db": {},
            "scan_type": {},
        }
        if reset_cache:
            logger.warning("Cache reset requested. Rebuilding dtype cache...")
            return db

        if self.cache_name.is_file() and not reset_cache:
            try:
                prev_db = json.loads(self.cache_name.read_text())
                curr_version = prev_db.get("version", "0.2.0")
                if compare_versions(curr_version, self.min_version):
                    prev_db["version"] = __version__
                    prev_db["datetime"] = self.time_now
                    db = prev_db
            except Exception:
                logger.warning(
                    f"{self.cache_name} is corrupted. Rebuilding dtype cache..."
                )

        return db

    def build_cache(self):
        for entry in sorted(self.folder.iterdir(), key=lambda x: x.name):
            if is_valid_entry(entry):
                self.append_record(entry)

    def append_record(self, entry):
        if not isinstance(entry, Path):
            entry = Path(entry)

        full_path = str(entry.resolve())
        scan_type = self.db["scan_type"].get(full_path, None)
        # directories and valid files cached won't be re-computed
        if scan_type in (None, "writing"):
            scan_type = get_scan_type(entry)
            self.db["scan_type"][full_path] = scan_type
            if scan_type in ("exafs", "laserd"):
                index = int(entry.name[-5:])
                prefix = entry.name[:-5]
                if prefix not in self.db["prefix_db"]:
                    self.db["prefix_db"][prefix] = {"exafs": [], "laserd": []}
                self.db["prefix_db"][prefix][scan_type].append(index)
        return scan_type

    def get_record(self, entry):
        return self.append_record(entry)

    def save_dtype_cache(self):
        with open(self.cache_name, "w") as f:
            json.dump(self.db, f, indent=4)

    def get_file_indexes(self, current_prefix, scan_type):
        file_indexes = self.db["prefix_db"][current_prefix][scan_type]
        return file_indexes

    def get_index_range(self, current_prefix, scan_type):
        file_indexes = self.get_file_indexes(current_prefix, scan_type)
        if len(file_indexes) == 0:
            return (0, 1)
        else:
            return min(file_indexes), max(file_indexes)

    def get_experiment_types(self):
        combos = []
        prefix_db = self.db["prefix_db"]
        for key in prefix_db.keys():
            for scan_type in ("exafs", "laserd"):
                if len(prefix_db[key][scan_type]) > 0:
                    combos.append(f"{key}@{scan_type}")
        return combos

    def get_valid_filepaths(self):
        ans = [k for k, v in self.db["scan_type"].items() if v in ("exafs", "laserd")]
        return ans

    def get_valid_filepaths_with_condition(self, prefix, scan_type, idx_min, idx_max):
        file_paths = []
        file_indexes = self.get_file_indexes(prefix, scan_type)
        for idx in range(idx_min, idx_max + 1):
            if idx in file_indexes:
                full_path = Path(self.folder) / f"{prefix}{idx:05d}"
                file_paths.append(str(full_path))
        return file_paths

    @staticmethod
    def get_scan_type(filepath):
        return get_scan_type(filepath)
