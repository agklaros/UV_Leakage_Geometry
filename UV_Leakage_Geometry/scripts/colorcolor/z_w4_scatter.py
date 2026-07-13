from pathlib import Path

from astropy.cosmology import FlatLambdaCDM
import astropy.units as u
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_CSV = BASE_DIR / "data/matched/FINAL_COMBINED_QSOs_W2M.csv"
CAND_CSV = BASE_DIR / "data/matched/uv_excess_candidates_w2m.csv"

# TARGETID must stay integer: as float64 these 17-digit IDs exceed 2^53 and
# distinct IDs collapse together, over-matching candidates.
df = pd.read_csv(DATA_CSV, dtype={"TARGETID": "Int64"})

# Flag which QSOs are in the UV-excess candidate sample. W2M-only rows have
# no DESI TARGETID, so those candidates are matched via designation instead
# (see colorcolor.py / build_control_sample_w2m.py).
cand = pd.read_csv(CAND_CSV, dtype={"TARGETID": "Int64"})
matched_by_id = df["TARGETID"].isin(cand["TARGETID"].dropna()) & df["TARGETID"].notna()
matched_by_designation = df["designation"].isin(cand.loc[cand["TARGETID"].isna(), "designation"].dropna()) & df["designation"].notna()
is_candidate = matched_by_id | matched_by_designation

# DESI rows carry Z/W4mag, W2M rows carry zsp/w4mag — take whichever is set.
# Both are AllWISE profile mags in Vega; convert to AB using the SVO FPS
# WISE/WISE.W4 Vega zero point (8.363 Jy) against the AB zero point (3631 Jy).
# Note config/qso_params.yaml lists 6.620 (WISE Explanatory Supplement) —
# differs by 0.026 mag due to zero-point choice.
W4_VEGA_TO_AB = 2.5 * np.log10(3631 / 8.363)  # ≈ 6.594
z = df["Z"].where(df["Z"].notna(), df["zsp"])
w4 = df["W4mag"].where(df["W4mag"].notna(), df["w4mag"]) + W4_VEGA_TO_AB

mask = z.notna() & w4.notna() & (z > 0)

# Absolute magnitude via cosmological distance modulus (per absmag_vs_z.ipynb)
cosmo = FlatLambdaCDM(H0=70 * u.km / u.s / u.Mpc, Tcmb0=2.725 * u.K, Om0=0.3)
lumdist = cosmo.luminosity_distance(z[mask].to_numpy())
distmod = 5 * np.log10(lumdist / u.Mpc) + 25  # m - M
absW4 = w4[mask] - distmod

fig, axes = plt.subplots(
    2, 2, figsize=(10, 7.5),
    gridspec_kw={"width_ratios": [4, 1], "height_ratios": [1, 4], "wspace": 0.05, "hspace": 0.05},
)
ax_histx, ax_corner = axes[0]
ax, ax_hist = axes[1]
ax_hist.sharey(ax)
ax_histx.sharex(ax)
ax_corner.set_visible(False)
ax.scatter(z[mask & ~is_candidate], absW4[~is_candidate[mask]], s=8, alpha=0.4, color="tab:blue", label="Not UV-excess")
ax.scatter(z[mask & is_candidate], absW4[is_candidate[mask]], s=20, alpha=0.9, color="tab:red", label="UV-excess")

ax.set_xlabel("Redshift (Z / zsp)", fontsize=12)
ax.set_ylabel(r"Absolute W4 magnitude $M_{W4}$ [AB mag]", fontsize=12)
ax.invert_yaxis()
ax.grid(linestyle=":", alpha=0.5)
ax.legend(loc="best")

# Marginal histogram of absolute W4 mag: bins run up the shared y-axis,
# counts run horizontally. Log counts so the small UV-excess sample stays
# visible next to the full sample.
bins = np.histogram_bin_edges(absW4, bins=30)
ax_hist.hist(absW4, bins=bins, orientation="horizontal", color="tab:blue", alpha=0.4, label="All sources")
ax_hist.hist(absW4[is_candidate[mask]], bins=bins, orientation="horizontal", color="tab:red", alpha=0.9, label="UV-excess")
ax_hist.set_xscale("log")
ax_hist.set_xlabel("Number of sources", fontsize=12)
ax_hist.grid(linestyle=":", alpha=0.5)
ax_hist.tick_params(labelleft=False)

# Same treatment for redshift: bins run along the shared x-axis, log counts
# on the vertical axis.
zbins = np.histogram_bin_edges(z[mask], bins=30)
ax_histx.hist(z[mask], bins=zbins, color="tab:blue", alpha=0.4, label="All sources")
ax_histx.hist(z[mask & is_candidate], bins=zbins, color="tab:red", alpha=0.9, label="UV-excess")
ax_histx.set_yscale("log")
ax_histx.set_ylabel("Number of sources", fontsize=12)
ax_histx.grid(linestyle=":", alpha=0.5)
ax_histx.tick_params(labelbottom=False)

fig.suptitle("Redshift vs. absolute WISE W4 magnitude — FINAL_COMBINED_QSOs_W2M")
plt.show()