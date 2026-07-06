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
