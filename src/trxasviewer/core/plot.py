import logging
from itertools import cycle
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter1d

logging.getLogger("fontTools.subset").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)

FIG_WIDTH = 4.8  # inches
FIG_HEIGHT = FIG_WIDTH / 1.618033988749
FIG_TYPES = (".png", ".pdf")
SAVE_DPI = 600

_MPL_CONFIGURED = False


def _configure_matplotlib():
    """Import and configure matplotlib on first use (safe for headless environments)."""
    global _MPL_CONFIGURED
    if _MPL_CONFIGURED:
        return
    import matplotlib.pyplot as plt
    try:
        import scienceplots  # noqa: F401 — registers matplotlib styles
        plt.style.use(["science", "no-latex"])
    except ImportError:
        pass
    plt.rcParams["pdf.fonttype"] = 42  # TrueType fonts for Illustrator compatibility
    plt.rcParams["font.size"] = 7
    plt.rcParams["font.sans-serif"] = "Arial"
    _MPL_CONFIGURED = True


def convert_time_array_human_readable(time_array, prefix="Time"):
    """
    Convert a NumPy array of times (in seconds) to a human-readable scale,
    using the largest appropriate unit based on the maximum absolute value.

    Parameters
    ----------
    time_array : numpy.ndarray
        Input array representing time in seconds.
    prefix : str, optional
        Label prefix to include in the returned unit string. Default is "Time".

    Returns
    -------
    converted_array : numpy.ndarray
        The time array scaled to human-readable units.
    unit : str
        String label of the new time unit (e.g., "Time (ms)").
    """
    labels = [
        (f"{prefix} (s)", 1),
        (f"{prefix} (ms)", 1e-3),
        (f"{prefix} (µs)", 1e-6),
        (f"{prefix} (ns)", 1e-9),
        (f"{prefix} (ps)", 1e-12),
        (f"{prefix} (fs)", 1e-15),
        (f"{prefix} (as)", 1e-18),
    ]

    max_abs = np.max(np.abs(time_array))

    for label, factor in labels:
        if max_abs >= factor:
            return time_array / factor, label

    return time_array, f"{prefix} (s)"


def plot_results(results, folder=None):
    """
    Plot the results of a TRXAS analysis and save the figures.

    Parameters
    ----------
    results : dict
        Dictionary containing keys like 'data', 'diff', 'kinetics', 'x_axis', 't_axis'.
    folder : str or pathlib.Path, optional
        Directory to save plots. If None, uses current working directory.

    Returns
    -------
    None
    """
    _configure_matplotlib()
    if folder is None:
        folder = Path(".")
    else:
        folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    x_axis = results["x_axis"]
    t_axis = results["t_axis"]
    plot_2d_scan(folder / "data_full", results["data"], x_axis, t_axis)
    plot_2d_scan(
        folder / "data_diff", results["diff"], x_axis, t_axis, force_symmetry=True
    )
    plot_kinetics(folder / "kinetics", results["kinetics"])


def plot_2d_scan(save_name, diff, x_axis_obj, t_axis, title=None, force_symmetry=False):
    """
    Plot a 2D scan using the provided data and axis information.

    Parameters
    ----------
    save_name : pathlib.Path
        The base filename (without extension) to save the plot to.
    diff : numpy.ndarray
        A 2D array of the scan data to be plotted.
    x_axis_obj : dict
        Dictionary containing x-axis data:
            - "value": 1D numpy array of x-axis values.
            - "label": str, x-axis label, e.g., "Energy".
    t_axis : numpy.ndarray
        A 1D array representing the time or vertical axis.
    title : str, optional
        Plot title. Default is None.
    force_symmetry : bool, optional
        Whether to force symmetry in color scale about 0. Default is False.

    Returns
    -------
    None
    """
    _configure_matplotlib()
    import matplotlib.pyplot as plt
    t_axis, ylabel = convert_time_array_human_readable(t_axis, "Time")
    x_axis = x_axis_obj["value"]
    data = np.flipud(diff.T)

    if x_axis_obj["label"] != "Energy":
        x_axis, xlabel = convert_time_array_human_readable(x_axis, "Delay")
        extent = (x_axis[0], x_axis[-1], t_axis[0], t_axis[-1])
    else:
        xlabel = "Energy (keV)"
        extent = (0, data.shape[1] - 1, t_axis[0], t_axis[-1])

    vmin, vmax = np.percentile(data, [0.5, 99.5])
    if force_symmetry:
        vmin = min(vmin, -vmax)
        vmax = -1 * vmin

    fig, ax = plt.subplots(1, 1, figsize=(FIG_WIDTH, FIG_HEIGHT))
    im = ax.imshow(data, extent=extent, aspect="auto", cmap="bwr", vmin=vmin, vmax=vmax)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if x_axis_obj["label"] == "Energy":
        filtered = gaussian_filter1d(np.mean(data, axis=0), sigma=2)
        i_peak = np.argmax(filtered)
        xticks = [0, data.shape[1] - 1, i_peak]
        xtick_labels = [x_axis[n] for n in xticks]
        ax.set_xticks(xticks)
        ax.set_xticklabels(xtick_labels)

    ax.set_title(title)
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Intensity (a.u.)")
    plt.tight_layout()
    for ftype in FIG_TYPES:
        name = save_name.with_suffix(ftype)
        plt.savefig(name, dpi=SAVE_DPI)
    plt.close(fig)


def plot_2d_scan_equal_energy(
    save_name, diff, x_axis_obj, t_axis, title=None, force_symmetry=False
):
    """
    Plot a 2D scan using `pcolormesh`, preserving axis scaling based on energy/time values.

    Parameters
    ----------
    save_name : str or pathlib.Path
        Filename to save the plot.
    diff : numpy.ndarray
        A 2D array of data values.
    x_axis_obj : dict
        Dictionary with keys:
            - "value": 1D numpy array for x-axis.
            - "label": description (e.g., "Energy").
    t_axis : numpy.ndarray
        1D array representing time axis.
    title : str, optional
        Title of the plot. Default is None.
    force_symmetry : bool, optional
        Force symmetric color scale around zero. Default is False.

    Returns
    -------
    None
    """
    _configure_matplotlib()
    import matplotlib.pyplot as plt
    t_axis, ylabel = convert_time_array_human_readable(t_axis, "Time")
    x_axis = x_axis_obj["value"]

    if x_axis_obj["label"] != "Energy":
        x_axis, xlabel = convert_time_array_human_readable(x_axis, "Delay")
    else:
        xlabel = "Energy (keV)"

    data = np.flipud(diff.T)
    vmin, vmax = np.percentile(data, [0.5, 99.5])
    if force_symmetry:
        vmin = min(vmin, -vmax)
        vmax = -1 * vmin

    fig, ax = plt.subplots(1, 1, figsize=(FIG_WIDTH, FIG_HEIGHT))
    T, E = np.meshgrid(t_axis, x_axis, indexing="ij")
    im = ax.pcolormesh(E, T, data, shading="auto", cmap="bwr", vmin=vmin, vmax=vmax)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Intensity (a.u.)")
    plt.tight_layout()
    plt.savefig(save_name, dpi=SAVE_DPI)
    plt.close(fig)


def plot_kinetics(save_name, data_list):
    """
    Plot Delay vs Intensity curves with optional error bars for each trace.

    Parameters
    ----------
    save_name : pathlib.Path or str
        Prefix for saved figure file.
    data_list : dict
        Dictionary where each value contains:
            - 'profile': 2D array of shape (2, N) or (3, N).
            - 'long_label': str, label for the curve.

    Returns
    -------
    None
    """
    _configure_matplotlib()
    import matplotlib.pyplot as plt
    markers = cycle(["o", "s", "D", "^", "v", "*", "P", "X"])
    colors = cycle(plt.cm.tab10.colors)

    fig, ax = plt.subplots(1, 1, figsize=(FIG_WIDTH, FIG_HEIGHT))

    for val in data_list.values():
        data = val["profile"]
        label = val["long_label"]
        marker = next(markers)
        color = next(colors)
        t_axis, t_label = convert_time_array_human_readable(data["main"][0], "Time")
        if data["main"].shape[0] == 3:
            ax.errorbar(
                t_axis,
                data["main"][1],
                yerr=data["main"][2],
                fmt=marker + "-",
                capsize=1,
                label=label,
                color=color,
                markerfacecolor="none",
                markersize=1,
            )
        else:
            ax.plot(data["main"][0], data["main"][1], marker + "-", label=label, color=color)

    ax.set_xlabel(t_label)
    ax.set_ylabel("Intensity (a.u.)")
    ax.legend()
    ax.grid(True)
    plt.tight_layout()
    for ftype in FIG_TYPES:
        name = save_name.with_suffix(ftype)
        plt.savefig(name, dpi=SAVE_DPI)
    plt.close(fig)


def describe_structure(obj, indent=0, max_elements=10):
    """
    Recursively print the structure of a nested Python object (e.g., dict from npz file).

    Parameters
    ----------
    obj : any
        Object to describe (typically a dict or list with arrays).
    indent : int, optional
        Indentation level for nested structures. Default is 0.
    max_elements : int, optional
        Maximum number of elements to print from lists/tuples. Default is 10.

    Returns
    -------
    None
    """
    pad = "  " * indent
    if isinstance(obj, dict):
        for key, value in obj.items():
            print(f"{pad}{key}:")
            describe_structure(value, indent + 1, max_elements)
    elif isinstance(obj, (list, tuple)):
        print(f"{pad}{type(obj).__name__} of length {len(obj)}")
        for i, item in enumerate(obj[:max_elements]):
            print(f"{pad}[{i}]:")
            describe_structure(item, indent + 1, max_elements)
        if len(obj) > max_elements:
            print(f"{pad}... (and {len(obj) - max_elements} more)")
    elif isinstance(obj, np.ndarray):
        if obj.size > 10:
            print(f"{pad}ndarray shape={obj.shape}, dtype={obj.dtype}")
        else:
            print(f"{pad}{obj}")
    else:
        print(f"{pad}{repr(obj)}")


def unpack_npz_object(obj):
    """
    Recursively unpack objects loaded from npz files, especially those pickled
    as object arrays, converting them into native Python types.

    Parameters
    ----------
    obj : any
        Loaded object (could be dict, array, list, etc.)

    Returns
    -------
    unpacked : any
        Unpacked native Python object (dict, list, etc.)
    """
    if isinstance(obj, np.ndarray) and obj.dtype == object:
        if obj.shape == ():
            return unpack_npz_object(obj.item())
        elif obj.shape == (1,):
            return unpack_npz_object(obj[0])
        else:
            return [unpack_npz_object(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: unpack_npz_object(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return type(obj)(unpack_npz_object(i) for i in obj)
    return obj


def load_npz_as_dict(npz_file):
    """
    Load a NumPy `.npz` file and recursively unpack all contained objects.

    Parameters
    ----------
    npz_file : str or pathlib.Path
        Path to the .npz file to load.

    Returns
    -------
    results : dict
        Dictionary with all top-level keys unpacked to native types.
    """
    raw = np.load(npz_file, allow_pickle=True)
    results = {k: unpack_npz_object(v) for k, v in raw.items()}
    return results


def load_and_plot(result_file_name):
    """
    Load results from a .npz file and show its structure.

    Parameters
    ----------
    result_file_name : str or pathlib.Path
        Path to the `.npz` results file.

    Returns
    -------
    None
    """
    _configure_matplotlib()
    results = load_npz_as_dict(result_file_name)
    describe_structure(results)
    plot_results(results, "images")
    # put plots in the same folder as the results file
    # plot_results(results)


if __name__ == "__main__":
    load_and_plot("results.npz")
