# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import runpy
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
ENTRYPOINT = REPO_ROOT / "packaging" / "entrypoint.py"


def test_entrypoint_calls_freeze_support_then_main():
    calls = []
    with patch(
        "multiprocessing.freeze_support",
        side_effect=lambda: calls.append("freeze_support"),
    ), patch(
        "trxasviewer.cli.main",
        side_effect=lambda: calls.append("main"),
    ):
        runpy.run_path(str(ENTRYPOINT), run_name="__main__")

    assert calls == ["freeze_support", "main"]
