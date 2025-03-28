import time
from functools import lru_cache
from pathlib import Path
import logging
import json
import traceback
from .utilities import get_scan_type, compare_versions
from . import __version__


logger = logging.getLogger(__name__)

CACHE_PATH = ".cache"


class CacheDatabase:
    def __init__(self, folder, min_version="0.2.0"):
        self.folder = Path(folder)
        self.min_version = min_version
        self.cache_path = self.folder / CACHE_PATH
        self.cache_name = self.cache_path / "cache.json"
        self.time_now = time.strftime("%Y-%m-%d %H:%M:%S")
        self.cache_db = self._initialize_cache()

    def _initialize_cache(self):
        self.cache_path.mkdir(parents=True, exist_ok=True)
        cache_template = {
            "version": __version__,
            "datetime": self.time_now,
            "prefix_db": {},
            "scan_type": {},
        }

        if self.cache_name.is_file():
            try:
                temp_db = json.loads(self.cache_name.read_text())
                curr_version = temp_db.get("version", "0.2.0")
                if compare_versions(curr_version, self.min_version):
                    temp_db["version"] = __version__
                    temp_db["datetime"] = self.time_now
                    return temp_db
            except json.JSONDecodeError:
                logger.warning(f"{self.cache_name} is corrupted. Rebuilding cache...")

        return cache_template

    def append_entry(self, entry):

        try:
            if not isinstance(entry, Path):
                entry = Path(entry)

            if not entry.is_file():
                return False

            full_path = str(entry.resolve())
            scan_type = self.cache_db["scan_type"].get(full_path)
            if scan_type in (None, "writting"):
                scan_type = get_scan_type(entry)
                if scan_type in ("exafs", "laserd"):
                    self.cache_db["scan_type"][full_path] = scan_type

            if scan_type in ("exafs", "laserd"):
                self._append_entry(scan_type, entry)

            index = int(entry.name[-5:])
            prefix = entry.name[:-5]
            if prefix not in self.cache_db["prefix_db"]:
                self.cache_db["prefix_db"][prefix] = {"exafs": [], "laserd": []}
            self.cache_db["prefix_db"][prefix][scan_type].append(index)

        except Exception as e:
            logging.error(f"Skipping {entry.name}: Invalid filename format")
            traceback.print_exc()
            return False
        
        return True

    def build(self):
        flag_save = False
        for entry in sorted(self.folder.iterdir(), key=lambda x: x.name):
            self.append_entry(entry)
        if flag_save:
            self.cache_name.write_text(json.dumps(self.cache_db, indent=4))
        return self.cache_db
