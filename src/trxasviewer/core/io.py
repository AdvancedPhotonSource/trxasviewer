import json
import shutil
import numpy as np
import h5py
from pathlib import Path


def save_as_origin_format(origin_folder, results):
    for key, label in zip(("data", "diff"), ("data_full", "data_diff")):
        temp = results[key]
        shape = temp.shape
        data_full = np.zeros(np.array(shape) + 1, dtype=np.float32)
        data_full[1:, 1:] = temp
        data_full[1:, 0] = results["x_axis"]["value"]
        data_full[0, 1:] = results["t_axis"]
        data_full = data_full.astype(object)
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
            comments="",
        )


def save_as_json(fname, results):
    with open(fname, "w") as f:
        json.dump(results["analysis_kwargs"], f, indent=4)


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


def save_results(
    results,
    directory=None,
    subdirectory="Avg",
    save_image=True,
    save_numpy=True,
    save_hdf=True,
    save_origin=True,
):
    from trxasviewer.core.plot import plot_results  # imported here to avoid circular import

    folder = Path(directory) / subdirectory
    folder.mkdir(parents=True, exist_ok=True)

    if save_numpy:
        np.savez_compressed(folder / "results.npz", **results)
        package_path = Path(__file__).parent
        shutil.copy(package_path / "plot.py", folder / "load_and_plot.py")

    if save_image:
        img_folder = folder / "images"
        img_folder.mkdir(parents=True, exist_ok=True)
        plot_results(results, folder=img_folder)

    if save_origin:
        o_folder = folder / "origin"
        o_folder.mkdir(parents=True, exist_ok=True)
        save_as_origin_format(o_folder, results)

    if save_hdf:
        save_as_hdf5(folder / "results.hdf", results)

    save_as_json(folder / "settings.json", results)
