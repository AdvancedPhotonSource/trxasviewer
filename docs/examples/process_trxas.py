"""
Example: process TrXAS datasets headlessly (no GUI required).

Run this script from the command line or adapt it for a Jupyter notebook.
"""
from pathlib import Path

# All core symbols are available from trxasviewer.core — no Qt dependency
from trxasviewer.core import (
    TrXASDataset,
    TrXASDatasetManager,
    TrXASResult,
    save_results,
)

DATA_DIR = Path("/home/beams/MQICHU/Datasets/trxas_datasets/Dugan_2024_3_saveddata")
SAVE_DIR = Path("/tmp/trxas_output")


# ── Common processing kwargs ──────────────────────────────────────────────────

NORM_KWARGS = {
    "sync_type": "bunch",
    "sync_value": 1820,          # bunch index where the laser fires
    "gs_method": "bunch-average",
    "gs_value": 5,               # number of pre-laser bunches for ground state
}
BINNING_KWARGS = {
    "method": "Linear",
    "lin_num": 5,                # bin every 5 bunches
}
KINETICS_KWARGS = {
    "ROI1": {"center_energy": 7.126, "delta_energy": 0.002, "enabled": True,  "label": "ROI1"},
    "ROI2": {"center_energy": 7.131, "delta_energy": 0.002, "enabled": False, "label": "ROI2"},
    "ROI3": {"center_energy": 7.136, "delta_energy": 0.002, "enabled": False, "label": "ROI3"},
    "ROI4": {"center_energy": 7.141, "delta_energy": 0.002, "enabled": False, "label": "ROI4"},
}


# ── Single file ───────────────────────────────────────────────────────────────

def process_single(fname: Path):
    dset = TrXASDataset(fname)
    results = dset.get_energy_vs_time(
        target="normalized-GS",
        norm_kwargs=NORM_KWARGS,
        binning_kwargs=BINNING_KWARGS,
        kinetics_kwargs=KINETICS_KWARGS,
    )
    print(f"Loaded: {fname.name}")
    print(f"  scan type  : {results['dset_type']}")
    print(f"  diff shape : {results['diff'].shape}  (energy × time)")
    print(f"  time range : {results['t_axis'][0]*1e6:.1f} – {results['t_axis'][-1]*1e6:.1f} µs")
    return results


# ── Average multiple files ────────────────────────────────────────────────────

def average_files(flist: list[Path]):
    manager = TrXASDatasetManager()
    manager.update_flist(flist)
    avg = manager.get_energy_vs_time(
        target="normalized-GS",
        norm_kwargs=NORM_KWARGS,
        binning_kwargs=BINNING_KWARGS,
        kinetics_kwargs=KINETICS_KWARGS,
    )
    print(f"Averaged {len(flist)} files → label: {avg['label']}")
    return avg


# ── Work with TrXASResult ─────────────────────────────────────────────────────

def inspect_result(results: dict):
    res = TrXASResult(results)
    print(f"Diff map      : {res.diff.shape}  (time × energy after transpose)")
    print(f"SVD singular values: {res.svd[1][:5].round(3)}")  # computed lazily
    for label in res.kinetic_labels:
        profile = res.get_kinetic_profile(label)
        print(f"  Kinetics {label}: {profile['profile'].shape}")
    return res


# ── Save ──────────────────────────────────────────────────────────────────────

def save(results: dict, subdirectory: str = "Avg"):
    save_results(
        results,
        directory=SAVE_DIR,
        subdirectory=subdirectory,
        save_image=False,       # set True to generate PNG/PDF plots
        save_numpy=True,
        save_hdf=True,
        save_origin=True,
    )
    print(f"Saved to {SAVE_DIR / subdirectory}/")


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Single file
    single_results = process_single(DATA_DIR / "setup-full-00178")
    inspect_result(single_results)
    save(single_results, subdirectory="Single")

    # Average a range
    flist = [DATA_DIR / f"setup-full-{n:05d}" for n in range(178, 183)]
    flist = [f for f in flist if f.exists()]
    if flist:
        avg_results = average_files(flist)
        inspect_result(avg_results)
        save(avg_results, subdirectory="Avg_178-182")
