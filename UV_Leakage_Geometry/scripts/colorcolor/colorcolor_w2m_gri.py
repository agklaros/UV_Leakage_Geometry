

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

#for cursors
import mplcursors

import synphot
from synphot import SourceSpectrum
from synphot import units as su
from synphot import SpectralElement
from synphot.observation import Observation

from scipy.interpolate import interp1d
from scipy.optimize import curve_fit

#from quasar_unred import load_template, extinguish, fit_composite, find_ebv, mc_spec

BASE_DIR = Path(__file__).resolve().parents[2]
file = str(BASE_DIR / "data/matched/FINAL_COMBINED_QSOs_W2M.csv")
table = Table.read(file)


targetID = (table['TARGETID'])
ra = np.array(table['RA'])
dec = np.array(table['DEC'])
redshift = (table['Z'])
ebv = (table['EBV'])


# define the wavelength array

lam = [1549, 2303, 4810, 6170, 7520, 8660, 9620] * u.AA

# convert to flambda #(fr/1E-23)*(1/3.34E4)*(1/lam[1])**2
# flam = 10**(-0.4*( mag + 2.406 + 5*np.log10(lam[0]) ))
# use the units module in astropy -- this doesnt really get used anymore...

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


FUVmags = np.array(table['FUVmag'])
NUVmags = np.array(table['NUVmag'])
gmags = np.array(table['gmag'])
rmags = np.array(table['rmag'])
imags = np.array(table['imag'])
zmags = np.array(table['zmag'])

fuvnuv = flam_fuv / flam_nuv
nuvg = flam_nuv / flam_g
gr = flam_g / flam_r
ri = flam_r / flam_i

# mask out rows where any of the underlying mags used in these colors is 0
# (0 indicates a missing/bad measurement, not a real magnitude)
zero_mask = (
    (FUVmags == 0) | (NUVmags == 0) | (gmags == 0) | (rmags == 0) | (imags == 0)
)
fuvnuv[zero_mask] = np.nan
nuvg[zero_mask] = np.nan
gr[zero_mask] = np.nan
ri[zero_mask] = np.nan


#Only display E(B-V) > 0.2:
#ebv[ebv < 0.2] = np.nan


fig, ax_blue = plt.subplots(figsize=(10, 10))
ax_red = ax_blue.twiny().twinx()

sc_blue = ax_blue.scatter(nuvg, fuvnuv, c='blue', s=100, zorder=2, alpha=0.5, label='FUV/NUV vs NUV/G')
sc_red = ax_red.scatter(gr, nuvg, c='red', s=100, zorder=2, alpha=0.5, label='NUV/G vs G/R')

ax_blue.set_xlabel('NUV/G (blue)', color='blue')
ax_blue.set_ylabel('FUV/NUV (blue)', color='blue')
ax_blue.tick_params(axis='x', colors='blue')
ax_blue.tick_params(axis='y', colors='blue')

ax_red.xaxis.set_label_position('top')
ax_red.xaxis.tick_top()
ax_red.set_xlabel('G/R (red)', color='red')
ax_red.set_ylabel('NUV/G (red)', color='red')
ax_red.tick_params(axis='x', colors='red')
ax_red.tick_params(axis='y', colors='red')


ax_blue.axhline(y=1)
ax_blue.axvline(x=1)

handles = [sc_blue, sc_red]
labels = [h.get_label() for h in handles]
ax_blue.legend(handles, labels, loc='best')

plt.show()
