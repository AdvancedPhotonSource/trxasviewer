import logging
import time
import traceback
from collections import defaultdict
from multiprocessing import Process
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot

from trxasviewer.core.dataset import TrXASDatasetManager, create_trxas_cache_from_flist

logger = logging.getLogger(__name__)


class _SignalLogHandler(logging.Handler):
    """Forwards log records matching exactly one level to a Qt signal."""

    def __init__(self, signal, level):
        super().__init__()
        self.signal = signal
        self._level = level

    def emit(self, record):
        if record.levelno == self._level:
            self.signal.emit(self.format(record))


class AverageWorker(QObject):
    finished = Signal()
    progress = Signal(int)
    start_task = Signal()
    stop_worker = Signal()
    error = Signal(str)
    warning = Signal(str)
    error_log = Signal(str)

    def __init__(self):
        super().__init__()
        self.dset_manager = TrXASDatasetManager()
        self.flist = None
        self.kwargs = None
        self.results = None
        self.start_task.connect(self.run)

    def set_kwargs(self, flist, **kwargs):
        self.flist = flist
        self.kwargs = kwargs

    @Slot()
    def run(self):
        t0 = time.perf_counter()
        self.dset_manager.update_flist(self.flist)
        _warn_handler = _SignalLogHandler(self.warning, logging.WARNING)
        _err_handler = _SignalLogHandler(self.error_log, logging.ERROR)
        _dset_logger = logging.getLogger("trxasviewer.core.dataset")
        _dset_logger.addHandler(_warn_handler)
        _dset_logger.addHandler(_err_handler)
        try:
            self.results = self.dset_manager.get_energy_vs_time(
                progress=self.progress, **self.kwargs
            )
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Error in AverageWorker.run: {e}")
            self.results = None
            self.error.emit(str(e))
        finally:
            _dset_logger.removeHandler(_warn_handler)
            _dset_logger.removeHandler(_err_handler)
        self.finished.emit()
        t1 = time.perf_counter()
        n = len(self.flist)
        if self.results is not None:
            r = self.results
            shape = r.get("shape", [])
            ch, orb, bunch = (int(x) for x in shape) if len(shape) == 3 else (0, 0, 0)
            dtype = r.get("dset_type", "?")
            names = ", ".join(f.name if hasattr(f, "name") else str(f).split("/")[-1] for f in self.flist)
            logger.info(
                f"{names} | {dtype} | ch={ch} orb={orb} bunch={bunch} | "
                f"{n} file{'s' if n != 1 else ''} in {t1 - t0:.3f}s"
            )
        else:
            logger.info(f"Processed {n} file{'s' if n != 1 else ''} in {t1 - t0:.3f}s | no result")

    def get_results(self):
        return self.results

    def quit(self):
        self.stop_worker.emit()


def _exclude_latest_per_prefix(file_list: list) -> list:
    """Remove the highest-index file for each scan prefix.

    The highest-index file in each series may still be actively written to by
    the acquisition system. Caching it would capture incomplete data. Once the
    next scan file appears (N+1), file N is guaranteed immutable and will be
    cached by the watch-timer logic.
    """
    prefix_max: dict = defaultdict(lambda: (-1, None))
    for f in file_list:
        name = Path(f).name
        try:
            prefix, index = name[:-5], int(name[-5:])
        except (ValueError, IndexError):
            continue
        if index > prefix_max[prefix][0]:
            prefix_max[prefix] = (index, f)
    excluded = {item[1] for item in prefix_max.values() if item[1] is not None}
    filtered = [f for f in file_list if f not in excluded]
    if excluded:
        logger.debug(f"CacheWorker: skipping {len(excluded)} latest file(s) (may be ongoing): "
                     f"{[Path(f).name for f in excluded]}")
    return filtered


class CacheWorker(QThread):
    """Manages multiple processes for cache generation"""

    finished = Signal()

    def __init__(self, file_list, number_of_processes=4, cache_folder=None):
        super().__init__()
        self.file_list = file_list
        self.processes = []
        self.number_of_processes = number_of_processes
        self.cache_folder = cache_folder
        self.is_done = False

    def run(self):
        t0 = time.perf_counter()
        # Never cache the highest-index file per prefix — it may still be growing.
        file_list = _exclude_latest_per_prefix(self.file_list)
        k, m = divmod(len(file_list), self.number_of_processes)
        flist_parts = [
            file_list[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)]
            for i in range(self.number_of_processes)
        ]
        logger.info(
            f"Starting CacheWorker with {self.number_of_processes} processes "
            f"to prepare {len(file_list)} datasets."
        )
        for part in flist_parts:
            process = Process(target=create_trxas_cache_from_flist,
                              args=(part, self.cache_folder))
            process.start()
            self.processes.append(process)
        for process in self.processes:
            process.join()
        self.finished.emit()
        self.is_done = True
        t1 = time.perf_counter()
        logger.info(f"CacheWorker: cached {len(file_list)} files in {t1 - t0:.3f}s")


class SaveWorker(QObject):
    """Saves analysis results to disk in a background thread."""

    finished = Signal()
    progress = Signal(str)   # step description for status bar
    error = Signal(str)      # error message on failure
    start_save = Signal()

    def __init__(self):
        super().__init__()
        self.results = None
        self.kwargs = None
        self.start_save.connect(self.run)

    def setup(self, results: dict, kwargs: dict):
        self.results = results
        self.kwargs = kwargs

    @Slot()
    def run(self):
        try:
            from trxasviewer.core.io import save_results_with_progress
            save_results_with_progress(self.results, self.kwargs, self.progress.emit)
        except Exception as e:
            logger.error(f"Save failed: {e}")
            self.error.emit(str(e))
        finally:
            self.finished.emit()
