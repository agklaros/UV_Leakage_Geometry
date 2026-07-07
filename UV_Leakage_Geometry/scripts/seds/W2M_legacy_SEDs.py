

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

w2m_table_file = '/home/agklaros/Documents/UV_Leakage_Geometry-1/UV_Leakage_Geometry/data/archive/W2M_QSOs.csv'
w2m_table = Table.read(w2m_table_file)

redshift = (w2m_table['zsp'])
src = (w2m_table['src'])
designation = (w2m_table['designation'])
ra = np.array(w2m_table['ra'])
dec = np.array(w2m_table['dec'])

# define the wavelength array for w1mpro,g,w2mpro,r,i,J,H,K,W1,w3mpro,W2,W3,W4,w4mpro
lam = [3542.,4686., 6165., 7481., 8923., 12355., 16458., 21603.,33680.,46180.,120820.,221940.] * u.AA

# convert to flambda #(fr/1E-23)*(1/3.34E4)*(1/lam[1])**2
# flam = 10**(-0.4*( mag + 2.406 + 5*np.log10(lam[0]) ))
# use the units module in astropy -- this doesnt really get used anymore...
flam_u = (np.array(w2m_table['umag'])*u.ABmag).to((su.FLAM), u.spectral_density(lam[0]))
flam_g = (np.array(w2m_table['gmag'])*u.ABmag).to((su.FLAM), u.spectral_density(lam[1]))
flam_r = (np.array(w2m_table['rmag'])*u.ABmag).to((su.FLAM), u.spectral_density(lam[2]))
flam_i = (np.array(w2m_table['imag'])*u.ABmag).to((su.FLAM), u.spectral_density(lam[3]))
flam_z = (np.array(w2m_table['zmag'])*u.ABmag).to((su.FLAM), u.spectral_density(lam[4]))
flam_j = (np.array(w2m_table['j_m_2mass'] + 0.894) * u.ABmag).to((su.FLAM), u.spectral_density(lam[5]))
flam_h = (np.array(w2m_table['h_m_2mass'] + 1.374) * u.ABmag).to((su.FLAM), u.spectral_density(lam[6]))
flam_k = (np.array(w2m_table['k_m_2mass'] + 1.840) * u.ABmag).to((su.FLAM), u.spectral_density(lam[7]))
flam_w1mpro = (np.array(w2m_table['w1mpro']+2.699) * u.ABmag).to((su.FLAM), u.spectral_density(lam[8]))
flam_w2mpro = (np.array(w2m_table['w2mpro']+3.339) * u.ABmag).to((su.FLAM), u.spectral_density(lam[9]))
flam_w3mpro = (np.array(w2m_table['w3mpro']+5.174) * u.ABmag).to((su.FLAM), u.spectral_density(lam[10]))
flam_w4mpro = (np.array(w2m_table['w4mpro']+6.620) * u.ABmag).to((su.FLAM), u.spectral_density(lam[11]))

names = [substring[1:5] + substring[10:15] for substring in designation]
print(names)

for index, name in enumerate(names):
    zsp = redshift[index]
    # set up a plot
    plt.figure()
    # plot the original SED
    plt.plot(lam.value/(1+zsp),
             [flam_u.value[index],flam_g.value[index],flam_r.value[index],flam_i.value[index],flam_z.value[index],flam_j.value[index],flam_h.value[index],flam_k.value[index],flam_w1mpro.value[index],flam_w2mpro.value[index],flam_w3mpro.value[index],flam_w4mpro.value[index]],
             marker='o', label=name+' {}'.format(round(zsp,5)))
#     plt.xlim(3000/(1+zsp),24500/(1+zsp))
#     plt.ylim(0,0.5e-15)
    plt.legend()
    plt.show()