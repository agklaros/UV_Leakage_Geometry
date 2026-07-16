"""Build the per-target input sheet for manual Kast ETC runs.

For each UV-excess candidate this writes the magnitude to type into the ETC
(g-band AB + 0.752 polarization-optics penalty) and the filename to save the
downloaded CSV table as. The ETC form settings, identical for every target,
are printed once at the end.

Output: data/processed/kast_etc_inputs.csv
"""

from pathlib import Path

import pandas as pd
import yaml

BASE_DIR = Path(__file__).resolve().parents[2]
CAND_CSV = BASE_DIR / "data/matched/uv_excess_candidates_w2m.csv"
OUT_CSV = BASE_DIR / "data/processed/kast_etc_inputs.csv"


def target_name(row):
    """Stable per-target identifier: designation if present, else TARGETID."""
    if pd.notna(row.get("designation")):
        return str(row["designation"])
    return f"TARGETID_{row['TARGETID']}"


def main():
    with open(BASE_DIR / "config/qso_params.yaml") as f:
        cfg = yaml.safe_load(f)
    obs = cfg["observing"]
    pol_offset = float(obs["pol_flux_offset_mag"])
    etc_exptime = float(obs["etc_exptime_s"])

    # TARGETID must stay integer: as float64 these 17-digit IDs exceed 2^53
    # and distinct IDs collapse together (see gmag_histogram.py).
    cand = pd.read_csv(CAND_CSV, dtype={"TARGETID": "Int64"})
    # DESI rows carry gmag, W2M rows carry gmag_2 — take whichever is set.
    gmag = cand["gmag"].where(cand["gmag"].notna(), cand["gmag_2"])

    rows = []
    for idx, src in cand.iterrows():
        name = target_name(src)
        g = gmag.loc[idx]
        rows.append({
            "target": name,
            "RA": src["RA"] if pd.notna(src["RA"]) else src["ra"],
            "DEC": src["DEC"] if pd.notna(src["DEC"]) else src["dec"],
            "gmag_AB": round(g, 3) if pd.notna(g) else None,
            "mag_to_enter": round(g + pol_offset, 2) if pd.notna(g) else None,
            "exptime_to_enter_s": etc_exptime,
            "save_download_as": f"{name}.csv",
        })

    out = pd.DataFrame(rows).sort_values("gmag_AB")
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    n_missing = out["mag_to_enter"].isna().sum()
    print(f"wrote {OUT_CSV} ({len(out)} targets"
          + (f", {n_missing} without g mag" if n_missing else "") + ")")
    print(f"\nETC page: {obs['etc_page']}")
    print("Same form settings for every target:")
    for k, v in obs["etc_settings"].items():
        print(f"  {k}: {v}")
    print(f"  exposure time: {etc_exptime:g} s (always — do not vary per target)")
    print(f"\nSave each 'Return csv table for exposure' download to "
          f"{obs['etc_downloads_dir']}/<save_download_as>")


if __name__ == "__main__":
    main()
