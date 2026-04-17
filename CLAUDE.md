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

# Run the viewer GUI (default subcommand is 'view')
trxasviewer view --rawfolder /path/to/data --syncbunch 4334
trxasviewer model
```

Version is managed by `setuptools_scm` — do not set it manually.


## Conda environment

use /home/beams/MQICHU/miniforge3/envs/d2602_trxasviewer when on linux


## Architecture

**TrXASViewer** is a PySide6 GUI for visualizing and analyzing Time-Resolved X-ray Absorption Spectroscopy (TrXAS) data from the APS synchrotron. Two independent GUIs share the same data layer:

| File | Role |
|------|------|
| `trxasviewer_gui.py` | Main viewer: file browser, energy-time heatmap, kinetics extraction, SVD |
| `trxas_modeling.py` | Secondary GUI: kinetic model fitting and visualization |
| `trxas_dataset.py` | Data loading, header parsing, normalization, binning, HDF5 caching |
| `fitting.py` | ODE-based kinetic model construction and scipy optimization |
| `utilities.py` | Binning matrix, normalization, outlier removal, file I/O helpers |
| `widgets.py` | Custom Qt widgets (ROI, export dialogs, table views) |
| `plot.py` | Matplotlib export plots |
| `generated_ui.py` | Auto-generated from `viewer.ui` — do not edit directly |
| `generated_modeling_ui.py` | Auto-generated from `modeling.ui` — do not edit directly |

### Data model

Raw data files are SPEC-format text files. Each column is either a metadata column or an XAS payload column encoded as `c{channel}o{orbital}b{bunch}` (parsed by `TRXAS_PATTERN`). There are always exactly 3 channels: **ch0 = background**, ch1 and ch2 = signals.

Two scan types are detected from the `#L` header line:
- **EXAFS**: energy axis (`Energy` keyword) — used for static/energy-resolved spectra
- **LASERD**: delay axis (`laserd`/`dutd` keyword) — used for pump-probe time-resolved data

`process_header()` (LRU-cached) parses the `#L` header line into `(dset_type, shape, labels, labels_mask, payload_mask)` where `shape = (num_channels, num_orbitals, num_bunches)`.

### Processing pipeline (inside `TrXASDataset`)

1. **Header parse** → determine shape and scan type
2. **Load** raw columns → reshape to `(num_energy, num_channel, total_bunches)`
3. **`normalize(xas_data, shape, num_rows, ...)`** in `utilities.py`:
   - Optionally calls `remove_outlier()` (MAD or std-dev based, on background ch0)
   - Returns `(xas_data, norm_data)` — xas_data is the outlier-corrected copy, norm_data is `(num_rows, total_bunches)` float32
4. **`prepare_binning_matrix()`** (LRU-cached): converts bunch index → time bin via a sparse transform matrix
5. **Ground-state subtraction** and kinetics extraction happen in `get_energy_vs_time()`

`TrXASDatasetManager` aggregates multiple `TrXASDataset` files using `safe_mean()` (NaN-aware weighted mean).

Processed data is cached to HDF5 under a `.cache/` subdirectory alongside the raw files.

### GUI threading

Background work runs in QThread workers to keep the GUI responsive:
- `CacheWorker`: parallel scan-type detection for the file browser
- `AverageWorker`: dataset averaging on selection change
- `FitWorker`: kinetic parameter optimization in `trxas_modeling.py`

### Kinetic modeling (`fitting.py`)

Rate matrices are constructed from user-defined adjacency/rate parameters → ODEs solved with `scipy.integrate.solve_ivp` → concentrations convolved with IRF → residuals minimized with `scipy.optimize.minimize`.

### Constant

`P0 = 352055282.000000 / 1296` — APS RF frequency (Hz) divided by number of buckets per orbit. Used throughout to convert bunch indices to real time.
