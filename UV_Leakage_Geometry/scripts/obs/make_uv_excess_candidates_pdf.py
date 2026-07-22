"""Render a per-target summary table of the UV-excess candidate sample.

One row per candidate: designation/TARGETID, ra, dec, redshift, E(B-V),
FUV/NUV/g/r magnitudes, and the base (P=100%, no polarization penalty)
imaging-polarimetry exposure time at the ideal S/N target, computed via
single_kast_etc_imaging.required_exptime() against each target's downloaded
Kast ETC table.

Pipeline: candidates_to_csv_w2m.py -> make_etc_inputs.py ->
fetch_etc_downloads.py -> make_uv_excess_candidates_pdf.py (this script).

Output: figures/uv_excess_candidates.pdf
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import yaml
from matplotlib.backends.backend_pdf import PdfPages

sys.path.insert(0, str(Path(__file__).resolve().parent))
import single_kast_etc_imaging as etc_imaging

BASE_DIR = Path(__file__).resolve().parents[2]
CAND_CSV = BASE_DIR / "data/matched/uv_excess_candidates_w2m.csv"
ETC_INPUTS_CSV = BASE_DIR / "data/processed/kast_etc_inputs.csv"
OUT_PDF = BASE_DIR / "figures/uv_excess_candidates.pdf"

PAGE = (8.5, 11)  # US letter, portrait
ROWS_PER_PAGE = 18


def fmt_time(seconds):
    if pd.isna(seconds):
        return "—"
    if seconds < 180:
        return f"{seconds:.0f} s"
    if seconds < 5400:
        return f"{seconds/60:.1f} m"
    return f"{seconds/3600:.1f} h"


def target_name(row):
    """Stable per-target identifier: designation if present, else TARGETID."""
    if pd.notna(row.get("designation")):
        return str(row["designation"])
    return f"TARGETID_{row['TARGETID']}"


def load_candidates():
    """Resolve the DESI/W2M parallel column sets in uv_excess_candidates_w2m.csv
    into one clean row per candidate."""
    cand = pd.read_csv(CAND_CSV, dtype={"TARGETID": "Int64"})

    def pick(a, b):
        return cand[a].where(cand[a].notna(), cand[b])

    df = pd.DataFrame({
        "designation": [target_name(row) for _, row in cand.iterrows()],
        "ra": pick("RA", "ra"),
        "dec": pick("DEC", "dec"),
        "z": pick("Z", "zsp"),
        "ebv": pick("EBV", "ebv"),
        "fuv_mag": cand["FUVmag"],
        "nuv_mag": cand["NUVmag"],
        "g_mag": pick("gmag", "gmag_2"),
        "r_mag": pick("rmag", "rmag_2"),
    })
    return df


def compute_exptimes(df, obs):
    """Base (P=100%) imaging-polarimetry exposure time at target_snr, from each
    target's downloaded Kast ETC table."""
    inputs = pd.read_csv(ETC_INPUTS_CSV)
    name_to_download = dict(zip(inputs["target"], inputs["save_download_as"]))
    downloads = BASE_DIR / obs["etc_downloads_dir"]
    filter_path = BASE_DIR / obs["imaging_filter"]
    etc_exptime = float(obs["etc_exptime_s"])
    snr = float(obs["target_snr"])

    t_base = []
    notes = []
    for name in df["designation"]:
        save_as = name_to_download.get(name)
        if save_as is None:
            t_base.append(float("nan"))
            notes.append("not in kast_etc_inputs.csv")
            continue
        etc_file = downloads / save_as
        if not etc_file.exists():
            t_base.append(float("nan"))
            notes.append("ETC download missing")
            continue
        t_base.append(etc_imaging.required_exptime(etc_file, filter_path, etc_exptime, snr))
        notes.append("")
    df["t_base_s"] = t_base
    df["note"] = notes
    return df


def table_page(pdf, chunk, page_num, n_pages, snr):
    cols = ["Designation", "RA", "Dec", "z", "E(B-V)", "FUV", "NUV", "g", "r", "Base exp. time"]
    cells = [[
        r["designation"],
        f"{r['ra']:.4f}",
        f"{r['dec']:.4f}",
        f"{r['z']:.3f}" if pd.notna(r["z"]) else "—",
        f"{r['ebv']:.3f}" if pd.notna(r["ebv"]) else "—",
        f"{r['fuv_mag']:.2f}" if pd.notna(r["fuv_mag"]) else "—",
        f"{r['nuv_mag']:.2f}" if pd.notna(r["nuv_mag"]) else "—",
        f"{r['g_mag']:.2f}" if pd.notna(r["g_mag"]) else "—",
        f"{r['r_mag']:.2f}" if pd.notna(r["r_mag"]) else "—",
        fmt_time(r["t_base_s"]),
    ] for _, r in chunk.iterrows()]

    fig, ax = plt.subplots(figsize=PAGE)
    ax.axis("off")
    title = "UV-excess candidate sample — photometry and base imaging-polarimetry exposure time"
    subtitle = f"S/N = {snr:g}, PS1 g band, P = 100% (no polarization penalty), brightest first"
    if n_pages > 1:
        subtitle += f"  (page {page_num} of {n_pages})"
    ax.set_title(f"{title}\n{subtitle}", fontsize=10.5, pad=18)
    tab = ax.table(cellText=cells, colLabels=cols, loc="upper center", cellLoc="center")
    tab.auto_set_font_size(False)
    tab.set_fontsize(7)
    tab.scale(1.0, 1.3)
    tab.auto_set_column_width(list(range(len(cols))))
    for (row, _), cell in tab.get_celld().items():
        cell.set_edgecolor("0.8")
        if row == 0:
            cell.set_text_props(weight="bold")
            cell.set_facecolor("#d9edf7")

    missing = chunk[chunk["t_base_s"].isna()]
    if len(missing):
        ax.text(0.0, 0.02, "Not tabulated: " + ", ".join(
            f"{r['designation']} ({r['note']})" for _, r in missing.iterrows()),
            transform=ax.transAxes, fontsize=7, color="0.4")
    pdf.savefig(fig)
    plt.close(fig)


def main():
    with open(BASE_DIR / "config/qso_params.yaml") as f:
        cfg = yaml.safe_load(f)
    obs = cfg["observing"]

    df = load_candidates()
    df = compute_exptimes(df, obs)
    df = df.sort_values("g_mag")

    n_pages = -(-len(df) // ROWS_PER_PAGE)  # ceil div
    with PdfPages(OUT_PDF) as pdf:
        for page_num in range(1, n_pages + 1):
            start = (page_num - 1) * ROWS_PER_PAGE
            chunk = df.iloc[start:start + ROWS_PER_PAGE]
            table_page(pdf, chunk, page_num, n_pages, obs["target_snr"])
        meta = pdf.infodict()
        meta["Title"] = "UV-Excess Candidate Sample — Photometry & Base Exposure Time"
        meta["Subject"] = "Per-target RA/Dec/z/E(B-V)/FUV/NUV/g/r and base imaging-polarimetry exposure time"
    print(f"wrote {OUT_PDF} ({len(df)} candidates, {n_pages} page(s))")


if __name__ == "__main__":
    main()
