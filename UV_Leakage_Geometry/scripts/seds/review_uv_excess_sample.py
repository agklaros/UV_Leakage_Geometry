"""Interactive final visual-inspection step for the UV-excess candidate sample.

Steps through each candidate in data/matched/uv_excess_candidates_w2m.csv,
plotting its observed SED with the unreddened QSO template overlaid (same
flux conversion / template-scaling logic as Combined_SEDs_w2m.py), and lets
the user Accept or Reject it via on-figure buttons.

Decisions are written incrementally to UV_EXCESS_SAMPLE_progress.csv so the
review can be safely interrupted and resumed. Once every candidate has a
decision, the accepted rows are written to UV_EXCESS_SAMPLE.csv.

Run: python scripts/seds/review_uv_excess_sample.py
"""
import warnings
warnings.filterwarnings("ignore")

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from astropy.table import Table
from astropy.io import ascii
import astropy.units as u

import synphot
from synphot import SourceSpectrum
from synphot import units as su
from synphot import SpectralElement
from synphot.models import Empirical1D
from synphot.observation import Observation


BASE_DIR = Path(__file__).resolve().parents[2]
CAND_CSV = BASE_DIR / "data/matched/uv_excess_candidates_w2m.csv"
FILTDIR = BASE_DIR / "data/filters"
TEMPLATE_QSO = BASE_DIR / "templates/qso_template.txt"
PROGRESS_CSV = BASE_DIR / "data/matched/UV_EXCESS_SAMPLE_progress.csv"
FINAL_CSV = BASE_DIR / "data/matched/UV_EXCESS_SAMPLE.csv"

table = Table.read(CAND_CSV)

_spec = ascii.read(str(TEMPLATE_QSO))
templateWave = _spec['col1']
templateFlux = _spec['col2']


def mag_arr(col):
    if hasattr(col, 'filled'):
        return np.array(col.filled(np.nan), dtype=float)
    arr = np.array(col, dtype=str)
    arr[arr == '--'] = 'nan'
    return arr.astype(float)


lam_fuv = 1549 * u.AA
lam_nuv = 2303 * u.AA
lam_g = 4810 * u.AA
lam_r = 6170 * u.AA
lam_i = 7520 * u.AA
lam_z = 8660 * u.AA
lam_y = 9620 * u.AA
lam_Y_uk = 10305 * u.AA
lam_J_uk = 12483 * u.AA
lam_H_uk = 16313 * u.AA
lam_K_uk = 22010 * u.AA
lam_J_2m = 12350 * u.AA
lam_H_2m = 16620 * u.AA
lam_K_2m = 21590 * u.AA
lam_W1 = 33526 * u.AA
lam_W2 = 46028 * u.AA
lam_W3 = 115608 * u.AA
lam_W4 = 220883 * u.AA

filt_files = [
    "GALEX_GALEX.FUV.dat",
    "GALEX_GALEX.NUV.dat",
    "PAN-STARRS_PS1.g.dat",
    "PAN-STARRS_PS1.r.dat",
    "PAN-STARRS_PS1.i.dat",
    "PAN-STARRS_PS1.z.dat",
    "PAN-STARRS_PS1.y.dat",
    "UKIRT_UKIDSS.Y.dat",
    "UKIRT_UKIDSS.J.dat",
    "UKIRT_UKIDSS.H.dat",
    "UKIRT_UKIDSS.K.dat",
    "2MASS_2MASS.J.dat",
    "2MASS_2MASS.H.dat",
    "2MASS_2MASS.Ks.dat",
    "WISE_WISE.W1.dat",
    "WISE_WISE.W2.dat",
    "WISE_WISE.W3.dat",
    "WISE_WISE.W4.dat",
]

X_LO, X_HI = 1000, 15000

# DESI rows populate gmag/rmag/imag/zmag; W2M rows populate gmag_2/rmag_2/imag_2/zmag_2.
gmag = mag_arr(table['gmag'])
gmag = np.where(np.isfinite(gmag), gmag, mag_arr(table['gmag_2']))
rmag = mag_arr(table['rmag'])
rmag = np.where(np.isfinite(rmag), rmag, mag_arr(table['rmag_2']))
imag = mag_arr(table['imag'])
imag = np.where(np.isfinite(imag), imag, mag_arr(table['imag_2']))
zmag = mag_arr(table['zmag'])
zmag = np.where(np.isfinite(zmag), zmag, mag_arr(table['zmag_2']))

flam_fuv = (mag_arr(table['FUVmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_fuv))
flam_fuv[flam_fuv > (1e-11 * su.FLAM)] = np.nan
flam_nuv = (mag_arr(table['NUVmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_nuv))
flam_nuv[flam_nuv > (1e-11 * su.FLAM)] = np.nan

flam_g = (gmag * u.ABmag).to(su.FLAM, u.spectral_density(lam_g))
flam_g[flam_g > (1e-11 * su.FLAM)] = np.nan
flam_r = (rmag * u.ABmag).to(su.FLAM, u.spectral_density(lam_r))
flam_r[flam_r > (1e-11 * su.FLAM)] = np.nan
flam_i = (imag * u.ABmag).to(su.FLAM, u.spectral_density(lam_i))
flam_i[flam_i > (1e-11 * su.FLAM)] = np.nan
flam_z = (zmag * u.ABmag).to(su.FLAM, u.spectral_density(lam_z))
flam_z[flam_z > (1e-11 * su.FLAM)] = np.nan
flam_y = (mag_arr(table['ymag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_y))
flam_y[flam_y > (1e-11 * su.FLAM)] = np.nan

flam_Yuk = ((mag_arr(table['yAperMag3']) + 0.634) * u.ABmag).to(su.FLAM, u.spectral_density(lam_Y_uk))
flam_Yuk[flam_Yuk > (1e-10 * su.FLAM)] = np.nan
flam_Juk = ((mag_arr(table['j_1AperMag3']) + 0.938) * u.ABmag).to(su.FLAM, u.spectral_density(lam_J_uk))
flam_Juk[flam_Juk > (1e-10 * su.FLAM)] = np.nan
flam_Huk = ((mag_arr(table['hAperMag3']) + 1.379) * u.ABmag).to(su.FLAM, u.spectral_density(lam_H_uk))
flam_Huk[flam_Huk > (1e-10 * su.FLAM)] = np.nan
flam_Kuk = ((mag_arr(table['kAperMag3']) + 1.900) * u.ABmag).to(su.FLAM, u.spectral_density(lam_K_uk))
flam_Kuk[flam_Kuk > (1e-10 * su.FLAM)] = np.nan

flam_J2m = ((mag_arr(table['Jmag']) + 0.894) * u.ABmag).to(su.FLAM, u.spectral_density(lam_J_2m))
flam_J2m[flam_J2m > (1e-10 * su.FLAM)] = np.nan
flam_H2m = ((mag_arr(table['Hmag']) + 1.374) * u.ABmag).to(su.FLAM, u.spectral_density(lam_H_2m))
flam_H2m[flam_H2m > (1e-10 * su.FLAM)] = np.nan
flam_K2m = ((mag_arr(table['Kmag']) + 1.839) * u.ABmag).to(su.FLAM, u.spectral_density(lam_K_2m))
flam_K2m[flam_K2m > (1e-10 * su.FLAM)] = np.nan

flam_W1 = ((mag_arr(table['W1mag']) + 2.699) * u.ABmag).to(su.FLAM, u.spectral_density(lam_W1))
flam_W1[flam_W1 > (1e-10 * su.FLAM)] = np.nan
flam_W2 = ((mag_arr(table['W2mag']) + 3.339) * u.ABmag).to(su.FLAM, u.spectral_density(lam_W2))
flam_W2[flam_W2 > (1e-10 * su.FLAM)] = np.nan
flam_W3 = ((mag_arr(table['W3mag']) + 5.174) * u.ABmag).to(su.FLAM, u.spectral_density(lam_W3))
flam_W3[flam_W3 > (1e-10 * su.FLAM)] = np.nan
flam_W4 = ((mag_arr(table['W4mag']) + 6.620) * u.ABmag).to(su.FLAM, u.spectral_density(lam_W4))
flam_W4[flam_W4 > (1e-10 * su.FLAM)] = np.nan

_filter_bandpasses = [SpectralElement.from_file(str(FILTDIR / ff)) for ff in filt_files]


def target_name(index):
    """Stable per-row identifier: designation if present, else TARGETID."""
    desig = str(table['designation'][index])
    if desig not in ('', '--', 'nan', 'None'):
        return desig
    return f"TARGETID_{table['TARGETID'][index]}"


def pick(index, col_a, col_b):
    a = mag_arr(table[col_a])[index]
    if np.isfinite(a):
        return a
    return mag_arr(table[col_b])[index]


def candidate_redshift(index):
    z_desi = mag_arr(table['Z'])[index]
    if np.isfinite(z_desi):
        return z_desi
    return mag_arr(table['zsp'])[index]


def build_candidate_list():
    """All rows with a usable redshift, in table order (DESI rows use Z, W2M rows use zsp)."""
    candidates = []
    for index in range(len(table)):
        z = candidate_redshift(index)
        if np.isnan(z):
            continue
        candidates.append(index)
    return candidates


def plot_sed(ax, index):
    ax.clear()
    zsp = candidate_redshift(index)

    lam_all = np.array([
        1549, 2303, 4810, 6170, 7520, 8660, 9620,
        10305, 12350, 12483, 16313, 16620, 21590, 22010,
        33526, 46028, 115608, 220883,
    ])
    flam_all = np.array([
        flam_fuv.value[index], flam_nuv.value[index],
        flam_g.value[index], flam_r.value[index],
        flam_i.value[index], flam_z.value[index], flam_y.value[index],
        flam_Yuk.value[index], flam_J2m.value[index], flam_Juk.value[index],
        flam_Huk.value[index], flam_H2m.value[index], flam_K2m.value[index],
        flam_Kuk.value[index],
        flam_W1.value[index], flam_W2.value[index],
        flam_W3.value[index], flam_W4.value[index],
    ])
    ax.plot(lam_all / (1 + zsp), flam_all,
            marker='o', linestyle='-', label=target_name(index))

    sp = SourceSpectrum(Empirical1D, points=templateWave * u.AA,
                         lookup_table=templateFlux * su.FLAM, z=zsp)
    synth_flx = []
    for bp in _filter_bandpasses:
        try:
            obs = Observation(sp, bp, force='extrap')
            synth_flx.append(obs.effstim('flam').value)
        except (synphot.exceptions.DisjointError, synphot.exceptions.SynphotError):
            synth_flx.append(np.nan)
    synth_flx = np.array(synth_flx)

    valid = np.isfinite(flam_all) & np.isfinite(synth_flx) & (synth_flx > 0)
    scale = np.nanmedian(flam_all[valid] / synth_flx[valid]) if valid.any() else 1.0

    ax.plot(templateWave, scale * templateFlux,
            color='gray', alpha=0.6, label='QSO template')

    lam_rest = lam_all / (1 + zsp)
    in_window = np.isfinite(flam_all) & (lam_rest >= X_LO) & (lam_rest <= X_HI)
    y_hi = flam_all[in_window].max() * 1.1 if in_window.any() else 3e-17

    ax.set_xlim(X_LO, X_HI)
    ax.set_ylim(0, y_hi)
    ax.set_xlabel('Rest-frame Wavelength (Å)')
    ax.set_ylabel(r'$F_\lambda$ (erg s$^{-1}$ cm$^{-2}$ Å$^{-1}$)')
    ra = pick(index, 'RA', 'ra')
    dec = pick(index, 'DEC', 'dec')
    ebv = pick(index, 'EBV', 'ebv')
    ax.set_title(
        f"{target_name(index)}\n"
        f"RA = {ra:.4f}   DEC = {dec:.4f}   z = {zsp:.3f}   E(B-V) = {ebv:.3f}"
    )
    ax.legend(fontsize=8)


def load_progress():
    if PROGRESS_CSV.exists():
        return pd.read_csv(PROGRESS_CSV, index_col='designation')['ACCEPTED'].to_dict()
    return {}


def save_decision(decisions):
    df = pd.DataFrame(
        [{'designation': name, 'ACCEPTED': val} for name, val in decisions.items()]
    )
    df.to_csv(PROGRESS_CSV, index=False)


def write_final_sample(decisions):
    accepted_names = {name for name, val in decisions.items() if val == 'YES'}
    keep_mask = [target_name(i) in accepted_names for i in range(len(table))]
    accepted_table = table[np.array(keep_mask)]
    accepted_table.write(FINAL_CSV, format='csv', overwrite=True)
    print(f"wrote {FINAL_CSV} ({len(accepted_table)} accepted of {len(decisions)} reviewed)")


def main():
    candidates = build_candidate_list()
    decisions = load_progress()

    remaining = [i for i in candidates if target_name(i) not in decisions]
    if not remaining:
        print("All candidates already reviewed.")
        write_final_sample(decisions)
        return

    fig, ax = plt.subplots(figsize=(8, 6))
    plt.subplots_adjust(bottom=0.22)

    state = {'pos': 0}

    def show_current():
        index = remaining[state['pos']]
        plot_sed(ax, index)
        n_done = len(candidates) - len(remaining) + state['pos']
        fig.suptitle(f"Candidate {n_done + 1} / {len(candidates)}")
        fig.canvas.draw_idle()

    def advance(decision):
        index = remaining[state['pos']]
        decisions[target_name(index)] = decision
        save_decision(decisions)
        state['pos'] += 1
        if state['pos'] >= len(remaining):
            plt.close(fig)
            write_final_sample(decisions)
            return
        show_current()

    def on_accept(event):
        advance('YES')

    def on_reject(event):
        advance('NO')

    ax_reject = fig.add_axes([0.3, 0.05, 0.15, 0.08])
    ax_accept = fig.add_axes([0.55, 0.05, 0.15, 0.08])
    btn_reject = Button(ax_reject, 'Reject', color='#f4a3a3', hovercolor='#e57373')
    btn_accept = Button(ax_accept, 'Accept', color='#a3d9a5', hovercolor='#66bb6a')
    btn_reject.on_clicked(on_reject)
    btn_accept.on_clicked(on_accept)

    show_current()
    plt.show()

    if len(decisions) < len(candidates):
        print(f"Review paused: {len(decisions)}/{len(candidates)} decided. "
              f"Re-run this script to resume.")


if __name__ == "__main__":
    main()
