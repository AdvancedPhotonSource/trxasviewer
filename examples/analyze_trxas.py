"""
Analyze TrXAS datasets using the trxasviewer core library.

This script demonstrates the full headless workflow:
  1. Load a single raw SPEC-format scan file
  2. Average multiple scan files
  3. Inspect the processed difference map and kinetics profiles
  4. Apply SVD decomposition
  5. Plot results (requires a display or the 'Agg' matplotlib backend)
  6. Save results to disk

No GUI or Qt installation is required — the core library is fully
standalone.  Run from the command line or adapt cells for a Jupyter
notebook.

Usage
-----
    python examples/analyze_trxas.py

Dependencies
------------
    pip install trxasviewer            # includes numpy, scipy, matplotlib, h5py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")           # headless backend — swap to "TkAgg" for interactive
import matplotlib.pyplot as plt
import numpy as np

# ── Public API ────────────────────────────────────────────────────────────────
# Everything needed for data processing lives in trxasviewer.core.
# No Qt, no PySide6, no pyqtgraph is imported.
from trxasviewer.core import (
    TrXASDataset,
    TrXASDatasetManager,
    TrXASResult,
    save_results,
    format_time,
    TIME_SCALES,
)

# ── Paths — edit these ───────────────────────────────────────────────────────
DATA_DIR = Path("/home/beams/MQICHU/Datasets/trxas_datasets/Dugan_2024_3_saveddata")
SAVE_DIR = Path("/tmp/trxas_output")
SAVE_DIR.mkdir(parents=True, exist_ok=True)


# ── Processing parameters ─────────────────────────────────────────────────────

NORM_KWARGS = {
    "sync_type": "bunch",
    "sync_value": 1820,           # bunch index where the laser fires
    "gs_method": "bunch-average", # "bunch-average" or "orbital-average"
    "gs_value": 5,                # pre-laser bunches/orbitals for ground state
}

BINNING_KWARGS = {
    "method": "Linear",           # "Linear", "Log", or "Manual"
    "lin_num": 5,                 # bunches per time bin
}

KINETICS_KWARGS = {
    # Each ROI defines an energy window; the average ΔA inside is plotted
    # vs. time as a kinetics trace.  Set enabled=False to skip a ROI.
    "ROI1": {"center_energy": 7.126, "delta_energy": 0.002,
              "enabled": True,  "label": "ROI1"},
    "ROI2": {"center_energy": 7.131, "delta_energy": 0.002,
              "enabled": False, "label": "ROI2"},
    "ROI3": {"center_energy": 7.136, "delta_energy": 0.002,
              "enabled": False, "label": "ROI3"},
    "ROI4": {"center_energy": 7.141, "delta_energy": 0.002,
              "enabled": False, "label": "ROI4"},
}


# ══════════════════════════════════════════════════════════════════════════════
# 1.  Single-file processing
# ══════════════════════════════════════════════════════════════════════════════

def load_single(fname: Path) -> dict:
    """Load one raw scan file and return processed results dict."""
    dset = TrXASDataset(fname)

    print(f"\n── Single file: {fname.name}")
    print(f"   scan type  : {dset.dset_type}")
    print(f"   rows       : {dset.num_rows}")
    print(f"   shape      : ch={dset.shape[0]}  orbitals={dset.shape[1]}"
          f"  bunches={dset.shape[2]}")
    print(f"   time step  : {format_time(dset.delta_t_s)}")

    results = dset.get_energy_vs_time(
        target="normalized-GS",
        norm_kwargs=NORM_KWARGS,
        binning_kwargs=BINNING_KWARGS,
        kinetics_kwargs=KINETICS_KWARGS,
    )

    diff = results["diff"]          # shape: (n_energy, n_time)
    t_axis = results["t_axis"]      # seconds
    energy = results["x_axis"]["value"]  # keV

    print(f"   diff map   : {diff.shape[0]} energies × {diff.shape[1]} time bins")
    print(f"   time range : {format_time(t_axis.min())} – {format_time(t_axis.max())}")
    print(f"   energy range: {energy.min():.3f} – {energy.max():.3f} keV")
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 2.  Multi-file averaging
# ══════════════════════════════════════════════════════════════════════════════

def average_files(flist: list[Path]) -> dict:
    """Average a list of scan files and return the averaged results dict."""
    manager = TrXASDatasetManager()
    manager.update_flist(flist)

    print(f"\n── Averaging {len(flist)} files")
    avg = manager.get_energy_vs_time(
        target="normalized-GS",
        norm_kwargs=NORM_KWARGS,
        binning_kwargs=BINNING_KWARGS,
        kinetics_kwargs=KINETICS_KWARGS,
    )
    print(f"   label      : {avg['label']}")
    print(f"   diff map   : {avg['diff'].shape}")
    return avg


# ══════════════════════════════════════════════════════════════════════════════
# 3.  Inspect with TrXASResult
# ══════════════════════════════════════════════════════════════════════════════

def inspect(results: dict) -> TrXASResult:
    """Wrap the results dict in TrXASResult for higher-level analysis."""
    res = TrXASResult(results)

    print(f"\n── TrXASResult inspection")
    print(f"   diff (time×energy) : {res.diff.shape}")  # transposed vs raw dict

    # SVD — computed lazily on first access
    U, S, Vt = res.svd
    print(f"   SVD singular values: {S[:5].round(4)}")
    print(f"   Kinetics labels    : {res.kinetic_labels}")

    for label in res.kinetic_labels:
        profile = res.get_kinetic_profile(label)
        t = profile["profile"]["main"][0]   # time axis (s)
        da = profile["profile"]["main"][1]  # ΔA values
        print(f"   {label}: {len(t)} time points, "
              f"ΔA range [{da.min():.4f}, {da.max():.4f}]")

    return res


# ══════════════════════════════════════════════════════════════════════════════
# 4.  Quick matplotlib plots
# ══════════════════════════════════════════════════════════════════════════════

def plot_overview(results: dict, save_path: Path) -> None:
    """Generate a two-panel overview: difference map + kinetics."""
    diff = results["diff"]                  # (n_energy, n_time)
    t_us = results["t_axis"] * 1e6          # seconds → µs
    energy = results["x_axis"]["value"]     # keV
    kinetics = results["kinetics"]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    # --- Difference map ---
    ax = axes[0]
    vmax = np.nanpercentile(np.abs(diff), 99.5)
    ax.imshow(
        diff, aspect="auto", cmap="bwr",
        vmin=-vmax, vmax=vmax, origin="lower",
        extent=[t_us[0], t_us[-1], energy[0], energy[-1]],
    )
    ax.set_xlabel("Time (µs)")
    ax.set_ylabel("Energy (keV)")
    ax.set_title("ΔA difference map")

    # --- Kinetics ---
    ax = axes[1]
    for label, data in kinetics.items():
        profile = data["profile"]
        if isinstance(profile, dict):
            t = profile["main"][0] * 1e6    # seconds → µs
            da = profile["main"][1]
        else:
            t = profile[0] * 1e6
            da = profile[1]
        ax.plot(t, da, label=label)
    ax.axhline(0, color="k", lw=0.5, ls="--")
    ax.set_xlabel("Time (µs)")
    ax.set_ylabel("ΔA (a.u.)")
    ax.set_title("Kinetics traces")
    ax.legend()

    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    print(f"\n── Saved plot → {save_path}")


# ══════════════════════════════════════════════════════════════════════════════
# 5.  Save to disk
# ══════════════════════════════════════════════════════════════════════════════

def save(results: dict, subdirectory: str) -> None:
    """Save results as NPZ, HDF5, OriginLab CSV and a settings JSON."""
    save_results(
        results,
        directory=SAVE_DIR,
        subdirectory=subdirectory,
        save_image=False,    # set True to also generate PNG/PDF via plot.py
        save_numpy=True,     # results.npz  — reloadable with np.load()
        save_hdf=True,       # results.hdf  — open with h5py or HDFView
        save_origin=True,    # origin/*.txt — import into OriginLab directly
    )
    print(f"   Saved to {SAVE_DIR / subdirectory}/")


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Verify we can find some data files
    files = sorted(DATA_DIR.glob("setup-full-*"))
    if not files:
        print(f"No files found in {DATA_DIR}. Edit DATA_DIR and try again.")
        raise SystemExit(1)

    print(f"Found {len(files)} files in {DATA_DIR.name}")

    # 1. Single file
    results_single = load_single(files[0])
    plot_overview(results_single, SAVE_DIR / "single_overview.png")
    save(results_single, subdirectory="Single")

    # 2. Average a range of files (first 5 that exist)
    flist = files[:5]
    results_avg = average_files(flist)
    plot_overview(results_avg, SAVE_DIR / "avg_overview.png")
    save(results_avg, subdirectory="Avg")

    # 3. Higher-level inspection
    res = inspect(results_avg)
    low_rank = res.get_low_rank_approximation(rank=3)
    print(f"\n   Rank-3 approximation shape: {low_rank.shape}")

    print("\n✓ Done. Output files:")
    for f in sorted(SAVE_DIR.rglob("*")):
        if f.is_file():
            print(f"   {f.relative_to(SAVE_DIR)}")
