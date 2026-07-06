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
