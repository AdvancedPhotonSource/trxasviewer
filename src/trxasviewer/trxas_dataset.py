import re
import time
from functools import lru_cache

import matplotlib.pyplot as plt
import numpy as np

TRXAS_PATTERN = re.compile(r"c(\d+)o(\d+)b(\d+)")
P0 = 271555.0  # 271.555 kHz is P0 for APS, i.e. frequency of orbits


def is_sample_data(fname):
    with open(fname, "r") as f:
        line = f.readline()
        if re.match(r"#L .* Energy ", line):
            return True
        else:
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
        self.dsets_cache = {}
        self.ignore_incomplete = ignore_incomplete
        self.energy_axis = None
        self.delta_t_ns = None
        self.data_avg = None
        self.analysis_kwargs = None

    def update_flist(self, flist):
        self.flist = flist

    def save_results(self, fname):
        if self.analysis_kwargs is None:
            return

        results = {
            "flist": self.flist,
            "analysis_type": "average_energy_vs_time",
            "diff_data": self.data_avg,
            "analysis_kwargs": self.analysis_kwargs,
            "energy_axis": self.energy_axis,
            "delta_t_ns": self.delta_t_ns,
        }
        np.savez(fname, **results)

    def get_energy_vs_time(self, **kwargs):
        if len(self.flist) == 0:
            return None, None, None
        self.analysis_kwargs = kwargs
        data = []
        shapes = []
        for fname in self.flist:
            if fname not in self.dsets_cache:
                self.dsets_cache[fname] = TrXASDataset(fname, self.ignore_incomplete)
            t_data, energy, dt_ns = self.dsets_cache[fname].get_energy_vs_time(**kwargs)
            data.append(t_data)
            shapes.append(t_data.shape)

        shapes = np.array(shapes)
        shape_full = np.max(shapes, axis=0)
        data_full = np.full((len(self.flist), *shape_full), np.nan)

        for i, d in enumerate(data):
            data_full[i, : d.shape[0], : d.shape[1]] = d
        data_avg = np.nanmean(data_full, axis=0)

        good_idx = np.argmin(np.prod(shapes, axis=1) == np.prod(shape_full))

        self.energy_axis = self.dsets_cache[self.flist[good_idx]].energy
        self.delta_t_ns = self.dsets_cache[self.flist[good_idx]].delta_t_ns
        self.data_avg = data_avg
        return data_avg, self.energy_axis, self.delta_t_ns


class TrXASDataset:
    def __init__(self, fname, ignore_incomplete=True):
        self.fname = fname
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
        self.delta_t_ns = 1 / P0 / self.shape[2] * 1e9
        self.xas_data = xas_full.reshape(self.num_energys, self.shape[0], -1)
        self.xas_data_norm = self.normalize()
        self.xas_data_subgs = None

    def get_energy_vs_time(self, channel=0, target="raw", norm_kwargs=None):
        if target == "raw":
            return self.xas_data[:, channel], self.energy, self.delta_t_ns
        elif target == "normalized":
            return self.xas_data_norm, self.energy, self.delta_t_ns
        elif target == "normalized-GS":
            if self.xas_data_subgs is None or norm_kwargs != self.xas_data_subgs.get(
                "norm_kwargs"
            ):
                avg, diff, dt_ns = self.process_energy(**norm_kwargs)
                self.xas_data_subgs = {
                    "norm_kwargs": norm_kwargs,
                    "avg_data": avg,
                    "diff_data": diff,
                    "dt_ns": dt_ns,
                }
            return (
                self.xas_data_subgs["diff_data"],
                self.energy,
                self.xas_data_subgs["dt_ns"],
            )
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
        return np.mean(norm_data[:, 1:3], axis=(1,))  # average over channels 1 and 2

    def plot(self, channel=0, orbital=0, bunch=0):
        num_channels = self.shape[0]
        fig, ax = plt.subplots(1, num_channels, figsize=(4 * num_channels, 3))
        extent = (self.energys[0], self.energys[-1], 0, np.prod(self.shape[1:]))

        for i in range(num_channels):
            ax[i].imshow(self.xas_data[:, i].T, aspect="auto", extent=extent)
            ax[i].set_title(f"Channel {i}")
            ax[i].set_xlabel("Energy (keV)")
            ax[i].set_ylabel("XAS")
        plt.show()

    def process_energy(
        self,
        fileout=None,
        trig_index=1820,
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

        trig_index, slice_pre = get_multiples(
            num_bunches * num_orbitals, trig_index, num_bunches
        )
        data = data[:, slice_pre]  # num_energys * -1
        data = data.reshape(self.num_energys, -1, num_bunches)

        preavg_orbit_idx = trig_index // num_bunches
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
        result = []
        num_elements = slice_pre.stop - slice_pre.start
        bin_index, slice_aft = get_multiples(num_elements, trig_index, aft_avg_bunches)
        for x in [data, diff]:
            x = x.reshape(self.num_energys, -1)
            x = x[:, slice_aft].reshape(self.num_energys, -1, aft_avg_bunches)
            x = np.mean(x, axis=(2,))
            result.append(x)
        return result[0], result[1], self.delta_t_ns * aft_avg_bunches


if __name__ == "__main__":
    # read_trsaxs_dataset('/Users/mqichu/Documents/trxas/XTA_data/setup-full-00099')
    for n in range(1):
        t0 = time.perf_counter()
        dset = TrXASDataset("/Users/mqichu/Documents/trxas/XTA_data/setup-full-00099")
        dset.normalize()
        # dset.plot()
        dset.process_energy()
        t1 = time.perf_counter()
        print(f"Time elapsed: {t1 - t0:.2f} seconds")
