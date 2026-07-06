import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QThread

from trxasviewer.core.io import save_results
from trxasviewer.core.dtype_cache import DataTypeCache
from trxasviewer.gui.control.workers import AverageWorker, CacheWorker
from trxasviewer.gui.model.viewer_model import ViewerModel

if TYPE_CHECKING:
    from trxasviewer.gui.view.viewer_view import ViewerView

logger = logging.getLogger(__name__)


class ViewerController(QObject):
    def __init__(self, model: ViewerModel, view: "ViewerView", parent=None):
        super().__init__(parent)
        self._model = model
        self._view = view

        self._thread = QThread()
        self._avg_worker = AverageWorker()
        self._avg_worker.moveToThread(self._thread)
        self._thread.start()

        self._connect()

    def _connect(self):
        # View → Controller (user actions)
        self._view.folder_selected.connect(self.on_folder_selected)
        self._view.files_selected.connect(self.on_files_selected)
        self._view.replot_requested.connect(self.on_replot)
        self._view.save_requested.connect(self.on_save)

        # Worker → Controller / Model
        self._avg_worker.finished.connect(self._on_worker_finished)
        self._avg_worker.progress.connect(self._model.loading_progress.emit)
        self._avg_worker.error.connect(
            lambda msg: self._model.error_occurred.emit("Processing Error", msg)
        )
        self._avg_worker.warning.connect(self._on_worker_warning)
        self._avg_worker.error_log.connect(
            lambda msg: self._model.error_occurred.emit("Error", msg)
        )

        # Model → View (data updates)
        self._model.result_ready.connect(self._view.update_image)
        self._model.result_ready.connect(self._view.update_kinetics)
        self._model.result_cleared.connect(self._view.clear_display)
        self._model.loading_started.connect(lambda: self._view.set_loading(True))
        self._model.loading_finished.connect(lambda: self._view.set_loading(False))
        self._model.loading_progress.connect(self._view.update_progress_bar)
        self._model.error_occurred.connect(self._view.show_error)
        self._model.warning_occurred.connect(self._view.show_warning)
        self._model.status_message.connect(self._view.update_status)

    # --- View event handlers ---

    def on_folder_selected(self, path: Path):
        self._model.dtype_db = DataTypeCache(str(path), reset_cache=self._model.reset_cache)
        self._model.reset_cache = False
        combos = self._model.dtype_db.get_experiment_types()
        self._view.update_folder_ui(path, combos, self._model.dtype_db)
        self._model.set_folder(path)
        self._build_cache()

    def on_files_selected(self, flist: list):
        if not flist:
            self._model.clear_result()
            return
        self._model.set_file_list(flist)
        self._start_average()

    def on_replot(self):
        if self._model.file_list:
            self._start_average()

    def on_save(self, kwargs: dict):
        if self._model.result is not None:
            save_results(self._model.result, **kwargs)

    # --- Internal ---

    def _start_average(self):
        kwargs = {
            "channel": self._view.get_channel(),
            "target": self._view.get_target(),
            "preprocessing_kwargs": self._view.get_preprocessing_kwargs(),
            "norm_kwargs": self._view.get_normalization_subgs_kwargs(),
            "binning_kwargs": self._view.get_binning_kwargs(),
            "kinetics_kwargs": self._view.get_kinetics_kwargs(),
            "use_cache": self._model.use_cache,
        }
        self._model.loading_started.emit()
        self._avg_worker.set_kwargs(self._model.file_list, **kwargs)
        self._avg_worker.start_task.emit()

    def _build_cache(self):
        num_workers = max(2, os.cpu_count() // 2)
        file_paths = self._model.dtype_db.get_valid_filepaths()
        if file_paths:
            num_workers = min(num_workers, len(file_paths))
            cache_worker = CacheWorker(file_paths, num_workers)
            cache_worker.start()

    def _on_worker_finished(self):
        results = self._avg_worker.get_results()
        self._model.loading_finished.emit()
        if results is not None:
            self._model.set_result(results)
        else:
            self._model.clear_result()

    def _on_worker_warning(self, msg: str):
        self._model.warning_occurred.emit("Warning", msg)

    def shutdown(self):
        self._avg_worker.quit()
        self._thread.quit()
        self._thread.wait()
