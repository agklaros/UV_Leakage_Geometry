from pathlib import Path

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

# DESI rows carry gmag, W2M rows carry gmag_2 — take whichever is set.
# Apparent magnitudes, no absolute-magnitude correction.
gmag = df["gmag"].where(df["gmag"].notna(), df["gmag_2"])
mask = gmag.notna()
app_g = gmag[mask]

bin_edges = np.arange(np.floor(app_g.min()), np.ceil(app_g.max()) + 0.25, 0.25)

# Colors match ebv_uv_excess_histogram.py. The candidate sample is far
# smaller than the full sample, so it gets its own count scale on the
# right-hand axis to keep both distributions visible.
fig, ax = plt.subplots(figsize=(8, 6))
ax_cand = ax.twinx()

ax.hist(app_g, bins=bin_edges, histtype="stepfilled",
        color="steelblue", alpha=0.7, label="All QSOs")
ax_cand.hist(app_g[is_candidate[mask]], bins=bin_edges, histtype="stepfilled",
             color="darkorange", alpha=0.9, label="UV-excess")

ax.set_xlabel("Apparent g magnitude", fontsize=12)
ax.set_ylabel("Number (all QSOs)", fontsize=12, color="steelblue")
ax.tick_params(axis="y", labelcolor="steelblue")
ax_cand.set_ylabel("Number (UV-excess)", fontsize=12, color="darkorange")
ax_cand.tick_params(axis="y", labelcolor="darkorange")
ax_cand.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

ax.set_title(f"Apparent gmag distribution — FINAL_COMBINED_QSOs_W2M ({mask.sum()} QSOs)")
ax.grid(linestyle=":", alpha=0.5)
# Merge the two axes' legend entries into one box
handles1, labels1 = ax.get_legend_handles_labels()
handles2, labels2 = ax_cand.get_legend_handles_labels()
ax.legend(handles1 + handles2, labels1 + labels2, loc="best")

plt.tight_layout()
plt.show()
