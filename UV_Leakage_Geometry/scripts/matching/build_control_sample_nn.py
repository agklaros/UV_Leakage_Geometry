"""Build a UV-excess + nearest-neighbor-matched control sample CSV.

For each member of the visually-vetted UV-excess sample (UV_EXCESS_SAMPLE.csv),
finds its single nearest neighbor in FINAL_COMBINED_QSOs_W2M.csv in standardized
3D (z, E(B-V), g-mag) space (Euclidean distance after dividing each axis by its
catalog-wide standard deviation, so no dimension dominates purely from units).
g-band is matched in addition to z/E(B-V) so controls are also luminosity-matched,
not just reddening/redshift-matched.

The nearest-neighbor pool excludes not only the 29 known sample members but also
any other parent-catalog row that independently satisfies the UV-excess selection
criterion (uv_excess_mask, ported from 01_crossmatch.ipynb) even though it was
never reviewed — so no accidental UV-excess QSO can be selected as a control.

Controls may be reused across candidates (true 1-NN; not forced-unique/greedy).

Output: data/matched/uv_excess_with_controls_nn.csv — candidate rows first
(UV_EXCESS = YES) then control rows (UV_EXCESS = NO), no duplicate rows.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import yaml
import astropy.units as u
from astropy.table import Table
from synphot import units as su

BASE_DIR = Path(__file__).resolve().parents[2]
SAMPLE_CSV = BASE_DIR / "data/matched/UV_EXCESS_SAMPLE.csv"
FULL_CSV = BASE_DIR / "data/matched/FINAL_COMBINED_QSOs_W2M.csv"
OUT_CSV = BASE_DIR / "data/matched/uv_excess_with_controls_nn.csv"

with open(BASE_DIR / "config/qso_params.yaml") as f:
    PARAMS = yaml.safe_load(f)

LAM_FUV = PARAMS["band_wavelengths_AA"]["FUV"] * u.AA
LAM_NUV = PARAMS["band_wavelengths_AA"]["NUV"] * u.AA
LAM_G = PARAMS["band_wavelengths_AA"]["g"] * u.AA
LAM_R = PARAMS["band_wavelengths_AA"]["r"] * u.AA
FLAM_MAX_GALEX_PS1 = PARAMS["flux_outlier_thresholds_flam"]["galex_panstarrs"] * su.FLAM
EBV_MIN = PARAMS["uv_excess"]["ebv_min"]


def mag_arr(col):
    if hasattr(col, 'filled'):
        return np.array(col.filled(np.nan), dtype=float)
    arr = np.array(col, dtype=str)
    arr[arr == '--'] = 'nan'
    return arr.astype(float)


def _flam(tbl, col, lam):
    flam = (mag_arr(tbl[col]) * u.ABmag).to(su.FLAM, u.spectral_density(lam))
    flam[flam > FLAM_MAX_GALEX_PS1] = np.nan
    return flam


def uv_excess_mask(tbl, gmag_col, rmag_col, require_ebv=True, ebv_col='EBV'):
    """UV-excess criterion: FUV > NUV AND (NUV/G upturn OR FUV/NUV upturn),
    optionally AND E(B-V) > EBV_MIN. Ported from 01_crossmatch.ipynb."""
    flam_fuv = _flam(tbl, 'FUVmag', LAM_FUV)
    flam_nuv = _flam(tbl, 'NUVmag', LAM_NUV)
    flam_g = _flam(tbl, gmag_col, LAM_G)
    flam_r = _flam(tbl, rmag_col, LAM_R)

    f_fn = flam_fuv / flam_nuv
    f_ng = flam_nuv / flam_g
    f_gr = flam_g / flam_r

    flux_criterion = (
        ((f_ng > 1) & (f_gr < 1)) |
        ((f_fn > 1) & (f_ng < 1))
    )

    if require_ebv:
        ebv = mag_arr(tbl[ebv_col])
        return flux_criterion & (ebv > EBV_MIN)
    return flux_criterion


def coalesce(df, primary, fallback):
    """DESI rows carry Z/EBV/gmag, W2M rows carry zsp/ebv/gmag_2 — take whichever is set."""
    return df[primary].where(df[primary].notna(), df[fallback])


def main():
    cand = pd.read_csv(SAMPLE_CSV)
    full = pd.read_csv(FULL_CSV)

    for df in (cand, full):
        df["_z"] = coalesce(df, "Z", "zsp")
        df["_ebv"] = coalesce(df, "EBV", "ebv")
        df["_gmag"] = coalesce(df, "gmag", "gmag_2")

    print(f"UV-excess sample: {len(cand)} candidates")

    # identifiers of the sample members so they never appear as their own control
    cand_ids = set(cand["TARGETID"].dropna()) | set(cand["designation"].dropna())

    full_tbl = Table.from_pandas(full)
    desi_mask = uv_excess_mask(full_tbl, gmag_col='gmag', rmag_col='rmag',
                                ebv_col='EBV', require_ebv=True)
    w2m_mask = uv_excess_mask(full_tbl, gmag_col='gmag_2', rmag_col='rmag_2',
                               require_ebv=False)
    excess_like = np.asarray(desi_mask) | np.asarray(w2m_mask)

    id_excluded = full["TARGETID"].isin(cand_ids) | full["designation"].isin(cand_ids)
    excluded = id_excluded | excess_like
    print(f"Excluded from control pool: {excluded.sum()} "
          f"({id_excluded.sum()} known sample members, "
          f"{excess_like.sum()} independently UV-excess-like, "
          f"{(id_excluded & excess_like).sum()} overlap)")

    pool = full[~excluded].copy()
    pool = pool[pool["_z"].notna() & pool["_ebv"].notna() & pool["_gmag"].notna()]
    print(f"Control pool size: {len(pool)}")

    z_std = pool["_z"].std()
    ebv_std = pool["_ebv"].std()
    gmag_std = pool["_gmag"].std()

    pool_coords = np.column_stack([
        pool["_z"].to_numpy() / z_std,
        pool["_ebv"].to_numpy() / ebv_std,
        pool["_gmag"].to_numpy() / gmag_std,
    ])

    control_idx = []
    raw_deltas = []
    for _, c in cand.iterrows():
        c_coord = np.array([c["_z"] / z_std, c["_ebv"] / ebv_std, c["_gmag"] / gmag_std])
        dist = np.linalg.norm(pool_coords - c_coord, axis=1)
        best = np.argmin(dist)
        best_row = pool.iloc[best]
        control_idx.append(best_row.name)
        raw_deltas.append((
            abs(c["_z"] - best_row["_z"]),
            abs(c["_ebv"] - best_row["_ebv"]),
            abs(c["_gmag"] - best_row["_gmag"]),
        ))

    raw_deltas = np.array(raw_deltas)
    n_shared = len(control_idx) - len(set(control_idx))
    print(f"Control matches found: {len(control_idx)}/{len(cand)} "
          f"({len(set(control_idx))} unique, {n_shared} shared by >1 candidate)")
    print(f"Mean |Δz| = {raw_deltas[:, 0].mean():.4f}, "
          f"Mean |ΔE(B-V)| = {raw_deltas[:, 1].mean():.4f}, "
          f"Mean |Δg| = {raw_deltas[:, 2].mean():.4f}")
    print(f"Max  |Δz| = {raw_deltas[:, 0].max():.4f}, "
          f"Max  |ΔE(B-V)| = {raw_deltas[:, 1].max():.4f}, "
          f"Max  |Δg| = {raw_deltas[:, 2].max():.4f}")

    controls = full.loc[sorted(set(control_idx))].copy()

    cand["UV_EXCESS"] = "YES"
    controls["UV_EXCESS"] = "NO"

    out = pd.concat([cand, controls], ignore_index=True)
    out = out.drop(columns=["_z", "_ebv", "_gmag"])
    out = out.drop_duplicates()
    out.to_csv(OUT_CSV, index=False)
    print(f"Wrote {len(out)} rows -> {OUT_CSV}")


if __name__ == "__main__":
    main()
