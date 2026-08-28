===========
TrXASViewer
===========

.. image:: https://img.shields.io/pypi/v/trxasviewer.svg
        :target: https://pypi.python.org/pypi/trxasviewer

A PySide6 GUI for visualizing and analyzing **Time-Resolved X-ray Absorption
Spectroscopy (TrXAS)** datasets collected at synchrotron light sources such as
the Advanced Photon Source (APS).

* Free software: Apache Software License 2.0
* Source: https://github.com/AdvancedPhotonSource/trxasviewer


Features
--------

**Viewer GUI** (``trxasviewer view``)

* File browser for SPEC-format raw TrXAS scan files with live detection of new
  scans during acquisition (NFS-safe polling)
* Interactive 2-D energy–time difference map with crosshair line-cuts and
  zoom-in ROI
* Flexible time-binning: linear, logarithmic, or manual multi-level binning
* Ground-state subtraction: bunch-average or orbital-average methods
* Kinetics extraction: up to four user-defined energy ROIs with interactive
  drag handles on the 2-D map, ±1σ error bars from scan-to-scan variance
* Outlier removal: median absolute deviation (MAD) or standard deviation
* Multiple output formats: NumPy NPZ, HDF5, OriginLab CSV, PNG/PDF plots
* Background saving thread — GUI stays responsive during export

**Modeler GUI** (``trxasviewer model``)

* Load kinetics traces exported from the viewer
* Build arbitrary multi-state kinetic models via an adjacency matrix
* ODE-based rate-equation fitting with ``scipy.optimize``
* Parallel multi-start optimization for robust global minimum search
* SVD decomposition of the difference map


Installation
------------

.. code-block:: bash

    pip install trxasviewer


Usage
-----

.. code-block:: bash

    # Open viewer with a raw data folder
    trxasviewer view --rawfolder /path/to/data --syncbunch 1820

    # Open the kinetic modeler
    trxasviewer model

    # Use a dedicated NPZ cache folder for faster repeated loading
    trxasviewer view --rawfolder /path/to/data --cachefolder /path/to/cache

See ``trxasviewer view --help`` for the full list of options.


Scripting / Jupyter
-------------------

The ``trxasviewer.core`` module is fully Qt-free and can be imported in
plain Python scripts or Jupyter notebooks without launching the GUI:

.. code-block:: python

    from trxasviewer.core import TrXASDataset, TrXASDatasetManager, save_results

    dset = TrXASDataset("/path/to/setup-full-00178")
    results = dset.get_energy_vs_time(
        target="normalized-GS",
        norm_kwargs={"sync_type": "bunch", "sync_value": 1820,
                     "gs_method": "bunch-average", "gs_value": 5},
        binning_kwargs={"method": "Linear", "lin_num": 5},
    )
    print(results["diff"].shape)   # (n_energy, n_time)

A full worked example covering single-file loading, multi-file averaging,
SVD, plotting, and saving is in ``examples/analyze_trxas.py``.


Development
-----------

.. code-block:: bash

    git clone https://github.com/AdvancedPhotonSource/trxasviewer
    cd trxasviewer
    pip install -e ".[dev]"
    pytest tests/
    ruff check src/
