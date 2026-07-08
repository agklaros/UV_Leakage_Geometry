"""Build a UV-excess + matched-control sample CSV.

Takes every UV-excess candidate (uv_excess_candidates_w2m.csv) with redshift
> 0.1 and, for each one, pulls control QSOs from FINAL_COMBINED_QSOs_W2M.csv
that fall in the same E(B-V) histogram bin (width 0.1, matching
05_histograms.ipynb) and within DZ_TOL in redshift.

DZ_TOL = 0.016 was chosen by scanning tolerances so that each candidate gets
~1 control match on average (mean 0.97 at 0.016; 0.62 at 0.01, 1.29 at 0.02).

Output: data/matched/uv_excess_with_controls_w2m.csv — candidate rows first
(UV_EXCESS = YES) then control rows (UV_EXCESS = NO), no duplicate rows.
"""

from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
CAND_CSV = BASE_DIR / "data/matched/uv_excess_candidates_w2m.csv"
FULL_CSV = BASE_DIR / "data/matched/FINAL_COMBINED_QSOs_W2M.csv"
OUT_CSV  = BASE_DIR / "data/matched/uv_excess_with_controls_w2m.csv"

Z_MIN    = 0.1    # keep candidates with redshift above this
EBV_BIN  = 0.1    # E(B-V) histogram bin width (see 05_histograms.ipynb)
DZ_TOL   = 0.016  # redshift radius: ~1 control per candidate on average


def coalesce(df, primary, fallback):
    """DESI rows carry Z/EBV, W2M rows carry zsp/ebv — take whichever is set."""
    return df[primary].where(df[primary].notna(), df[fallback])


def main():
    cand = pd.read_csv(CAND_CSV)
    full = pd.read_csv(FULL_CSV)

    for df in (cand, full):
        df["_z"]   = coalesce(df, "Z", "zsp")
        df["_ebv"] = coalesce(df, "EBV", "ebv")

    cand = cand[cand["_z"] > Z_MIN].copy()
    print(f"UV-excess candidates with z > {Z_MIN}: {len(cand)}")

    # identifiers of the candidates so they never appear as their own control
    cand_ids = set(cand["TARGETID"].dropna()) | set(cand["designation"].dropna())

    cand_bins = np.floor(cand["_ebv"] / EBV_BIN)
    full_bins = np.floor(full["_ebv"] / EBV_BIN)

    control_idx = set()
    for (_, c), cbin in zip(cand.iterrows(), cand_bins):
        sel = full[(full_bins == cbin) & (np.abs(full["_z"] - c["_z"]) <= DZ_TOL)]
        sel = sel[~(sel["TARGETID"].isin(cand_ids) | sel["designation"].isin(cand_ids))]
        control_idx.update(sel.index)

    controls = full.loc[sorted(control_idx)].copy()
    print(f"Control QSOs matched (unique): {len(controls)} "
          f"({len(controls) / len(cand):.2f} per candidate)")

    cand["UV_EXCESS"] = "YES"
    controls["UV_EXCESS"] = "NO"

    out = pd.concat([cand, controls], ignore_index=True)
    out = out.drop(columns=["_z", "_ebv"])
    out = out.drop_duplicates()
    out.to_csv(OUT_CSV, index=False)
    print(f"Wrote {len(out)} rows -> {OUT_CSV}")


if __name__ == "__main__":
    main()
