# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Lint
ruff check src/

# Run tests
pytest tests/

# Run the viewer GUI
trxasviewer view --rawfolder /home/beams/MQICHU/Datasets/trxas_datasets/Dugan_2024_3_saveddata --syncbunch 4334

# Run with NPZ cache folder
trxasviewer view --rawfolder /path/to/data --cachefolder /path/to/cache

# Run the kinetic modeler
trxasviewer model
```

Version is managed by `setuptools_scm` — do not set it manually.


## Conda environment

Always use `/home/beams/MQICHU/miniforge3/envs/d2602_trxasviewer` when debugging or implementing new features on Linux:

```bash
conda activate /home/beams/MQICHU/miniforge3/envs/d2602_trxasviewer
```


## Architecture

**TrXASViewer** is a PySide6 GUI for visualizing and analyzing Time-Resolved X-ray Absorption Spectroscopy (TrXAS) data from the APS synchrotron. The project follows an MVC pattern with a clean Qt-free `core/` library.

### Module layout

```
src/trxasviewer/
├── core/                        # Qt-free; importable standalone
│   ├── dataset.py               # TrXASDataset, TrXASDatasetManager, parse_header()
│   ├── array_ops.py             # preprocess_xas_data, normalize_by_orbitalmean
│   ├── utilities.py             # prepare_binning_matrix, remove_outlier, format_time
│   ├── file_io.py               # get_scan_type, FolderIndex, scan_data_folder, NFS helpers
│   ├── result.py                # TrXASResult (container with lazy SVD)
│   ├── fitting.py               # ODE-based kinetic model, global_fit_kinetic_model
│   ├── graph.py                 # Matplotlib decay diagram rendering
│   ├── io.py                    # save_results_with_progress, save_as_hdf5/json/origin
│   ├── plot.py                  # Matplotlib export plots (lazy import)
│   └── constants.py             # TIME_SCALES, SCALE_TO_TIME
├── gui/
│   ├── model/viewer_model.py    # ViewerModel(QObject) — app state + Qt signals
│   ├── view/
│   │   ├── viewer_view.py       # ViewerView(QMainWindow) — widgets only, emits signals
│   │   ├── viewer.ui            # Qt Designer source
│   │   ├── generated_ui.py      # Auto-generated — do not edit directly
│   │   ├── widgets.py           # Custom Qt widgets (ROI, SaveOptionsDialog, etc.)
│   │   └── pg_plot.py           # PyQtGraph kinetics rendering
│   └── control/
│       ├── viewer_controller.py # ViewerController — wires model ↔ view, calls core/
│       └── workers.py           # AverageWorker, CacheWorker, SaveWorker (QThread)
├── modeling_gui/
│   ├── trxas_modeling.py        # Kinetic modeler GUI (untouched in MVC refactor)
│   └── generated_modeling_ui.py # Auto-generated — do not edit directly
├── cli.py                       # Entry points: trxasviewer view / model
└── __init__.py                  # Lazy-loads GUI; exposes TrXASDataset at top level
```

### Data model

Raw data files are SPEC-format text files. Each column is either a metadata column or an XAS payload column encoded as `c{channel}o{orbital}b{bunch}` (parsed by `TRXAS_PATTERN` in `dataset.py`). There are always exactly 3 channels: **ch0 = background**, ch1 and ch2 = sample signals.

Two scan types are detected from the `#L` header line:
- **EXAFS**: energy axis (`Energy` keyword) — kinetics ROI extraction is available
- **LASERD**: delay axis (`laserd`/`dutd` keyword) — no energy ROIs; kinetics group disabled in GUI

`parse_header(fname)` (LRU-cached on filename) reads the `#L` header line and delegates to `_parse_header_line(header_str, is_double)` (pure, testable). Returns `(dset_type, shape, labels, labels_mask, is_double)` where `shape = (num_channels, num_orbitals, num_bunches)`.

### Processing pipeline (inside `TrXASDataset`)

1. **Header parse** → determine shape, scan type, column layout
2. **Load** raw columns via `np.loadtxt` → reshape to `(num_energy, num_channel, total_bunches)`
3. **`preprocess_xas_data()`** in `array_ops.py`:
   - Calls `remove_outlier()` (MAD or std-dev based, on background ch0) if enabled
   - Calls `normalize_by_orbitalmean_and_background()` → returns `norm_data` of shape `(num_rows, total_bunches)`
4. **`prepare_binning_matrix()`** (LRU-cached in `utilities.py`): converts bunch index → time bin via a sparse transform matrix
5. **`subtract_groundstate()`**: bunch-average or orbital-average GS subtraction
6. **`apply_binning()`**: time-bin the difference map
7. **`extract_kenetics()`**: average ΔA within each enabled energy ROI

`TrXASDatasetManager` aggregates multiple `TrXASDataset` files using `safe_mean()` (NaN-aware mean).

### MVC signal flow

```
User action (widget)
  → ViewerView emits signal (folder_selected, files_selected, replot_requested, ...)
  → ViewerController slot (on_folder_selected, on_files_selected, ...)
  → core/ processing via AverageWorker (QThread)
  → ViewerModel.result_ready emitted
  → ViewerView.update_image / update_kinetics called
```

### GUI threading

- **AverageWorker**: runs `TrXASDatasetManager.get_energy_vs_time()` in a QThread
- **CacheWorker**: spawns multiprocessing workers to pre-build NPZ caches
- **SaveWorker**: writes results to disk in a QThread (keeps GUI responsive)
- **`_watch_timer`** (2 s): polls for new files and file size changes using `statx(AT_STATX_FORCE_SYNC)` to bypass NFS attribute cache

### Caching

Dataset NPZ cache goes to a user-specified `--cachefolder` (off by default). The old `.cache/` subdirectory alongside raw files is no longer used. `DataTypeCache` (JSON file-type cache) was removed; scan-type detection now uses in-memory `FolderIndex` built by `scan_data_folder()`.

### Kinetic modeling (`fitting.py`)

Rate matrices are constructed from user-defined adjacency parameters → ODEs solved with `scipy.integrate.solve_ivp` → concentrations multiplied by species spectra → residuals minimized with `scipy.optimize.minimize`. Multi-start optimization uses multiprocessing for robustness.

### Constants

`P0 = 352055282.0 / 1296` — APS RF frequency (Hz) divided by buckets per orbit. Used to convert bunch index to real time. The maximum bunch mode at APS is 1296.

### Standalone library use

`core/` has no Qt dependency and is safe to import in scripts and Jupyter notebooks:

```python
from trxasviewer.core import TrXASDataset, TrXASDatasetManager, TrXASResult, save_results
```

See `examples/analyze_trxas.py` for a full worked example.
