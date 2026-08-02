"""One-off: save individual SED PNGs for two specified designations.

Reuses the plotting logic in uv_excess_review_report.py rather than duplicating it.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import uv_excess_review_report as report

BASE_DIR = Path(__file__).resolve().parents[2]
OUTDIR = BASE_DIR / "figures"

TARGET_DESIGNATIONS = ["J150746.11+093731.2", "J150152.94+020604.9"]

for desig in TARGET_DESIGNATIONS:
    index = [i for i in range(len(report.table)) if report.target_name(i) == desig][0]
    fig, ax = plt.subplots(figsize=(8, 6))
    plt.subplots_adjust(bottom=0.12)
    report.plot_sed(ax, index)
    outpath = OUTDIR / f"SED_{desig}.png"
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"wrote {outpath}")
