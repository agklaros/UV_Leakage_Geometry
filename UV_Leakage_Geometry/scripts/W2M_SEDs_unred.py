import warnings
warnings.filterwarnings("ignore")

import numpy as np
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

BASE_DIR    = "/home/agklaros/Documents/UV_Leakage_Geometry-1/UV_Leakage_Geometry"
file        = f"{BASE_DIR}/data/matched/W2M_matched.csv"
filtdir     = f"{BASE_DIR}/filters/"
templateQSO = f"{BASE_DIR}/templates/qso_template.txt"

table = Table.read(file)

_spec        = ascii.read(templateQSO)
templateWave = _spec['col1']
templateFlux = _spec['col2']


def _mag_arr(col):
    if hasattr(col, 'filled'):
        return np.array(col.filled(np.nan), dtype=float)
    arr = np.array(col, dtype=str)
    arr[arr == '--'] = 'nan'
    return arr.astype(float)


targetID = np.array(table['designation'])
redshift = _mag_arr(table['zsp'])

# Effective wavelengths (Angstrom)
lam_fuv  = 1549   * u.AA
lam_nuv  = 2303   * u.AA
lam_g    = 4810   * u.AA
lam_r    = 6170   * u.AA
lam_i    = 7520   * u.AA
lam_z    = 8660   * u.AA
lam_y    = 9620   * u.AA
lam_J_2m = 12350  * u.AA
lam_H_2m = 16620  * u.AA
lam_K_2m = 21590  * u.AA
lam_w1   = 33680  * u.AA
lam_w2   = 46180  * u.AA
lam_w3   = 120820 * u.AA
lam_w4   = 221940 * u.AA

# Filter files for template synthetic photometry (GALEX + PS1 + WISE)
filt_files = [
    "GALEX_GALEX.FUV.dat",
    "GALEX_GALEX.NUV.dat",
    "PAN-STARRS_PS1.g.dat",
    "PAN-STARRS_PS1.r.dat",
    "PAN-STARRS_PS1.i.dat",
    "PAN-STARRS_PS1.z.dat",
    "PAN-STARRS_PS1.y.dat",
    "WISE_WISE.W1.dat",
    "WISE_WISE.W2.dat",
    "WISE_WISE.W3.dat",
    "WISE_WISE.W4.dat",
]
lam_template = [lam_fuv, lam_nuv, lam_g, lam_r, lam_i, lam_z, lam_y,
                lam_w1, lam_w2, lam_w3, lam_w4]

# GALEX (AB system) — from crossmatch
flam_fuv = (_mag_arr(table['FUVmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_fuv))
flam_fuv[flam_fuv > (1e-11 * su.FLAM)] = np.nan
flam_nuv = (_mag_arr(table['NUVmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_nuv))
flam_nuv[flam_nuv > (1e-11 * su.FLAM)] = np.nan

# PanSTARRS DR1 (AB system) — from crossmatch (PS1_ prefix to avoid W2M column collision)
flam_g = (_mag_arr(table['PS1_gmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_g))
flam_g[flam_g > (1e-11 * su.FLAM)] = np.nan
flam_r = (_mag_arr(table['PS1_rmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_r))
flam_r[flam_r > (1e-11 * su.FLAM)] = np.nan
flam_i = (_mag_arr(table['PS1_imag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_i))
flam_i[flam_i > (1e-11 * su.FLAM)] = np.nan
flam_z = (_mag_arr(table['PS1_zmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_z))
flam_z[flam_z > (1e-11 * su.FLAM)] = np.nan
flam_y = (_mag_arr(table['PS1_ymag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_y))
flam_y[flam_y > (1e-11 * su.FLAM)] = np.nan

# 2MASS (Vega -> AB: J +0.894, H +1.374, K +1.839) — from W2M base catalog
flam_J2m = ((_mag_arr(table['j_m_2mass']) + 0.894) * u.ABmag).to(su.FLAM, u.spectral_density(lam_J_2m))
flam_J2m[flam_J2m > (1e-10 * su.FLAM)] = np.nan
flam_H2m = ((_mag_arr(table['h_m_2mass']) + 1.374) * u.ABmag).to(su.FLAM, u.spectral_density(lam_H_2m))
flam_H2m[flam_H2m > (1e-10 * su.FLAM)] = np.nan
flam_K2m = ((_mag_arr(table['k_m_2mass']) + 1.839) * u.ABmag).to(su.FLAM, u.spectral_density(lam_K_2m))
flam_K2m[flam_K2m > (1e-10 * su.FLAM)] = np.nan

# WISE (Vega -> AB: W1 +2.699, W2 +3.339, W3 +5.174, W4 +6.620) — from W2M base catalog
flam_w1 = ((_mag_arr(table['w1mpro']) + 2.699) * u.ABmag).to(su.FLAM, u.spectral_density(lam_w1))
flam_w2 = ((_mag_arr(table['w2mpro']) + 3.339) * u.ABmag).to(su.FLAM, u.spectral_density(lam_w2))
flam_w3 = ((_mag_arr(table['w3mpro']) + 5.174) * u.ABmag).to(su.FLAM, u.spectral_density(lam_w3))
flam_w4 = ((_mag_arr(table['w4mpro']) + 6.620) * u.ABmag).to(su.FLAM, u.spectral_density(lam_w4))

f_fn = flam_fuv / flam_nuv
f_ng = flam_nuv / flam_g
f_gr = flam_g   / flam_r


def HasUV(index):
    return np.isfinite(flam_fuv.value[index]) or np.isfinite(flam_nuv.value[index])


for index, name in enumerate(targetID):
    zsp = redshift[index]
    if not HasUV(index):
        continue

    plt.figure()

    lam_all = np.array([
        1549,  2303,  4810,   6170,   7520,   8660,   9620,
        12350, 16620, 21590,  33680,  46180,  120820, 221940,
    ])
    flam_all = np.array([
        flam_fuv.value[index], flam_nuv.value[index],
        flam_g.value[index],   flam_r.value[index],
        flam_i.value[index],   flam_z.value[index],   flam_y.value[index],
        flam_J2m.value[index], flam_H2m.value[index], flam_K2m.value[index],
        flam_w1.value[index],  flam_w2.value[index],
        flam_w3.value[index],  flam_w4.value[index],
    ])
    plt.plot(lam_all / (1 + zsp), flam_all,
             marker='o', linestyle='-', label=str(name))

    sp = SourceSpectrum(Empirical1D, points=templateWave * u.AA,
                        lookup_table=templateFlux * su.FLAM, z=zsp)
    synth_flx = []
    for ff in filt_files:
        bp = SpectralElement.from_file(filtdir + ff)
        try:
            obs = Observation(sp, bp, force='extrap')
            synth_flx.append(obs.effstim('flam').value)
        except (synphot.exceptions.DisjointError, synphot.exceptions.SynphotError):
            synth_flx.append(np.nan)
    synth_flx = np.array(synth_flx)

    # Scale template to GALEX + PS1 + WISE photometry
    obs_for_scale = np.array([
        flam_fuv.value[index], flam_nuv.value[index],
        flam_g.value[index],   flam_r.value[index],  flam_i.value[index],
        flam_z.value[index],   flam_y.value[index],
        flam_w1.value[index],  flam_w2.value[index],
        flam_w3.value[index],  flam_w4.value[index],
    ])
    valid = np.isfinite(obs_for_scale) & np.isfinite(synth_flx) & (synth_flx > 0)
    scale = np.nanmedian(obs_for_scale[valid] / synth_flx[valid]) if valid.any() else 1.0

    plt.plot(templateWave, scale * templateFlux,
             color='gray', alpha=0.6, label='QSO template')
    lam_tpl_rest = np.array([l.value for l in lam_template]) / (1 + zsp)
    valid_tpl = np.isfinite(synth_flx)
    plt.scatter(lam_tpl_rest[valid_tpl], scale * synth_flx[valid_tpl],
                color='orange', marker='s', zorder=5, label='template synth phot')

    plt.xscale('log')
    plt.yscale('log')
    plt.ylim(1e-18, 1e-15)
    plt.xlabel('Rest Wavelength (Å)')
    plt.ylabel(r'$F_\lambda$ (erg s$^{-1}$ cm$^{-2}$ Å$^{-1}$)')
    plt.title(f'{name}   z = {zsp:.4f}')
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.show()
