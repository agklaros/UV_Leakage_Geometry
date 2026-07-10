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
# (see z_w4_scatter.py / colorcolor.py).
cand = pd.read_csv(CAND_CSV, dtype={"TARGETID": "Int64"})
matched_by_id = df["TARGETID"].isin(cand["TARGETID"].dropna()) & df["TARGETID"].notna()
matched_by_designation = df["designation"].isin(cand.loc[cand["TARGETID"].isna(), "designation"].dropna()) & df["designation"].notna()
is_candidate = matched_by_id | matched_by_designation

# DESI rows carry Z/gmag, W2M rows carry zsp/gmag_2 — take whichever is
# set, then correct to absolute magnitude via the cosmological distance
# modulus (per absmag_vs_z.ipynb).
z = df["Z"].where(df["Z"].notna(), df["zsp"])
gmag = df["gmag"].where(df["gmag"].notna(), df["gmag_2"])
mask = gmag.notna() & z.notna() & (z > 0)

cosmo = FlatLambdaCDM(H0=70 * u.km / u.s / u.Mpc, Tcmb0=2.725 * u.K, Om0=0.3)
lumdist = cosmo.luminosity_distance(z[mask].to_numpy())
distmod = 5 * np.log10(lumdist / u.Mpc) + 25  # m - M
abs_g = gmag[mask] - distmod

bin_edges = np.arange(np.floor(abs_g.min()), np.ceil(abs_g.max()) + 0.25, 0.25)

fig, ax = plt.subplots(figsize=(8, 6))
ax.hist(abs_g, bins=bin_edges, color="tab:blue", edgecolor="black", linewidth=0.5, label="All QSOs")
# Overlay the UV-excess candidates in the same bins, drawn narrower so the
# orange bars sit inside the blue ones.
ax.hist(abs_g[is_candidate[mask]], bins=bin_edges, color="tab:orange",
        edgecolor="black", linewidth=0.5, rwidth=0.5, label="UV-excess")

ax.set_xlabel("Absolute g magnitude", fontsize=12)
ax.set_ylabel("Number", fontsize=12)
ax.set_title(f"Absolute gmag distribution — FINAL_COMBINED_QSOs_W2M ({mask.sum()} QSOs)")
ax.grid(linestyle=":", alpha=0.5)
ax.legend(loc="best")

plt.tight_layout()
plt.show()
