

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import matplotlib.pyplot as plt
import sys, os
import glob
from pathlib import Path

#import astropy
from astropy.table import vstack, Table, QTable, join
from astropy.io import ascii
from astropy.io import fits
from astropy.convolution import convolve, Box1DKernel
import astropy.units as u
from astropy.coordinates import SkyCoord

import synphot
from synphot import SourceSpectrum
from synphot import units as su
from synphot import SpectralElement
from synphot.models import Empirical1D
from synphot.observation import Observation

from scipy.interpolate import interp1d
from scipy.optimize import curve_fit

from quasar_unred import load_template, extinguish, fit_composite, find_ebv, mc_spec

BASE_DIR = Path(__file__).resolve().parents[2]
file = str(BASE_DIR / "data/matched/PSG_matched.csv")
table = Table.read(file)


targetID = (table['TARGETID'])
ra = np.array(table['RA'])
dec = np.array(table['DEC'])
redshift = (table['Z'])
ebv = (table['EBV'])


# define the wavelength array for fuv, nuv, g, r, i, z, y
lam = [1549, 2303, 4810, 6170, 7520, 8660, 9620] * u.AA

# QSO template setup 
filtdir = str(BASE_DIR / "data/filters/")
templateQSO = str(BASE_DIR / "templates/qso_template.txt")
_spec = ascii.read(str(templateQSO))
templateWave = _spec['col1']
templateFlux = _spec['col2']

filt_files = [
    "GALEX_GALEX.FUV.dat",
    "GALEX_GALEX.NUV.dat",
    "PAN-STARRS_PS1.g.dat",
    "PAN-STARRS_PS1.r.dat",
    "PAN-STARRS_PS1.i.dat",
    "PAN-STARRS_PS1.z.dat",
    "PAN-STARRS_PS1.y.dat",
]
lam_template = lam  

# GALEX (1549, 2303) -> lam indices 0, 1

flam_fuv = (np.array(table['FUVmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam[0]))
flam_fuv[flam_fuv > (1e-11 * su.FLAM)] = np.nan

flam_nuv = (np.array(table['NUVmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam[1]))
flam_nuv[flam_nuv > (1e-11 * su.FLAM)] = np.nan


# PanSTARRS (4810, 6170, 7520, 8660, 9620) -> lam indices 2, 3, 4, 5, 6

flam_g = (np.array(table['gmag'])*u.ABmag).to((su.FLAM), u.spectral_density(lam[2]))
flam_g[flam_g > (1e-11 * su.FLAM)] = np.nan
flam_r = (np.array(table['rmag'])*u.ABmag).to((su.FLAM), u.spectral_density(lam[3]))
flam_r[flam_r > (1e-11 * su.FLAM)] = np.nan
flam_i = (np.array(table['imag'])*u.ABmag).to((su.FLAM), u.spectral_density(lam[4]))
flam_i[flam_i > (1e-11 * su.FLAM)] = np.nan
flam_z = (np.array(table['zmag'])*u.ABmag).to((su.FLAM), u.spectral_density(lam[5]))
flam_z[flam_z > (1e-11 * su.FLAM)] = np.nan
flam_y = (np.array(table['ymag'])*u.ABmag).to((su.FLAM), u.spectral_density(lam[6]))
flam_y[flam_y > (1e-11 * su.FLAM)] = np.nan


print(targetID)
f_fn = flam_fuv / flam_nuv
f_ng = flam_nuv / flam_g
f_gr = flam_g / flam_r

def UVExcess(index):
    if (((f_ng[index] > 1 and f_gr[index] < 1) or (f_fn[index] > 1 and f_ng[index] < 1)) and (ebv[index] > 0.2)):
        return True
    return False


for index, name in enumerate(targetID):
    zsp = redshift[index]


    if UVExcess(index):
        plt.figure()

        plt.plot(lam.value/(1+zsp),
                [flam_fuv.value[index],
                flam_nuv.value[index],
                flam_g.value[index],
                flam_r.value[index],
                flam_i.value[index],
                flam_z.value[index],
                flam_y.value[index]],
                marker='o', label=name)

        # overlay unreddened QSO template ---
        sp = SourceSpectrum(Empirical1D, points=templateWave*u.AA,
                            lookup_table=templateFlux*su.FLAM, z=zsp)
        synth_flx = []
        for filt_file in filt_files:
            bp = SpectralElement.from_file(filtdir + filt_file)
            try:
                obs = Observation(sp, bp, force='extrap')
                synth_flx.append(obs.effstim('flam').value)
            except (synphot.exceptions.DisjointError, synphot.exceptions.SynphotError):
                synth_flx.append(np.nan)
        synth_flx = np.array(synth_flx)

        obs_flam = np.array([
            flam_fuv.value[index], flam_nuv.value[index],
            flam_g.value[index],   flam_r.value[index],  flam_i.value[index],
            flam_z.value[index],   flam_y.value[index],
        ])
        valid = np.isfinite(obs_flam) & np.isfinite(synth_flx) & (synth_flx > 0)
        scale = np.nanmedian(obs_flam[valid] / synth_flx[valid]) if valid.any() else 1.0

        plt.plot(templateWave, scale * templateFlux,
                 color='gray', alpha=0.6, label='QSO template')
        plt.scatter(lam_template.value/(1+zsp), scale * synth_flx,
                    color='orange', marker='s', zorder=5, label='template synth phot')
        # --- end template overlay ---

        plt.xscale('log')
        plt.yscale('log')
        plt.xlim(1000,7000)
        plt.ylim(1e-17,1e-15)
        plt.title(ebv[index])
        plt.legend()
        plt.show()
