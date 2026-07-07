===========
TrXASViewer
===========

.. image:: https://img.shields.io/pypi/v/trxasviewer.svg
        :target: https://pypi.python.org/pypi/trxasviewer

A PySide6 GUI for visualizing and analyzing **Time-Resolved X-ray Absorption
Spectroscopy (TrXAS)** datasets collected at synchrotron light sources such as
the Advanced Photon Source (APS).

* Free software: MIT license
* Source: https://github.com/AZjk/trxasviewer


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

The ``graphviz`` Python package requires the Graphviz binaries to be installed
separately (``apt install graphviz`` / ``brew install graphviz`` / conda).


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


Development
-----------

.. code-block:: bash

    git clone https://github.com/AZjk/trxasviewer
    cd trxasviewer
    pip install -e ".[dev]"
    pytest tests/
    ruff check src/
