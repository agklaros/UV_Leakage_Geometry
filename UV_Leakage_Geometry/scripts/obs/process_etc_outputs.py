"""Turn manually downloaded Kast ETC tables into the observing plan.

Reads every <target>.csv in data/etc_downloads/ (saved by hand from the
ETC's "Return csv table for exposure" button, per the input sheet from
make_etc_inputs.py), then for each target computes the exposure time needed
to reach the configured S/N — at both target_snr (10, advisor's "ideally")
and snr_floor (5, hard minimum) — for:

  - spectropolarimetry: per-pixel S/N, median pixel in the blue window
  - imaging polarimetry: counts integrated over the PS1 g profile (synphot),
    CCD equation

and scales each by 1/P for the configured polarization fractions.

Outputs:
  data/processed/kast_obs_plan.csv  — per-target observing table
  figures/kast_exptime_vs_gmag.png  — sanity plot (brighter -> shorter)
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kast_etc

BASE_DIR = Path(__file__).resolve().parents[2]
INPUTS_CSV = BASE_DIR / "data/processed/kast_etc_inputs.csv"
OUT_CSV = BASE_DIR / "data/processed/kast_obs_plan.csv"
OUT_FIG = BASE_DIR / "figures/kast_exptime_vs_gmag.png"


def main():
    cfg = kast_etc.load_config()
    obs = cfg["observing"]
    etc_exptime = float(obs["etc_exptime_s"])
    pol_fractions = [float(p) for p in obs["pol_fractions"]]
    snr_levels = {"snr%g" % obs["target_snr"]: float(obs["target_snr"]),
                  "snr%g" % obs["snr_floor"]: float(obs["snr_floor"])}
    window = [float(w) for w in obs["spectropol_window_AA"]]
    max_exp = float(obs["max_single_exptime_s"])
    downloads = BASE_DIR / obs["etc_downloads_dir"]

    filt_wave, filt_thru = kast_etc.load_filter(BASE_DIR / obs["imaging_filter"])
    inputs = pd.read_csv(INPUTS_CSV)

    rows, n_found = [], 0
    for _, tgt in inputs.iterrows():
        row = {k: tgt[k] for k in ["target", "RA", "DEC", "gmag_AB", "mag_to_enter"]}
        etc_file = downloads / str(tgt["save_download_as"])
        if pd.isna(tgt["mag_to_enter"]):
            row["note"] = "no g magnitude"
            rows.append(row)
            continue
        if not etc_file.exists():
            row["note"] = "ETC download missing"
            rows.append(row)
            continue
        n_found += 1
        etc = kast_etc.read_etc_csv(etc_file)

        spec_rates = kast_etc.spectropol_pixel_rates(etc, window, etc_exptime)
        img_rates = kast_etc.filter_band_rates(etc, filt_wave, filt_thru, etc_exptime)
        for label, snr in snr_levels.items():
            t_spec = kast_etc.required_exptime(snr, *spec_rates)
            t_img = kast_etc.required_exptime(snr, *img_rates)
            row[f"t_spec_{label}_s"] = t_spec
            row[f"t_img_{label}_s"] = t_img
            for p in pol_fractions:
                tag = f"{label}_p{p*100:g}"
                row[f"t_spec_{tag}_s"] = t_spec / p
                row[f"t_img_{tag}_s"] = t_img / p
                row[f"n_exp_img_{tag}"] = int(np.ceil(t_img / p / max_exp))
        rows.append(row)

    out = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV}: {n_found}/{len(inputs)} targets with ETC downloads"
          f" (missing ones flagged in 'note' column)")
    if n_found == 0:
        print(f"no ETC files found in {downloads} — nothing to plot")
        return

    base = f"snr{obs['target_snr']:g}"
    ok = out.dropna(subset=[f"t_img_{base}_s"])
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(ok["gmag_AB"], ok[f"t_img_{base}_s"], color="darkorange",
               label=f"Imaging pol. (PS1 g, S/N={obs['target_snr']:g}, base)")
    ax.scatter(ok["gmag_AB"], ok[f"t_spec_{base}_s"], color="steelblue",
               label=f"Spectropol. ({window[0]:.0f}-{window[1]:.0f} A, "
                     f"S/N={obs['target_snr']:g}/pix, base)")
    ax.set_yscale("log")
    ax.set_xlabel("Apparent g magnitude (AB)", fontsize=12)
    ax.set_ylabel("Required exposure time [s] (before 1/P scaling)", fontsize=12)
    ax.set_title(f"Kast exposure times — UV-excess candidates ({len(ok)} targets)")
    ax.grid(linestyle=":", alpha=0.5)
    ax.legend(loc="best")
    plt.tight_layout()
    fig.savefig(OUT_FIG, dpi=150)
    print(f"wrote {OUT_FIG}")


if __name__ == "__main__":
    main()
