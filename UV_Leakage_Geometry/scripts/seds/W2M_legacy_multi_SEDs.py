

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

BASE_DIR = Path(__file__).resolve().parents[2]
file = str(BASE_DIR / "data/archive/W2M_multi_2arc.csv")
table = Table.read(file)


targetID = (table['designation'])
ra = np.array(table['ra'])
dec = np.array(table['dec'])
redshift = (table['zsp'])



# define the wavelength array for FUV, NUV, g, r, i, z, y, Y, J, H, K, w1, w2, w3, w4
lam = [1549, 2303, 4810, 6170, 7520, 8660, 9620 ,10305, 12483, 16313, 22010,33680, 46180, 120820, 221940] * u.AA

# convert to flambda #(fr/1E-23)*(1/3.34E4)*(1/lam[1])**2
# flam = 10**(-0.4*( mag + 2.406 + 5*np.log10(lam[0]) ))
# use the units module in astropy -- this doesnt really get used anymore...






# GALEX (1549, 2303)
flam_fuv = (np.array(table['FUVmag']) * u.ABmag).to((su.FLAM), u.spectral_density(lam[0]))
flam_nuv = (np.array(table['NUVmag']) * u.ABmag).to((su.FLAM), u.spectral_density(lam[1]))

# PanSTARRS (4810, 6170, 7520, 8660, 9620)
flam_g = (np.array(table['gmag'])*u.ABmag).to((su.FLAM), u.spectral_density(lam[2]))
flam_r = (np.array(table['rmag'])*u.ABmag).to((su.FLAM), u.spectral_density(lam[3]))
flam_i = (np.array(table['imag'])*u.ABmag).to((su.FLAM), u.spectral_density(lam[4]))
flam_z = (np.array(table['zmag'])*u.ABmag).to((su.FLAM), u.spectral_density(lam[5]))
flam_y = (np.array(table['ymag'])*u.ABmag).to((su.FLAM), u.spectral_density(lam[6]))

#UKIDSS (10305, 12483, 16313, 22010)

flam_Y = (np.array(table['yAperMag3']+0.634)*u.ABmag).to((su.FLAM), u.spectral_density(lam[7]))
flam_J = (np.array(table['j_1AperMag3']+0.938)*u.ABmag).to((su.FLAM), u.spectral_density(lam[8]))
flam_H = (np.array(table['hAperMag3']+1.379)*u.ABmag).to((su.FLAM), u.spectral_density(lam[9]))
flam_K = (np.array(table['kAperMag3']+1.900)*u.ABmag).to((su.FLAM), u.spectral_density(lam[10]))


# WISE (33680, 46180, 120820, 221940)
flam_w1 = (np.array(table['w1mpro']+2.699) * u.ABmag).to((su.FLAM), u.spectral_density(lam[11]))
flam_w2 = (np.array(table['w2mpro']+3.339) * u.ABmag).to((su.FLAM), u.spectral_density(lam[12]))
flam_w3 = (np.array(table['w3mpro']+5.174) * u.ABmag).to((su.FLAM), u.spectral_density(lam[13]))
flam_w4 = (np.array(table['w4mpro']+6.620) * u.ABmag).to((su.FLAM), u.spectral_density(lam[14]))


names = [substring[1:5] + substring[10:15] for substring in str(targetID)]
print(names)

# ... [Keep your setup and unit conversions exactly as they are] ...

for index, name in enumerate(names):
    zsp = redshift[index]

    # 1. Gather all the flux values for this specific row/quasar
    fluxes = np.array([
        flam_fuv.value[index],
        flam_nuv.value[index],
        flam_g.value[index],
        flam_r.value[index],
        flam_i.value[index],
        flam_z.value[index],
        flam_y.value[index],
        flam_Y.value[index],
        flam_J.value[index],
        flam_H.value[index],
        flam_K.value[index],
        flam_w1.value[index],
        flam_w2.value[index],
        flam_w3.value[index],
        flam_w4.value[index]
    ])

    rlam = lam.value / (1 + zsp)

    # 3. Create a mask to filter out unphysical/placeholder fluxes
    # (e.g., extremely close to 0, negative values, or NaN artifacts from '99' magnitudes)
    # Since higher magnitude = lower flux, a mag of 99 results in an incredibly tiny flux (~0).
    # If your catalog uses -99, it results in an astronomical unphysical flux.

    # Pull the raw magnitude values for this row to check for standard catalog flags
    raw_mags = np.array([
        table['FUVmag'][index], table['NUVmag'][index],
        table['gmag'][index], table['rmag'][index], table['imag'][index], table['zmag'][index], table['ymag'][index],
        table['yAperMag3'][index], table['j_1AperMag3'][index], table['hAperMag3'][index], table['kAperMag3'][index],
        table['w1mpro'][index], table['w2mpro'][index], table['w3mpro'][index], table['w4mpro'][index]
    ])

    # Keep data only if the magnitude isn't a flag (e.g., between 0 and 50)
    # and the flux is a valid positive number
    mask = (raw_mags > 0) & (raw_mags < 45) & (fluxes > 0)


    plt.figure()

    # Plot only the valid, detected points
    plt.plot(rlam[mask], fluxes[mask],
             marker='o', linestyle='-', label=name+' z={}'.format(round(zsp,5)))

    plt.xscale('log')
    plt.yscale('log')
    plt.legend(targetID)
    plt.show()