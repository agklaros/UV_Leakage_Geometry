"""Render the Kast observing plan (kast_obs_plan.csv) as a PDF report.

Pages: (1) methodology and sample summary, (2) exposure time vs magnitude,
(3) per-target exposure-time table at the ideal S/N target. All numbers come
from process_etc_outputs.py output; run that (after fetch_etc_downloads.py
or manual ETC downloads) before this.

Output: figures/kast_obs_plan.pdf
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kast_etc

BASE_DIR = Path(__file__).resolve().parents[2]
PLAN_CSV = BASE_DIR / "data/processed/kast_obs_plan.csv"
OUT_PDF = BASE_DIR / "figures/kast_obs_plan.pdf"

PAGE = (8.5, 11)  # US letter, portrait


def fmt_time(seconds):
    if pd.isna(seconds):
        return "—"
    if seconds < 180:
        return f"{seconds:.0f} s"
    if seconds < 5400:
        return f"{seconds/60:.1f} m"
    return f"{seconds/3600:.1f} h"


def summary_page(pdf, df, obs):
    snr = obs["target_snr"]
    n = df["t_img_snr10_s"].notna().sum()
    fig = plt.figure(figsize=PAGE)
    fig.text(0.5, 0.94, "Lick Kast Polarimetry — Exposure Time & S/N Plan",
             ha="center", fontsize=16, weight="bold")
    fig.text(0.5, 0.915, f"UV-excess QSO candidates ({n} targets with g photometry)",
             ha="center", fontsize=11, color="0.35")

    s = obs["etc_settings"]
    within = lambda col, h: int((df[col] < h * 3600).sum())
    body = f"""\
Methodology (K. Leighly notes 2026-07; Chromey, "To Measure the Sky", sec. 9.5.4)

  1.  Each target is run through the Kast ETC ({obs['etc_page']})
      with a flat template and its PS1 g-band AB magnitude + {obs['pol_flux_offset_mag']} mag: the
      polarization optics pass half the flux (m_pol = m + 2.5 log 2).
  2.  ETC settings, identical for all targets:  dichroic {s['dichroic']}, slit {s['slitwidth']},
      binning {s['binning']}, grism {s['grism']}, grating {s['grating']}, seeing {s['seeing']}\",
      airmass {s['airmass']}, reference exposure {obs['etc_exptime_s']:.0f} s.
  3.  The ETC returns per-pixel object counts, sky counts, and read noise vs.
      wavelength. Spectropolarimetry uses the per-pixel S/N of the median pixel
      in {obs['spectropol_window_AA'][0]:.0f}-{obs['spectropol_window_AA'][1]:.0f} A; imaging polarimetry integrates the counts over the
      PS1 g profile (synphot) and applies the CCD equation
      S/N = Nqso / sqrt(Nqso + Nsky + Noise).
  4.  The exposure time reaching the required S/N is the exact solution of the
      CCD equation (Chromey eq. 9.77). Required S/N = {obs['target_snr']:g} (advisor: "ideally
      >10"); the {obs['snr_floor']:g} floor ("definitely >5") is tabulated in kast_obs_plan.csv.
  5.  Polarimetry penalty: to be sensitive to polarization fraction P, the normal
      exposure time is multiplied by 1/P (rough rule per notes) — x25 for P = 4%,
      x100 for P = 1%. Note P is NOT the scattered fraction: scattering with
      unfavorable geometry can cancel to zero net polarization.

Sample summary at S/N = {snr:g}, imaging polarimetry (PS1 g)

      P = 4%:  {within('t_img_snr10_p4_s', 1)} targets within 1 h,  {within('t_img_snr10_p4_s', 2)} within 2 h,  {within('t_img_snr10_p4_s', 4)} within 4 h
      P = 1%:  {within('t_img_snr10_p1_s', 2)} targets within 2 h,  {within('t_img_snr10_p1_s', 4)} within 4 h,  {within('t_img_snr10_p1_s', 8)} within 8 h

Spectropolarimetry at S/N = {snr:g}/pixel is feasible unscaled for the brightest
targets ({within('t_spec_snr10_s', 1)} within 1 h) but no target fits 4 h once the 1/P factor is
applied — imaging polarimetry first, spectropolarimetry only for bright
detections, is the natural protocol.

Caveats:  g magnitudes are observed-frame, not corrected for Galactic
extinction; the 1/P rule is approximate (a 3-sigma detection criterion via
sigma_P = sqrt(2)/(S/N) scales as 1/P^2) — confirm convention before the
proposal; several candidates lie at z < 0.5 (W2M rows) — vet before targeting."""
    fig.text(0.07, 0.87, body, fontsize=8.5, family="monospace", va="top")
    pdf.savefig(fig)
    plt.close(fig)


def figure_page(pdf, df, obs):
    ok = df.dropna(subset=["gmag_AB", "t_img_snr10_s"])
    snr = obs["target_snr"]
    fig, ax = plt.subplots(figsize=PAGE)
    fig.subplots_adjust(top=0.7, bottom=0.32)
    ax.scatter(ok["gmag_AB"], ok["t_img_snr10_s"], color="darkorange",
               label=f"Imaging pol. base (PS1 g, S/N={snr:g})")
    ax.scatter(ok["gmag_AB"], ok["t_img_snr10_p4_s"], color="darkorange",
               marker="^", label="Imaging pol., P=4% (x25)")
    ax.scatter(ok["gmag_AB"], ok["t_spec_snr10_s"], color="steelblue",
               label=f"Spectropol. base (S/N={snr:g}/pix)")
    for hours, txt in [(1, "1 h"), (4, "4 h")]:
        ax.axhline(hours * 3600, color="0.5", linestyle="--", linewidth=0.8)
        ax.text(ok["gmag_AB"].max(), hours * 3600, f" {txt}", va="bottom",
                color="0.4", fontsize=9)
    ax.set_yscale("log")
    ax.set_xlabel("Apparent g magnitude (AB)", fontsize=12)
    ax.set_ylabel("Required exposure time [s]", fontsize=12)
    ax.set_title(f"Kast exposure times — UV-excess candidates ({len(ok)} targets)")
    ax.grid(linestyle=":", alpha=0.5)
    ax.legend(loc="upper left", fontsize=9)
    pdf.savefig(fig)
    plt.close(fig)


def table_page(pdf, df, obs):
    snr = obs["target_snr"]
    ok = df.dropna(subset=["t_img_snr10_s"]).sort_values("gmag_AB")
    cols = ["Target", "g (AB)", "ETC mag",
            "Img base", "Img P=4%", "Img P=1%", "N exp (4%)",
            "Spec base", "Spec P=4%"]
    cells = [[
        r["target"], f"{r['gmag_AB']:.2f}", f"{r['mag_to_enter']:.2f}",
        fmt_time(r["t_img_snr10_s"]), fmt_time(r["t_img_snr10_p4_s"]),
        fmt_time(r["t_img_snr10_p1_s"]), f"{r['n_exp_img_snr10_p4']:.0f}",
        fmt_time(r["t_spec_snr10_s"]), fmt_time(r["t_spec_snr10_p4_s"]),
    ] for _, r in ok.iterrows()]

    fig, ax = plt.subplots(figsize=PAGE)
    ax.axis("off")
    ax.set_title(f"Per-target exposure times at S/N = {snr:g} "
                 f"(brightest first; imaging = PS1 g band)", fontsize=11, pad=18)
    tab = ax.table(cellText=cells, colLabels=cols, loc="upper center",
                   cellLoc="center")
    tab.auto_set_font_size(False)
    tab.set_fontsize(7)
    tab.scale(1.0, 1.25)
    tab.auto_set_column_width(list(range(len(cols))))
    for (row, _), cell in tab.get_celld().items():
        cell.set_edgecolor("0.8")
        if row == 0:
            cell.set_text_props(weight="bold")
            cell.set_facecolor("#d9edf7")
    missing = df[df["t_img_snr10_s"].isna()]
    if len(missing):
        ax.text(0.0, 0.02, "Not tabulated: " + ", ".join(
            f"{r['target']} ({r.get('note', 'no data')})" for _, r in missing.iterrows()),
            transform=ax.transAxes, fontsize=7, color="0.4")
    pdf.savefig(fig)
    plt.close(fig)


def main():
    obs = kast_etc.load_config()["observing"]
    df = pd.read_csv(PLAN_CSV)
    with PdfPages(OUT_PDF) as pdf:
        summary_page(pdf, df, obs)
        figure_page(pdf, df, obs)
        table_page(pdf, df, obs)
        meta = pdf.infodict()
        meta["Title"] = "Lick Kast Polarimetry Exposure Plan — UV-excess QSOs"
        meta["Subject"] = "Exposure times and S/N for spectropolarimetry and imaging polarimetry"
    print(f"wrote {OUT_PDF}")


if __name__ == "__main__":
    main()
