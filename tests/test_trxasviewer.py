#!/usr/bin/env python
# Copyright © UChicago Argonne LLC
# See LICENSE file for details

"""Tests for `trxasviewer` package."""


def test_core_modules_importable():
    from trxasviewer.core import constants, utilities, fitting, graph
    from trxasviewer.core.array_ops import preprocess_xas_data
    from trxasviewer.core.file_io import get_scan_type, FolderIndex, scan_data_folder
    from trxasviewer.core.utilities import format_time
    from trxasviewer.core.fitting import create_initial_state_array
    assert hasattr(constants, "TIME_SCALES")
    assert hasattr(utilities, "format_time")
    assert callable(scan_data_folder)
    assert callable(preprocess_xas_data)
    assert callable(create_initial_state_array)
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


def test_viewer_view_importable():
    from trxasviewer.gui.view.viewer_view import ViewerView
    assert callable(ViewerView)
