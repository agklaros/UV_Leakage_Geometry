

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
from synphot.observation import Observation

from scipy.interpolate import interp1d
from scipy.optimize import curve_fit

#from quasar_unred import load_template, extinguish, fit_composite, find_ebv, mc_spec

file = '/home/agklaros/Documents/UV_Leakage_Geometry/data/matched/UKPSAWG_matched.csv'
table = Table.read(file)


targetID = (table['TARGETID'])
ra = np.array(table['RA'])
dec = np.array(table['DEC'])
redshift = (table['Z'])
ebv = (table['EBV'])


# define the wavelength array for g, r, i, z, y, w1, w2, w3, w4
lam = [1549, 2303, 4810, 6170, 7520, 8660, 9620,10305, 12483, 16313, 22010,33680, 46180, 120820, 221940] * u.AA

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

#UKIDSS (10305, 12483, 16313, 22010)

flam_Y = (np.array(table['yAperMag3']+0.634)*u.ABmag).to((su.FLAM), u.spectral_density(lam[7]))
flam_Y[flam_Y > (1e-10 * su.FLAM)] = np.nan
flam_J = (np.array(table['j_1AperMag3']+0.938)*u.ABmag).to((su.FLAM), u.spectral_density(lam[8]))
flam_J[flam_J > (1e-10 * su.FLAM)] = np.nan
flam_H = (np.array(table['hAperMag3']+1.379)*u.ABmag).to((su.FLAM), u.spectral_density(lam[9]))
flam_H[flam_H > (1e-10 * su.FLAM)] = np.nan
flam_K = (np.array(table['kAperMag3']+1.900)*u.ABmag).to((su.FLAM), u.spectral_density(lam[10]))
flam_K[flam_K > (1e-10 * su.FLAM)] = np.nan


# WISE (33680, 46180, 120820, 221940)
flam_w1 = (np.array(table['W1mag']+2.699) * u.ABmag).to((su.FLAM), u.spectral_density(lam[11]))
flam_w2 = (np.array(table['W2mag']+3.339) * u.ABmag).to((su.FLAM), u.spectral_density(lam[12]))
flam_w3 = (np.array(table['W3mag']+5.174) * u.ABmag).to((su.FLAM), u.spectral_density(lam[13]))
flam_w4 = (np.array(table['W4mag']+6.620) * u.ABmag).to((su.FLAM), u.spectral_density(lam[14]))



print(targetID)
plt.figure(figsize=(10, 6))

for index, name in enumerate(targetID):
    zsp = redshift[index]
    
    


    plt.plot(lam.value/(1+zsp), [flam_fuv.value[index], flam_nuv.value[index],
        flam_g.value[index], flam_r.value[index], flam_i.value[index], flam_z.value[index], flam_y.value[index],flam_Y.value[index],flam_J.value[index],flam_H.value[index],flam_K.value[index],
        flam_w1.value[index], flam_w2.value[index], flam_w3.value[index], flam_w4.value[index]],
             marker='o', linestyle='-', alpha=0.7,
             label=f"{name} (z={round(zsp, 3)})")


plt.xscale('log')
plt.yscale('log')
plt.show()

# flam_Y.value[index],flam_J.value[index],flam_H.value[index],flam_K.value[index],
# table['yAperMag3'][index], table['j_1AperMag3'][index], table['hAperMag3'][index], table['kAperMag3'][index],