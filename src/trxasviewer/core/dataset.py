import json
import re
import time
from functools import lru_cache
from pathlib import Path
import numpy as np
import logging
import datetime
import traceback
from .utilities import prepare_binning_matrix
from .array_ops import preprocess_xas_data, pad_last_dim
from .file_io import is_recently_modified


logger = logging.getLogger(__name__)

TRXAS_PATTERN = re.compile(r"c(\d+)o(\d+)b(\d+)")
P0 = 352055282.000000 / 1296  # RF frequency in Hz / number of bucket
# Each orbital has 1296 bunket, so the maximum bunch mode can be 1296
# at the APS, the RF frequency can be read from
# caget A014-IETS:BTC:CFG:SRNomFreqM -f8 -a
# A014-IETS:BTC:CFG:SRNomFreqM   2025-11-11 13:15:24.536419 352055282.00000000


CACHE_PATH = "trxasviewer_cache"


def get_scan_type_from_header(header_line):
    """
    Determines the scan type from a header line.

    - If the header contains "Energy", returns "exafs".
    - If the header contains "laserd", returns "laserd".
    - Otherwise, returns "invalid".
    """
    header = header_line[3:128]
    if re.match(r".* Energy ", header):
        return "EXAFS"
    elif re.match(r".* laserd ", header) or re.match(r".* dutd ", header):
        return "LASERD"
    else:
        return "INVALID"


def _parse_header_line(header_line: str, is_double: bool = False):
    """Pure: parse an ``#L`` header line into dataset metadata.

    Parameters
    ----------
    header_line : str
        The raw ``#L ...`` header line (including the ``#L`` prefix).
    is_double : bool
        Whether the file uses double-length acquisition mode.

    Returns
    -------
    dset_type : str
        ``"EXAFS"`` or ``"LASERD"``.
    shape : list of int
        ``[num_channels, num_orbitals, num_bunches]``.
    labels : list of str
        Column labels with XAS payload columns removed.
    labels_mask : numpy.ndarray
        Boolean mask — ``True`` for metadata columns, ``False`` for XAS columns.
    is_double : bool
        Echoes back the ``is_double`` argument (for caller convenience).
    """
    dset_type = get_scan_type_from_header(header_line)

    header = header_line[3:].strip()
    labels = header.split()
    if dset_type == "LASERD" and "dutd" in labels:
        index = labels.index("dutd")
        labels[index] = "laserd"

    labels_mask = np.ones(len(labels), dtype=bool)
    record = []
    matches = [TRXAS_PATTERN.match(col) for col in labels]
    for index, match in enumerate(matches):
        if match:
            labels_mask[index] = False
            record.append(tuple(map(int, match.groups())))
    labels = [labels[n] for n in range(len(labels)) if labels_mask[n]]

    record = np.array(record)
    c_min, o_min, b_min = record.min(axis=0)
    c_max, o_max, b_max = record.max(axis=0)

    if c_min != 0 or o_min != 0 or b_min != 0:
        raise ValueError(f"Column indices must start at 0; got c_min={c_min}, o_min={o_min}, b_min={b_min}")
    shape = [c_max + 1, o_max + 1, b_max + 1]  # channel, orbital, bunch
    return dset_type, shape, labels, labels_mask, is_double


@lru_cache(maxsize=128)
def parse_header(fname):
    """
    Processes a header line to determine the dataset type and extract relevant metadata.

    This function extracts the dataset type (either "Energy" or "laserd") from the header line,
    parses labels, and computes indexing information for a structured dataset.

    Parameters
    ----------
    fname : path-like
        Path to the data file. The ``#L`` header line and optional
        ``doublelength`` marker are read from this file.

    Returns
    -------
    dset_type : str
        The dataset type, either "EXAFS" or "LASERD".
    shape : tuple of int
        The shape of the dataset inferred from parsed indices, given as (channels, orbitals, bunches).
    labels : list of str
        The cleaned column labels after processing.
    labels_mask : numpy.ndarray
        A boolean array indicating which labels are retained (`True`) and which are removed (`False`).
    is_double_length : bool
        Whether the file uses double-length acquisition mode.

    Raises
    ------
    ValueError
        If the dataset type cannot be determined from the header.
    """
    is_double_length = False
    with open(fname, "r") as f:
        for line in f:
            if "acquisition.message1 = doublelength" in line:
                # this line is always ahead of the header line
                is_double_length = True
            if line.startswith("#L "):  # Header line
                header_line = line
                break

    return _parse_header_line(header_line, is_double=is_double_length)


def safe_mean(data_list, compute_kinetics_errorbar=False):
    """Compute the element-wise mean of a list of arrays, ignoring None entries.

    Args:
        data_list: List of numpy arrays of identical shape, or None placeholders.
        compute_kinetics_errorbar: If True, also return the per-element standard
            deviation across the list. Default False.

    Returns:
        Mean array if compute_kinetics_errorbar is False; tuple (mean, std) otherwise.
        Returns None if data_list is empty or contains only None entries.
    """
    if any(item is None for item in data_list):
        return None

    num_dsets = len(data_list)
    if num_dsets == 0:
        return None

    shapes = np.array([d.shape for d in data_list])
    max_shape = np.max(shapes, axis=0)
    max_time_steps = max(shapes[:, 0])

    data_full = np.full((num_dsets, max_time_steps, max_shape[1]), np.nan)

    # Fill the array with valid data
    for i, d in enumerate(data_list):
        valid_rows, valid_cols = d.shape
        # Only fill valid regions
        data_full[i, :valid_rows, :valid_cols] = d

    data_sum = np.nansum(data_full, axis=0)
    data_count = np.nansum(~np.isnan(data_full), axis=0)
    data_count = np.clip(data_count, 1, None)
    data_avg = data_sum / data_count

    if not compute_kinetics_errorbar:
        return data_avg
    else:
        nan_row = np.full(data_avg.shape[1], np.nan)
        if num_dsets < 2:
            return np.vstack([data_avg, nan_row]), None
        # get the kinetics profile row and compute the error bar
        # using the standard error of the mean as the error bar
        errorbar = np.nanstd(data_full[:, 1], axis=0) / np.sqrt(num_dsets)
        data_avg = np.vstack((data_avg[0], data_avg[1], errorbar))

        # compute errorbar as function of num_dsets
        data_err_num = []
        data_full = np.nan_to_num(data_full, nan=0.0)

        for n in range(2, num_dsets):
            # compute the normalized error bar and get the mean value
            error_t = np.nanstd(data_full[:n, 1], axis=0) / np.sqrt(n)
            # norm_error = error_t / np.abs(np.nanmean(data_full[:n, 1], axis=0))
            norm_error = error_t / 1.0  # np.abs(np.nanmean(data_full[:n, 1], axis=0))
            data_err_num.append((n, np.mean(norm_error)))
        data_err_num = np.array(data_err_num)
        return data_avg, data_err_num


class TrXASDatasetManager:
    """Aggregate multiple TrXASDataset files and compute their average."""

    def __init__(self):
        self.flist = []
        self.label = None

    def update_flist(self, flist):
        """Set the list of files to process and generate a result label.

        Args:
            flist: List of path-like objects pointing to raw scan files.
        """
        self.flist = flist
        if len(flist) == 1:
            self.label = f"result_{Path(flist[0]).name}"
        else:
            flist.sort()
            self.label = f"result_{Path(flist[0]).name}-{Path(flist[-1]).name[-5:]}"

    def get_energy_vs_time(self, progress=None, cache_folder=None, **kwargs):
        """Load, process, and average all datasets in the file list.

        Args:
            progress: Optional callable accepting an int (0–100) for progress updates
                (typically a Qt signal).
            cache_folder: If provided, load from / save to NPZ cache files at this path.
            **kwargs: Forwarded to :meth:`TrXASDataset.get_energy_vs_time`
                (``channel``, ``target``, ``preprocessing_kwargs``, ``norm_kwargs``,
                ``binning_kwargs``, ``kinetics_kwargs``).

        Returns:
            Averaged results dict, or ``None`` if no files could be loaded.
        """
        if len(self.flist) == 0:
            return None, None, None
        data_list = []
        diff_list = []
        kinetics_dict = {}
        dset_type = None
        good_results = None
        # Load datasets
        for n, fname in enumerate(self.flist):
            if progress is not None:
                progress.emit(int(100 * (n + 1) / len(self.flist)))
            dset = create_trxas_dataset(fname, cache_folder=cache_folder,
                                        preprocessing_kwargs=kwargs.get("preprocessing_kwargs"))
            if dset is None:
                logger.error(f"Failed to load dataset from {fname}")
                continue

            logger.debug(f"{dset.num_rows} rows in {fname}")
            if dset_type is None:
                dset_type = dset.dset_type
            elif dset_type != dset.dset_type:
                continue
            results = dset.get_energy_vs_time(**kwargs)
            if good_results is None:
                good_results = results
            diff_list.append(results["diff"])
            data_list.append(results["data"])
            if results["kinetics"]:
                for key in results["kinetics"].keys():
                    if key not in kinetics_dict.keys():
                        kinetics_dict[key] = []
                    kinetics_dict[key].append(results["kinetics"][key]["profile"])

        if good_results is None:
            logger.error(f"Failed to load any dataset from {self.flist}")
            return None

        good_results["data"] = safe_mean(data_list)
        good_results["diff"] = safe_mean(diff_list)
        for key in kinetics_dict.keys():
            profile, err_profile = safe_mean(
                kinetics_dict[key], compute_kinetics_errorbar=True
            )
            good_results["kinetics"][key]["profile"] = {
                "main": profile,
                "error": err_profile,
            }

        good_results.update(
            {
                "flist": self.flist,
                "label": self.label,
                "analysis_type": "normalized-GS",
                "analysis_kwargs": kwargs,
                "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        return good_results


# @lru_cache(maxsize=512)
def create_trxas_dataset(fname, cache_folder=None, preprocessing_kwargs=None):
    """Load a single scan file and return a TrXASDataset, or None on failure.

    Args:
        fname: Path to the raw SPEC-format data file.
        cache_folder: Directory for NPZ cache files. Pass ``None`` to disable caching.
        preprocessing_kwargs: Outlier-removal settings forwarded to :class:`TrXASDataset`.

    Returns:
        A :class:`TrXASDataset` instance, or ``None`` if loading fails.
    """
    fname = Path(fname)
    if not fname.exists():
        logger.error(f"check dataset file: {fname}")
        return None
    try:
        return TrXASDataset(fname, cache_folder=cache_folder,
                            preprocessing_kwargs=preprocessing_kwargs)
    except Exception as e:
        logger.error(f"Failed to load TrXASDataset from {fname}: {e}")
        traceback.print_exc()
        return None


def create_trxas_cache_from_flist(flist, cache_folder, preprocessing_kwargs=None):
    """Pre-compute NPZ caches for a list of scan files.

    Args:
        flist: Iterable of file paths to process.
        cache_folder: Directory where NPZ cache files will be written.
        preprocessing_kwargs: Outlier-removal settings applied before caching.
    """
    for fname in flist:
        create_trxas_cache(fname, cache_folder, preprocessing_kwargs)


def create_trxas_cache(fname, cache_folder, preprocessing_kwargs=None):
    """Pre-compute the NPZ cache for a single scan file.

    Skips files that are too recently modified (likely still being written).

    Args:
        fname: Path to the raw scan file.
        cache_folder: Directory for the NPZ cache file.
        preprocessing_kwargs: Outlier-removal settings applied before caching.

    Returns:
        Path to the written cache file, or ``None`` if skipped or failed.
    """
    fname = Path(fname)
    if not fname.exists():
        logger.error(f"check dataset file: {fname}")
        return None
    if is_recently_modified(fname):
        logger.warning(f"{fname} is recently modified, skip caching")
        return None
    try:
        cache_name, cache_exists = TrXASDataset.check_cache(fname, cache_folder)
        if not cache_exists:
            TrXASDataset(fname, cache_folder=cache_folder,
                         preprocessing_kwargs=preprocessing_kwargs)
            return cache_name
    except Exception as e:
        logger.error(f"Failed to load TrXASDataset from {fname}: {e}")
        traceback.print_exc()
        return None


def _preprocessing_equals(a: dict, b: dict) -> bool:
    """Semantically compare preprocessing kwargs.

    When ``outlier_method`` is ``None`` in both dicts, the threshold value is
    irrelevant (no outlier removal is applied either way).
    """
    if a.get("outlier_method") is None and b.get("outlier_method") is None:
        return True
    return a == b


class TrXASDataset:
    """Load and process a single raw SPEC-format TrXAS scan file.

    Data is read via :func:`numpy.loadtxt`. Preprocessing (outlier removal,
    normalization, ground-state subtraction, binning) is applied on demand.
    Processed data can be cached as an NPZ file for faster subsequent access.
    """

    def __init__(self, fname, cache_folder=None, preprocessing_kwargs=None):
        """Initialize from a raw scan file, loading from cache when available.

        Args:
            fname: Path to the raw SPEC-format data file.
            cache_folder: Directory for NPZ cache files. If ``None``, caching is disabled.
            preprocessing_kwargs: Outlier-removal settings used when building the cache.
                Passed to :func:`preprocess_xas_data`. If ``None``, no outlier removal.
        """
        self.fname = Path(fname)
        self.cache_name, cache_exists = self.check_cache(fname, cache_folder)
        self.dset_attributes = [
            "energy",
            "laserd",
            "num_rows",
            "labels",
            "meta_data",
            "dset_type",
            "shape",
            "delta_t_s",
            "xas_data_norm",
            "cached_preprocessing_kwargs_json",  # stores kwargs used at cache-build time
        ]
        if preprocessing_kwargs is None:
            preprocessing_kwargs = {"outlier_method": None}
        self.curr_preprocessing_kwargs = preprocessing_kwargs
        self.cached_preprocessing_kwargs_json = np.array(json.dumps(preprocessing_kwargs))
        self.xas_data = None
        if cache_folder is not None and cache_exists:
            self._load_npz(self.cache_name)
        else:
            self.init_from_file(fname, self.curr_preprocessing_kwargs)
            if cache_folder is not None:
                self.save_to_cache()

    @staticmethod
    def check_cache(fname, cache_folder=None):
        """Return the cache file path and whether it already exists.

        Args:
            fname: Path to the raw scan file.
            cache_folder: Cache directory. If ``None``, returns ``(None, False)``.

        Returns:
            Tuple ``(cache_path, exists)`` where cache_path is a Path or None.
        """
        if cache_folder is None:
            return None, False
        fname = Path(fname)
        cache_name = Path(cache_folder) / f"{fname.stem}.npz"
        flag_exist = cache_name.exists()
        return cache_name, flag_exist

    def _load_npz(self, path):
        """Populate dataset attributes from a pre-existing NPZ cache file."""
        data = np.load(path, allow_pickle=True)
        self.dset_attributes = list(data.files)
        for attr in self.dset_attributes:
            setattr(self, attr, data[attr])
        self.dset_type = str(self.dset_type)
        # Restore preprocessing kwargs used at cache-build time so get_energy_vs_time
        # can compare them against the current settings.
        if "cached_preprocessing_kwargs_json" in data.files:
            self.curr_preprocessing_kwargs = json.loads(
                str(self.cached_preprocessing_kwargs_json)
            )
        else:
            # Old cache without stored kwargs; assume no outlier removal.
            self.curr_preprocessing_kwargs = {"outlier_method": None}
        logger.info(f"Loaded from cache {path}")

    def save_to_cache(self, fname=None):
        """Save this dataset to an npz cache file.

        Parameters
        ----------
        fname : path-like, optional
            Destination path. Defaults to ``self.cache_name``.
        """
        dest = Path(fname) if fname is not None else self.cache_name
        if dest is None:
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".tmp.npz")
        # Uncompressed save: faster to read on NFS; ~3-4× larger than savez_compressed
        np.savez(tmp, **{attr: getattr(self, attr) for attr in self.dset_attributes})
        tmp.replace(dest)
        logger.info(f"Cache saved to {dest}")

    @classmethod
    def load_from_cache(cls, fname):
        """Load a dataset from an npz cache file and return a new instance.

        Parameters
        ----------
        fname : path-like
            Path to the ``.npz`` cache file.

        Returns
        -------
        TrXASDataset
        """
        fname = Path(fname)
        obj = cls.__new__(cls)
        obj.fname = fname
        obj.cache_name = fname
        obj.curr_preprocessing_kwargs = {"outlier_method": None}
        obj.xas_data = None
        obj._load_npz(fname)
        return obj

    def _setup_metadata(self, raw_table, labels, labels_mask, dset_type):
        """Populate metadata attributes from the raw data table and header info."""
        self.num_rows = raw_table.shape[0]
        self.labels = labels
        self.dset_type = dset_type
        self.meta_data = raw_table[:, labels_mask[: raw_table.shape[1]]]
        if self.dset_type == "EXAFS":
            self.energy = self.get("Energy")
            self.laserd = 0.0
        elif self.dset_type == "LASERD":
            self.laserd = self.get("laserd") * 1e-9  # convert to seconds
            self.energy = 0.0

    @staticmethod
    def _extract_xas_payload(raw_table, labels_mask, shape):
        """Extract XAS columns, drop the last (potentially incomplete) bunch, and pad."""
        num_channel, num_orbital, num_bunch = shape
        num_row = raw_table.shape[0]
        xas_part = raw_table[:, ~labels_mask[: raw_table.shape[1]]].reshape(num_row, num_channel, -1)
        xas_part = xas_part[:, :, :-1]  # drop last bunch — may be incomplete
        return pad_last_dim(xas_part, num_orbital * num_bunch)

    @staticmethod
    def _split_xas_parts(xas_part, shape, is_double):
        """Return (xas_parts, part_shape, full_shape).

        For double-length mode the interleaved acquisition is de-interleaved into
        two sub-parts; otherwise the data is returned as-is.
        """
        num_channel, num_orbital, num_bunch = shape
        num_row = xas_part.shape[0]
        if not is_double:
            return [xas_part], shape, shape
        xas_part = xas_part.reshape(num_row, num_channel, num_orbital, num_bunch // 2, 2)
        part_0 = xas_part[:, :, :, :, 0].reshape(num_row, num_channel, -1)
        part_1 = xas_part[:, :, :, :, 1].reshape(num_row, num_channel, -1)
        full_shape = np.array([num_channel, num_orbital * 2, num_bunch // 2])
        part_shape = np.array([num_channel, num_orbital, num_bunch // 2])
        return [part_1, part_0], part_shape, full_shape

    @staticmethod
    def _preprocess_and_combine(xas_parts, part_shape, num_rows, preprocessing_kwargs):
        """Preprocess each part and concatenate along the bunch axis."""
        raw_parts, norm_parts = zip(*[
            preprocess_xas_data(part, part_shape, num_rows, **preprocessing_kwargs)
            for part in xas_parts
        ])
        if len(raw_parts) == 1:
            return raw_parts[0], norm_parts[0]
        return np.concatenate(raw_parts, axis=2), np.hstack(norm_parts)

    def init_from_file(self, fname, preprocessing_kwargs=None):
        """Parse the raw scan file and run initial preprocessing.

        Args:
            fname: Path to the raw SPEC-format data file.
            preprocessing_kwargs: Forwarded to :func:`preprocess_xas_data`.
        """
        if preprocessing_kwargs is None:
            preprocessing_kwargs = {}

        dset_type, shape, labels, labels_mask, is_double = parse_header(fname)
        if shape[0] != 3:
            raise ValueError(f"Only 3-channel datasets are supported; got {shape[0]} channels in {fname}")

        raw_table = np.loadtxt(fname, comments="#", dtype=np.float64, delimiter="\t")
        if raw_table.size == 0:
            raise ValueError(f"No data found in {fname}")
        if raw_table.ndim == 1:
            raw_table = raw_table.reshape(1, -1)

        self._setup_metadata(raw_table, labels, labels_mask, dset_type)

        xas_part = self._extract_xas_payload(raw_table, labels_mask, shape)
        xas_parts, part_shape, shape = self._split_xas_parts(xas_part, shape, is_double)
        self.xas_data, self.xas_data_norm = self._preprocess_and_combine(
            xas_parts, part_shape, self.num_rows, preprocessing_kwargs
        )
        self.shape = shape
        self.delta_t_s = 1 / P0 / self.shape[2] 

    def get_energy_vs_time(
        self,
        channel=0,
        target="raw",
        preprocessing_kwargs=None,
        norm_kwargs=None,
        binning_kwargs=None,
        kinetics_kwargs=None,
    ):
        """Extract and process XAS data for the requested output target.

        Args:
            channel: Detector channel index (0 = background, 1 or 2 = sample signal).
            target: Processing level: ``"raw"``, ``"normalized"``, or ``"normalized-GS"``.
            preprocessing_kwargs: Forwarded to :func:`preprocess_xas_data`.
            norm_kwargs: Forwarded to :meth:`subtract_groundstate`.
            binning_kwargs: Forwarded to :meth:`apply_binning`.
            kinetics_kwargs: Forwarded to :meth:`extract_kenetics`.

        Returns:
            Results dict as produced by :meth:`compile_results`.
        """
        if preprocessing_kwargs is None:
            preprocessing_kwargs = {}
        reprocess_flag = not _preprocessing_equals(self.curr_preprocessing_kwargs, preprocessing_kwargs)
        if reprocess_flag:
            logger.debug(f"Reprocessing {self.fname} with {preprocessing_kwargs}")
            self.curr_preprocessing_kwargs = preprocessing_kwargs

        if target == "raw":
            # raw target needs xas_data (full 3-channel array); always init if absent
            if self.xas_data is None or reprocess_flag:
                self.init_from_file(self.fname, preprocessing_kwargs)
        else:
            # normalized / normalized-GS only needs xas_data_norm; cache provides it
            if self.xas_data_norm is None or reprocess_flag:
                self.init_from_file(self.fname, preprocessing_kwargs)
                # Auto-rebuild the NPZ cache with the new settings so the next
                # session doesn't fall back to re-reading the raw file again.
                if reprocess_flag and self.cache_name is not None:
                    self.cached_preprocessing_kwargs_json = np.array(
                        json.dumps(preprocessing_kwargs)
                    )
                    self.save_to_cache()

        if target == "raw":
            t_axis = np.arange(self.xas_data.shape[2]) * self.delta_t_s
            return self.compile_results(
                "raw", None, self.xas_data[:, channel, :], t_axis
            )
        elif target == "normalized":
            t_axis = np.arange(self.xas_data_norm.shape[1]) * self.delta_t_s
            return self.compile_results("normalized", None, self.xas_data_norm, t_axis)
        elif target == "normalized-GS":
            if self.dset_type == "LASERD":
                return self.process_laserd(norm_kwargs, binning_kwargs)
            elif self.dset_type == "EXAFS":
                return self.process_energy(norm_kwargs, binning_kwargs, kinetics_kwargs)
        else:
            raise ValueError("Unknown target")

    def get(self, label):
        """Return the metadata column matching the given label.

        Args:
            label: Column label string (e.g. ``"Energy"`` or ``"laserd"``).

        Returns:
            1-D array of values for that column across all rows.
        """
        index = self.labels.index(label)
        return self.meta_data[:, index]

    def get_temporal_coordinates(self, index):
        """Return the (orbital, bunch) coordinates for a linear bunch index.

        Args:
            index: Linear bunch index within the orbit.

        Returns:
            Tuple ``(orbital, bunch)``.
        """
        bunch = index % self.shape[0]
        orbital = index // self.shape[0]
        return (orbital, bunch)

    def subtract_groundstate(
        self,
        sync_type="time",
        sync_value=1820,
        gs_method="per_bunch",
        gs_value=5,
    ):
        """Subtract the pre-laser ground state from normalized XAS data.

        Args:
            sync_type: Interpretation of sync_value: ``"time"`` (seconds) or ``"bunch"`` (index).
            sync_value: Laser fire time in seconds or bunch index, depending on sync_type.
            gs_method: Averaging method: ``"bunch-average"`` or ``"orbital-average"``.
            gs_value: Number of bunches or orbitals used to compute the ground state.

        Returns:
            Tuple ``(data, diff, sync_index)`` where data is the normalized XAS array,
            diff is the difference signal, and sync_index is the resolved bunch index.
        """
        data = self.xas_data_norm  # (num_energys, total_bunches)
        num_bunches = self.shape[2]

        if sync_type == "time":
            sync_index = int(sync_value / self.delta_t_s)
        else:
            sync_index = sync_value

        if gs_method == "orbital-average":
            max_gs = sync_index // num_bunches
            if gs_value > max_gs:
                logger.warning(
                    f"gs_value={gs_value} exceeds available orbitals before sync "
                    f"({max_gs}); clamping to {max_gs}"
                )
                gs_value = max_gs
            avg_slice = slice(sync_index - gs_value * num_bunches, sync_index)
            avg_data = data[:, avg_slice].reshape(-1, gs_value, num_bunches)
            avg_data = np.mean(avg_data, axis=1)  # num_energys * num_bunches
            offset = (-1 * sync_index) % num_bunches
            cycle_indices = (np.arange(data.shape[1]) + offset) % num_bunches
            assert cycle_indices[sync_index] == 0, "sync_index not aligned"
            diff = data - avg_data[:, cycle_indices]

        elif gs_method == "bunch-average":
            if gs_value > sync_index:
                logger.warning(
                    f"gs_value={gs_value} exceeds available bunches before sync "
                    f"({sync_index}); clamping to {sync_index}"
                )
                gs_value = sync_index
            avg_slice = slice(sync_index - gs_value, sync_index)
            avg_data = np.mean(data[:, avg_slice], axis=1)
            diff = data - avg_data.reshape(-1, 1)
        else:
            raise ValueError(f"Unknown gs_method: {gs_method}")

        return data, diff, sync_index

    def compile_results(self, target, data, diff, t_axis, kinetics=None):
        """Assemble a standardized results dict from processed arrays.

        Returns:
            Dict with keys: ``target``, ``data``, ``diff``, ``t_axis``, ``x_axis``,
            ``kinetics``, ``bunch_mode``, ``delta_t_s``, ``shape``, ``dset_type``.
        """
        if self.dset_type == "EXAFS":
            x_axis = {"value": self.energy, "label": "Energy", "unit": "keV"}
        elif self.dset_type == "LASERD":
            x_axis = {"value": self.laserd * (-1), "label": "Delay", "unit": "s"}
        # y_axis = {"value": t_axis, "label": "Time", "unit": "s"}

        results = {
            "target": target,
            "data": data,
            "diff": diff,
            "t_axis": t_axis,
            "x_axis": x_axis,
            "kinetics": kinetics,
            "bunch_mode": self.shape[2],
            "delta_t_s": self.delta_t_s,
            "shape": self.shape,
            "dset_type": self.dset_type,
        }
        return results

    def apply_binning(self, data, diff, t_axis_raw, sync_index, **binning_kwargs):
        """Apply time binning to the difference map and raw data.

        Args:
            data: Normalized XAS array of shape ``(num_energy, total_bunches)``.
            diff: Difference signal array of the same shape as data.
            t_axis_raw: 1-D array of raw bunch times in seconds.
            sync_index: Resolved laser bunch index.
            **binning_kwargs: Forwarded to :func:`prepare_binning_matrix`.

        Returns:
            Tuple ``(binned_data, binned_diff, t_axis_binned)``.
        """
        size = diff.shape[1]
        binning_mat, nobin_laserd_idx = prepare_binning_matrix(
            size, sync_index, **binning_kwargs
        )
        # diff is always 2d
        b_data = (data @ binning_mat)[:, 1:]
        b_diff = (diff @ binning_mat)[:, 1:]
        if t_axis_raw.ndim == 1:
            t_axis = (t_axis_raw @ binning_mat)[1:]
        else:
            t_axis = (t_axis_raw @ binning_mat)[:, 1:]
        return b_data, b_diff, t_axis, nobin_laserd_idx

    def extract_single_kinetics(
        self, avg, t_axis, center_energy, delta_energy, label, enabled=True
    ):
        """Extract one kinetics trace for a single energy ROI.

        Args:
            avg: Difference map of shape ``(num_energy, num_time)``.
            t_axis: 1-D time axis array (seconds).
            center_energy: ROI center in keV.
            delta_energy: ROI half-width in keV.
            label: String label for this ROI (e.g. ``"ROI1"``).
            enabled: If False, returns an empty placeholder dict. Default True.

        Returns:
            Dict with key ``"profile"`` containing the kinetics trace array.
        """
        if self.dset_type != "EXAFS":
            raise ValueError(f"Expected EXAFS scan; got {self.dset_type}")
        if not enabled:
            return None
        e0, e1 = center_energy - delta_energy, center_energy + delta_energy
        slected = (self.energy >= e0) & (self.energy <= e1)
        if np.sum(slected) == 0:
            kinetics_profile = np.stack([t_axis, np.zeros_like(t_axis)])
        else:
            kinetics_profile = np.stack([t_axis, avg[slected].mean(axis=0)])

        single_result = {
            "profile": kinetics_profile,
            "long_label": f"{label}: {center_energy:.3f}±{delta_energy:.3f} keV",
        }
        return single_result

    def extract_kenetics(self, avg, t_axis, kwargs_all):
        """Extract kinetics traces for all enabled ROIs.

        Args:
            avg: Difference map of shape ``(num_energy, num_time)``.
            t_axis: 1-D time axis array (seconds).
            kwargs_all: Dict of ROI configurations keyed by label (``"ROI1"``–``"ROI4"``).

        Returns:
            Dict mapping ROI label to its kinetics profile dict.
        """
        results = {}
        if not kwargs_all:
            return results
        for label, kwargs in kwargs_all.items():
            temp = self.extract_single_kinetics(avg, t_axis, **kwargs)
            if temp:
                results[label] = temp
        return results

    def process_energy(
        self,
        norm_kwargs,
        binning_kwargs,
        kinetics_kwargs,
    ):
        """Full normalized-GS pipeline for EXAFS (energy-axis) datasets.

        Args:
            norm_kwargs: Forwarded to :meth:`subtract_groundstate`.
            binning_kwargs: Forwarded to :meth:`apply_binning`.
            kinetics_kwargs: Forwarded to :meth:`extract_kenetics`.

        Returns:
            Results dict from :meth:`compile_results`.
        """
        if self.dset_type != "EXAFS":
            raise ValueError(f"Expected EXAFS scan; got {self.dset_type}")
        data, diff, sync_index = self.subtract_groundstate(**norm_kwargs)
        t_axis_raw = (np.arange(diff.shape[1]) - sync_index) * self.delta_t_s
        b_data, b_diff, t_axis, _ = self.apply_binning(
            data, diff, t_axis_raw, sync_index, **binning_kwargs
        )
        kinetics = self.extract_kenetics(b_diff, t_axis, kinetics_kwargs)
        return self.compile_results(
            "normalized-GS", b_data, b_diff, t_axis, kinetics=kinetics
        )

    def process_laserd(
        self,
        norm_kwargs,
        binning_kwargs,
    ):
        """Full normalized-GS pipeline for LASERD (delay-axis) datasets.

        Args:
            norm_kwargs: Forwarded to :meth:`subtract_groundstate`.
            binning_kwargs: Forwarded to :meth:`apply_binning`.

        Returns:
            Results dict from :meth:`compile_results`.
        """
        if self.dset_type != "LASERD":
            raise ValueError(f"Expected LASERD scan; got {self.dset_type}")
        data, diff, sync_index = self.subtract_groundstate(**norm_kwargs)
        t_mat = (np.arange(diff.shape[1]) - sync_index) * self.delta_t_s
        # append a non-delayed time axis to the begining for display
        laserd = np.insert(self.laserd, 0, 0)
        t_mat = t_mat - laserd[:, np.newaxis]
        b_data, b_diff, t_mat2, nobin_idx = self.apply_binning(
            data, diff, t_mat, sync_index, **binning_kwargs
        )
        # separate the time axis from the rest of the matrix
        t_axis = t_mat2[0]
        t_mat2 = t_mat2[1:]

        # assemble kinetics
        nobin_set = set(nobin_idx)
        sval = []
        tval = []
        for n in range(b_diff.shape[1]):
            if n in nobin_set:
                sval.extend(b_diff[:, n].tolist())
                tval.extend(t_mat2[:, n].tolist())
            else:
                sval.append(np.mean(b_diff[:, n]))
                tval.append(np.mean(t_mat2[:, n]))

        profile = np.stack((tval, sval))
        profile = profile[:, profile[0].argsort()]
        kinetics = {
            "profile": profile,
            "long_label": "Laser Delay",
        }
        return self.compile_results(
            "normalized-GS", b_data, b_diff, t_axis, kinetics={"laserd": kinetics}
        )


if __name__ == "__main__":
    # read_trsaxs_dataset('/Users/mqichu/Documents/trxas/XTA_data/setup-full-00099')
    for n in range(1):
        t0 = time.perf_counter()
        # fname = "/Users/mqichu/Documents/trxas/XTA_data/setup-full-00099"
        fname = "/local/MQICHU/playground/Dugan_2024_3_saveddata/setup-full-00737"
        dset = TrXASDataset(fname)
        # dset.plot()
        dset.process_energy()
        t1 = time.perf_counter()
        print(f"Time elapsed: {t1 - t0:.2f} seconds")
