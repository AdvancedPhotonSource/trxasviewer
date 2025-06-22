import numpy as np
import matplotlib.pyplot as plt
from .utilities import format_time


def _process_item(item):
    """
    Recursively processes an item to handle nested structures.
    - Converts numpy arrays to lists, unless they are int/float.
    - Recursively processes dictionaries and lists/tuples.
    """
    # If the item is a dictionary, process its values recursively
    if isinstance(item, dict):
        return {k: _process_item(v) for k, v in item.items()}

    # If the item is a list or tuple, process its elements recursively
    if isinstance(item, (list, tuple)):
        # Create a new list of the same type (list or tuple)
        return type(item)(_process_item(i) for i in item)

    # If the item is a numpy array, apply the conversion logic
    if isinstance(item, np.ndarray):
        # If it's a 0-d array wrapping an object, unwrap and process it
        if item.ndim == 0 and item.dtype == "object":
            return _process_item(item.item())
        # Keep int/float arrays as numpy arrays
        elif np.issubdtype(item.dtype, np.integer) or np.issubdtype(
            item.dtype, np.floating
        ):
            return item
        # Convert other array types (e.g., string, bool) to lists
        else:
            return item.tolist()

    # Return the item as is if it's any other type (e.g., int, str, float)
    return item


def convert_npz_obj(loaded_npz):
    """
    Converts numpy arrays from an .npz file into Python objects where applicable.
    """
    if isinstance(loaded_npz, dict):
        return loaded_npz
    else:
        python_dict = {}
        for key in loaded_npz.files:
            python_dict[key] = _process_item(loaded_npz[key])
        loaded_npz.close()
        return python_dict


def get_levels(data, percentile=(0.2, 99.8)):
    levels = np.percentile(data, percentile)
    vmax = np.max(np.abs(levels))
    levels = (-vmax, vmax)
    return levels


class TrXASResult:
    def __init__(self, npz_obj):
        data = convert_npz_obj(npz_obj)
        # transpose diff data so: axis 0: time, axis 1: energy/delay
        data["diff"] = data["diff"].T
        self.__dict__.update(data)
        self.svd = self.get_svd()
        self.kinetic_labels = list(data["kinetics"].keys())
        self.num_kinetic_profiles = len(self.kinetic_labels)

    def __getitem__(self, key):
        # add class["member"] access
        return self.__dict__[key]

    def describe(self):
        msg = "TrXASResult object with the following attributes:\n"
        msg += f"  - Energy: {self.energy.shape}, {np.min(self.energy)} - {np.max(self.energy)} keV\n"
        msg += f"  - Time axis: {self.t_axis.shape}, {np.min(self.t_axis)} - {np.max(self.t_axis)} s\n"
        msg += f"  - Difference map: {self.diff.shape}\n"
        print(msg)
        return

    def get_levels(self, percentile=(0.2, 99.2)):
        return get_levels(self.diff, percentile=percentile)

    def get_time_range_and_unit(self):
        tmin, tmax = np.min(self.t_axis), np.max(self.t_axis)
        _, tunit, scale = format_time(np.max(np.abs([tmin, tmax])), as_string=False)
        return tmin / scale, tmax / scale, tunit

    def get_fitted_line(self, concentration, spectra):
        y = concentration @ spectra  # N_t x 1
        xy = np.stack((self.t_axis, y[:, 0]))
        return xy

    def combined_fitting_data(
        self, concentration=None, spectra=None, h_gap=2, full_range=False
    ):
        """
        Computes the fit and residue, and compiles them with the original data
        for visualization, separated by horizontal gaps.
        """
        if concentration is None or spectra is None:
            fit = np.zeros_like(self.diff)
            residue = np.zeros_like(self.diff)
        else:
            fit = concentration @ spectra
            residue = self.diff - fit

        # Create a NaN-filled array for the horizontal gaps
        gap = np.full((self.diff.shape[0], h_gap), np.nan)

        cdata = np.hstack([self.diff, gap, fit, gap, residue])
        cdata = np.ascontiguousarray(np.flipud(cdata))

        cdata_valid = cdata[~np.isnan(cdata)]
        levels = get_levels(cdata_valid)
        return cdata, levels

    def get_diff_map(self):
        energy = self.x_axis["value"]
        return energy, self.t_axis, self.diff

    def plot_diff(self):
        plt.imshow(self.diff, cmap="coolwarm", origin="lower")
        plt.colorbar()
        plt.show()
        plt.close()

    def get_svd(self):
        begin_idx = np.where(self.t_axis >= 0)[0][0]
        u, s, v = np.linalg.svd(self.diff[begin_idx:], full_matrices=False)
        return (u, s, v)

    def get_svd_spectrum(self):
        return self.svd[1]

    def get_low_rank_approximation(self, rank=3):
        u, s, v = self.svd
        up = u[0:, :rank]
        sp = np.diag(s[0:rank])
        vp = v[:rank, 0:]
        return up @ sp @ vp

    def get_kinetic_profile(self, idx=0):
        label = self.kinetic_labels[idx]
        xy = self.data["kinetics"][label]["profile"]["main"]
        t_axis, diff, err = xy[0], xy[1], xy[2]
        diff = diff.reshape(-1, 1)
        err = err.reshape(-1, 1)
        return label, t_axis, diff, err

    def get_kinetic_data(self, target: str):
        if target == "global":
            return target, self.data["t_axis"], self.diff_raw, None
        elif target.startswith("profile"):
            idx = int(target.split(":")[1])
            return self.get_kinetic_profile(idx)


if __name__ == "__main__":
    f = "/Users/mqichu/Documents/trxas_data/kinetics_results/result_setup-full-00242-00258/results.npz"
    data = np.load(f, allow_pickle=True)
    tr = TrXASResult(data)
    label, x = tr.get_kinetic_profile()
    print(label, x.shape)
