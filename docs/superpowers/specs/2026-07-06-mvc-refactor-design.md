# MVC Refactor — Viewer Design Spec

**Date:** 2026-07-06  
**Scope:** Viewer only (`trxasviewer_gui.py` and related files). Modeling GUI is moved as-is and left untouched for a later cycle.  
**Approach:** MVC with Qt signals in `gui/model/` (Approach B).

---

## Goals

1. Separate core data/analysis logic from GUI code so `core/` is importable in headless Python scripts with no Qt dependency.
2. Introduce a clean MVC structure for the viewer: `gui/model/` (state), `gui/view/` (widgets), `gui/control/` (wiring + workers).
3. Eliminate the ~1000-line `TrXASViewer` monolith by splitting responsibilities across the three layers.
4. No logic is lost — only relocated.

---

## Folder Layout

```
src/trxasviewer/
├── __init__.py
├── cli.py                          # unchanged
│
├── core/                           # pure Python, zero Qt
│   ├── __init__.py
│   ├── constants.py                # moved as-is
│   ├── utilities.py                # moved as-is
│   ├── dataset.py                  # from trxas_dataset.py — strip plot/save static methods
│   ├── result.py                   # from trxas_result.py — strip plot_diff()
│   ├── dtype_cache.py              # moved as-is
│   ├── plot.py                     # matplotlib export plots; absorbs plot_results()
│   ├── io.py                       # new: save_as_hdf5/json/origin (from dataset static methods)
│   ├── fitting.py                  # moved as-is (modeling — touch later)
│   └── graph.py                    # from trxas_graph.py (modeling — touch later)
│
├── gui/
│   ├── __init__.py
│   ├── model/
│   │   ├── __init__.py
│   │   └── viewer_model.py         # ViewerModel(QObject) — state + signals
│   ├── view/
│   │   ├── __init__.py
│   │   ├── viewer.ui               # Qt Designer source (unchanged)
│   │   ├── generated_ui.py         # auto-generated, moved from root
│   │   ├── viewer_view.py          # TrXASViewer → ViewerView, presentation only
│   │   ├── widgets.py              # custom Qt widgets, moved from root
│   │   └── pg_plot.py              # pyqtgraph rendering, moved from root
│   └── control/
│       ├── __init__.py
│       ├── viewer_controller.py    # ViewerController — wires model ↔ view, calls core
│       └── workers.py              # AverageWorker, CacheWorker (moved from trxasviewer_gui.py)
│
└── modeling_gui/                   # all files moved verbatim, no changes
    ├── __init__.py
    ├── modeling.ui
    ├── generated_modeling_ui.py
    ├── trxas_modeling.py
    └── kinetics_optimizer.py       # Qt worker for modeling (currently unused, moved as-is)
```

---

## Core Layer (`core/`)

**Invariant:** No Qt imports anywhere in `core/`. Safe to use in a headless script:
```python
from trxasviewer.core.dataset import TrXASDataset, TrXASDatasetManager
from trxasviewer.core.result import TrXASResult
from trxasviewer.core.io import save_as_hdf5
```

### `dataset.py` changes
Remove static methods that don't belong on the data class:
- `TrXASDataset.plot_results()` → moved to `core/plot.py`
- `TrXASDataset.save_as_origin_format()` → moved to `core/io.py`
- `TrXASDataset.save_as_hdf5()` → moved to `core/io.py`
- `TrXASDataset.save_as_json()` → moved to `core/io.py`
- `TrXASDatasetManager.save_results()` loses its plot call

All data loading, normalization, binning, caching, and `get_energy_vs_time()` are unchanged.

### `result.py` changes
Remove `plot_diff()` (matplotlib rendering). All data extraction methods stay:
`get_svd()`, `get_diff_map()`, `get_kinetic_profile()`, `combined_fitting_data()`, etc.

### `plot.py`
Absorbs `plot_results()` from the dataset class as a standalone function. Existing functions (`plot_2d_scan()`, `plot_kinetics()`, etc.) stay unchanged.

### `io.py` (new)
Standalone functions relocated from `TrXASDataset`:
- `save_as_hdf5(result, path)`
- `save_as_json(result, path)`
- `save_as_origin_format(result, path)`

### All other core files
`constants.py`, `utilities.py`, `dtype_cache.py`, `fitting.py`, `graph.py` — moved verbatim, no changes.

---

## Model Layer (`gui/model/viewer_model.py`)

`ViewerModel(QObject)` is the single source of truth for viewer state. It holds data and emits signals when state changes. It never calls `core/` directly — that is the controller's job.

### State
```python
raw_folder: Path
file_list: list[Path]
dataset_manager: TrXASDatasetManager
result: TrXASResult | None
preprocessing_kwargs: dict      # normalization / outlier params
binning_kwargs: dict            # time-bin params
normalization_subgs_kwargs: dict
kinetics_kwargs: dict
```

### Signals
```python
folder_changed = Signal(Path)
selection_changed = Signal(list)
result_ready = Signal(object)       # TrXASResult
result_cleared = Signal()
loading_started = Signal()
loading_finished = Signal()
status_message = Signal(str)
error_occurred = Signal(str, str)   # title, message
warning_occurred = Signal(str, str)
```

---

## Control Layer (`gui/control/`)

### `viewer_controller.py`

`ViewerController(QObject)` is the only layer that imports from `core/`. On construction it receives `ViewerModel` and `ViewerView` and wires their signals together.

**Responsibilities:**
- Connect view interaction signals → handler methods
- Connect model signals → view display methods
- Assemble processing kwargs from model state (the `get_*_kwargs()` methods migrate here from `TrXASViewer`)
- Start/stop workers
- Update model state from worker results

**Key signal flow:**
```
user selects files
  → view.files_selected(flist)
  → controller.on_selection_changed(flist)
      model.file_list = flist
      model.loading_started.emit()
      start AverageWorker(flist, model's kwargs)

AverageWorker.finished(result)
  → controller.on_result_ready(result)
      model.result = result
      model.loading_finished.emit()
      model.result_ready.emit(result)

model.result_ready(result)
  → view.update_image(result)
  → view.update_kinetics(result)
```

### `workers.py`

Moved from `trxasviewer_gui.py` — no logic changes in this cycle:

- `AverageWorker(QObject)`: runs `TrXASDatasetManager.get_energy_vs_time()` in a QThread. Signals: `finished(TrXASResult)`, `progress(str)`, `error(str, str)`, `warning(str, str)`.
- `CacheWorker(QThread)`: spawns a `multiprocessing.Process` for cache generation.

---

## View Layer (`gui/view/`)

### `viewer_view.py`

`TrXASViewer` renamed to `ViewerView`. After refactor it:
- Inherits `QMainWindow` and `Ui_MainWindow` (from `generated_ui.py`)
- Sets up and lays out widgets only
- Emits signals on user interaction — **no calls to `core/`**
- Has pure display methods called by the controller:

```python
# Signals emitted by the view
folder_selected = Signal(Path)
files_selected = Signal(list)
parameter_changed = Signal(str, object)   # name, value

# Display methods called from controller/model signals
def update_image(self, result: TrXASResult): ...
def update_kinetics(self, result: TrXASResult): ...
def update_status(self, message: str): ...
def show_error(self, title: str, message: str): ...
def show_warning(self, title: str, message: str): ...
def set_loading(self, loading: bool): ...
```

### `widgets.py`
All existing custom Qt classes moved here from `trxasviewer_gui.py` and the old `widgets.py`:
- `DatasetFilterModel(QSortFilterProxyModel)`
- `VlockedRectROI`, `HlockedRectROI`
- `TrXASResultTableModel`, `ParameterTableModel`
- `SaveOptionsDialog`
- `show_error_dialog()`, `show_warning_dialog()`

### `pg_plot.py`, `generated_ui.py`, `viewer.ui`
Moved as-is, no changes.

---

## Modeling GUI (`modeling_gui/`)

All files (`trxas_modeling.py`, `generated_modeling_ui.py`, `modeling.ui`, `kinetics_optimizer.py`) moved verbatim from the source root. No internal changes. Will be refactored in a later cycle.

---

## What Is Not Changing

- All core algorithms: data loading, normalization, binning, SVD, kinetics extraction
- All plotting functions in `plot.py` and `pg_plot.py`
- The `.ui` files and auto-generated UI classes
- Worker threading logic
- CLI entry points in `cli.py`
- Public API exports in `__init__.py` (updated to new import paths)

---

## Migration Notes

- `cli.py` import paths updated: `from trxasviewer.gui.view.viewer_view import ViewerView`
- `__init__.py` exports updated to reflect new module paths
- `modeling_gui/trxas_modeling.py` import paths updated for `core/` modules (e.g., `from trxasviewer.core.fitting import ...`)
- HDF5 cache path constant (`CACHE_PATH`) stays in `core/dataset.py`
