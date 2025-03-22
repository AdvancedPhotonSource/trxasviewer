import re
import time
from functools import lru_cache
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import logging
import json
import scienceplots
from .utilities import get_scan_type, compare_versions, prepare_binning_matrix
from . import __version__


logger = logging.getLogger(__name__)

TRXAS_PATTERN = re.compile(r"c(\d+)o(\d+)b(\d+)")
P0 = 271555.0  # 271.555 kHz is P0 for APS, i.e. frequency of orbits
CACHE_PATH = '.cache'


def build_cache_database(folder, min_version="0.2.0"):
    """
    Builds or updates a cache database in JSON format for a given folder.

    - Reads from an existing cache file if valid and meets `min_version`.
    - Iterates through files, categorizing them based on `get_scan_type()`.
    - Stores results in `cache.json` inside the `cache` subdirectory.
    """
    cache_path = Path(folder) / CACHE_PATH
    cache_name = cache_path / 'cache.json'

    # Ensure the cache directory exists before doing anything else
    cache_path.mkdir(parents=True, exist_ok=True)

    time_now = time.strftime("%Y-%m-%d %H:%M:%S")
    # Initialize an empty cache
    cache_db = {
        "version": __version__,
        "datetime": time_now,
        "prefix_db": {},
        "scan_type": {},
    }

    # Load existing cache if possible
    if cache_name.is_file():
        try:
            temp_db = json.loads(cache_name.read_text())
            curr_version = temp_db.get('version', "0.2.0")
            if compare_versions(curr_version, min_version):
                cache_db = temp_db  # Use the existing cache
                cache_db["version"] = __version__   # update version
                cache_db["datetime"] = time_now
        except json.JSONDecodeError:
            logger.warning(f"{cache_name} is corrupted. Rebuilding cache...")

    def append_entry(cache_db, scan_type, entry):
        """Adds a scan entry to the cache, ensuring structure integrity."""
        try:
            index = int(entry.name[-5:])  # Extract numeric index
            prefix = entry.name[:-5]
        except ValueError:
            logging.error(f"Skipping {entry.name}: Invalid filename format")
            return
        if prefix not in cache_db["prefix_db"]:
            cache_db["prefix_db"][prefix] = {"exafs": [], "laserd": []}
        cache_db["prefix_db"][prefix][scan_type].append(index)

    flag_save = False
    for entry in sorted(Path(folder).iterdir(), key=lambda x: x.name):
        if not entry.is_file():
            continue
        # Check scan type in cache or compute it
        full_path = str(entry.resolve())  # Ensure absolute path
        scan_type = cache_db["scan_type"].get(full_path)
        if scan_type in (None, "writting"):
            # retry to get type if it was writting, or if it was not in cache
            scan_type = get_scan_type(entry)
            cache_db["scan_type"][full_path] = scan_type
        if scan_type in ("exafs", "laserd"):
            append_entry(cache_db, scan_type, entry)
            flag_save = True

    # Save cache if updates were made
    if flag_save:
        cache_name.write_text(json.dumps(cache_db, indent=4))

    return cache_db


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
    shape = (c_max + 1, o_max + 1, b_max + 1)
    index = record[:, 0] * shape[1] * shape[2] + \
        record[:, 1] * shape[2] + record[:, 2]
    payload_mask = np.zeros(np.prod(shape), dtype=bool)
    payload_mask[index] = True
    return dset_type, shape, labels, labels_mask, payload_mask


def fix_incomplete_dataset(payload_mask, shape, xas_data):
    """
    Fix incomplete dataset by removing the incomplete part. It's used when the
    dataset is not complete, i.e., the number of bunches in the last orbital
    is less than the number of bunches in the previous orbital. This function
    will remove the incomplete part and return the fixed dataset and the new
    shape.

    Parameters
    ----------
    payload_mask : np.ndarray
        The mask of the payload.
    shape : tuple
        The shape of the dataset when it's a complete dataset.
    xas_data : np.ndarray
        The dataset to be fixed, the incomplete part is filled with np.nan.

    Returns
    -------
    xas_data : np.ndarray
        The fixed dataset.
    new_shape : tuple
        The new shape of the dataset.
    """
    total_bunches = np.sum(payload_mask)
    mask = np.zeros((shape[0], shape[1], shape[2]), dtype=bool)
    effective_orbital = total_bunches // (shape[0] * shape[2])
    new_shape = (shape[0], effective_orbital, shape[2])
    mask[:, 0:effective_orbital] = True
    xas_data = xas_data[:, mask.reshape(-1)]
    return xas_data, new_shape


def get_multiples(size, pos, unit_len):
    """
    Get the start and end positions of the multiples of unit_len that contain
    the position pos. 
    """
    assert 0 < pos < size, f"Sync Bunch [{pos}] is not valid."
    start = pos - pos // unit_len * unit_len
    end = pos + (size - pos) // unit_len * unit_len
    pos = pos - start
    return pos, slice(start, end)


def safe_mean(data_list):
    if len(data_list) == 0:
        return None

    shapes = np.array([d.shape for d in data_list])
    max_shape = np.max(shapes, axis=0)
    max_time_steps = max(shapes[:, 0])

    data_full = np.full(
        (len(data_list), max_time_steps, max_shape[1]), np.nan)

    # Fill the array with valid data
    for i, d in enumerate(data_list):
        valid_rows, valid_cols = d.shape
        # Only fill valid regions
        data_full[i, :valid_rows, :valid_cols] = d

    data_avg = np.nanmean(data_full, axis=0)
    return data_avg


class TrXASDatasetManager:
    def __init__(self, ignore_incomplete=True):
        self.flist = []
        self.ignore_incomplete = ignore_incomplete

    def update_flist(self, flist):
        self.flist = flist

    def save_results(self, fname, **kwargs):
        fname = Path(fname).with_suffix("")
        base_name = fname.name
        fname_origin = fname.with_name(f"{base_name}_origin.txt")
        fname_numpy = fname.with_name(f"{base_name}_numpy.npz")
        fname_plot = fname.with_name(f"{base_name}_plot.pdf")

        results = self.get_energy_vs_time(progress=None, **kwargs)
        results.update({
            "flist": self.flist,
            "analysis_type": "normalized-GS",
            "analysis_kwargs": kwargs,
        })
        np.savez_compressed(fname_numpy, **results)

        if results["dset_type"] == "EXAFS":
            diff = results.get("avg")
            x_axis = results.get("x_axis")["value"]
            t_axis = results.get("t_axis")
            TrXASDataset.plot_and_save(fname_plot, diff, x_axis, t_axis)
            TrXASDataset.save_as_origin_format(
                fname_origin, diff, x_axis, t_axis)
            logger.info(
                f"Saved results to {fname}_[numpy.npz, origin.txt, plot.pdf]")
        else:
            logger.info(
                f"Saved results to {fname}_numpy.npz. origin/plot not implemented for {results['dset_type']}")

    def get_energy_vs_time(self, progress=None, **kwargs):
        if len(self.flist) == 0:
            return None, None, None
        data_list = []
        kinetics_list = []
        dset_type = None
        # Load datasets
        for n, fname in enumerate(self.flist):
            if progress is not None:
                progress.emit(int(100 * (n + 1) / len(self.flist)))
            dset = create_trxas_dataset(
                fname, ignore_incomplete=self.ignore_incomplete)
            logger.info(f"{dset.num_rows} rows in {fname}")
            if dset_type is None:
                dset_type = dset.dset_type
            elif dset_type != dset.dset_type:
                continue
            if dset is not None:
                results = dset.get_energy_vs_time(**kwargs)
                data_list.append(results["avg"])
                if results["kinetics"] is not None:
                    kinetics_list.append(results["kinetics"])

        avg_data = safe_mean(data_list)
        avg_kinetics = safe_mean(kinetics_list)

        good_idx = 0  # np.argmax(shapes[:, 0])
        good_dset = create_trxas_dataset(self.flist[good_idx])
        good_results = good_dset.get_energy_vs_time(**kwargs)
        good_results["avg"] = avg_data
        good_results["kinetics"] = avg_kinetics
        return good_results


# @lru_cache(maxsize=512)
def create_trxas_dataset(fname, ignore_incomplete=True, load_cache=True):
    fname = Path(fname)
    if not fname.exists():  # or not is_sample_data(fname):
        logger.error(f"check dataset file: {fname}")
        return None
    try:
        return TrXASDataset(fname, ignore_incomplete=ignore_incomplete, load_cache=load_cache)
    except Exception as e:
        logger.error(f"Failed to load TrXASDataset from {fname}: {e}")
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
    try:
        cache_name, cache_exists = TrXASDataset.check_cache(fname)
        if not cache_exists:
            TrXASDataset(fname, ignore_incomplete=ignore_incomplete,
                         load_cache=load_cache)
            return cache_name
    except Exception as e:
        logger.error(f"Failed to load TrXASDataset from {fname}: {e}")
        return None


class TrXASDataset:
    def __init__(self, fname, ignore_incomplete=True, load_cache=True):
        self.fname = Path(fname)
        self.cache_name, cache_exists = self.check_cache(fname)
        self.dset_attributes = ["energy", "laserd", "num_rows", "labels",
                                "meta_data", "dset_type", "shape", "delta_t_s",
                                "xas_data_norm"]

        if load_cache and cache_exists:
            self.init_from_cache(self.cache_name)
        else:
            self.init_from_file(fname, ignore_incomplete=ignore_incomplete)
            # if not self.cache_name.exists():
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

    def save_to_cache(self):
        self.cache_name.parent.mkdir(parents=True, exist_ok=True)
        temp_cache_name = self.cache_name.with_suffix(".tmp.npz")
        np.savez(temp_cache_name, **{attr: getattr(self, attr) for attr in
                                     self.dset_attributes})
        temp_cache_name.replace(self.cache_name)

    def init_from_file(self, fname, ignore_incomplete=True):
        with open(fname, "r") as f:
            for line in f:
                if line.startswith("#L "):  # Header line
                    dset_type, shape, labels, labels_mask, payload_mask = (
                        process_header(line)
                    )
                    break
        data = np.loadtxt(fname, comments="#",
                          dtype=np.float32, delimiter="\t")
        self.num_rows = data.shape[0]
        self.labels = labels
        self.meta_data = data[:, labels_mask]
        self.dset_type = dset_type

        if self.dset_type == 'EXAFS':
            self.energy = self.get("Energy")
            self.laserd = 0.0
        elif self.dset_type == 'LASERD':
            self.laserd = self.get("laserd") * 1e-9  # convert to seconds
            self.energy = 0.0

        xas_part = data[:, ~labels_mask]
        # fill the missing data with NaN, create a whole dataset
        xas_full = np.full((self.num_rows, np.prod(shape)), np.nan)
        xas_full[:, payload_mask] = xas_part
        if ignore_incomplete and np.prod(shape) != np.sum(payload_mask):
            # fix the incomplete dataset and remove all nan items
            xas_full, shape = fix_incomplete_dataset(
                payload_mask, shape, xas_full)

        self.shape = shape
        self.delta_t_s = 1 / P0 / self.shape[2]
        self.xas_data = xas_full.reshape(self.num_rows, self.shape[0], -1)
        self.xas_data_norm = self.normalize()

    def get_energy_vs_time(self, channel=0, target="raw", norm_kwargs=None,
                           binning_kwargs=None):
        if target == "raw":
            t_axis = np.arange(self.xas_data.shape[2]) * self.delta_t_s
            return self.compile_results(self.xas_data[:, channel, :], t_axis)

        elif target == "normalized":
            t_axis = np.arange(self.xas_data_norm.shape[1]) * self.delta_t_s
            return self.compile_results(self.xas_data_norm, t_axis)

        elif target == "normalized-GS":
            if self.dset_type == 'LASERD':
                return self.process_laserd(norm_kwargs, binning_kwargs)
            elif self.dset_type == 'EXAFS':
                return self.process_energy(norm_kwargs, binning_kwargs)
        else:
            raise ValueError("Unknown target")

    def get(self, label):
        index = self.labels.index(label)
        return self.meta_data[:, index]

    def get_temporal_coordinates(self, index):
        bunch = index % self.shape[0]
        orbital = index // self.shape[0]
        return (orbital, bunch)

    def normalize(self, repeat_rate=0):
        acquire_time = self.get("Seconds")
        xas_data = np.copy(self.xas_data)

        if repeat_rate > 0:
            offset = xas_data / (repeat_rate * acquire_time)
            xas_data = -np.log(1.0 - offset)

        xas_data = xas_data.reshape(
            self.num_rows, *self.shape
        )  # (rows, channel, orbital, bunch)
        ortial_mean_ch0 = np.nanmean(xas_data[:, 0], axis=1)  # rows x bunch
        xas_data[:, 1:] /= ortial_mean_ch0[
            :, np.newaxis, np.newaxis, :
        ]  # normalize other channels
        norm_data = xas_data.reshape(self.num_rows, self.shape[0], -1)
        # average over channels 1 and 2
        norm_data = np.mean(norm_data[:, 1:3], axis=(1,))
        return norm_data.astype(np.float32)

    @staticmethod
    def plot_and_save(save_name, diff, energy_axis, t_axis, title=None):
        # plt.style.use('science')
        plt.rcParams["text.usetex"] = False
        t_axis = t_axis * 1e6   # convert to microseconds
        extent = (energy_axis[0], energy_axis[-1], t_axis[0], t_axis[-1])
        data = np.flipud(diff.T)
        fig_width = 4.8
        fig_height = fig_width / 1.618033988749
        vmin, vmax = np.percentile(data, [0.5, 99.5])
        vmin = min(vmin, -vmax)
        vmax = -1 * vmin

        fig, ax = plt.subplots(1, 1, figsize=(fig_width, fig_height))
        im = ax.imshow(data, aspect="auto", extent=extent, cmap='bwr',
                       vmin=vmin, vmax=vmax)
        # ax.set_aspect(1/aspect)
        ax.set_xlabel("Energy (keV)")
        ax.set_ylabel("Time (μs)")
        ax.set_title(title)
        plt.tight_layout()
        plt.colorbar(im, ax=ax)
        plt.savefig(save_name, dpi=600)
        plt.close(fig)

    @staticmethod
    def save_as_origin_format(save_name, diff, energy_axis, t_axis, title=None):
        shape = diff.shape
        data_full = np.zeros(np.array(shape) + 1, dtype=np.float32)
        data_full[0, 1:] = t_axis
        data_full[1:, 0] = energy_axis
        np.savetxt(save_name, data_full, fmt="%.8e")

    def subtract_groundstate(
        self,
        sync_type="time",
        sync_value=1820,
        pre_avg_orbitals=5,
        do_perbunch="per_bunch",
    ):
        # average over the channels 1 and channel 2
        data = self.xas_data_norm  # num_energys * (orbitals * bunches)
        num_orbitals, num_bunches = self.shape[1:3]

        if sync_type == "time":
            sync_index = int(sync_value / self.delta_t_s)
        else:
            sync_index = sync_value

        sync_index, slice_pre = get_multiples(
            num_bunches * num_orbitals, sync_index, num_bunches
        )
        data = data[:, slice_pre]  # num_energys * -1
        data = data.reshape(self.num_rows, -1, num_bunches)

        preavg_orbit_idx = sync_index // num_bunches
        preavg_slice = slice(
            max(0, preavg_orbit_idx - pre_avg_orbitals), preavg_orbit_idx
        )
        # average along orbitals, num_energys * bunches
        preavg = np.mean(data[:, preavg_slice], axis=(1,))

        if do_perbunch == "per_bunch":
            diff = data - preavg[:, np.newaxis, :]
        elif do_perbunch == "avg_bunch":
            diff = data - np.mean(preavg, axis=1)[:, np.newaxis, np.newaxis]
        else:
            raise ValueError("Unknown do_perbunch value %s method")
        diff = diff.reshape(self.num_rows, -1)
        return diff, sync_index

    def compile_results(self, avg, t_axis, kinetics=None):
        if self.dset_type == 'EXAFS':
            x_axis = {
                "value": self.energy,
                "label": "Energy",
                "unit": "keV"
            }
        elif self.dset_type == 'LASERD':
            x_axis = {
                "value": self.laserd * (-1),
                "label": "Delay",
                "unit": "s"}
        # y_axis = {"value": t_axis, "label": "Time", "unit": "s"}

        results = {
            "avg": avg,
            "t_axis": t_axis,
            "x_axis": x_axis,
            "kinetics": kinetics,
            "bunch_mode": self.shape[2],
            "delta_t_s": self.delta_t_s,
            "shape": self.shape,
            "dset_type": self.dset_type
        }
        return results

    def apply_binning(self, diff, t_axis_raw, sync_index, **binning_kwargs):
        size = diff.shape[1]
        self.idx_mask, self.binning_mat = prepare_binning_matrix(
            size, sync_index, **binning_kwargs)
        avg = diff @ self.binning_mat
        t_axis = t_axis_raw @ self.binning_mat
        return avg, t_axis

    def process_energy(
        self,
        norm_kwargs,
        binning_kwargs,
    ):
        assert self.dset_type == "EXAFS", "Not an EXAFS scan"
        diff, sync_index = self.subtract_groundstate(**norm_kwargs)
        t_axis_raw = (np.arange(diff.shape[1]) - sync_index) * self.delta_t_s
        avg, t_axis = self.apply_binning(diff, t_axis_raw, sync_index,
                                         **binning_kwargs)
        return self.compile_results(avg, t_axis)

    def process_laserd(
        self,
        norm_kwargs,
        binning_kwargs,
    ):
        assert self.dset_type == "LASERD", "Not a LASERD scan"
        diff, sync_index = self.subtract_groundstate(**norm_kwargs)
        t_mat = (np.arange(diff.shape[1]) - sync_index) * self.delta_t_s
        t_mat = t_mat - self.laserd[:, np.newaxis]
        avg, t_mat2 = self.apply_binning(diff, t_mat, sync_index,
                                         **binning_kwargs)
        t_axis = np.copy(t_mat2[0])
        roi = t_mat2 > 0
        t_val = t_mat2[roi]
        diff_val = avg[roi]
        kinetics = np.stack((t_val, diff_val), axis=1)
        kinetics = kinetics[kinetics[:, 0].argsort()]
        return self.compile_results(avg, t_axis, kinetics=kinetics)


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
