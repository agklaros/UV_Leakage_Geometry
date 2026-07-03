

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

file = '/home/agklaros/Documents/UV_Leakage_Geometry-1/UV_Leakage_Geometry/data/matched/uv_excess_candidates.csv'
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

fuvnuv = FUVmags - NUVmags
nuvg = NUVmags - gmags
gr = gmags - rmags



#Only display E(B-V) > 0.2:
#ebv[ebv < 0.2] = np.nan



plt.figure(figsize=(10, 10))
sc = plt.scatter(nuvg, gr, c=redshift, cmap='inferno', s=100)


#Cursor to show each DESI TARGETID
# cursor = mplcursors.cursor(sc, hover=True)
# @cursor.connect("add")
# def on_add(sel):
#     idx = sel.index
#     sel.annotation.set_text(f"RA: {ra[idx]}")

plt.title('Color vs Color for 24 QSOs with UV Excess')
plt.colorbar(label='E(B-V)')
plt.axhline(y=0)
plt.axvline(x=0)
plt.xlabel('G-R <0')
plt.ylabel('NUV-G >0')
plt.show()
    



