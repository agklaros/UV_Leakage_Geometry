import warnings
warnings.filterwarnings("ignore")

from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
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
file = str(BASE_DIR / "data/matched/uv_excess_candidates_w2m.csv")
filtdir = str(BASE_DIR / "data/filters/")
templateQSO = str(BASE_DIR / "templates/qso_template.txt")
outdir = str(Path.home() / "Downloads/")

table = Table.read(file)

_spec        = ascii.read(templateQSO)
templateWave = _spec['col1']
templateFlux = _spec['col2']


def mag_arr(col):
    if hasattr(col, 'filled'):
        return np.array(col.filled(np.nan), dtype=float)
    arr = np.array(col, dtype=str)
    arr[arr == '--'] = 'nan'
    return arr.astype(float)


ebv = mag_arr(table['EBV'])

lam_fuv  = 1549  * u.AA
lam_nuv  = 2303  * u.AA
lam_g    = 4810  * u.AA
lam_r    = 6170  * u.AA
lam_i    = 7520  * u.AA
lam_z    = 8660  * u.AA
lam_y    = 9620  * u.AA
lam_Y_uk = 10305 * u.AA
lam_J_uk = 12483 * u.AA
lam_H_uk = 16313 * u.AA
lam_K_uk = 22010 * u.AA
lam_J_2m = 12350 * u.AA
lam_H_2m = 16620 * u.AA
lam_K_2m = 21590 * u.AA
lam_W1   = 33526 * u.AA
lam_W2   = 46028 * u.AA
lam_W3   = 115608 * u.AA
lam_W4   = 220883 * u.AA

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
lam_template = [lam_fuv, lam_nuv, lam_g, lam_r, lam_i, lam_z, lam_y,
                lam_Y_uk, lam_J_uk, lam_H_uk, lam_K_uk,
                lam_J_2m, lam_H_2m, lam_K_2m,
                lam_W1, lam_W2, lam_W3, lam_W4]

# Common x-axis bounds (shared across all SEDs so plots are directly comparable).
X_LO, X_HI = 1000, 15000

flam_fuv = (mag_arr(table['FUVmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_fuv))
flam_fuv[flam_fuv > (1e-11 * su.FLAM)] = np.nan
flam_nuv = (mag_arr(table['NUVmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_nuv))
flam_nuv[flam_nuv > (1e-11 * su.FLAM)] = np.nan

# DESI rows populate gmag/rmag/imag/zmag; W2M rows populate gmag_2/rmag_2/imag_2/zmag_2 instead.
gmag = mag_arr(table['gmag'])
gmag = np.where(np.isfinite(gmag), gmag, mag_arr(table['gmag_2']))
rmag = mag_arr(table['rmag'])
rmag = np.where(np.isfinite(rmag), rmag, mag_arr(table['rmag_2']))
imag = mag_arr(table['imag'])
imag = np.where(np.isfinite(imag), imag, mag_arr(table['imag_2']))
zmag = mag_arr(table['zmag'])
zmag = np.where(np.isfinite(zmag), zmag, mag_arr(table['zmag_2']))

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

flam_Yuk = ((mag_arr(table['yAperMag3'])   + 0.634) * u.ABmag).to(su.FLAM, u.spectral_density(lam_Y_uk))
flam_Yuk[flam_Yuk > (1e-10 * su.FLAM)] = np.nan
flam_Juk = ((mag_arr(table['j_1AperMag3']) + 0.938) * u.ABmag).to(su.FLAM, u.spectral_density(lam_J_uk))
flam_Juk[flam_Juk > (1e-10 * su.FLAM)] = np.nan
flam_Huk = ((mag_arr(table['hAperMag3'])   + 1.379) * u.ABmag).to(su.FLAM, u.spectral_density(lam_H_uk))
flam_Huk[flam_Huk > (1e-10 * su.FLAM)] = np.nan
flam_Kuk = ((mag_arr(table['kAperMag3'])   + 1.900) * u.ABmag).to(su.FLAM, u.spectral_density(lam_K_uk))
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


def plot_sed(index, name, ra, dec, zsp):
    plt.figure()

    lam_all = np.array([
        1549,   2303,   4810,   6170,   7520,   8660,   9620,
        10305,  12350,  12483,  16313,  16620,  21590,  22010,
        33526,  46028,  115608, 220883,
    ])
    flam_all = np.array([
        flam_fuv.value[index], flam_nuv.value[index],
        flam_g.value[index],   flam_r.value[index],
        flam_i.value[index],   flam_z.value[index],   flam_y.value[index],
        flam_Yuk.value[index], flam_J2m.value[index], flam_Juk.value[index],
        flam_Huk.value[index], flam_H2m.value[index], flam_K2m.value[index],
        flam_Kuk.value[index],
        flam_W1.value[index],  flam_W2.value[index],
        flam_W3.value[index],  flam_W4.value[index],
    ])
    plt.plot(lam_all / (1 + zsp), flam_all,
             marker='o', linestyle='-', label=str(name))

    sp = SourceSpectrum(Empirical1D, points=templateWave * u.AA,
                        lookup_table=templateFlux * su.FLAM, z=zsp)
    synth_flx = []
    for ff in filt_files:
        bp = SpectralElement.from_file(str(Path(filtdir) / ff))
        try:
            obs = Observation(sp, bp, force='extrap')
            synth_flx.append(obs.effstim('flam').value)
        except (synphot.exceptions.DisjointError, synphot.exceptions.SynphotError):
            synth_flx.append(np.nan)
    synth_flx = np.array(synth_flx)

    # obs_for_scale order need not match lam_all; only finite pairs are used for median scaling
    obs_for_scale = np.array([
        flam_fuv.value[index], flam_nuv.value[index],
        flam_g.value[index],   flam_r.value[index],  flam_i.value[index],
        flam_z.value[index],   flam_y.value[index],
        flam_Yuk.value[index], flam_Juk.value[index],
        flam_Huk.value[index], flam_Kuk.value[index],
        flam_J2m.value[index], flam_H2m.value[index], flam_K2m.value[index],
        flam_W1.value[index],  flam_W2.value[index],
        flam_W3.value[index],  flam_W4.value[index],
    ])
    valid = np.isfinite(obs_for_scale) & np.isfinite(synth_flx) & (synth_flx > 0)
    scale = np.nanmedian(obs_for_scale[valid] / synth_flx[valid]) if valid.any() else 1.0

    plt.plot(templateWave, scale * templateFlux,
             color='gray', alpha=0.6, label='QSO template')

    # X range is fixed for cross-object comparability; the y range is sized to the
    # photometry actually inside that window, so the model may run off-frame but no
    # observed data point is ever clipped out of view.
    lam_rest = lam_all / (1 + zsp)
    in_window = np.isfinite(flam_all) & (lam_rest >= X_LO) & (lam_rest <= X_HI)
    y_hi = flam_all[in_window].max() * 1.1 if in_window.any() else 3e-17

    plt.xscale('linear')
    plt.yscale('linear')
    plt.xlim(X_LO, X_HI)
    plt.ylim(0, y_hi)
    plt.xlabel('Rest-frame Wavelength (Å)')
    plt.ylabel(r'$F_\lambda$ (erg s$^{-1}$ cm$^{-2}$ Å$^{-1}$)')
    plt.title(f'RA = {ra:.4f}   DEC = {dec:.4f}')
    plt.legend(fontsize=8)
    plt.tight_layout()

    safe_name = "".join(c if (c.isalnum() or c in "._-") else "_" for c in str(name))
    plt.savefig(str(Path(outdir) / f"SED_{safe_name}.png"), dpi=150)
    plt.close()


# Loop 1: DESI candidates — rows where Z is set
# uv_excess_candidates_w2m.csv is an outer-join vstack (01_crossmatch.ipynb), so a row from
# the other catalog leaves Z masked/NaN, not 0.0 — skip on isnan, not == 0.0.
targetID = np.array(table['TARGETID'], dtype=str)
redshift = mag_arr(table['Z'])
RA       = mag_arr(table['RA'])
DEC      = mag_arr(table['DEC'])

for index in range(len(table)):
    if np.isnan(redshift[index]):
        continue
    plot_sed(index, targetID[index], RA[index], DEC[index], redshift[index])

# Loop 2: W2M candidates — rows where zsp is set (NaN, not 0.0, marks a DESI row)
designation = np.array(table['designation'], dtype=str)
ra_w2m  = mag_arr(table['ra'])
dec_w2m = mag_arr(table['dec'])
zsp_w2m = mag_arr(table['zsp'])

for index in range(len(table)):
    if np.isnan(zsp_w2m[index]):
        continue
    plot_sed(index, designation[index], ra_w2m[index], dec_w2m[index], zsp_w2m[index])
