import logging
import time
import traceback
from multiprocessing import Process

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
        logger.info(
            f"AverageWorker.run finished in {t1 - t0:.3f} seconds on {len(self.flist)} files"
        )

    def get_results(self):
        return self.results

    def quit(self):
        self.stop_worker.emit()


class CacheWorker(QThread):
    """Manages multiple processes for cache generation"""

    finished = Signal()

    def __init__(self, file_list, number_of_processes=4):
        super().__init__()
        self.file_list = file_list
        self.processes = []
        self.number_of_processes = number_of_processes
        self.is_done = False

    def run(self):
        t0 = time.perf_counter()
        k, m = divmod(len(self.file_list), self.number_of_processes)
        flist_parts = [
            self.file_list[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)]
            for i in range(self.number_of_processes)
        ]
        logger.info(
            f"Starting CacheWorker with {self.number_of_processes} processes "
            f"to prepare {len(self.file_list)} datasets."
        )
        for part in flist_parts:
            process = Process(target=create_trxas_cache_from_flist, args=(part,))
            process.start()
            self.processes.append(process)
        for process in self.processes:
            process.join()
        self.finished.emit()
        self.is_done = True
        t1 = time.perf_counter()
        logger.info(f"CacheWorker.run finished in {t1 - t0:.3f} seconds")
