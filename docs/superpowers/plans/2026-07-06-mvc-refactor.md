# MVC Refactor — Viewer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganise the viewer into an MVC structure: pure-Python `core/`, Qt application-state `gui/model/`, widget-only `gui/view/`, wiring `gui/control/` — without changing any data-processing logic.

**Architecture:** Approach B from the design spec. `ViewerModel(QObject)` holds state and emits Qt signals. `ViewerController` is the only layer that imports from `core/`. `ViewerView` (renamed from `TrXASViewer`) only owns widgets and emits user-action signals. Modeling files move verbatim and are not refactored.

**Tech Stack:** Python 3.10+, PySide6, pyqtgraph, numpy, h5py, scipy, setuptools_scm.

**Conda env (Linux):** `/home/beams/MQICHU/miniforge3/envs/d2602_trxasviewer`

**Design spec:** `docs/superpowers/specs/2026-07-06-mvc-refactor-design.md`

---

## File Map

| Source | Destination | Change |
|--------|-------------|--------|
| `constants.py` | `core/constants.py` | move only |
| `utilities.py` | `core/utilities.py` | move only |
| `dtype_cache.py` | `core/dtype_cache.py` | move; fix `__version__` import |
| `fitting.py` | `core/fitting.py` | move; fix `.trxas_graph` → `.graph` |
| `trxas_graph.py` | `core/graph.py` | rename + move |
| `trxas_dataset.py` | `core/dataset.py` | rename + move; strip 3 static save methods + `plot_results` static method |
| `plot.py` | `core/plot.py` | move |
| *(new)* | `core/io.py` | extract save functions from `TrXASDatasetManager.save_results()` and `TrXASDataset` statics |
| `trxas_result.py` | `core/result.py` | rename + move; remove dead `matplotlib` import |
| `trxas_modeling.py` | `modeling_gui/trxas_modeling.py` | move; fix relative imports |
| `generated_modeling_ui.py` | `modeling_gui/generated_modeling_ui.py` | move |
| `modeling.ui` | `modeling_gui/modeling.ui` | move |
| `kinetics_optimizer.py` | `modeling_gui/kinetics_optimizer.py` | move |
| `generated_ui.py` | `gui/view/generated_ui.py` | move |
| `viewer.ui` | `gui/view/viewer.ui` | move |
| `widgets.py` | `gui/view/widgets.py` | move; receive `DatasetFilterModel` + `_SignalLogHandler` from `trxasviewer_gui.py` |
| `pg_plot.py` | `gui/view/pg_plot.py` | move |
| *(new)* | `gui/model/viewer_model.py` | new — `ViewerModel(QObject)` |
| *(new)* | `gui/control/workers.py` | extract `AverageWorker`, `CacheWorker` from `trxasviewer_gui.py` |
| *(new)* | `gui/control/viewer_controller.py` | new — `ViewerController(QObject)` |
| `trxasviewer_gui.py` | `gui/view/viewer_view.py` | rename + slim: remove all core calls, add view signals |
| `__init__.py` | `__init__.py` | update import paths |
| `cli.py` | `cli.py` | update import paths |

---

## Task 1: Scaffold directory structure

**Files:**
- Create: `src/trxasviewer/core/__init__.py`
- Create: `src/trxasviewer/gui/__init__.py`
- Create: `src/trxasviewer/gui/model/__init__.py`
- Create: `src/trxasviewer/gui/view/__init__.py`
- Create: `src/trxasviewer/gui/control/__init__.py`
- Create: `src/trxasviewer/modeling_gui/__init__.py`

- [ ] **Step 1: Create directories and empty `__init__.py` files**

```bash
cd src/trxasviewer
mkdir -p core gui/model gui/view gui/control modeling_gui
touch core/__init__.py gui/__init__.py gui/model/__init__.py \
      gui/view/__init__.py gui/control/__init__.py modeling_gui/__init__.py
```

- [ ] **Step 2: Verify the package tree resolves**

```bash
python -c "import trxasviewer; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Commit**

```bash
git add src/trxasviewer/core/__init__.py \
        src/trxasviewer/gui/__init__.py \
        src/trxasviewer/gui/model/__init__.py \
        src/trxasviewer/gui/view/__init__.py \
        src/trxasviewer/gui/control/__init__.py \
        src/trxasviewer/modeling_gui/__init__.py
git commit -m "chore: scaffold mvc directory structure"
```

---

## Task 2: Move pure-Python core modules

Move `constants.py`, `utilities.py`, `dtype_cache.py`, `fitting.py`, `trxas_graph.py` into `core/`. Fix all cross-file imports in one pass. The app must still launch after this task.

**Files:**
- Modify (git mv): `constants.py` → `core/constants.py`
- Modify (git mv): `utilities.py` → `core/utilities.py`
- Modify (git mv): `dtype_cache.py` → `core/dtype_cache.py`
- Modify (git mv): `fitting.py` → `core/fitting.py`
- Modify (git mv): `trxas_graph.py` → `core/graph.py`
- Modify: `core/dtype_cache.py` (fix `__version__` import)
- Modify: `core/fitting.py` (fix `trxas_graph` import)
- Modify: `trxas_dataset.py` (still at root — fix utilities import)
- Modify: `trxas_result.py` (still at root — fix utilities import)
- Modify: `trxasviewer_gui.py` (still at root — fix utilities + dtype_cache import)
- Modify: `trxas_modeling.py` (still at root — fix constants, fitting, graph, utilities imports)
- Test: `tests/test_trxasviewer.py`

- [ ] **Step 1: git mv the five files**

```bash
cd src/trxasviewer
git mv constants.py core/constants.py
git mv utilities.py core/utilities.py
git mv dtype_cache.py core/dtype_cache.py
git mv fitting.py core/fitting.py
git mv trxas_graph.py core/graph.py
```

- [ ] **Step 2: Fix `core/dtype_cache.py` — update `__version__` import**

In `src/trxasviewer/core/dtype_cache.py`, replace:
```python
from . import __version__
```
with:
```python
from trxasviewer import __version__
```

(All other imports in this file use `from .utilities import ...` which resolve correctly within `core/`.)

- [ ] **Step 3: Fix `core/fitting.py` — update graph import**

In `src/trxasviewer/core/fitting.py`, replace:
```python
from .trxas_graph import create_initial_state_array
```
with:
```python
from .graph import create_initial_state_array
```

- [ ] **Step 4: Fix `trxas_dataset.py` (still at root)**

Replace:
```python
from .utilities import (
```
with:
```python
from .core.utilities import (
```

- [ ] **Step 5: Fix `trxas_result.py` (still at root)**

Replace:
```python
from .utilities import format_time
```
with:
```python
from .core.utilities import format_time
```

- [ ] **Step 6: Fix `trxasviewer_gui.py` (still at root)**

Replace:
```python
from .utilities import format_time
```
with:
```python
from .core.utilities import format_time
```

Replace:
```python
from .dtype_cache import DataTypeCache
```
with:
```python
from .core.dtype_cache import DataTypeCache
```

- [ ] **Step 7: Fix `trxas_modeling.py` (still at root)**

Replace the import block:
```python
from . import __version__
from .constants import TIME_SCALES
from .fitting import run_single_optimization
```
with:
```python
from trxasviewer import __version__
from .core.constants import TIME_SCALES
from .core.fitting import run_single_optimization
```

Replace:
```python
from .trxas_graph import draw_decay_graph_with_top_nodes
```
with:
```python
from .core.graph import draw_decay_graph_with_top_nodes
```

Replace:
```python
from .utilities import NumpyEncoder
```
with:
```python
from .core.utilities import NumpyEncoder
```

- [ ] **Step 8: Write import smoke test**

In `tests/test_trxasviewer.py`, add:
```python
def test_core_modules_importable():
    from trxasviewer.core import constants, utilities, dtype_cache, fitting, graph
    assert hasattr(constants, "TIME_SCALES")
    assert hasattr(utilities, "format_time")
    assert hasattr(dtype_cache, "DataTypeCache")
    assert hasattr(fitting, "global_fit_kinetic_model")
    assert hasattr(graph, "draw_decay_graph_with_top_nodes")
```

- [ ] **Step 9: Run the smoke test**

```bash
pytest tests/test_trxasviewer.py::test_core_modules_importable -v
```

Expected: `PASSED`

- [ ] **Step 10: Verify the CLI still resolves**

```bash
python -c "from trxasviewer import TrXASDataset; print('ok')"
```

Expected: `ok`

- [ ] **Step 11: Commit**

```bash
git add -u
git commit -m "refactor: move pure-python modules to core/"
```

---

## Task 3: Move dataset + plot to core/, create core/io.py

Extract the four save/plot static methods from `TrXASDataset` into `core/io.py` (standalone functions). Move `trxas_dataset.py` → `core/dataset.py` and `plot.py` → `core/plot.py`. Update `TrXASDatasetManager.save_results()` to call the new standalone functions.

**Files:**
- Create: `src/trxasviewer/core/io.py`
- Modify (git mv): `trxas_dataset.py` → `core/dataset.py`
- Modify (git mv): `plot.py` → `core/plot.py`
- Modify: `core/dataset.py` (fix imports, remove 4 static methods, remove `from .plot import plot_results`)
- Modify: `core/io.py` (new standalone functions + `save_results`)
- Modify: `trxasviewer_gui.py` (update import path for dataset)
- Modify: `trxas_modeling.py` (no dataset import needed — already clean)
- Test: `tests/test_trxasviewer.py`

- [ ] **Step 1: Write failing test for `core/io.py`**

In `tests/test_trxasviewer.py`, add:
```python
def test_io_importable():
    from trxasviewer.core.io import save_as_hdf5, save_as_json, save_as_origin_format, save_results
    assert callable(save_as_hdf5)
    assert callable(save_as_json)
    assert callable(save_as_origin_format)
    assert callable(save_results)
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
pytest tests/test_trxasviewer.py::test_io_importable -v
```

Expected: `FAILED` — `ModuleNotFoundError: No module named 'trxasviewer.core.io'`

- [ ] **Step 3: git mv the two files**

```bash
cd src/trxasviewer
git mv trxas_dataset.py core/dataset.py
git mv plot.py core/plot.py
```

- [ ] **Step 4: Fix imports in `core/dataset.py`**

The file currently starts with:
```python
from .utilities import (
    ...
)
from .plot import plot_results
```

Change to (removing the `from .plot import plot_results` line entirely — the static method that used it will be deleted):
```python
from .utilities import (
    prepare_binning_matrix,
    preprocess_xas_data,
    pad_last_dim,
    is_recently_modified,
)
```

(All other imports in `core/dataset.py` use standard library or third-party packages — no other relative import changes needed since utilities is already in core/.)

- [ ] **Step 5: Remove the four static methods from `core/dataset.py`**

Delete these four methods entirely from `TrXASDataset` (lines 510–572 in the original file):
```python
@staticmethod
def plot_results(results, save_name): ...

@staticmethod
def save_as_origin_format(origin_folder, results): ...

@staticmethod
def save_as_json(fname, results): ...

@staticmethod
def save_as_hdf5(fname, results_raw): ...
```

- [ ] **Step 6: Create `src/trxasviewer/core/io.py`**

```python
import json
import shutil
import numpy as np
import h5py
from pathlib import Path


def save_as_origin_format(origin_folder, results):
    for key, label in zip(("data", "diff"), ("data_full", "data_diff")):
        temp = results[key]
        shape = temp.shape
        data_full = np.zeros(np.array(shape) + 1, dtype=np.float32)
        data_full[1:, 1:] = temp
        data_full[1:, 0] = results["x_axis"]["value"]
        data_full[0, 1:] = results["t_axis"]
        data_full = data_full.astype(object)
        if results["dset_type"] == "EXAFS":
            data_full[0, 0] = "Energy(keV)/Time(s)"
        else:
            data_full[0, 0] = "Delay(s)/Time(s)"
        np.savetxt(
            origin_folder / f"{label}.txt", data_full, fmt="%s", delimiter=","
        )
    for key, value in results["kinetics"].items():
        np.savetxt(
            origin_folder / f"kinetics_{key}.txt",
            value["profile"]["main"].T,
            fmt="%.7e",
            delimiter=",",
            header="Delay(s),Intensity,Error",
            comments="",
        )


def save_as_json(fname, results):
    with open(fname, "w") as f:
        json.dump(results["analysis_kwargs"], f, indent=4)


def save_as_hdf5(fname, results_raw):
    results = results_raw.copy()

    def save_recursively(group, data):
        for key, value in data.items():
            if value is None:
                continue
            if isinstance(value, dict):
                subgroup = group.create_group(key)
                save_recursively(subgroup, value)
            else:
                if isinstance(value, str):
                    string_dt = h5py.string_dtype(encoding="utf-8")
                    group.create_dataset(key, data=value, dtype=string_dt)
                else:
                    compression = None
                    if isinstance(value, np.ndarray):
                        value = np.ascontiguousarray(value)
                        compression = "gzip" if value.size > 4096 else None
                    group.create_dataset(key, data=value, compression=compression)

    with h5py.File(fname, "w") as f:
        save_recursively(f, results)


def save_results(
    results,
    directory=None,
    subdirectory="Avg",
    save_image=True,
    save_numpy=True,
    save_hdf=True,
    save_origin=True,
):
    from trxasviewer.core.plot import plot_results  # imported here to avoid circular import

    folder = Path(directory) / subdirectory
    folder.mkdir(parents=True, exist_ok=True)

    if save_numpy:
        np.savez_compressed(folder / "results.npz", **results)
        package_path = Path(__file__).parent
        shutil.copy(package_path / "plot.py", folder / "load_and_plot.py")

    if save_image:
        img_folder = folder / "images"
        img_folder.mkdir(parents=True, exist_ok=True)
        plot_results(results, folder=img_folder)

    if save_origin:
        o_folder = folder / "origin"
        o_folder.mkdir(parents=True, exist_ok=True)
        save_as_origin_format(o_folder, results)

    if save_hdf:
        save_as_hdf5(folder / "results.hdf", results)

    save_as_json(folder / "settings.json", results)
```

- [ ] **Step 7: Update `TrXASDatasetManager.save_results()` in `core/dataset.py`**

Replace the body of `TrXASDatasetManager.save_results()` (the method that previously called `TrXASDataset.plot_results()` etc.) with a delegation to `core/io.save_results()`:

```python
def save_results(self, results, **kwargs):
    from trxasviewer.core.io import save_results
    save_results(results, **kwargs)
```

- [ ] **Step 8: Fix `trxasviewer_gui.py` — update dataset import**

Replace:
```python
from .trxas_dataset import (
    TrXASDatasetManager,
    create_trxas_cache_from_flist,
    CACHE_PATH,
)
```
with:
```python
from .core.dataset import (
    TrXASDatasetManager,
    create_trxas_cache_from_flist,
    CACHE_PATH,
)
```

- [ ] **Step 9: Update `__init__.py` — fix TrXASDataset import**

Replace:
```python
from .trxas_dataset import TrXASDataset
```
with:
```python
from .core.dataset import TrXASDataset
```

- [ ] **Step 10: Run smoke tests**

```bash
pytest tests/test_trxasviewer.py::test_io_importable tests/test_trxasviewer.py::test_core_modules_importable -v
```

Expected: both `PASSED`

- [ ] **Step 11: Verify the package imports cleanly**

```bash
python -c "from trxasviewer import TrXASDataset; from trxasviewer.core.io import save_results; print('ok')"
```

Expected: `ok`

- [ ] **Step 12: Commit**

```bash
git add -u src/trxasviewer/core/io.py
git commit -m "refactor: move dataset+plot to core/, extract io.py"
```

---

## Task 4: Move result.py → core/result.py

**Files:**
- Modify (git mv): `trxas_result.py` → `core/result.py`
- Modify: `core/result.py` (fix import, remove dead matplotlib import)
- Modify: `trxasviewer_gui.py` (update import path)
- Modify: `trxas_modeling.py` (update import path)
- Test: `tests/test_trxasviewer.py`

- [ ] **Step 1: Write failing test**

```python
def test_result_importable():
    from trxasviewer.core.result import TrXASResult, convert_npz_obj, get_levels
    assert callable(TrXASResult)
```

- [ ] **Step 2: Run test to confirm failure**

```bash
pytest tests/test_trxasviewer.py::test_result_importable -v
```

Expected: `FAILED`

- [ ] **Step 3: git mv**

```bash
cd src/trxasviewer && git mv trxas_result.py core/result.py
```

- [ ] **Step 4: Fix imports in `core/result.py`**

Replace:
```python
import matplotlib.pyplot as plt
from .utilities import format_time
```
with:
```python
from .utilities import format_time
```

(`matplotlib.pyplot` was unused — remove it.)

- [ ] **Step 5: Fix `trxasviewer_gui.py`**

Replace:
```python
from .trxas_result import TrXASResult
```
with:
```python
from .core.result import TrXASResult
```

- [ ] **Step 6: Fix `trxas_modeling.py`**

Replace:
```python
from .trxas_result import TrXASResult
```
with:
```python
from .core.result import TrXASResult
```

- [ ] **Step 7: Run tests**

```bash
pytest tests/test_trxasviewer.py::test_result_importable -v
```

Expected: `PASSED`

- [ ] **Step 8: Commit**

```bash
git add -u
git commit -m "refactor: move trxas_result.py → core/result.py"
```

---

## Task 5: Move modeling files to `modeling_gui/`

Move all four modeling files verbatim. Fix their relative imports to use absolute paths into `core/` and `gui/view/` (pg_plot hasn't moved yet — use a forward-looking path; pg_plot moves in Task 6).

**Files:**
- Modify (git mv): `trxas_modeling.py` → `modeling_gui/trxas_modeling.py`
- Modify (git mv): `generated_modeling_ui.py` → `modeling_gui/generated_modeling_ui.py`
- Modify (git mv): `modeling.ui` → `modeling_gui/modeling.ui`
- Modify (git mv): `kinetics_optimizer.py` → `modeling_gui/kinetics_optimizer.py`
- Modify: `modeling_gui/trxas_modeling.py` (fix all relative imports)
- Modify: `__init__.py` (update `main_modeling_gui` import)

- [ ] **Step 1: git mv the four files**

```bash
cd src/trxasviewer
git mv trxas_modeling.py modeling_gui/trxas_modeling.py
git mv generated_modeling_ui.py modeling_gui/generated_modeling_ui.py
git mv modeling.ui modeling_gui/modeling.ui
git mv kinetics_optimizer.py modeling_gui/kinetics_optimizer.py
```

- [ ] **Step 2: Fix imports in `modeling_gui/trxas_modeling.py`**

Replace the entire import block at the top of the file with:
```python
import logging
import random
import sys
import json
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
import psutil
import pyqtgraph as pg
from PySide6.QtCore import QByteArray, QObject, Qt, QThread, Signal, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
)

from trxasviewer import __version__
from trxasviewer.core.constants import TIME_SCALES
from trxasviewer.core.fitting import run_single_optimization
from trxasviewer.core.graph import draw_decay_graph_with_top_nodes
from trxasviewer.core.result import TrXASResult
from trxasviewer.core.utilities import NumpyEncoder
from trxasviewer.modeling_gui.generated_modeling_ui import Ui_MainWindow
from trxasviewer.gui.view.pg_plot import plot_kinetics_profile   # pg_plot moves in Task 6
from trxasviewer.gui.view.widgets import (                        # widgets moves in Task 6
    ParameterTableModel,
    TrXASResultTableModel,
    show_error_dialog,
)
```

- [ ] **Step 3: Fix `__init__.py` — update modeling_gui import**

Replace:
```python
from .trxas_modeling import main_modeling_gui
```
with:
```python
from .modeling_gui.trxas_modeling import main_modeling_gui
```

- [ ] **Step 4: Verify modeling entry point imports**

```bash
python -c "from trxasviewer import main_modeling_gui; print('ok')"
```

Expected: `ok` (pg_plot and widgets not yet in gui/view/ so this may fail — see note below)

**Note:** If step 4 fails because `trxasviewer.gui.view.pg_plot` doesn't exist yet, that is expected — pg_plot and widgets move in Task 6. The `modeling_gui/trxas_modeling.py` import of pg_plot and widgets will resolve correctly after Task 6. To keep the app importable at this step, temporarily use the old relative path for pg_plot and widgets:

Temporary (until Task 6 is done):
```python
from trxasviewer.pg_plot import plot_kinetics_profile
from trxasviewer.widgets import (ParameterTableModel, TrXASResultTableModel, show_error_dialog)
```

Then Task 6 will update these to the final paths.

- [ ] **Step 5: Commit**

```bash
git add -u
git commit -m "refactor: move modeling files to modeling_gui/"
```

---

## Task 6: Move view assets to `gui/view/`

Move `generated_ui.py`, `viewer.ui`, `widgets.py`, `pg_plot.py` into `gui/view/`. Also move `DatasetFilterModel` and `_SignalLogHandler` from `trxasviewer_gui.py` into `gui/view/widgets.py`. Fix all import paths.

**Files:**
- Modify (git mv): `generated_ui.py` → `gui/view/generated_ui.py`
- Modify (git mv): `viewer.ui` → `gui/view/viewer.ui`
- Modify (git mv): `widgets.py` → `gui/view/widgets.py`
- Modify (git mv): `pg_plot.py` → `gui/view/pg_plot.py`
- Modify: `gui/view/widgets.py` (add `DatasetFilterModel`, `_SignalLogHandler`; fix imports)
- Modify: `trxasviewer_gui.py` (update all view-asset imports; remove `DatasetFilterModel`, `_SignalLogHandler` class bodies)
- Modify: `modeling_gui/trxas_modeling.py` (update pg_plot + widgets imports to final paths)

- [ ] **Step 1: git mv the four view assets**

```bash
cd src/trxasviewer
git mv generated_ui.py gui/view/generated_ui.py
git mv viewer.ui gui/view/viewer.ui
git mv widgets.py gui/view/widgets.py
git mv pg_plot.py gui/view/pg_plot.py
```

- [ ] **Step 2: Update imports in `gui/view/widgets.py`**

`widgets.py` has no internal relative imports that need changing (it imports pyqtgraph and pandas only). No changes needed beyond the move.

- [ ] **Step 3: Add `DatasetFilterModel` and `_SignalLogHandler` to `gui/view/widgets.py`**

In `trxasviewer_gui.py`, cut the `DatasetFilterModel` class (lines 85–129) and the `_SignalLogHandler` class (lines 132–142), and paste them at the bottom of `gui/view/widgets.py`.

Add the required imports at the top of `gui/view/widgets.py` (if not already present):
```python
import logging
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSortFilterProxyModel
from trxasviewer.core.dtype_cache import DataTypeCache
from trxasviewer.core.dataset import CACHE_PATH
```

- [ ] **Step 4: Update `trxasviewer_gui.py` — fix all view-asset imports**

Replace:
```python
from .generated_ui import Ui_MainWindow
```
with:
```python
from .gui.view.generated_ui import Ui_MainWindow
```

Replace:
```python
from .widgets import VlockedRectROI, SaveOptionsDialog, show_error_dialog, show_warning_dialog
```
with:
```python
from .gui.view.widgets import (
    VlockedRectROI, SaveOptionsDialog, show_error_dialog, show_warning_dialog,
    DatasetFilterModel, _SignalLogHandler,
)
```

Replace:
```python
from .pg_plot import plot_kinetics_profile, plot_kinetics_error
```
with:
```python
from .gui.view.pg_plot import plot_kinetics_profile, plot_kinetics_error
```

Remove the `DatasetFilterModel` and `_SignalLogHandler` class definitions from `trxasviewer_gui.py` (they now live in `gui/view/widgets.py`).

- [ ] **Step 5: Update modeling_gui imports to final paths**

In `modeling_gui/trxas_modeling.py`, update from the temporary paths to the final ones:
```python
from trxasviewer.gui.view.pg_plot import plot_kinetics_profile
from trxasviewer.gui.view.widgets import (
    ParameterTableModel,
    TrXASResultTableModel,
    show_error_dialog,
)
```

- [ ] **Step 6: Run smoke test for view assets**

Add to `tests/test_trxasviewer.py`:
```python
def test_view_assets_importable():
    from trxasviewer.gui.view.generated_ui import Ui_MainWindow
    from trxasviewer.gui.view.widgets import (
        VlockedRectROI, SaveOptionsDialog, DatasetFilterModel, _SignalLogHandler
    )
    from trxasviewer.gui.view.pg_plot import plot_kinetics_profile, plot_kinetics_error
    assert callable(plot_kinetics_profile)
```

```bash
pytest tests/test_trxasviewer.py::test_view_assets_importable -v
```

Expected: `PASSED`

- [ ] **Step 7: Verify CLI still imports**

```bash
python -c "from trxasviewer import main_gui, main_modeling_gui; print('ok')"
```

Expected: `ok`

- [ ] **Step 8: Commit**

```bash
git add -u
git commit -m "refactor: move view assets to gui/view/"
```

---

## Task 7: Create `gui/model/viewer_model.py`

**Files:**
- Create: `src/trxasviewer/gui/model/viewer_model.py`
- Test: `tests/test_trxasviewer.py`

- [ ] **Step 1: Write failing test**

```python
def test_viewer_model_signals(qtbot):
    from trxasviewer.gui.model.viewer_model import ViewerModel
    from pathlib import Path
    model = ViewerModel()
    received = []
    model.folder_changed.connect(lambda p: received.append(p))
    model.set_folder(Path("/tmp"))
    assert received == [Path("/tmp")]
```

(Requires `pytest-qt`. Install: `pip install pytest-qt` if not present.)

- [ ] **Step 2: Run test to confirm failure**

```bash
pytest tests/test_trxasviewer.py::test_viewer_model_signals -v
```

Expected: `FAILED` — `ModuleNotFoundError`

- [ ] **Step 3: Create `src/trxasviewer/gui/model/viewer_model.py`**

```python
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
```

- [ ] **Step 4: Run test**

```bash
pytest tests/test_trxasviewer.py::test_viewer_model_signals -v
```

Expected: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add src/trxasviewer/gui/model/viewer_model.py tests/test_trxasviewer.py
git commit -m "feat: add ViewerModel with state and signals"
```

---

## Task 8: Extract workers to `gui/control/workers.py`

Copy `AverageWorker` and `CacheWorker` from `trxasviewer_gui.py` to `gui/control/workers.py`. Fix their imports to use new core paths.

**Files:**
- Create: `src/trxasviewer/gui/control/workers.py`
- Modify: `trxasviewer_gui.py` (import workers from new location; remove class bodies)
- Test: `tests/test_trxasviewer.py`

- [ ] **Step 1: Write failing test**

```python
def test_workers_importable():
    from trxasviewer.gui.control.workers import AverageWorker, CacheWorker
    assert issubclass(AverageWorker, object)
    assert issubclass(CacheWorker, object)
```

- [ ] **Step 2: Run test to confirm failure**

```bash
pytest tests/test_trxasviewer.py::test_workers_importable -v
```

Expected: `FAILED`

- [ ] **Step 3: Create `src/trxasviewer/gui/control/workers.py`**

```python
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
```

Note: `_SignalLogHandler` is duplicated here from `gui/view/widgets.py`. Remove it from `widgets.py` if it was added there in Task 6, and import it from `workers.py` instead in both places — or keep the duplicate since it's a 10-line utility. Either is acceptable.

- [ ] **Step 4: Update `trxasviewer_gui.py` — import workers, remove class bodies**

Add at the top of `trxasviewer_gui.py`:
```python
from .gui.control.workers import AverageWorker, CacheWorker
```

Remove the `AverageWorker` and `CacheWorker` class definitions from `trxasviewer_gui.py` (lines 145–236 in the original file).

- [ ] **Step 5: Run test**

```bash
pytest tests/test_trxasviewer.py::test_workers_importable -v
```

Expected: `PASSED`

- [ ] **Step 6: Verify CLI still imports**

```bash
python -c "from trxasviewer import main_gui; print('ok')"
```

Expected: `ok`

- [ ] **Step 7: Commit**

```bash
git add src/trxasviewer/gui/control/workers.py tests/test_trxasviewer.py
git add -u
git commit -m "feat: extract AverageWorker and CacheWorker to gui/control/workers.py"
```

---

## Task 9: Create `gui/control/viewer_controller.py`

**Files:**
- Create: `src/trxasviewer/gui/control/viewer_controller.py`
- Test: `tests/test_trxasviewer.py`

- [ ] **Step 1: Write failing import test**

```python
def test_controller_importable():
    from trxasviewer.gui.control.viewer_controller import ViewerController
    assert callable(ViewerController)
```

- [ ] **Step 2: Run test to confirm failure**

```bash
pytest tests/test_trxasviewer.py::test_controller_importable -v
```

Expected: `FAILED`

- [ ] **Step 3: Create `src/trxasviewer/gui/control/viewer_controller.py`**

```python
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QThread

from trxasviewer.core.result import TrXASResult
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
        self._model.result_ready.connect(self._view.update_sync_timing)
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
        self._avg_worker.stop_worker.emit()
        self._thread.quit()
        self._thread.wait()
```

- [ ] **Step 4: Run test**

```bash
pytest tests/test_trxasviewer.py::test_controller_importable -v
```

Expected: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add src/trxasviewer/gui/control/viewer_controller.py tests/test_trxasviewer.py
git commit -m "feat: add ViewerController"
```

---

## Task 10: Create `gui/view/viewer_view.py` (refactor TrXASViewer)

The largest task. Rename `TrXASViewer` to `ViewerView`. Add view signals. Replace `process_flist()` with a signal. Move `get_*_kwargs()` methods to be called by the controller (they stay on the view as "widget state readers"). Remove direct core/ calls from the class body. Add display methods for controller to call via model signals.

**Files:**
- Create: `src/trxasviewer/gui/view/viewer_view.py`
- Modify: `trxasviewer_gui.py` (gut the file — only `main_gui` placeholder remains, updated in Task 11)
- Test: `tests/test_trxasviewer.py`

- [ ] **Step 1: Write failing import test**

```python
def test_viewer_view_importable():
    from trxasviewer.gui.view.viewer_view import ViewerView
    assert callable(ViewerView)
```

- [ ] **Step 2: Run test to confirm failure**

```bash
pytest tests/test_trxasviewer.py::test_viewer_view_importable -v
```

Expected: `FAILED`

- [ ] **Step 3: Create `src/trxasviewer/gui/view/viewer_view.py`**

Copy the full content of `trxasviewer_gui.py` to `viewer_view.py`, then make the following changes:

**3a. Update the import block at the top:**

```python
import os
import sys
import time
import json
import logging
import traceback
from pathlib import Path

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QDir, QThread, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QFileSystemModel
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QMainWindow,
    QSortFilterProxyModel,
)

from trxasviewer import __version__
from trxasviewer.core.utilities import format_time
from trxasviewer.core.dataset import CACHE_PATH
from trxasviewer.gui.view.generated_ui import Ui_MainWindow
from trxasviewer.gui.view.widgets import (
    VlockedRectROI,
    SaveOptionsDialog,
    DatasetFilterModel,
    show_error_dialog,
    show_warning_dialog,
)
from trxasviewer.gui.view.pg_plot import plot_kinetics_profile, plot_kinetics_error
```

**3b. Rename the class and add view signals:**

```python
PGCOLORS = ("r", "b", "k", "m", "g", "m", "y")
PGSYMBOLS = ("o", "s", "t", "d", "+", "*", "x", "p", "h")

pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")
pg.setConfigOptions(antialias=True)
pg.setConfigOptions(imageAxisOrder="row-major")


class ViewerView(QMainWindow, Ui_MainWindow):
    # Signals emitted by the view for controller to handle
    folder_selected = Signal(Path)
    files_selected = Signal(list)
    replot_requested = Signal()
    save_requested = Signal(dict)
```

**3c. Update `__init__` signature and remove worker/thread setup:**

```python
    def __init__(self, syncbunch=None, autoload=False, parent=None):
        super().__init__()
        self.setupUi(self)
        self.image = None
        self.results = None
        self.last_position = None
        self.roi = None
        self.dtype_db = None
        self.kinetics_roi = {}
        self.is_processing = False
        self.modeler = None
        self.setWindowTitle(f"TrXASViewer v{__version__}")

        self.setup_imageview()
        self.update_colormap()
        self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath(QDir.homePath())
        self.proxy_model = DatasetFilterModel()
        self.proxy_model.setSourceModel(self.fs_model)
        self.treeView_fs.setModel(self.proxy_model)
        self.treeView_fs.setColumnWidth(0, 200)
        self.treeView_fs.setSortingEnabled(True)

        # Widget → Signal connections
        self.pushButton_select_rawfolder.clicked.connect(self._on_folder_button_clicked)
        self.treeView_fs.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.comboBox_cmap.currentIndexChanged.connect(self.update_colormap)
        self.spinBox_roix.valueChanged.connect(self.update_roi)
        self.spinBox_roiy.valueChanged.connect(self.update_roi)
        self.comboBox_channel_num.currentIndexChanged.connect(self.replot_requested.emit)
        self.comboBox_target.currentIndexChanged.connect(self.replot_requested.emit)
        self.pushButton_replot.clicked.connect(self.replot_requested.emit)
        self.pushButton_select_savefname.clicked.connect(self._on_save_clicked)
        self.comboBox_fileindex_prefix.currentIndexChanged.connect(self.update_fileindex)
        self.toolButton_refresh.clicked.connect(self.reload_rawfolder)
        self.spinBox_syncbunch_number.valueChanged.connect(self._on_sync_param_changed)
        self.doubleSpinBox_sync_time_us.valueChanged.connect(self._on_sync_param_changed)
        self.radioButton_sync_time.toggled.connect(self._on_sync_param_changed)
        self.pushButton_select_savefname.setDisabled(True)
        self.comboBox_groundstate_method.currentIndexChanged.connect(self.update_groundstate_label)
        self.pushButton_model.clicked.connect(self._on_model_button_clicked)

        for n in range(5):
            def callback(index=n):
                self.update_binning_params(index=index)
            self.__dict__[f"spinBox_anchor{n}"].editingFinished.connect(callback)
            self.__dict__[f"spinBox_numb{n}"].editingFinished.connect(callback)

        self.setup_tooltips()

        if autoload:
            self.save_load_settings(mode="load")
        if syncbunch:
            self.spinBox_syncbunch_number.setValue(syncbunch)
        self.update_kinetics_signal()

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.refresh_filesystem)
        self.timer.start()
```

**3d. Add the new public display methods (called by controller via model signals):**

```python
    # --- Display methods (called by controller) ---

    def update_image(self, results: dict):
        """Update the 2D image view with new results."""
        if results is None:
            return
        if results.get("target") == "normalized-GS":
            self.pushButton_select_savefname.setEnabled(True)
        else:
            self.pushButton_select_savefname.setEnabled(False)
        self.results = results
        data = self.results["diff"].T
        if self.image is None or data.shape != self.image.shape:
            if self.roi is not None:
                self.pg_hdl_img2d.removeItem(self.roi)
                self.roi = None
            self.spinBox_roix.setValue(data.shape[1] // 10)
            self.spinBox_roiy.setValue(data.shape[0] // 10)
        if self.comboBox_target.currentText() == "normalized-GS":
            vmin, vmax = np.nanpercentile(data.ravel(), [0.2, 99.8])
            vmax = max(abs(vmax), abs(vmin))
            vmin = -vmax
        else:
            vmin, vmax = np.nanpercentile(data.ravel(), [0, 100])
        self.image, prev_image = np.flipud(data), self.image
        self.pg_hdl_img2d.setImage(self.image, levels=(vmin, vmax))
        if (
            prev_image is None
            or prev_image.shape[0] != self.image.shape[0]
            or self.results["dset_type"] != "EXAFS"
        ):
            self.remove_kinetics_ROIs()
        if not self.kinetics_roi:
            self.create_kinetics_ROIs()
        self.mouse_clicked()

    def update_kinetics(self, results: dict):
        """Update the kinetics plot with new results."""
        if not results or not results.get("kinetics"):
            return
        use_errorbar = self.checkBox_kinetics_errorbar.isChecked()
        plot_kinetics_profile(results, self.pg_hdl_kinetics, use_errorbar=use_errorbar)
        plot_kinetics_error(results, self.pg_hdl_kinetics_err)

    def update_sync_timing(self, results: dict):
        """Update sync timing group box title from results."""
        if results is None:
            return
        bunch_mode = results["bunch_mode"]
        dt_ns = results["delta_t_s"] * 1e9
        self.groupBox_timing.setTitle(
            f"Sync Timing: [{bunch_mode}-bunch]:[{dt_ns:.3f} ns]"
        )

    def clear_display(self):
        """Clear image and kinetics when result is invalidated."""
        self.image = None
        self.results = None

    def set_loading(self, loading: bool):
        self.is_processing = loading
        self.pushButton_replot.setText("Processing..." if loading else "Process")
        self.pushButton_replot.setDisabled(loading)

    def update_progress_bar(self, value: int):
        self.progressBar.setValue(value)

    def update_status(self, msg: str, timeout: int = 5000):
        self.statusBar().showMessage(msg, timeout)

    def show_error(self, title: str, message: str):
        show_error_dialog(self, title, message)

    def show_warning(self, title: str, message: str):
        show_warning_dialog(self, title, message)
        self.update_status(message, timeout=8000)

    def update_folder_ui(self, path: Path, combos: list, dtype_db):
        """Update folder-related widgets (called by controller after folder is set)."""
        self.lineEdit_rawfolder.setText(str(path))
        self.dtype_db = dtype_db
        self.proxy_model.update_cache_db(dtype_db)
        self.comboBox_fileindex_prefix.clear()
        self.comboBox_fileindex_prefix.addItems(combos)
        self.comboBox_fileindex_prefix.setCurrentIndex(0)
        new_index = self.fs_model.setRootPath(str(path))
        proxy_new_root = self.proxy_model.mapFromSource(new_index)
        self.treeView_fs.setRootIndex(proxy_new_root)
        self.treeView_fs.sortByColumn(0, Qt.AscendingOrder)
```

**3e. Add widget-state reader methods (called by controller):**

Keep `get_preprocessing_kwargs()`, `get_normalization_subgs_kwargs()`, `get_kinetics_kwargs()`, `get_binning_kwargs()` exactly as they are in `TrXASViewer` — they just read widget values and return dicts. Also add:

```python
    def get_channel(self) -> int:
        return int(self.comboBox_channel_num.currentText())

    def get_target(self) -> str:
        return self.comboBox_target.currentText()
```

**3f. Add private signal-emitting slots (called by widget signals):**

```python
    def _on_folder_button_clicked(self, placeholder=None):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder_path:
            self.folder_selected.emit(Path(folder_path))

    def _on_selection_changed(self, selected, deselected):
        if not self.radioButton_selection_by_mouse.isChecked():
            return
        indexes = self.treeView_fs.selectionModel().selectedIndexes()
        file_paths = []
        for proxy_index in indexes:
            if proxy_index.column() != 0:
                continue
            source_index = self.proxy_model.mapToSource(proxy_index)
            if source_index.isValid():
                file_paths.append(self.fs_model.filePath(source_index))
        self.files_selected.emit(file_paths)

    def _on_save_clicked(self):
        if self.is_processing or self.results is None:
            self.update_status("No data to save.", 3000)
            return
        prefix = self.results["label"]
        dialog = SaveOptionsDialog(parent=self, prefix=prefix)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            self.save_requested.emit(dialog.get_selected_options())

    def _on_model_button_clicked(self):
        # Modeler window management stays in view for now; pass result via signal in future
        from trxasviewer.modeling_gui.trxas_modeling import TrXASModeler
        from trxasviewer.core.result import TrXASResult
        if self.modeler is None:
            self.modeler = TrXASModeler()
            self.modeler.closed.connect(self._on_modeler_closed)
            self.modeler.show()
        else:
            self.modeler.raise_()
            self.modeler.activateWindow()
        if self.results is not None:
            res_dset = TrXASResult(self.results)
            self.modeler.select_dataset(res_dset)

    def _on_modeler_closed(self):
        self.modeler = None

    def _on_sync_param_changed(self):
        self.replot_requested.emit()
```

**3g. Update `closeEvent`:**

```python
    def closeEvent(self, event):
        if self.is_processing:
            return
        if hasattr(self, '_controller'):
            self._controller.shutdown()
        if self.auto_save_load:
            self.save_load_settings(mode="save")
        event.accept()
```

**3h. Remove from `ViewerView`** the following methods (they moved to the controller):
- `process_flist()` — replaced by `_on_selection_changed()` emitting `files_selected`
- `build_cache()` — moved to `ViewerController._build_cache()`
- `select_rawfolder()` — replaced by `_on_folder_button_clicked()`
- `send_result_to_modeler()` — replaced by `_on_model_button_clicked()`

**3i. Remove from `ViewerView`** the worker/thread setup that was in `__init__` (the `self.thread`, `self.avg_worker`, `self.avg_worker.progress.connect(...)` block — all of that is now in the controller).

- [ ] **Step 4: Run test**

```bash
pytest tests/test_trxasviewer.py::test_viewer_view_importable -v
```

Expected: `PASSED`

- [ ] **Step 5: Commit**

```bash
git add src/trxasviewer/gui/view/viewer_view.py tests/test_trxasviewer.py
git commit -m "feat: add ViewerView (slim TrXASViewer without core calls)"
```

---

## Task 11: Wire `__init__.py`, `cli.py`, and `main_gui`

Update the entry points to instantiate `ViewerModel`, `ViewerView`, and `ViewerController`. Remove the now-gutted `trxasviewer_gui.py` from the package.

**Files:**
- Modify: `src/trxasviewer/__init__.py`
- Modify: `src/trxasviewer/cli.py`
- Modify (or delete): `src/trxasviewer/trxasviewer_gui.py` — remove, replace with a compatibility shim or delete

- [ ] **Step 1: Update `src/trxasviewer/__init__.py`**

```python
"""Top-level package for TrXASViewer."""

from importlib.metadata import version, PackageNotFoundError

__author__ = "Miaoqi Chu"
__email__ = "mqichu@anl.gov"

try:
    __version__ = version("trxasviewer")
except PackageNotFoundError:
    __version__ = "0.1.0"

from .gui.view.viewer_view import main_gui
from .modeling_gui.trxas_modeling import main_modeling_gui
from .core.dataset import TrXASDataset

__all__ = ["main_gui", "TrXASDataset", "main_modeling_gui"]
```

- [ ] **Step 2: Move `main_gui()` function to `gui/view/viewer_view.py`**

At the bottom of `gui/view/viewer_view.py`, add:

```python
def main_gui(rawfolder=None, syncbunch=None, autoload=True, reset_cache=False, use_cache=False):
    from PySide6.QtWidgets import QApplication
    from trxasviewer.gui.model.viewer_model import ViewerModel
    from trxasviewer.gui.control.viewer_controller import ViewerController

    app = QApplication.instance() or QApplication(sys.argv)
    model = ViewerModel(reset_cache=reset_cache, use_cache=use_cache)
    view = ViewerView(syncbunch=syncbunch, autoload=autoload)
    controller = ViewerController(model, view)
    view._controller = controller  # so closeEvent can call controller.shutdown()
    if rawfolder:
        controller.on_folder_selected(Path(rawfolder))
    view.show()
    return app.exec()
```

- [ ] **Step 3: Delete `trxasviewer_gui.py`**

```bash
git rm src/trxasviewer/trxasviewer_gui.py
```

- [ ] **Step 4: Verify `cli.py` still works — no changes needed**

`cli.py` imports from `trxasviewer` (the package), not from `trxasviewer_gui` directly. Verify:

```bash
python -c "from trxasviewer.cli import main; print('ok')"
```

Expected: `ok`

- [ ] **Step 5: Run all tests**

```bash
pytest tests/ -v
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add -u src/trxasviewer/__init__.py src/trxasviewer/gui/view/viewer_view.py
git add -u
git commit -m "feat: wire MVC entry point in main_gui; remove trxasviewer_gui.py"
```

---

## Task 12: Integration smoke test

Verify the refactored viewer launches without errors using the test dataset.

**Files:**
- No code changes

- [ ] **Step 1: Activate the conda environment**

```bash
conda activate /home/beams/MQICHU/miniforge3/envs/d2602_trxasviewer
```

- [ ] **Step 2: Install in editable mode**

```bash
pip install -e ".[dev]"
```

- [ ] **Step 3: Run the viewer**

```bash
trxasviewer view --rawfolder /home/beams/MQICHU/Datasets/trxas_datasets/Dugan_2024_3_saveddata --syncbunch 4334
```

Expected: GUI opens without tracebacks. File browser shows dataset files. Selecting files triggers processing. Image and kinetics plots update.

- [ ] **Step 4: Run the modeler**

```bash
trxasviewer model
```

Expected: Modeling GUI opens without errors.

- [ ] **Step 5: Run linter**

```bash
ruff check src/
```

Expected: no errors (fix any that appear before declaring done).

- [ ] **Step 6: Run tests**

```bash
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 7: Final commit**

```bash
git add -u
git commit -m "chore: post-refactor lint and test cleanup"
```

---

## Self-Review Notes

- **Task 5, Step 4**: The modeling GUI imports `pg_plot` and `widgets` from `gui/view/` which doesn't exist until Task 6. The plan handles this with a temporary import swap explained in that step.
- **`_SignalLogHandler`**: Appears in both `workers.py` (new) and was in `widgets.py` (old, removed in Task 6). The version in `workers.py` is authoritative; `widgets.py` no longer needs it.
- **`self.model` rename**: `TrXASViewer.__init__` used `self.model` for `QFileSystemModel`. In `ViewerView`, this is renamed to `self.fs_model` to avoid collision with any future `self.model` reference (Task 10, Step 3c).
- **`auto_save_load`**: In `ViewerView.__init__`, `autoload` parameter maps to `self.auto_save_load` — keep this attribute assignment when copying from `TrXASViewer`.
- **`process_range()`**: This method reads `self.dtype_db` from view state and emits `files_selected`. Keep it in `ViewerView` connected to the appropriate radio button — it calls `self.files_selected.emit(file_paths)` instead of `self.process_flist(file_paths)`.
