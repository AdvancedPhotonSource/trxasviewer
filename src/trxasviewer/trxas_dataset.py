import re
import time
from functools import lru_cache
from pathlib import Path
import numpy as np
import logging
import json
import os
import datetime
import shutil
import h5py
import traceback
import warnings
from scipy.stats import median_abs_deviation

from .utilities import (
    prepare_binning_matrix,
    is_recently_modified,
)
from .plot import plot_results


logger = logging.getLogger(__name__)

TRXAS_PATTERN = re.compile(r"c(\d+)o(\d+)b(\d+)")
P0 = 352055282.000000 / 1296  # RF frequency in Hz / number of bucket
# Each orbital has 1296 bunket, so the maximum bunch mode can be 1296
# at the APS, the RF frequency can be read from
# caget A014-IETS:BTC:CFG:SRNomFreqM -f8 -a
# A014-IETS:BTC:CFG:SRNomFreqM   2025-11-11 13:15:24.536419 352055282.00000000


CACHE_PATH = ".cache"


@lru_cache(maxsize=128)
def process_header(header_line):
    """
    Processes a header line to determine the dataset type and extract relevant metadata.

    This function extracts the dataset type (either "Energy" or "laserd") from the header line,
    parses labels, and computes indexing information for a structured dataset.

    Parameters
    ----------
    header_line : str
        A header string, typically starting with `#L`, followed by column labels.

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
    payload_mask : numpy.ndarray
        A boolean mask of the dataset shape, marking valid payload indices.

    Raises
    ------
    ValueError
        If the dataset type cannot be determined from the header.

    Notes
    -----
    - The function uses a **least-recently used (LRU) cache** to store results for up to 128 unique inputs.
    - It expects the header line format to include "Energy" or "laserd" to classify the dataset type.
    - It uses a regex pattern (`TRXAS_PATTERN`) to extract index information from certain columns.

    Examples
    --------
    >>> header = "#L N  Epoch  Energy  mono  monoE  undE  c0o0b0  c0o0b1  c0o1b0  c0o1b1  c1o0b0  c1o0b1  c1o1b0  c1o1b1"
    >>> dset_type, shape, labels, labels_mask, payload_mask = process_header(header)
    >>> print(dset_type)
    'Energy'
    >>> print(shape)
    (2, 2, 2)
    >>> print(labels)
    ['N', 'Epoch', 'Energy', 'mono', 'monoE', 'undE']
    >>> print(payload_mask.shape)
    (8,)  # Flattened shape of (2, 2, 2)
    """
    header = header_line[3:].strip()
    if re.match(r".* Energy ", header):
        dset_type = "EXAFS"
    elif re.match(r".* laserd ", header):
        dset_type = "LASERD"
    else:
        raise ValueError("Unknown dataset type")

    labels = header.split()
    labels_mask = np.ones(len(labels), dtype=bool)
    record = []
    matches = [TRXAS_PATTERN.match(col) for col in labels]
    for index, match in enumerate(matches):
        if match:
            labels_mask[index] = False
            record.append(tuple(map(int, match.groups())))
    labels = [labels[n] for n in range(len(labels)) if labels_mask[n]]

    record = np.array(record)
    # np.savetxt('record.txt', record, fmt='%d')
    c_min, o_min, b_min = record.min(axis=0)
    c_max, o_max, b_max = record.max(axis=0)

    assert c_min == 0 and o_min == 0 and b_min == 0, "min index must be 0"
    shape = [c_max + 1, o_max + 1, b_max + 1]
    index = record[:, 0] * shape[1] * shape[2] + record[:, 1] * shape[2] + record[:, 2]
    payload_mask = np.zeros(np.prod(shape), dtype=bool)
    payload_mask[index] = True
    return dset_type, shape, labels, labels_mask, payload_mask


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


@lru_cache(maxsize=128)
def process_header_2(fname):
    """
    Processes a header line to determine the dataset type and extract relevant metadata.

    This function extracts the dataset type (either "Energy" or "laserd") from the header line,
    parses labels, and computes indexing information for a structured dataset.

    Parameters
    ----------
    header_line : str
        A header string, typically starting with `#L`, followed by column labels.

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
    payload_mask : numpy.ndarray
        A boolean mask of the dataset shape, marking valid payload indices.

    Raises
    ------
    ValueError
        If the dataset type cannot be determined from the header.

    Notes
    -----
    - The function uses a **least-recently used (LRU) cache** to store results for up to 128 unique inputs.
    - It expects the header line format to include "Energy" or "laserd" to classify the dataset type.
    - It uses a regex pattern (`TRXAS_PATTERN`) to extract index information from certain columns.

    Examples
    --------
    >>> header = "#L N  Epoch  Energy  mono  monoE  undE  c0o0b0  c0o0b1  c0o1b0  c0o1b1  c1o0b0  c1o0b1  c1o1b0  c1o1b1"
    >>> dset_type, shape, labels, labels_mask, payload_mask = process_header(header)
    >>> print(dset_type)
    'Energy'
    >>> print(shape)
    (2, 2, 2)
    >>> print(labels)
    ['N', 'Epoch', 'Energy', 'mono', 'monoE', 'undE']
    >>> print(payload_mask.shape)
    (8,)  # Flattened shape of (2, 2, 2)
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
    # np.savetxt('record.txt', record, fmt='%d')
    c_min, o_min, b_min = record.min(axis=0)
    c_max, o_max, b_max = record.max(axis=0)

    assert c_min == 0 and o_min == 0 and b_min == 0, "min index must be 0"
    shape = [c_max + 1, o_max + 1, b_max + 1]
    index = record[:, 0] * shape[1] * shape[2] + record[:, 1] * shape[2] + record[:, 2]
    payload_mask = np.zeros(np.prod(shape), dtype=bool)
    payload_mask[index] = True
    return dset_type, shape, labels, labels_mask, payload_mask, is_double_length


def safe_mean(data_list, compute_kinetics_errorbar=False):
    """
    Compute the mean of a list of datasets, handling None values and computing error bars if needed.
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
        if num_dsets < 2:
            return data_avg, None
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
            norm_error = error_t / 1.0 # np.abs(np.nanmean(data_full[:n, 1], axis=0))
            data_err_num.append((n, np.mean(norm_error)))
        data_err_num = np.array(data_err_num)
        return data_avg, data_err_num


class TrXASDatasetManager:
    def __init__(self, ignore_incomplete=True):
        self.flist = []
        self.label = None
        self.ignore_incomplete = ignore_incomplete

    def update_flist(self, flist):
        self.flist = flist
        if len(flist) == 1:
            self.label = f"result_{os.path.basename(flist[0])}"
        else:
            flist.sort()
            self.label = f"result_{os.path.basename(flist[0])}-{flist[-1][-5:]}"

    def save_results(
        self,
        results,
        directory=None,
        subdirectory="Avg",
        save_image=True,
        save_numpy=True,
        save_hdf=True,
        save_origin=True,
    ):
        folder = Path(directory) / subdirectory
        folder.mkdir(parents=True, exist_ok=True)
        if save_numpy:
            np.savez_compressed(folder / "results.npz", **results)
            # copy plot scripts to the result folder for users to edit
            package_path = Path(__file__).parent
            shutil.copy(package_path / "plot.py", folder / "load_and_plot.py")

        if save_image:
            img_folder = folder / "images"
            img_folder.mkdir(parents=True, exist_ok=True)
            TrXASDataset.plot_results(results, img_folder)

        if save_origin:
            o_folder = folder / "origin"
            o_folder.mkdir(parents=True, exist_ok=True)
            TrXASDataset.save_as_origin_format(o_folder, results)

        if save_hdf:
            TrXASDataset.save_as_hdf5(folder / "results.hdf", results)
        # save settings in human readable format
        TrXASDataset.save_as_json(folder / "settings.json", results)

    def get_energy_vs_time(self, progress=None, **kwargs):
        if len(self.flist) == 0:
            return None, None, None
        data_list = []
        diff_list = []
        kinetics_dict = {}
        dset_type = None
        # Load datasets
        for n, fname in enumerate(self.flist):
            if progress is not None:
                progress.emit(int(100 * (n + 1) / len(self.flist)))
            dset = create_trxas_dataset(fname, ignore_incomplete=self.ignore_incomplete)
            if dset is None:
                logger.error(f"Failed to load dataset from {fname}")
                continue

            logger.info(f"{dset.num_rows} rows in {fname}")
            if dset_type is None:
                dset_type = dset.dset_type
            elif dset_type != dset.dset_type:
                continue
            if dset is not None:
                results = dset.get_energy_vs_time(**kwargs)
                diff_list.append(results["diff"])
                data_list.append(results["data"])
                if results["kinetics"]:
                    for key in results["kinetics"].keys():
                        if key not in kinetics_dict.keys():
                            kinetics_dict[key] = []
                        kinetics_dict[key].append(results["kinetics"][key]["profile"])

        good_idx = 0  # np.argmax(shapes[:, 0])
        good_dset = create_trxas_dataset(self.flist[good_idx])
        if good_dset is None:
            logger.error(f"Failed to load dataset from {self.flist[good_idx]}")
            return None

        good_results = good_dset.get_energy_vs_time(**kwargs)

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
def create_trxas_dataset(fname, ignore_incomplete=True, load_cache=True):
    fname = Path(fname)
    if not fname.exists():  # or not is_sample_data(fname):
        logger.error(f"check dataset file: {fname}")
        return None
    try:
        return TrXASDataset(fname, load_cache=load_cache)
    except Exception as e:
        logger.error(f"Failed to load TrXASDataset from {fname}: {e}")
        traceback.print_exc()
        return None


def create_trxas_cache_from_flist(flist, **kwargs):
    for fname in flist:
        create_trxas_cache(fname=fname, **kwargs)
    return


def create_trxas_cache(fname, ignore_incomplete=True, load_cache=True):
    fname = Path(fname)
    if not fname.exists():  # or not is_sample_data(fname):
        logger.error(f"check dataset file: {fname}")
        return None
    if is_recently_modified(fname):
        logger.warning(f"{fname} is recently modified, skip caching")
        return None
    try:
        cache_name, cache_exists = TrXASDataset.check_cache(fname)
        if not cache_exists:
            TrXASDataset(
                fname, ignore_incomplete=ignore_incomplete, load_cache=load_cache
            )
            return cache_name
    except Exception as e:
        logger.error(f"Failed to load TrXASDataset from {fname}: {e}")
        traceback.print_exc()
        return None


class TrXASDataset:
    def __init__(self, fname, ignore_incomplete=True, load_cache=True):
        self.fname = Path(fname)
        self.cache_name, cache_exists = self.check_cache(fname)
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
        ]
        if load_cache and cache_exists:
            self.init_from_cache(self.cache_name)
        else:
            self.init_from_file(fname, ignore_incomplete=ignore_incomplete)
            # if not self.cache_name.exists() and not is_recently_modified(self.fname):
            #     self.save_to_cache()
        self.xas_data = None

    @staticmethod
    def check_cache(fname):
        fname = Path(fname)
        cache_name = fname.parent / CACHE_PATH / f"{fname.stem}.npz"
        flag_exist = cache_name.exists()
        return cache_name, flag_exist

    def init_from_cache(self, fname):
        data = np.load(fname, allow_pickle=True)
        for attr in self.dset_attributes:
            setattr(self, attr, data[attr])
        self.dset_type = str(self.dset_type)

    def save_to_cache(self):
        self.cache_name.parent.mkdir(parents=True, exist_ok=True)
        temp_cache_name = self.cache_name.with_suffix(".tmp.npz")
        np.savez(
            temp_cache_name,
            **{attr: getattr(self, attr) for attr in self.dset_attributes},
        )
        temp_cache_name.replace(self.cache_name)

    def init_from_file(self, fname, ignore_incomplete=True):
        dset_type, shape, labels, labels_mask, payload_mask, is_double_length = (
            process_header_2(fname)
        )
        num_channel = shape[0]
        assert num_channel == 3, f"only support 3 channels, but got {num_channel}"
        data = np.loadtxt(fname, comments="#", dtype=np.float32, delimiter="\t")
        self.num_rows = data.shape[0]
        self.labels = labels
        self.meta_data = data[:, labels_mask[0 : data.shape[1]]]
        self.dset_type = dset_type

        if self.dset_type == "EXAFS":
            self.energy = self.get("Energy")
            self.laserd = 0.0
        elif self.dset_type == "LASERD":
            self.laserd = self.get("laserd") * 1e-9  # convert to seconds
            self.energy = 0.0

        # xas_part is [num_energy, channel, total_bunches]
        data = data[:, ~labels_mask[0 : data.shape[1]]].reshape(
            self.num_rows, num_channel, -1
        )
        # remove the last bunch because it may be incomplete
        xas_part = data[:, :, :-1]  # (141, 3, 8668)
        # xas_part = np.full(
        #     (self.num_rows, num_channel, shape[1] * shape[2]), np.nan, dtype=float
        # )
        # xas_part[:, :, 0 : data.shape[2]] = data

        if is_double_length:
            shape_5d = (self.num_rows, shape[0], shape[1], shape[2] // 2, 2)
            xas_part = xas_part.reshape(shape_5d)
            xas_part_0 = xas_part[:, :, :, :, 0]
            xas_part_0 = xas_part_0.reshape(self.num_rows, shape[0], -1)
            xas_part_1 = xas_part[:, :, :, :, 1]
            xas_part_1 = xas_part_1.reshape(self.num_rows, shape[0], -1)

            # xas_part = np.concatenate((xas_part_0, xas_part_1), axis=-1)
            xas_part = np.concatenate((xas_part_1, xas_part_0), axis=-1)
            # xas_part = np.swapaxes(xas_part, -1, -3).reshape(-1)
            # xas_part = xas_part.reshape(self.num_rows, shape[0], -1)
            shape = [shape[0], shape[1] * 2, shape[2] // 2]

        # in cases, after removing the last bunch, the number of bunches
        # is a multiple of num_bunches. So we need to trim the shape
        # shape[1] = (xas_part.shape[2] + shape[2] - 1) // shape[2]
        self.shape = shape

        self.delta_t_s = 1 / P0 / self.shape[2]
        self.xas_data = xas_part
        self.xas_data_norm = self.normalize()

    def get_energy_vs_time(
        self,
        channel=0,
        target="raw",
        norm_kwargs=None,
        binning_kwargs=None,
        kinetics_kwargs=None,
    ):
        if target == "raw":
            if self.xas_data is None:
                self.init_from_file(self.fname)
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
        index = self.labels.index(label)
        return self.meta_data[:, index]

    def get_temporal_coordinates(self, index):
        bunch = index % self.shape[0]
        orbital = index // self.shape[0]
        return (orbital, bunch)
    
    def _remove_outlier(self, threshold=1):
        """
        Remove outliers from XAS data using median absolute deviation.
        
        Outliers are detected in the background channel (channel 0) and replaced
        with the average of neighboring values in all channels.
        
        Parameters
        ----------
        threshold : float, default=1
            Number of MAD units beyond which a point is considered an outlier.
            
        Returns
        -------
        xas_data : ndarray
            Corrected XAS data with outliers replaced.
        """
        xas_data = np.copy(self.xas_data)
        
        # Detect outliers using background channel (channel 0)
        background = xas_data[:, 0, :]
        mad_threshold = median_abs_deviation(background, axis=1, keepdims=True)
        outlier_mask = np.abs(background - np.median(background, axis=1, keepdims=True)) > threshold * mad_threshold
        
        # Replace outliers with average of neighbors in all channels
        # usually only one bunch is missing, so we can use the average of neighbors
        neighbor_up = np.roll(xas_data, 1, axis=2)
        neighbor_dn = np.roll(xas_data, -1, axis=2)
        xas_data[:, :, outlier_mask] = 0.5 * (neighbor_up[:, :, outlier_mask] + neighbor_dn[:, :, outlier_mask])
        
        return xas_data

    def normalize(self, repeat_rate=0):
        # acquire_time = self.get("Seconds")
        # xas_data = np.copy(self.xas_data)
        xas_data = self._remove_outlier(threshold=6)
        # if repeat_rate > 0:
        #     offset = xas_data / (repeat_rate * acquire_time)
        #     xas_data = -np.log(1.0 - offset)

        shape_4d = (self.num_rows, self.shape[0], self.shape[1], self.shape[2])
        shape_3d = (self.num_rows, self.shape[0], self.shape[1] * self.shape[2])

        xas_3d = np.full(shape_3d, np.nan)  # (rows, channel, orbital * bunch)
        xas_3d[:, :, 0 : xas_data.shape[2]] = xas_data
        xas_4d = xas_3d.reshape(shape_4d)
        # ch0 is background; ch1 and ch2 are signals
        orbital_mean_ch0 = np.nanmean(xas_4d[:, 0], axis=1)  # rows x bunch

        # it's (num_rows, total_bunches)
        norm_data = np.mean(xas_data[:, 1:3], axis=(1,))
        cycle_indices = np.arange(norm_data.shape[1]) % self.shape[2]
        norm_data /= orbital_mean_ch0[:, cycle_indices]

        return norm_data.astype(np.float32)

    @staticmethod
    def plot_results(results, save_name):
        plot_results(results, folder=save_name)

    @staticmethod
    def save_as_origin_format(origin_folder, results):
        # save diff and non-groundstate subtracted data
        for key, label in zip(("data", "diff"), ("data_full", "data_diff")):
            temp = results[key]
            shape = temp.shape
            data_full = np.zeros(np.array(shape) + 1, dtype=np.float32)
            data_full[1:, 1:] = temp
            data_full[1:, 0] = results["x_axis"]["value"]
            data_full[0, 1:] = results["t_axis"]
            data_full = data_full.astype(object)
            # add header
            if results["dset_type"] == "EXAFS":
                data_full[0, 0] = "Energy(keV)/Time(s)"
            else:
                data_full[0, 0] = "Delay(s)/Time(s)"
            np.savetxt(
                origin_folder / f"{label}.txt", data_full, fmt="%s", delimiter=","
            )

        for key, value in results["kinetics"].items():
            np.savetxt(
                origin_folder / f"kinetics_{key}.txt",
                value["profile"]["main"].T,
                fmt="%.7e",
                delimiter=",",
                header="Delay(s),Intensity,Error",
                comments="",  # remove '#' so header is raw and easy to parse
            )

    @staticmethod
    def save_as_json(fname, results):
        with open(fname, "w") as f:
            json.dump(results["analysis_kwargs"], f, indent=4)

    @staticmethod
    def save_as_hdf5(fname, results_raw):
        results = results_raw.copy()

        def save_recursively(group, data):
            for key, value in data.items():
                if value is None:
                    continue
                if isinstance(value, dict):
                    subgroup = group.create_group(key)
                    save_recursively(subgroup, value)
                else:
                    if isinstance(value, str):
                        string_dt = h5py.string_dtype(encoding="utf-8")
                        group.create_dataset(key, data=value, dtype=string_dt)
                    else:
                        compression = None
                        if isinstance(value, np.ndarray):
                            value = np.ascontiguousarray(value)
                            compression = "gzip" if value.size > 4096 else None
                        group.create_dataset(key, data=value, compression=compression)

        with h5py.File(fname, "w") as f:
            save_recursively(f, results)

    def subtract_groundstate(
        self,
        sync_type="time",
        sync_value=1820,
        gs_method="per_bunch",
        gs_value=5,
    ):
        data = self.xas_data_norm  # (num_energys, total_bunches)
        num_bunches = self.shape[2]

        if sync_type == "time":
            sync_index = int(sync_value / self.delta_t_s)
        else:
            sync_index = sync_value

        if gs_method == "orbital-average":
            avg_slice = slice(sync_index - gs_value * num_bunches, sync_index)
            assert avg_slice.start >= 0, "ground state start < 0"
            avg_data = data[:, avg_slice].reshape(-1, gs_value, num_bunches)
            avg_data = np.mean(avg_data, axis=1)  # num_energys * num_bunches
            offset = (-1 * sync_index) % num_bunches
            cycle_indices = (np.arange(data.shape[1]) + offset) % num_bunches
            assert cycle_indices[sync_index] == 0, "sync_index not aligned"
            diff = data - avg_data[:, cycle_indices]

        elif gs_method == "bunch-average":
            avg_slice = slice(sync_index - gs_value, sync_index)
            assert avg_slice.start >= 0, "ground state start < 0"
            avg_data = np.mean(data[:, avg_slice], axis=1)
            # print(data.shape, avg_data.shape, data[:, avg_slice].shape)
            diff = data - avg_data.reshape(-1, 1)
        else:
            raise ValueError(f"Unknown gs_method: {gs_method}")

        return data, diff, sync_index

    def compile_results(self, target, data, diff, t_axis, kinetics=None):
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
        assert self.dset_type == "EXAFS", "Not an EXAFS scan"
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
        assert self.dset_type == "EXAFS", "Not an EXAFS scan"
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
        assert self.dset_type == "LASERD", "Not a LASERD scan"
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
        sval = []
        tval = []
        for n in range(b_diff.shape[1]):
            if n in nobin_idx:
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
        dset.normalize()
        # dset.plot()
        dset.process_energy()
        t1 = time.perf_counter()
        print(f"Time elapsed: {t1 - t0:.2f} seconds")
