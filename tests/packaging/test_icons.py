# Copyright © UChicago Argonne LLC
# See LICENSE file for details
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_icon_png_exists_and_is_square():
    icon_png = REPO_ROOT / "packaging" / "icon.png"
    assert icon_png.exists()
    with Image.open(icon_png) as im:
        width, height = im.size
        assert width == height
        assert width >= 256


def test_icon_ico_contains_multiple_resolutions():
    icon_ico = REPO_ROOT / "packaging" / "icon.ico"
    assert icon_ico.exists()
    with Image.open(icon_ico) as im:
        sizes = set(im.info.get("sizes", []))
        assert (16, 16) in sizes
        assert (32, 32) in sizes
        assert (256, 256) in sizes
