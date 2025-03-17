import re
import os
import time
from functools import lru_cache
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import logging
import scienceplots

logger = logging.getLogger(__name__)

TRXAS_PATTERN = re.compile(r"c(\d+)o(\d+)b(\d+)")
P0 = 271555.0  # 271.555 kHz is P0 for APS, i.e. frequency of orbits
CACHE_PATH = '.cache'


def is_sample_data(fname):
    """Check if a file contains a line starting with '#L ' followed by 'Energy '."""
    if not Path(fname).is_file():
        return False

    try:
        with open(fname, "r", encoding="utf-8", errors="replace") as f:  # Safe reading
            for line in f:
                if re.match(r"#L .* Energy ", line):
                    return True
    except (OSError, IOError):
        return False

    return False


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
        The dataset type, either "Energy" or "laserd".
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
        dset_type = "Energy"
    elif re.match(r".* laserd ", header):
        dset_type = "laserd"
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
    index = record[:, 0] * shape[1] * shape[2] + record[:, 1] * shape[2] + record[:, 2]
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

        diff, energy, t_axis = self.get_energy_vs_time(progress=None, **kwargs)
        results = {
            "flist": self.flist,
            "analysis_type": "normalized-GS",
            "diff_data": diff.astype(np.float32),
            "analysis_kwargs": kwargs,
            "energy_axis": energy,
            "t_axis": t_axis,
        }
        np.savez_compressed(fname_numpy, **results)
        TrXASDataset.plot_and_save(fname_plot, diff, energy, t_axis)
        TrXASDataset.save_as_origin_format(fname_origin, diff, energy, t_axis)
        logger.info(f"Saved results to {fname}_[numpy.npz, origin.txt, plot.pdf]")

    def get_energy_vs_time(self, progress=None, **kwargs):
        if len(self.flist) == 0:
            return None, None, None
        data_list = []
        shapes = []
        # Load datasets
        for fname in self.flist:
            dset = create_trxas_dataset(fname, ignore_incomplete=self.ignore_incomplete)
            if dset is None:
                continue
            t_data, _, _ = dset.get_energy_vs_time(**kwargs)
            data_list.append(t_data)
            shapes.append(t_data.shape)
            if progress is not None:
                progress.emit(int(100 * len(data_list) / len(self.flist)))

        if len(data_list) == 0:
            return None, None, None
        shapes = np.array(shapes)
        # Determine maximum valid shape
        max_shape = np.max(shapes, axis=0)  # Get the largest shape
        max_time_steps = max(shapes[:, 0])  # Get the maximum shape along axis 0

        # Create a NaN-filled array with the max shape
        data_full = np.full((len(data_list), max_time_steps, max_shape[1]), np.nan)

        # Fill the array with valid data
        for i, d in enumerate(data_list):
            valid_rows, valid_cols = d.shape
            data_full[i, :valid_rows, :valid_cols] = d  # Only fill valid regions

        # Compute the average, ignoring NaNs
        data_avg = np.nanmean(data_full, axis=0)
        good_idx = np.argmax(shapes[:, 0])  # Select dataset with max time steps
        good_dset = create_trxas_dataset(self.flist[good_idx])
        _, energy_axis, t_axis = good_dset.get_energy_vs_time(**kwargs)
        return data_avg, energy_axis, t_axis


@lru_cache(maxsize=512)
def create_trxas_dataset(fname, ignore_incomplete=True, load_cache=True):
    fname = Path(fname)
    if not fname.exists() or not is_sample_data(fname):
        logger.error(f"check dataset file: {fname}")
        return None
    try:
        return TrXASDataset(fname, ignore_incomplete=ignore_incomplete, load_cache=load_cache)
    except Exception as e:
        logger.error(f"[ERROR] Failed to load TrXASDataset from {fname}: {e}")
        return None


def create_trxas_cache_from_flist(flist, **kwargs):
    for fname in flist:
        create_trxas_cache(fname=fname, **kwargs)
    return


def create_trxas_cache(fname, ignore_incomplete=True, load_cache=True):
    if not fname.exists() or not is_sample_data(fname):
        logger.error(f"check dataset file: {fname}")
        return None
    try:
        cache_name, cache_exists = TrXASDataset.check_cache(fname)
        if not cache_exists:
            TrXASDataset(fname, ignore_incomplete=ignore_incomplete,
                         load_cache=load_cache)
            return cache_name
    except Exception as e:
        logger.error(f"[ERROR] Failed to load TrXASDataset from {fname}: {e}")
        return None


class TrXASDataset:
    def __init__(self, fname, ignore_incomplete=True, load_cache=True):
        self.fname = Path(fname)
        self.cache_name, cache_exists = self.check_cache(fname)
        self.dset_attributes = ["energy", "num_energys", "labels", "meta_data", 
                      "dset_type", "shape", "delta_t_ns", "xas_data_norm"]

        if load_cache and cache_exists:
            self.init_from_cache(self.cache_name)
        else:
            self.init_from_file(fname, ignore_incomplete=ignore_incomplete)
            if not self.cache_name.exists():
                self.save_to_cache()
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
        data = np.loadtxt(fname, comments="#", dtype=np.float32, delimiter="\t")
        self.num_energys = data.shape[0]
        self.labels = labels
        self.meta_data = data[:, labels_mask]
        self.dset_type = dset_type
        self.energy = self.get("Energy")

        xas_part = data[:, ~labels_mask]
        # fill the missing data with NaN, create a whole dataset
        xas_full = np.full((self.num_energys, np.prod(shape)), np.nan)
        xas_full[:, payload_mask] = xas_part
        if ignore_incomplete and np.prod(shape) != np.sum(payload_mask):
            # fix the incomplete dataset and remove all nan items
            xas_full, shape = fix_incomplete_dataset(payload_mask, shape, xas_full)

        self.shape = shape
        self.delta_t_ns = 1 / P0 / self.shape[2] * 1e9  # bunch time in ns
        self.xas_data = xas_full.reshape(self.num_energys, self.shape[0], -1)
        self.xas_data_norm = self.normalize()

    def get_energy_vs_time(self, channel=0, target="raw", norm_kwargs=None):
        if target == "raw":
            t_axis = np.arange(self.xas_data.shape[2]) * self.delta_t_ns 
            return self.xas_data[:, channel], self.energy, t_axis 
        elif target == "normalized":
            t_axis = np.arange(self.xas_data_norm.shape[1]) * self.delta_t_ns 
            return self.xas_data_norm, self.energy, t_axis 
        elif target == "normalized-GS":
            return self.process_energy(**norm_kwargs)
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
            self.num_energys, *self.shape
        )  # (rows, channel, orbital, bunch)
        ortial_mean_ch0 = np.nanmean(xas_data[:, 0], axis=1)  #  rows x bunch
        xas_data[:, 1:] /= ortial_mean_ch0[
            :, np.newaxis, np.newaxis, :
        ]  # normalize other channels
        norm_data = xas_data.reshape(self.num_energys, self.shape[0], -1)
        norm_data = np.mean(norm_data[:, 1:3], axis=(1,))  # average over channels 1 and 2
        return norm_data.astype(np.float32)

    @staticmethod
    def plot_and_save(save_name, diff, energy_axis, t_axis, title=None):
        plt.style.use('science')
        t_axis /= 1000  # convert to microseconds
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
        ax.set_ylabel("Time ($\\mu$s)")
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

    def process_energy(
        self,
        fileout=None,
        sync_type="time",
        sync_value=1820,
        pre_avg_orbitals=5,
        aft_avg_bunches=11,
        do_perbunch="per_bunch",
    ):
        if self.dset_type != "Energy":
            raise TypeError(
                f"Expect Energy scan, but the file is {self.dset_type} scan."
            )

        # average over the channels 1 and channel 2
        data = self.xas_data_norm  # num_energys * (orbitals * bunches)
        num_orbitals = self.shape[1]
        num_bunches = self.shape[2]

        def get_multiples(size, pos, unit_len):
            assert 0 < pos < size
            start = pos - pos // unit_len * unit_len
            end = pos + (size - pos) // unit_len * unit_len
            pos = pos - start
            return pos, slice(start, end)
        
        if sync_type == "time":
            sync_index = int(sync_value * 1000 / self.delta_t_ns) 
        else:
            sync_index = sync_value

        sync_index, slice_pre = get_multiples(
            num_bunches * num_orbitals, sync_index, num_bunches
        )
        data = data[:, slice_pre]  # num_energys * -1
        data = data.reshape(self.num_energys, -1, num_bunches)

        preavg_orbit_idx = sync_index // num_bunches
        preavg_slice = slice(
            max(0, preavg_orbit_idx - pre_avg_orbitals), preavg_orbit_idx
        )
        # average along orbitals
        preavg = np.mean(data[:, preavg_slice], axis=(1,))  # num_energys * bunches

        if do_perbunch == "per_bunch":
            diff = data - preavg[:, np.newaxis, :]
        elif do_perbunch == "avg_bunch":
            diff = data - np.mean(preavg, axis=1)[:, np.newaxis, np.newaxis]
        else:
            raise ValueError("Unknown do_perbunch value %s method")

        # apply binning
        num_elements = slice_pre.stop - slice_pre.start
        diff = diff.reshape(self.num_energys, -1)
        avg_delta_t_ns = self.delta_t_ns * aft_avg_bunches

        if aft_avg_bunches > 1:
            sync_index, slice_aft = get_multiples(num_elements, sync_index, aft_avg_bunches)
            diff = diff[:, slice_aft].reshape(self.num_energys, -1, aft_avg_bunches)
            diff = np.mean(diff, axis=(2,))

        t_offset = sync_index // aft_avg_bunches * avg_delta_t_ns
        t_axis = np.arange(0, diff.shape[1]) * avg_delta_t_ns - t_offset
        return diff, self.energy, t_axis 


if __name__ == "__main__":
    # read_trsaxs_dataset('/Users/mqichu/Documents/trxas/XTA_data/setup-full-00099')
    for n in range(1):
        t0 = time.perf_counter()
        fname = "/Users/mqichu/Documents/trxas/XTA_data/setup-full-00099"
        dset = TrXASDataset(fname)
        print(is_sample_data(fname))
        dset.normalize()
        # dset.plot()
        dset.process_energy()
        t1 = time.perf_counter()
        print(f"Time elapsed: {t1 - t0:.2f} seconds")
