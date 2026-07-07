import numpy as np
from .utilities import format_time
import logging
import copy


logger = logging.getLogger(__name__)


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
        python_dict = loaded_npz
    else:
        python_dict = {}
        for key in loaded_npz.files:
            python_dict[key] = _process_item(loaded_npz[key])
        loaded_npz.close()
    return copy.deepcopy(python_dict)


def get_levels(data, percentile=(0.2, 99.8)):
    """Compute symmetric color-scale bounds from percentiles of the data.

    Args:
        data: Array from which to compute levels.
        percentile: ``(low, high)`` percentile pair. Default ``(0.2, 99.8)``.

    Returns:
        Tuple ``(-vmax, vmax)`` where vmax is the larger absolute percentile value.
    """
    levels = np.percentile(data[~np.isnan(data)], percentile)
    vmax = np.max(np.abs(levels))
    levels = (-vmax, vmax)
    return levels


class TrXASResult:
    """Container for a processed TrXAS result.

    Provides convenience accessors for the difference map, kinetics profiles,
    SVD decomposition, and fitting results.
    """

    def __init__(self, npz_obj):
        """Load a result from an NPZ archive or a plain dict.

        The ``diff`` array is transposed on load so that axis 0 is time and axis 1 is
        energy/delay.

        Args:
            npz_obj: Either a :class:`numpy.lib.npyio.NpzFile` object or a plain dict
                with the same keys (as returned by
                :meth:`TrXASDatasetManager.get_energy_vs_time`).
        """
        data = convert_npz_obj(npz_obj)
        # transpose diff data so: axis 0: time, axis 1: energy/delay
        data["diff"] = data["diff"].T
        self.__dict__.update(data)
        self._svd = None
        self.kinetic_labels = list(data["kinetics"].keys())
        self.num_kinetic_profiles = len(self.kinetic_labels)
        self.fitting_results = {}

    def __getitem__(self, key):
        """Allow dict-style attribute access via ``result["key"]``."""
        return self.__dict__[key]

    def describe(self):
        """Print a human-readable summary of the result's shape and axis ranges."""
        msg = "TrXASResult object with the following attributes:\n"
        msg += f"  - Energy: {self.energy.shape}, {np.min(self.energy)} - {np.max(self.energy)} keV\n"
        msg += f"  - Time axis: {self.t_axis.shape}, {np.min(self.t_axis)} - {np.max(self.t_axis)} s\n"
        msg += f"  - Difference map: {self.diff.shape}\n"
        print(msg)
        return

    def get_levels(self, percentile=(0.2, 99.2)):
        """Return symmetric color-scale bounds using the stored difference map."""
        return get_levels(self.diff, percentile=percentile)

    def get_time_range_and_unit(self):
        """Return the time axis range in human-readable units.

        Returns:
            Tuple ``(tmin, tmax, unit_string)`` where tmin and tmax are expressed in
            the auto-selected unit (ns, µs, ms, or s).
        """
        tmin, tmax = np.min(self.t_axis), np.max(self.t_axis)
        _, tunit, scale = format_time(np.max(np.abs([tmin, tmax])), as_string=False)
        return tmin / scale, tmax / scale, tunit

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

    def plot_diff(self):
        """Plot the difference map to the current matplotlib figure."""
        import matplotlib.pyplot as plt
        plt.imshow(self.diff, cmap="coolwarm", origin="lower")
        plt.colorbar()
        plt.show()
        plt.close()

    @property
    def svd(self):
        """Singular-value decomposition of the difference map, computed on first access.

        Returns:
            Tuple ``(U, S, Vt)`` from :func:`numpy.linalg.svd`.
        """
        if self._svd is None:
            self._svd = self._compute_svd()
        return self._svd

    def _compute_svd(self):
        """Compute the SVD of the trimmed difference map and cache it."""
        begin_idx = np.where(self.t_axis >= 0)[0][0]
        u, s, v = np.linalg.svd(self.diff[begin_idx:], full_matrices=False)
        return (u, s, v)

    def get_svd_spectrum(self):
        """Return the right singular vectors (spectral components) from the SVD."""
        return self.svd[1]

    def get_low_rank_approximation(self, rank=3):
        """Return a rank-reduced reconstruction of the difference map.

        Args:
            rank: Number of singular components to retain. Default 3.

        Returns:
            Reconstructed difference map of the same shape as ``self.diff``.
        """
        u, s, v = self.svd
        up = u[0:, :rank]
        sp = np.diag(s[0:rank])
        vp = v[:rank, 0:]
        return up @ sp @ vp

    def get_diff_map(self):
        """Return the difference map array (time × energy)."""
        payload = {
            "t_axis": self.t_axis,  # N_time,
            "diff": self.diff,  # N_time X N_energy
            "err": None,
        }
        return {"global": payload}

    def get_kinetic_profile(self, label):
        """Return the kinetics profile for a given ROI label.

        Args:
            label: ROI label string (e.g. ``"ROI1"``).

        Returns:
            Dict with keys ``"profile"`` and optionally ``"err"``.
        """
        t_axis, diff, err = self.kinetics[label]["profile"]["main"]
        payload = {
            "t_axis": t_axis,
            "diff": diff.reshape(-1, 1),  # needs to be (N_time X N_energy)
            "err": err.reshape(-1, 1),
        }
        return {label: payload}

    def get_kinetic_data(
        self,
        bsl_trange=None,
        bsl_mode="Disabled",
        fit_method="IndividualFit",
        **kwargs,
    ):
        """Prepare kinetics data for fitting.

        Args:
            bsl_trange: Time range for baseline subtraction (seconds). If None, disabled.
            bsl_mode: Baseline correction mode. Default ``"Disabled"``.
            fit_method: ``"IndividualFit"`` or ``"JointFit"``.
            **kwargs: Additional fit configuration options.

        Returns:
            Dict containing the formatted kinetics data and metadata for the fitter.
        """
        # assemble fitting data
        all_data = {}
        all_data.update(self.get_diff_map())
        for kp_label in self.kinetic_labels:
            all_data.update(self.get_kinetic_profile(kp_label))

        if fit_method == "IndividualFit":
            logger.info(
                f"Using {fit_method}: the fitting of global map and kinetics profiles will be done independently."
            )
            fit_pack = {
                "num_payloads": len(all_data),
                "fit_method": fit_method,
                "payloads": all_data,
            }
        elif fit_method == "JointFit":
            logger.info(
                f"Using {fit_method}: combine all input data and use the same set of parameters for fitting."
            )
            all_diff = [value["diff"] for value in all_data.values()]
            all_size = [x.shape[1] for x in all_diff]
            labels = list(all_data.keys())
            indexes = [0] + np.cumsum(all_size).tolist()
            slices = [slice(indexes[i], indexes[i + 1]) for i in range(len(all_size))]
            fit_pack = {
                "fit_method": fit_method,
                "num_payloads": 1,
                "slices": slices,  # extra fields to decompress the results
                "labels": labels,
                "payloads": {
                    "joint": {
                        "diff": np.hstack(all_diff),
                        "t_axis": all_data["global"]["t_axis"],
                        "err": None,
                    },
                },
            }
        return fit_pack

    def reset_fitting_result(self):
        """Clear all stored fitting results."""
        self.fitting_results = {}

    def append_fitting_result(self, key, fit_result: dict, fit_pack: dict):
        """Store the output of a kinetic fit.

        Args:
            key: ROI label (e.g. ``"ROI1"``).
            fit_result: Dict returned by :func:`global_fit_kinetic_model`.
            fit_pack: Dict describing the fit configuration (method, slices, labels).
        """
        fit_method = fit_pack["fit_method"]
        if fit_method == "IndividualFit":
            self.fitting_results.update({key: fit_result})
        elif fit_method == "JointFit":
            slices, labels = fit_pack.get("slices"), fit_pack.get("labels")
            named_results = {}
            for sl, label in zip(slices, labels):
                spectra = fit_result["spectra"][:, sl]  # get the correspoing spectra
                named_results[label] = {
                    "params": fit_result["params"],
                    "concentrations": fit_result["concentrations"],
                    "spectra": spectra,
                    "fitted": fit_result["concentrations"] @ spectra,
                }
            self.fitting_results.update(named_results)

    def get_fitted_kinetic_profiles(self):
        """Return fitted kinetics curves for all ROIs.

        Returns:
            Dict mapping each ROI label to a ``(2, N)`` array of ``[time, fitted_signal]``.
        """
        result = {}
        for key in self.kinetic_labels:
            x = self.t_axis.flatten()
            y = self.fitting_results[key]["fitted"].flatten()
            result[key] = np.stack([x, y])
        return result


if __name__ == "__main__":
    f = "/Users/mqichu/Documents/trxas_data/kinetics_results/result_setup-full-00242-00258/results.npz"
    data = np.load(f, allow_pickle=True)
    tr = TrXASResult(data)
    label, x = tr.get_kinetic_profile()
