# Copyright © UChicago Argonne LLC
# See LICENSE file for details

"""Tests for ViewerController folder-loading behavior."""
from pathlib import Path
from unittest.mock import MagicMock

from trxasviewer.gui.control.viewer_controller import ViewerController
from trxasviewer.gui.model.viewer_model import ViewerModel


def _write_scan_file(path: Path, index: int = 65) -> None:
    lines = [
        f"#F /some/path/setup-full-{index:05d}\n",
        "#E 1739341861\n",
        "#D Wed Feb 12 00:31:01 2025\n",
        "\n",
        "\n",
        f"#S {index} exafs_scan Energy 7000 8000 200\n",
        "#N 3\n",
        "#L Energy c0o0b0 c1o0b0\n",
        "7000 1 1\n",
        "7001 1 1\n",
        "7002 1 1\n",
        "7003 1 1\n",
    ]
    path.write_text("".join(lines))


def test_on_folder_selected_resolves_relative_path(qtbot, tmp_path, monkeypatch):
    """A relative --rawfolder path must be resolved to an absolute path.

    QFileSystemModel.filePath() always returns canonicalized absolute paths,
    so a relative (or symlink-containing) root leaves DatasetFilterModel's
    type_db keyed differently from what the tree view queries — the root
    index then fails to map and the tree renders empty (see
    DatasetFilterModel.set_root_path's docstring).
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_scan_file(data_dir / "setup-full-00065")

    monkeypatch.chdir(tmp_path)

    model = ViewerModel()
    view = MagicMock()
    controller = ViewerController(model, view)
    try:
        controller.on_folder_selected(Path("data"))

        view.update_folder_ui.assert_called_once()
        resolved_path, combos, folder_index = view.update_folder_ui.call_args.args

        assert resolved_path.is_absolute()
        assert resolved_path == data_dir.resolve()
        assert combos == ["setup-full-@exafs"]
        assert folder_index.type_db
        for key in folder_index.type_db:
            assert Path(key).is_absolute()
    finally:
        controller.shutdown()
