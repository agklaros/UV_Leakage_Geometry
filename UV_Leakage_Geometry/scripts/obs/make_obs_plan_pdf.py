"""Render the Kast polarimetry observing plan as a PDF report.

Pages: (1) methodology and sample summary, (2-3) imaging exposure time vs
magnitude and per-target table at the ideal S/N target, (4-5) the same
imaging figure/table pair at the hard-minimum S/N floor, (6-7) the joint
spectropolarimetry figure/table pair (median S/N-good AND floor-fraction
S/N-floor), (8-9) a floor-only spectropolarimetry figure/table pair (just
95% of pixels >= S/N floor, no S/N-good requirement). Imaging exposure times
are computed via single_kast_etc_imaging's effstim()-based math;
spectropolarimetry times via single_kast_etc_spectropol's per-pixel
percentile math (required_exptime for the joint criterion,
required_exptime_floor_only for the 95%-floor-only variant — see that
module's docstring).

Pipeline: make_etc_inputs.py -> fetch_etc_downloads.py ->
single_kast_etc_imaging.py / single_kast_etc_spectropol.py ->
make_obs_plan_pdf.py (this script).

Output: figures/kast_obs_plan.pdf
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from matplotlib.backends.backend_pdf import PdfPages

sys.path.insert(0, str(Path(__file__).resolve().parent))
import single_kast_etc_imaging as etc_imaging
import single_kast_etc_spectropol as etc_spectropol

BASE_DIR = Path(__file__).resolve().parents[2]
INPUTS_CSV = BASE_DIR / "data/processed/kast_etc_inputs.csv"
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


def snr_levels(obs):
    """(label, snr) pairs for the two required S/N levels, e.g. [('snr10', 10.0), ('snr5', 5.0)]."""
    return [(f"snr{obs['target_snr']:g}", float(obs["target_snr"])),
            (f"snr{obs['snr_floor']:g}", float(obs["snr_floor"]))]


def build_plan(obs):
    """Per-target exposure times, computed straight from the downloaded ETC
    tables (no kast_obs_plan.csv intermediate): imaging polarimetry at both
    the ideal S/N target and the hard-minimum S/N floor, a joint
    spectropolarimetry exposure time (median-S/N-good and floor-fraction-S/N
    criteria combined into one number by
    single_kast_etc_spectropol.required_exptime), and a floor-only
    spectropolarimetry exposure time (just 95% of pixels >= S/N floor, via
    single_kast_etc_spectropol.required_exptime_floor_only)."""
    downloads = BASE_DIR / obs["etc_downloads_dir"]
    filter_path = BASE_DIR / obs["imaging_filter"]
    etc_exptime = float(obs["etc_exptime_s"])
    pol_fractions = [float(p) for p in obs["pol_fractions"]]
    max_exp = float(obs["max_single_exptime_s"])
    levels = snr_levels(obs)
    snr_good = float(obs["target_snr"])
    snr_floor = float(obs["snr_floor"])

    inputs = pd.read_csv(INPUTS_CSV)
    rows = []
    for _, tgt in inputs.iterrows():
        row = {k: tgt[k] for k in ["target", "gmag_AB", "mag_to_enter"]}
        if pd.isna(tgt["mag_to_enter"]):
            row["note"] = "no g magnitude"
            rows.append(row)
            continue
        etc_file = downloads / str(tgt["save_download_as"])
        if not etc_file.exists():
            row["note"] = "ETC download missing"
            rows.append(row)
            continue
        for label, snr in levels:
            t_img = etc_imaging.required_exptime(etc_file, filter_path, etc_exptime, snr)
            row[f"t_img_{label}_s"] = t_img
            for p in pol_fractions:
                tag = f"p{p*100:g}"
                row[f"t_img_{label}_{tag}_s"] = t_img / p
                row[f"n_exp_img_{label}_{tag}"] = int(np.ceil(t_img / p / max_exp))

        t_spec, frac_spec_good, frac_spec_floor = etc_spectropol.required_exptime(
            etc_file, etc_exptime,
            snr_good=snr_good, frac_good=0.50,
            snr_floor=snr_floor, frac_floor=0.90,
            wave_min=3150.0, wave_max=5400.0,
        )
        row["t_spec_s"] = t_spec
        row["frac_spec_ge_good"] = frac_spec_good
        row["frac_spec_ge_floor"] = frac_spec_floor
        for p in pol_fractions:
            tag = f"p{p*100:g}"
            row[f"t_spec_{tag}_s"] = t_spec / p
            row[f"n_exp_spec_{tag}"] = int(np.ceil(t_spec / p / max_exp))

        t_spec95, frac_spec95 = etc_spectropol.required_exptime_floor_only(
            etc_file, etc_exptime,
            snr_floor=snr_floor, frac_floor=0.95,
            wave_min=3150.0, wave_max=5400.0,
        )
        row["t_spec95_s"] = t_spec95
        row["frac_spec95_ge_floor"] = frac_spec95
        for p in pol_fractions:
            tag = f"p{p*100:g}"
            row[f"t_spec95_{tag}_s"] = t_spec95 / p
            row[f"n_exp_spec95_{tag}"] = int(np.ceil(t_spec95 / p / max_exp))
        rows.append(row)
    return pd.DataFrame(rows)


def summary_page(pdf, df, obs):
    snr = obs["target_snr"]
    label = f"snr{snr:g}"
    n = df[f"t_img_{label}_s"].notna().sum()
    fig = plt.figure(figsize=PAGE)
    fig.text(0.5, 0.94, "Lick Kast Polarimetry — Exposure Time & S/N Plan",
             ha="center", fontsize=16, weight="bold")
    fig.text(0.5, 0.915, f"UV-excess QSO candidates ({n} targets with g photometry) — imaging & spectropolarimetry",
             ha="center", fontsize=11, color="0.35")

    s = obs["etc_settings"]
    within = lambda col, h: int((df[col] < h * 3600).sum())
    body = f"""\
Methodology (K. Leighly notes 2026-07; E. Glikman's synphot notebook; Chromey,
"To Measure the Sky", sec. 9.5.4)

  1.  Each target is run through the Kast ETC ({obs['etc_page']})
      with a flat template and its PS1 g-band AB magnitude + {obs['pol_flux_offset_mag']} mag: the
      polarization optics pass half the flux (m_pol = m + 2.5 log 2).
  2.  ETC settings, identical for all targets:  dichroic {s['dichroic']}, slit {s['slitwidth']},
      binning {s['binning']}, grism {s['grism']}, grating {s['grating']}, seeing {s['seeing']}\",
      airmass {s['airmass']}, reference exposure {obs['etc_exptime_s']:.0f} s.
  3.  The ETC's per-pixel object/sky/noise counts vs. wavelength are integrated over the
      PS1 g bandpass via synphot's Observation.effstim() (a throughput-weighted mean),
      then combined with the CCD equation S/N = Nqso / sqrt(Nqso + Nsky + Noise).
  4.  The exposure time reaching the required S/N is the exact solution of the
      CCD equation (Chromey eq. 9.77). Required S/N = {obs['target_snr']:g} ; the {obs['snr_floor']:g} floor ("definitely >5") is plotted and tabulated separately below.
  5.  Polarimetry penalty: to be sensitive to polarization fraction P, the normal
      exposure time is multiplied by 1/P (rough rule per notes) — x10 for P = 10%,
      x100 for P = 1%. Note P is NOT the scattered fraction: scattering with
      unfavorable geometry can cancel to zero net polarization.
  6.  Spectropolarimetry has no filter to integrate over — every wavelength bin in
      the ETC download needs its own adequate S/N. The blue-grism side only
      (3150-5400 A, before the d55 dichroic split) is evaluated per pixel with the
      same CCD equation; the reported exposure time is the larger of two joint
      requirements: the median pixel reaches S/N >= {obs['target_snr']:g}, and 90% of
      pixels reach S/N >= {obs['snr_floor']:g}.

Sample summary at S/N = {snr:g}, imaging polarimetry (PS1 g)

      P = 10%: {within(f't_img_{label}_p10_s', 1)} targets within 1 h,  {within(f't_img_{label}_p10_s', 2)} within 2 h,  {within(f't_img_{label}_p10_s', 4)} within 4 h
      P = 1%:  {within(f't_img_{label}_p1_s', 2)} targets within 2 h,  {within(f't_img_{label}_p1_s', 4)} within 4 h,  {within(f't_img_{label}_p1_s', 8)} within 8 h

Sample summary, spectropolarimetry (blue side, joint median S/N >= {obs['target_snr']:g} / 90% S/N >= {obs['snr_floor']:g})

      P = 10%: {within('t_spec_p10_s', 1)} targets within 1 h,  {within('t_spec_p10_s', 2)} within 2 h,  {within('t_spec_p10_s', 4)} within 4 h
      P = 1%:  {within('t_spec_p1_s', 2)} targets within 2 h,  {within('t_spec_p1_s', 4)} within 4 h,  {within('t_spec_p1_s', 8)} within 8 h

Caveats:  g magnitudes are observed-frame, not corrected for Galactic
extinction; the 1/P rule is approximate (a 3-sigma detection criterion via
sigma_P = sqrt(2)/(S/N) scales as 1/P^2) — confirm convention before the
proposal; several candidates lie at z < 0.5 (W2M rows) — vet before targeting;
spectropolarimetry uses one joint exposure time (not split by ideal/floor
page) since both S/N criteria are solved together — see the dedicated
spectropolarimetry page below."""
    fig.text(0.07, 0.87, body, fontsize=8.5, family="monospace", va="top")
    pdf.savefig(fig)
    plt.close(fig)


def figure_page(pdf, df, snr, snr_desc):
    label = f"snr{snr:g}"
    ok = df.dropna(subset=["gmag_AB", f"t_img_{label}_s"])
    fig, ax = plt.subplots(figsize=PAGE)
    fig.subplots_adjust(top=0.7, bottom=0.32)
    ax.scatter(ok["gmag_AB"], ok[f"t_img_{label}_s"], color="darkorange",
               label=f"Imaging pol. base (PS1 g, S/N={snr:g})")
    ax.scatter(ok["gmag_AB"], ok[f"t_img_{label}_p10_s"], color="darkorange",
               marker="^", label="Imaging pol., P=10% (x10)")
    ax.scatter(ok["gmag_AB"], ok[f"t_img_{label}_p1_s"], color="darkorange",
               marker="s", label="Imaging pol., P=1% (x100)")
    for hours, txt in [(1, "1 h"), (4, "4 h"), (10, "10 h")]:
        ax.axhline(hours * 3600, color="0.5", linestyle="--", linewidth=0.8)
        ax.text(ok["gmag_AB"].max(), hours * 3600, f" {txt}", va="bottom",
                color="0.4", fontsize=9)
    ax.set_yscale("log")
    ax.set_xlabel("Apparent g magnitude (AB)", fontsize=12)
    ax.set_ylabel("Required exposure time [s]", fontsize=12)
    ax.set_title(f"Kast imaging-polarimetry exposure times at S/N = {snr:g} ({snr_desc}) — "
                 f"UV-excess candidates ({len(ok)} targets)")
    ax.grid(linestyle=":", alpha=0.5)
    ax.legend(loc="upper left", fontsize=9)
    pdf.savefig(fig)
    plt.close(fig)


def table_page(pdf, df, snr, snr_desc):
    label = f"snr{snr:g}"
    ok = df.dropna(subset=[f"t_img_{label}_s"]).sort_values("gmag_AB")
    cols = ["Target", "g (AB)", "ETC mag", "Img base", "Img P=10%", "Img P=1%", "N exp (10%)"]
    cells = [[
        r["target"], f"{r['gmag_AB']:.2f}", f"{r['mag_to_enter']:.2f}",
        fmt_time(r[f"t_img_{label}_s"]), fmt_time(r[f"t_img_{label}_p10_s"]),
        fmt_time(r[f"t_img_{label}_p1_s"]), f"{r[f'n_exp_img_{label}_p10']:.0f}",
    ] for _, r in ok.iterrows()]

    fig, ax = plt.subplots(figsize=PAGE)
    ax.axis("off")
    ax.set_title(f"Per-target imaging-polarimetry exposure times at S/N = {snr:g} ({snr_desc}) "
                 f"(brightest first; PS1 g band)", fontsize=11, pad=18)
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
    missing = df[df[f"t_img_{label}_s"].isna()]
    if len(missing):
        ax.text(0.0, 0.02, "Not tabulated: " + ", ".join(
            f"{r['target']} ({r.get('note', 'no data')})" for _, r in missing.iterrows()),
            transform=ax.transAxes, fontsize=7, color="0.4")
    pdf.savefig(fig)
    plt.close(fig)


def figure_page_spec(pdf, df, obs):
    ok = df.dropna(subset=["gmag_AB", "t_spec_s"])
    fig, ax = plt.subplots(figsize=PAGE)
    fig.subplots_adjust(top=0.7, bottom=0.32)
    ax.scatter(ok["gmag_AB"], ok["t_spec_s"], color="steelblue",
               label=f"Spectropol. base (blue side, S/N={obs['target_snr']:g}/{obs['snr_floor']:g})")
    ax.scatter(ok["gmag_AB"], ok["t_spec_p10_s"], color="steelblue",
               marker="^", label="Spectropol., P=10% (x10)")
    ax.scatter(ok["gmag_AB"], ok["t_spec_p1_s"], color="steelblue",
               marker="s", label="Spectropol., P=1% (x100)")
    for hours, txt in [(1, "1 h"), (4, "4 h"), (10, "10 h")]:
        ax.axhline(hours * 3600, color="0.5", linestyle="--", linewidth=0.8)
        ax.text(ok["gmag_AB"].max(), hours * 3600, f" {txt}", va="bottom",
                color="0.4", fontsize=9)
    ax.set_yscale("log")
    ax.set_xlabel("Apparent g magnitude (AB)", fontsize=12)
    ax.set_ylabel("Required exposure time [s]", fontsize=12)
    ax.set_title(f"Kast spectropolarimetry exposure times (blue side, 3150-5400 Å) — "
                 f"median S/N ≥ {obs['target_snr']:g}, 90% of pixels S/N ≥ {obs['snr_floor']:g} — "
                 f"UV-excess candidates ({len(ok)} targets)")
    ax.grid(linestyle=":", alpha=0.5)
    ax.legend(loc="upper left", fontsize=9)
    pdf.savefig(fig)
    plt.close(fig)


def table_page_spec(pdf, df):
    ok = df.dropna(subset=["t_spec_s"]).sort_values("gmag_AB")
    cols = ["Target", "g (AB)", "ETC mag", "Spec base", "Spec P=10%", "Spec P=1%", "N exp (10%)"]
    cells = [[
        r["target"], f"{r['gmag_AB']:.2f}", f"{r['mag_to_enter']:.2f}",
        fmt_time(r["t_spec_s"]), fmt_time(r["t_spec_p10_s"]),
        fmt_time(r["t_spec_p1_s"]), f"{r['n_exp_spec_p10']:.0f}",
    ] for _, r in ok.iterrows()]

    fig, ax = plt.subplots(figsize=PAGE)
    ax.axis("off")
    ax.set_title("Per-target spectropolarimetry exposure times (brightest first; blue side "
                 "only, 3150-5400 Å)\njoint requirement: median pixel S/N ≥ target, "
                 "90% of pixels S/N ≥ floor", fontsize=11, pad=18)
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
    missing = df[df["t_spec_s"].isna()]
    if len(missing):
        ax.text(0.0, 0.02, "Not tabulated: " + ", ".join(
            f"{r['target']} ({r.get('note', 'no data')})" for _, r in missing.iterrows()),
            transform=ax.transAxes, fontsize=7, color="0.4")
    pdf.savefig(fig)
    plt.close(fig)


def figure_page_spec95(pdf, df, obs):
    ok = df.dropna(subset=["gmag_AB", "t_spec95_s"])
    fig, ax = plt.subplots(figsize=PAGE)
    fig.subplots_adjust(top=0.7, bottom=0.32)
    ax.scatter(ok["gmag_AB"], ok["t_spec95_s"], color="seagreen",
               label=f"Spectropol. base (blue side, 95% of pixels S/N≥{obs['snr_floor']:g})")
    ax.scatter(ok["gmag_AB"], ok["t_spec95_p10_s"], color="seagreen",
               marker="^", label="Spectropol., P=10% (x10)")
    ax.scatter(ok["gmag_AB"], ok["t_spec95_p1_s"], color="seagreen",
               marker="s", label="Spectropol., P=1% (x100)")
    for hours, txt in [(1, "1 h"), (4, "4 h"), (10, "10 h")]:
        ax.axhline(hours * 3600, color="0.5", linestyle="--", linewidth=0.8)
        ax.text(ok["gmag_AB"].max(), hours * 3600, f" {txt}", va="bottom",
                color="0.4", fontsize=9)
    ax.set_yscale("log")
    ax.set_xlabel("Apparent g magnitude (AB)", fontsize=12)
    ax.set_ylabel("Required exposure time [s]", fontsize=12)
    ax.set_title(f"Kast spectropolarimetry exposure times (blue side, 3150-5400 Å) — "
                 f"95% of pixels S/N ≥ {obs['snr_floor']:g}, no S/N ≥ {obs['target_snr']:g} requirement — "
                 f"UV-excess candidates ({len(ok)} targets)")
    ax.grid(linestyle=":", alpha=0.5)
    ax.legend(loc="upper left", fontsize=9)
    pdf.savefig(fig)
    plt.close(fig)


def table_page_spec95(pdf, df, obs):
    ok = df.dropna(subset=["t_spec95_s"]).sort_values("gmag_AB")
    cols = ["Target", "g (AB)", "ETC mag", "Spec95 base", "Spec95 P=10%", "Spec95 P=1%", "N exp (10%)"]
    cells = [[
        r["target"], f"{r['gmag_AB']:.2f}", f"{r['mag_to_enter']:.2f}",
        fmt_time(r["t_spec95_s"]), fmt_time(r["t_spec95_p10_s"]),
        fmt_time(r["t_spec95_p1_s"]), f"{r['n_exp_spec95_p10']:.0f}",
    ] for _, r in ok.iterrows()]

    fig, ax = plt.subplots(figsize=PAGE)
    ax.axis("off")
    ax.set_title(f"Per-target spectropolarimetry exposure times (brightest first; blue side "
                 f"only, 3150-5400 Å)\nsingle requirement: 95% of pixels S/N ≥ {obs['snr_floor']:g} "
                 f"(no S/N ≥ {obs['target_snr']:g} requirement)", fontsize=11, pad=18)
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
    missing = df[df["t_spec95_s"].isna()]
    if len(missing):
        ax.text(0.0, 0.02, "Not tabulated: " + ", ".join(
            f"{r['target']} ({r.get('note', 'no data')})" for _, r in missing.iterrows()),
            transform=ax.transAxes, fontsize=7, color="0.4")
    pdf.savefig(fig)
    plt.close(fig)


def main():
    with open(BASE_DIR / "config/qso_params.yaml") as f:
        cfg = yaml.safe_load(f)
    obs = cfg["observing"]
    df = build_plan(obs)
    with PdfPages(OUT_PDF) as pdf:
        summary_page(pdf, df, obs)
        figure_page(pdf, df, obs["target_snr"], 'ideal')
        table_page(pdf, df, obs["target_snr"], 'ideal')
        figure_page(pdf, df, obs["snr_floor"], 'hard minimum')
        table_page(pdf, df, obs["snr_floor"], 'hard minimum')
        figure_page_spec(pdf, df, obs)
        table_page_spec(pdf, df)
        figure_page_spec95(pdf, df, obs)
        table_page_spec95(pdf, df, obs)
        meta = pdf.infodict()
        meta["Title"] = "Lick Kast Polarimetry Exposure Plan — UV-excess QSOs"
        meta["Subject"] = "Exposure times and S/N for imaging and spectropolarimetry"
    print(f"wrote {OUT_PDF}")


if __name__ == "__main__":
    main()
