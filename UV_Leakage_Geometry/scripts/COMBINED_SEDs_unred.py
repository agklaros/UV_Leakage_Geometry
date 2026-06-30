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
file        = f"{BASE_DIR}/data/matched/COMBINED_matched.csv"
filtdir     = f"{BASE_DIR}/filters/"
templateQSO = f"{BASE_DIR}/templates/qso_template.txt"

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


targetID = np.array(table['TARGETID'])
redshift = mag_arr(table['Z'])
ebv      = mag_arr(table['EBV'])

# Effective wavelengths (Angstrom)
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

# Filter files for template synthetic photometry (GALEX + PS1 + UKIDSS only; no 2MASS filters)
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
]
lam_template = [lam_fuv, lam_nuv, lam_g, lam_r, lam_i, lam_z, lam_y,
                lam_Y_uk, lam_J_uk, lam_H_uk, lam_K_uk]

#Flux Conversions

# GALEX (AB system)
flam_fuv = (mag_arr(table['FUVmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_fuv))
flam_fuv[flam_fuv > (1e-11 * su.FLAM)] = np.nan
flam_nuv = (mag_arr(table['NUVmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_nuv))
flam_nuv[flam_nuv > (1e-11 * su.FLAM)] = np.nan

# PanSTARRS DR1 (AB system)
flam_g = (mag_arr(table['gmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_g))
flam_g[flam_g > (1e-11 * su.FLAM)] = np.nan
flam_r = (mag_arr(table['rmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_r))
flam_r[flam_r > (1e-11 * su.FLAM)] = np.nan
flam_i = (mag_arr(table['imag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_i))
flam_i[flam_i > (1e-11 * su.FLAM)] = np.nan
flam_z = (mag_arr(table['zmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_z))
flam_z[flam_z > (1e-11 * su.FLAM)] = np.nan
flam_y = (mag_arr(table['ymag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_y))
flam_y[flam_y > (1e-11 * su.FLAM)] = np.nan

# UKIDSS (Vega -> AB offsets: Y +0.634, J +0.938, H +1.379, K +1.900)
flam_Yuk = ((mag_arr(table['yAperMag3'])   + 0.634) * u.ABmag).to(su.FLAM, u.spectral_density(lam_Y_uk))
flam_Yuk[flam_Yuk > (1e-10 * su.FLAM)] = np.nan
flam_Juk = ((mag_arr(table['j_1AperMag3']) + 0.938) * u.ABmag).to(su.FLAM, u.spectral_density(lam_J_uk))
flam_Juk[flam_Juk > (1e-10 * su.FLAM)] = np.nan
flam_Huk = ((mag_arr(table['hAperMag3'])   + 1.379) * u.ABmag).to(su.FLAM, u.spectral_density(lam_H_uk))
flam_Huk[flam_Huk > (1e-10 * su.FLAM)] = np.nan
flam_Kuk = ((mag_arr(table['kAperMag3'])   + 1.900) * u.ABmag).to(su.FLAM, u.spectral_density(lam_K_uk))
flam_Kuk[flam_Kuk > (1e-10 * su.FLAM)] = np.nan

# 2MASS (Vega -> AB offsets: J +0.894, H +1.374, K +1.839)
flam_J2m = ((mag_arr(table['Jmag_2mass']) + 0.894) * u.ABmag).to(su.FLAM, u.spectral_density(lam_J_2m))
flam_J2m[flam_J2m > (1e-10 * su.FLAM)] = np.nan
flam_H2m = ((mag_arr(table['Hmag_2mass']) + 1.374) * u.ABmag).to(su.FLAM, u.spectral_density(lam_H_2m))
flam_H2m[flam_H2m > (1e-10 * su.FLAM)] = np.nan
flam_K2m = ((mag_arr(table['Kmag_2mass']) + 1.839) * u.ABmag).to(su.FLAM, u.spectral_density(lam_K_2m))
flam_K2m[flam_K2m > (1e-10 * su.FLAM)] = np.nan

f_fn = flam_fuv / flam_nuv
f_ng = flam_nuv / flam_g
f_gr = flam_g   / flam_r


def UVExcess(index):
    # NUV/g > 1 & g/r < 1: NUV excess over optical continuum (NUV upturn)
    # FUV/NUV > 1 & NUV/g < 1: FUV upturn with suppressed NUV (patchy geometry signature)
    return (
        (
            (f_ng[index] > 1 and f_gr[index] < 1) or
            (f_fn[index] > 1 and f_ng[index] < 1)
        ) and ebv[index] > 0.2
    )


for index, name in enumerate(targetID):
    zsp = redshift[index]
    if not UVExcess(index):
        continue

    plt.figure()

    lam_all = np.array([
        1549,  2303,  4810,  6170,  7520,  8660,  9620,
        10305, 12350, 12483, 16313, 16620, 21590, 22010,
    ])
    flam_all = np.array([
        flam_fuv.value[index], flam_nuv.value[index],
        flam_g.value[index],   flam_r.value[index],
        flam_i.value[index],   flam_z.value[index],   flam_y.value[index],
        flam_Yuk.value[index], flam_J2m.value[index], flam_Juk.value[index],
        flam_Huk.value[index], flam_H2m.value[index], flam_K2m.value[index],
        flam_Kuk.value[index],
    ])
    plt.plot(lam_all / (1 + zsp), flam_all,
             marker='o', linestyle='-', label=str(name))

    # ── Unreddened QSO template overlay ──────────────────────────────────────
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

    # Scale template to observed (GALEX + PS1 + UKIDSS) photometry
    obs_for_scale = np.array([
        flam_fuv.value[index], flam_nuv.value[index],
        flam_g.value[index],   flam_r.value[index],  flam_i.value[index],
        flam_z.value[index],   flam_y.value[index],
        flam_Yuk.value[index], flam_Juk.value[index],
        flam_Huk.value[index], flam_Kuk.value[index],
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
    plt.title(f'TARGETID {name}   E(B-V) = {ebv[index]:.3f}')
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.show()
