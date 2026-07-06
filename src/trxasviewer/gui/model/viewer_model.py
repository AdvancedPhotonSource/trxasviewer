from pathlib import Path
from PySide6.QtCore import QObject, Signal


class ViewerModel(QObject):
    folder_changed = Signal(Path)
    selection_changed = Signal(list)
    result_ready = Signal(object)       # dict (raw results from TrXASDatasetManager)
    result_cleared = Signal()
    loading_started = Signal()
    loading_finished = Signal()
    loading_progress = Signal(int)
    status_message = Signal(str)
    error_occurred = Signal(str, str)   # title, message
    warning_occurred = Signal(str, str)

    def __init__(self, reset_cache=False, use_cache=False, parent=None):
        super().__init__(parent)
        self.raw_folder: Path | None = None
        self.file_list: list[Path] = []
        self.dtype_db = None
        self.result: dict | None = None
        self.reset_cache: bool = reset_cache
        self.use_cache: bool = use_cache

    def set_folder(self, path: Path) -> None:
        self.raw_folder = path
        self.folder_changed.emit(path)

    def set_file_list(self, flist: list) -> None:
        self.file_list = [Path(f) for f in flist]
        self.selection_changed.emit(self.file_list)

    def set_result(self, result: dict) -> None:
        self.result = result
        self.result_ready.emit(result)

    def clear_result(self) -> None:
        self.result = None
        self.result_cleared.emit()
