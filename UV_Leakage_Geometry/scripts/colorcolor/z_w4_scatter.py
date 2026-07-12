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
z = df["Z"].where(df["Z"].notna(), df["zsp"])
w4 = df["W4mag"].where(df["W4mag"].notna(), df["w4mag"])

mask = z.notna() & w4.notna() & (z > 0)

# Absolute magnitude via cosmological distance modulus (per absmag_vs_z.ipynb)
cosmo = FlatLambdaCDM(H0=70 * u.km / u.s / u.Mpc, Tcmb0=2.725 * u.K, Om0=0.3)
lumdist = cosmo.luminosity_distance(z[mask].to_numpy())
distmod = 5 * np.log10(lumdist / u.Mpc) + 25  # m - M
absW4 = w4[mask] - distmod

fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(z[mask & ~is_candidate], absW4[~is_candidate[mask]], s=8, alpha=0.4, color="tab:blue", label="Not UV-excess")
ax.scatter(z[mask & is_candidate], absW4[is_candidate[mask]], s=20, alpha=0.9, color="tab:red", label="UV-excess")

ax.set_xlabel("Redshift (Z / zsp)", fontsize=12)
ax.set_ylabel("Absolute W4 magnitude", fontsize=12)
ax.invert_yaxis()
ax.set_title("Redshift vs. absolute WISE W4 magnitude — FINAL_COMBINED_QSOs_W2M")
ax.grid(linestyle=":", alpha=0.5)
ax.legend(loc="best")

plt.tight_layout()
plt.show()