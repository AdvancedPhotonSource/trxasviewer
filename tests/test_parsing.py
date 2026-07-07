import pytest
from trxasviewer.core.file_io import _classify_scan_header
from trxasviewer.core.dataset import _parse_header_line


def test_classify_exafs():
    assert _classify_scan_header("#S 1 exafs_scan Energy 7000 8000 200\n") == "exafs"


def test_classify_exafsscan_no_underscore():
    assert _classify_scan_header("#S 1 exafsscan Energy\n") == "exafs"


def test_classify_laserd():
    assert _classify_scan_header("#S 2 rscan laserd 0 100 100\n") == "laserd"


def test_classify_dutd():
    assert _classify_scan_header("#S 3 tscan dutd 0 100\n") == "laserd"


def test_classify_invalid():
    assert _classify_scan_header("# just a comment\n") == "invalid"
    assert _classify_scan_header("#S 1 unknown_scan_type\n") == "invalid"


def test_parse_header_line_exafs():
    # Minimal EXAFS header with Energy keyword and XAS columns
    header = "#L N  Epoch  Energy  H  K  c0o0b0  c0o0b1  c1o0b0  c1o0b1  c2o0b0  c2o0b1\n"
    dset_type, shape, labels, labels_mask, is_double = _parse_header_line(header)
    assert dset_type == "EXAFS"
    assert shape[0] == 3   # 3 channels
    assert not is_double


def test_parse_header_line_laserd():
    header = "#L N  Epoch  laserd  H  K  c0o0b0  c0o0b1  c1o0b0  c1o0b1  c2o0b0  c2o0b1\n"
    dset_type, shape, labels, labels_mask, is_double = _parse_header_line(header)
    assert dset_type == "LASERD"
    assert shape[0] == 3
