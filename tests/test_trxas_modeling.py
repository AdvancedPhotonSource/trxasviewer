# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import io
from unittest.mock import MagicMock

import matplotlib.pyplot as plt
import pytest

import trxasviewer.modeling_gui.trxas_modeling as trxas_modeling
from trxasviewer.modeling_gui.trxas_modeling import TrXASModeler

SEQUENTIAL_ADJ = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]  # S1 -> S2 -> GS


def _tiny_png_bytes():
    fig = plt.figure(figsize=(1, 1))
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    return buf.getvalue()


@pytest.fixture
def modeler(qtbot):
    window = TrXASModeler()
    qtbot.addWidget(window)
    # __init__ already triggers one real graphviz-availability check via
    # change_model() -> draw_graph(); reset it so each test controls its own
    # "first render of the session" scenario independent of this machine's
    # actual graphviz install.
    window._graphviz_checked = False
    window._graphviz_available = False
    return window


def test_render_uses_graphviz_when_available(modeler, monkeypatch):
    monkeypatch.setattr(trxas_modeling, "is_graphviz_available", lambda: True)
    graphviz_spy = MagicMock(return_value=(True, _tiny_png_bytes()))
    monkeypatch.setattr(trxas_modeling, "render_decay_graph_graphviz", graphviz_spy)
    matplotlib_spy = MagicMock(return_value=(True, None))
    monkeypatch.setattr(trxas_modeling, "render_decay_graph", matplotlib_spy)

    flag, msg = modeler._render_decay_diagram(SEQUENTIAL_ADJ)

    assert flag
    graphviz_spy.assert_called_once_with(SEQUENTIAL_ADJ)
    matplotlib_spy.assert_not_called()


def test_render_falls_back_to_matplotlib_when_graphviz_missing(modeler, monkeypatch):
    monkeypatch.setattr(trxas_modeling, "is_graphviz_available", lambda: False)
    matplotlib_spy = MagicMock(return_value=(True, None))
    monkeypatch.setattr(trxas_modeling, "render_decay_graph", matplotlib_spy)
    warn_spy = MagicMock()
    monkeypatch.setattr(trxas_modeling, "show_warning_dialog", warn_spy)

    flag, msg = modeler._render_decay_diagram(SEQUENTIAL_ADJ)

    assert flag
    matplotlib_spy.assert_called_once()
    warn_spy.assert_called_once()


def test_missing_graphviz_dialog_shown_only_once_per_session(modeler, monkeypatch):
    availability_spy = MagicMock(return_value=False)
    monkeypatch.setattr(trxas_modeling, "is_graphviz_available", availability_spy)
    monkeypatch.setattr(trxas_modeling, "render_decay_graph", MagicMock(return_value=(True, None)))
    warn_spy = MagicMock()
    monkeypatch.setattr(trxas_modeling, "show_warning_dialog", warn_spy)

    modeler._render_decay_diagram(SEQUENTIAL_ADJ)
    modeler._render_decay_diagram(SEQUENTIAL_ADJ)

    availability_spy.assert_called_once()
    warn_spy.assert_called_once()


def test_render_falls_back_to_matplotlib_when_graphviz_render_raises(modeler, monkeypatch):
    monkeypatch.setattr(trxas_modeling, "is_graphviz_available", lambda: True)
    monkeypatch.setattr(
        trxas_modeling, "render_decay_graph_graphviz", MagicMock(side_effect=RuntimeError("dot crashed"))
    )
    matplotlib_spy = MagicMock(return_value=(True, None))
    monkeypatch.setattr(trxas_modeling, "render_decay_graph", matplotlib_spy)

    flag, msg = modeler._render_decay_diagram(SEQUENTIAL_ADJ)

    assert flag
    matplotlib_spy.assert_called_once()


@pytest.mark.parametrize(
    "system_name,expected_snippet",
    [
        ("Darwin", "brew install graphviz"),
        ("Linux", "apt install graphviz"),
        ("Windows", "graphviz.org"),
    ],
)
def test_graphviz_missing_dialog_is_platform_specific(modeler, monkeypatch, system_name, expected_snippet):
    monkeypatch.setattr(trxas_modeling, "is_graphviz_available", lambda: False)
    monkeypatch.setattr(trxas_modeling, "render_decay_graph", MagicMock(return_value=(True, None)))
    monkeypatch.setattr(trxas_modeling.platform, "system", lambda: system_name)
    warn_spy = MagicMock()
    monkeypatch.setattr(trxas_modeling, "show_warning_dialog", warn_spy)

    modeler._render_decay_diagram(SEQUENTIAL_ADJ)

    message = warn_spy.call_args.kwargs["message"]
    assert expected_snippet in message
