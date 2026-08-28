# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import numpy as np
import pytest
from trxasviewer.core.graph import (
    verify_decay_paths,
    draw_decay_graph_with_top_nodes,
    _compute_levels_and_edges,
    _order_by_barycenter,
    _count_crossings,
)


@pytest.fixture
def sequential_adj():
    # S1 -> S2 -> GS
    return np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=float)


@pytest.fixture
def parallel_adj():
    # S1 -> GS and S2 -> GS (both initial states decay directly to ground state)
    return np.array([[0, 0, 0], [0, 0, 0], [1, 1, 0]], dtype=float)


@pytest.fixture
def broken_adj():
    # S1 and S2 have self-loops but no path to GS (index 2)
    return np.array([[1, 0, 0], [0, 1, 0], [0, 0, 0]], dtype=float)


@pytest.fixture
def branchy_adj():
    # Two independent top states whose children interleave under naive
    # alphabetical ordering: S1 -> S3, S5 ; S2 -> S4, S6 ; all -> GS
    #                     S1 S2 S3 S4 S5 S6 GS
    return np.array([
        [1, 0, 0, 0, 0, 0, 0],  # S1
        [0, 1, 0, 0, 0, 0, 0],  # S2
        [1, 0, 1, 0, 0, 0, 0],  # S3 <- S1
        [0, 1, 0, 1, 0, 0, 0],  # S4 <- S2
        [1, 0, 0, 0, 1, 0, 0],  # S5 <- S1
        [0, 1, 0, 0, 0, 1, 0],  # S6 <- S2
        [0, 0, 1, 1, 1, 1, 1],  # GS <- S3, S4, S5, S6
    ], dtype=float)


def test_verify_valid_sequential(sequential_adj):
    flag, msg = verify_decay_paths(sequential_adj)
    assert flag
    assert msg is None


def test_verify_valid_parallel(parallel_adj):
    flag, msg = verify_decay_paths(parallel_adj)
    assert flag


def test_verify_invalid(broken_adj):
    flag, msg = verify_decay_paths(broken_adj)
    assert not flag
    assert msg is not None


def test_draw_graph_returns_png_bytes(sequential_adj):
    flag, result = draw_decay_graph_with_top_nodes(sequential_adj, output="bytes")
    assert flag
    assert isinstance(result, bytes)
    assert result[:4] == b"\x89PNG" or result[:2] == b"\x89P"


def test_draw_graph_invalid_returns_error(broken_adj):
    flag, result = draw_decay_graph_with_top_nodes(broken_adj, output="bytes")
    assert not flag
    assert isinstance(result, str)


def test_draw_graph_file_output(tmp_path, sequential_adj):
    out_stem = str(tmp_path / "decay_graph")
    flag, result = draw_decay_graph_with_top_nodes(sequential_adj, filename=out_stem, output="file")
    assert flag
    assert result == out_stem + ".png"

    written = tmp_path / "decay_graph.png"
    assert written.exists()
    assert written.read_bytes()[:4] == b"\x89PNG"


def test_barycenter_reduces_crossings(branchy_adj):
    top_nodes, edges, by_level, max_level = _compute_levels_and_edges(branchy_adj)

    naive_order = {lvl: sorted(by_level[lvl]) for lvl in range(max_level + 1)}
    optimized_order = _order_by_barycenter(by_level, edges, max_level)

    naive_crossings = _count_crossings(naive_order, edges, max_level)
    optimized_crossings = _count_crossings(optimized_order, edges, max_level)

    # Naive alphabetical order interleaves S1's children (S3, S5) with
    # S2's children (S4, S6), producing a crossing the barycenter sweep
    # should resolve by grouping each parent's children together.
    assert naive_crossings > 0
    assert optimized_crossings == 0
    assert optimized_crossings < naive_crossings

    # Every level should retain exactly its original members after reordering.
    for lvl in range(max_level + 1):
        assert sorted(optimized_order[lvl]) == sorted(by_level[lvl])
