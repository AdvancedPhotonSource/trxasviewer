# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QThread, QTimer

from trxasviewer.core.file_io import (
    scan_data_folder, get_scan_type, _statx_get_size, _statx_sync_dir,
)
from trxasviewer.gui.control.workers import AverageWorker, CacheWorker, SaveWorker
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

        self._save_thread = QThread()
        self._save_worker = SaveWorker()
        self._save_worker.moveToThread(self._save_thread)
        self._save_thread.start()

        self._folder_index = None
        self._file_sizes: dict = {}
        self._is_loading: bool = False
        self._watch_timer = QTimer(self)
        self._watch_timer.setInterval(2000)
        self._watch_timer.timeout.connect(self._on_watch_tick)
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

        # Loading state tracking (for watch-tick guard)
        self._model.loading_started.connect(lambda: setattr(self, "_is_loading", True))
        self._model.loading_finished.connect(lambda: setattr(self, "_is_loading", False))

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
        self._model.save_completed.connect(self._view.show_save_confirmation)

        # Save worker
        self._save_worker.finished.connect(self._on_save_finished)
        self._save_worker.progress.connect(self._model.status_message.emit)
        self._save_worker.error.connect(
            lambda msg: self._model.error_occurred.emit("Save Error", msg)
        )

    # --- View event handlers ---

    def on_folder_selected(self, path: Path):
        if path.is_file():
            path = path.parent
        self._folder_index = scan_data_folder(path)
        self._file_sizes.clear()
        combos = self._folder_index.get_experiment_types()
        self._view.update_folder_ui(path, combos, self._folder_index)
        self._model.set_folder(path)
        self._watch_timer.start()
        self._build_cache()

    def on_files_selected(self, flist: list):
        if not flist:
            self._model.clear_result()
            return
        self._model.set_file_list(flist)
        for f in self._model.file_list:
            try:
                self._file_sizes[str(f)] = _statx_get_size(str(f))
            except OSError:
                self._file_sizes[str(f)] = 0
        self._start_average()

    def on_replot(self):
        if self._model.file_list:
            self._start_average()

    def on_save(self, kwargs: dict):
        if self._model.result is None:
            return
        self._save_worker.setup(self._model.result, kwargs)
        self._view.set_save_in_progress(True)
        self._save_worker.start_save.emit()

    def _on_save_finished(self):
        self._view.set_save_in_progress(False)
        kwargs = self._save_worker.kwargs or {}
        dest = str(Path(kwargs.get("directory", "")) / kwargs.get("subdirectory", "Avg"))
        self._model.save_completed.emit(dest)

    # --- Internal ---

    def _start_average(self):
        kwargs = {
            "channel": self._view.get_channel(),
            "target": self._view.get_target(),
            "preprocessing_kwargs": self._view.get_preprocessing_kwargs(),
            "norm_kwargs": self._view.get_normalization_subgs_kwargs(),
            "binning_kwargs": self._view.get_binning_kwargs(),
            "kinetics_kwargs": self._view.get_kinetics_kwargs(),
            "cache_folder": self._model.cache_folder,
        }
        self._model.loading_started.emit()
        self._avg_worker.set_kwargs(self._model.file_list, **kwargs)
        self._avg_worker.start_task.emit()

    def _build_cache(self):
        if self._model.cache_folder is None or self._folder_index is None:
            return
        file_paths = self._folder_index.get_valid_filepaths()
        if file_paths:
            num_workers = min(max(2, os.cpu_count() // 2), len(file_paths))
            self._cache_worker = CacheWorker(file_paths, num_workers, self._model.cache_folder)
            self._cache_worker.start()

    def _on_worker_finished(self):
        results = self._avg_worker.get_results()
        self._model.loading_finished.emit()
        if isinstance(results, dict):
            self._model.set_result(results)
        else:
            self._model.clear_result()

    def _on_worker_warning(self, msg: str):
        self._model.warning_occurred.emit("Warning", msg)

    def _on_watch_tick(self):
        if self._folder_index is None:
            return
        self._discover_new_files()
        self._check_selected_file_sizes()

    def _discover_new_files(self):
        folder = self._folder_index.folder
        _statx_sync_dir(folder)
        try:
            entries = list(folder.iterdir())
        except OSError:
            return
        new_valid = False
        newly_completed: list = []  # files whose next-higher index just appeared
        for entry in entries:
            if entry.is_dir() or len(entry.name) < 10:
                continue
            key = str(entry)
            if key in self._folder_index.type_db:
                continue
            scan_type = get_scan_type(entry)
            self._folder_index.add_entry(entry, scan_type)
            if scan_type in ("exafs", "laserd"):
                new_valid = True
                # A new scan N appeared → the previous latest (N-1) is now complete.
                # Find and cache it if a cache folder is configured.
                if self._model.cache_folder is not None:
                    try:
                        prefix, index = entry.name[:-5], int(entry.name[-5:])
                        prev_path = folder / f"{prefix}{index - 1:05d}"
                        if prev_path.exists():
                            newly_completed.append(str(prev_path))
                    except (ValueError, IndexError):
                        pass
        if new_valid:
            self._view.proxy_model.update_type_db(self._folder_index.type_db)
            self._view.refresh_prefix_combos(self._folder_index.get_experiment_types())
        # Cache the now-complete predecessor files in the background (daemon threads).
        if newly_completed:
            import threading
            from trxasviewer.core.dataset import create_trxas_cache
            for path in newly_completed:
                threading.Thread(
                    target=create_trxas_cache,
                    args=(path, self._model.cache_folder),
                    daemon=True,
                ).start()

    def _check_selected_file_sizes(self):
        if self._is_loading or not self._model.file_list:
            return
        grew = False
        for f in self._model.file_list:
            key = str(f)
            try:
                size = _statx_get_size(str(f))
            except OSError:
                continue
            if size > self._file_sizes.get(key, 0):
                self._file_sizes[key] = size
                grew = True
        if grew:
            self._start_average()

    def shutdown(self):
        self._watch_timer.stop()
        self._avg_worker.quit()
        self._thread.quit()
        self._thread.wait()
        self._save_thread.quit()
        self._save_thread.wait()
