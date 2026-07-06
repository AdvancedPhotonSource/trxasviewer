#!/usr/bin/env python

"""Tests for `trxasviewer` package."""


import unittest

from trxasviewer import trxasviewer_gui


class TestTrxasviewer(unittest.TestCase):
    """Tests for `trxasviewer` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_something(self):
        """Test something."""


def test_core_modules_importable():
    from trxasviewer.core import constants, utilities, dtype_cache, fitting, graph
    assert hasattr(constants, "TIME_SCALES")
    assert hasattr(utilities, "format_time")
    assert hasattr(dtype_cache, "DataTypeCache")
    assert hasattr(fitting, "global_fit_kinetic_model")
    assert hasattr(graph, "draw_decay_graph_with_top_nodes")


def test_io_importable():
    from trxasviewer.core.io import save_as_hdf5, save_as_json, save_as_origin_format, save_results
    assert callable(save_as_hdf5)
    assert callable(save_as_json)
    assert callable(save_as_origin_format)
    assert callable(save_results)


def test_result_importable():
    from trxasviewer.core.result import TrXASResult, convert_npz_obj, get_levels
    assert callable(TrXASResult)


def test_view_assets_importable():
    from trxasviewer.gui.view.generated_ui import Ui_MainWindow
    from trxasviewer.gui.view.widgets import (
        VlockedRectROI, SaveOptionsDialog, DatasetFilterModel, _SignalLogHandler
    )
    from trxasviewer.gui.view.pg_plot import plot_kinetics_profile, plot_kinetics_error
    assert callable(plot_kinetics_profile)


def test_viewer_model_signals(qtbot):
    from trxasviewer.gui.model.viewer_model import ViewerModel
    from pathlib import Path
    model = ViewerModel()
    received = []
    model.folder_changed.connect(lambda p: received.append(p))
    model.set_folder(Path("/tmp"))
    assert received == [Path("/tmp")]


def test_workers_importable():
    from trxasviewer.gui.control.workers import AverageWorker, CacheWorker
    assert issubclass(AverageWorker, object)
    assert issubclass(CacheWorker, object)


def test_controller_importable():
    from trxasviewer.gui.control.viewer_controller import ViewerController
    assert callable(ViewerController)
