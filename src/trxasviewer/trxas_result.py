import numpy as np
import matplotlib.pyplot as plt


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


class TrXASResult:
    def __init__(self, npz_obj):
        self.data = convert_npz_obj(npz_obj)
        self.energy, self.t_axis, self.diff = self.get_diff_map()
        self.svd = self.get_svd()
        # self.plot_diff()
        # self.describe()

    def describe(self):
        msg = "TrXASResult object with the following attributes:\n"
        msg += f"  - Energy: {self.energy.shape}, {np.min(self.energy)} - {np.max(self.energy)} keV\n"
        msg += f"  - Time axis: {self.t_axis.shape}, {np.min(self.t_axis)} - {np.max(self.t_axis)} s\n"
        msg += f"  - Difference map: {self.diff.shape}\n"
        print(msg)
        return

    def get_diff_map(self, valid_only=True):
        t_axis = self.data["t_axis"]
        energy = self.data["x_axis"]["value"]
        diff = self.data["diff"].T
        if valid_only:
            valid_mask = t_axis >= 0
            diff = diff[valid_mask]
            t_axis = t_axis[valid_mask]
        return energy, t_axis, diff

    def plot_diff(self):
        plt.imshow(self.diff, cmap="coolwarm", origin="lower")
        plt.colorbar()
        plt.show()
        plt.close()

    def get_svd(self):
        u, s, v = np.linalg.svd(self.diff, full_matrices=False)
        return (u, s, v)

    def get_svd_spectrum(self):
        return self.svd[1]

    def get_low_rank_approximation(self, rank=3):
        u, s, v = self.svd
        up = u[0:, :rank]
        sp = np.diag(s[0:rank])
        vp = v[:rank, 0:]
        return up @ sp @ vp


if __name__ == "__main__":
    f = "/Users/mqichu/Documents/trxas_data/kinetics_results/result_setup-full-00242-00258/results.npz"
    data = np.load(f, allow_pickle=True)
    tr = TrXASResult(data)
    e, t, diff = tr.get_diff_map()
    print(e.shape, t.shape, diff.shape)
