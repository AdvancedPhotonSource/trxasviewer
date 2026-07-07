import json
import shutil
import numpy as np
import h5py
from pathlib import Path


def save_as_origin_format(origin_folder, results):
    """Save difference map and kinetics as OriginLab-compatible CSV files.

    Writes two 2-D arrays (``data_full.txt``, ``data_diff.txt``) where the first
    row holds the time axis and the first column holds the energy/delay axis.
    One kinetics file per ROI label is also written.

    Args:
        origin_folder: Destination directory (must already exist).
        results: Processed results dict from :class:`TrXASDatasetManager`.
    """
    corner_label = "Energy(keV)/Time(s)" if results["dset_type"] == "EXAFS" else "Delay(s)/Time(s)"
    for key, label in zip(("data", "diff"), ("data_full", "data_diff")):
        temp = results[key]
        shape = temp.shape
        data_full = np.zeros(np.array(shape) + 1, dtype=np.float32)
        data_full[1:, 1:] = temp
        data_full[1:, 0] = results["x_axis"]["value"]
        data_full[0, 1:] = results["t_axis"]
        data_full = data_full.astype(object)
        data_full[0, 0] = corner_label
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
            comments="",
        )


def save_as_json(fname, results):
    """Save the analysis settings from a results dict to a JSON file.

    Args:
        fname: Destination file path.
        results: Processed results dict; only ``results["analysis_kwargs"]`` is saved.
    """
    with open(fname, "w") as f:
        json.dump(results["analysis_kwargs"], f, indent=4)


def save_as_hdf5(fname, results_raw):
    """Save a results dict to an HDF5 file, recursively mirroring its structure.

    Dicts become HDF5 groups. Numeric numpy arrays larger than 4 KiB are stored
    with gzip compression. Object-dtype arrays and lists are stored as UTF-8 string
    datasets.

    Args:
        fname: Destination ``.hdf`` file path.
        results_raw: Processed results dict from :class:`TrXASDatasetManager`.
    """
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
                elif isinstance(value, (list, tuple)):
                    # Convert lists to string arrays (e.g. flist, labels)
                    try:
                        arr = np.array([str(v) for v in value])
                        string_dt = h5py.string_dtype(encoding="utf-8")
                        group.create_dataset(key, data=arr, dtype=string_dt)
                    except Exception:
                        pass
                else:
                    compression = None
                    if isinstance(value, np.ndarray):
                        if value.dtype == object:
                            # Convert object arrays to UTF-8 string datasets
                            try:
                                arr = value.astype(str)
                                string_dt = h5py.string_dtype(encoding="utf-8")
                                group.create_dataset(key, data=arr, dtype=string_dt)
                                continue
                            except Exception:
                                continue  # skip unconvertible object arrays
                        value = np.ascontiguousarray(value)
                        compression = "gzip" if value.size > 4096 else None
                    group.create_dataset(key, data=value, compression=compression)

    with h5py.File(fname, "w") as f:
        save_recursively(f, results)


def save_results_with_progress(results, kwargs, progress=None):
    """Save results to disk, emitting progress strings at each step.

    Args:
        results: raw results dict from TrXASDatasetManager
        kwargs: save options (directory, subdirectory, save_image, save_numpy, save_hdf, save_origin)
        progress: optional callable(str) for status updates
    """
    from trxasviewer.core.plot import plot_results  # deferred to avoid circular import

    directory = kwargs.get("directory")
    subdirectory = kwargs.get("subdirectory", "Avg")
    save_image = kwargs.get("save_image", True)
    save_numpy = kwargs.get("save_numpy", True)
    save_hdf = kwargs.get("save_hdf", True)
    save_origin = kwargs.get("save_origin", True)

    def emit(msg):
        if progress:
            progress(msg)

    folder = Path(directory) / subdirectory
    folder.mkdir(parents=True, exist_ok=True)

    if save_numpy:
        emit("Saving NPZ…")
        tmp = folder / "results.tmp.npz"
        np.savez_compressed(tmp, **results)
        tmp.replace(folder / "results.npz")          # atomic rename
        shutil.copy(Path(__file__).parent / "plot.py", folder / "load_and_plot.py")

    if save_image:
        emit("Saving images…")
        img_folder = folder / "images"
        img_folder.mkdir(parents=True, exist_ok=True)
        plot_results(results, folder=img_folder)

    if save_origin:
        emit("Saving Origin format…")
        o_folder = folder / "origin"
        o_folder.mkdir(parents=True, exist_ok=True)
        save_as_origin_format(o_folder, results)

    if save_hdf:
        emit("Saving HDF5…")
        save_as_hdf5(folder / "results.hdf", results)

    emit("Saving settings…")
    save_as_json(folder / "settings.json", results)
    emit("Saved.")


def save_results(
    results,
    directory=None,
    subdirectory="Avg",
    save_image=True,
    save_numpy=True,
    save_hdf=True,
    save_origin=True,
):
    """Backward-compatible wrapper around save_results_with_progress."""
    save_results_with_progress(results, {
        "directory": directory,
        "subdirectory": subdirectory,
        "save_image": save_image,
        "save_numpy": save_numpy,
        "save_hdf": save_hdf,
        "save_origin": save_origin,
    })
