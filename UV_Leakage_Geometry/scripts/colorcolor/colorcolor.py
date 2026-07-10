

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
designation = np.array(table['designation'], dtype=str)
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


# DESI rows populate gmag/rmag; W2M rows populate gmag_2/rmag_2 instead
# (see build_control_sample_w2m.py's coalesce() for the same pattern)
gmags = np.where(np.isnan(table['gmag']), table['gmag_2'], table['gmag'])
rmags = np.where(np.isnan(table['rmag']), table['rmag_2'], table['rmag'])
flam_g = (gmags*u.ABmag).to(su.FLAM, u.spectral_density(lam[2]))
flam_g[flam_g > (1e-11 * su.FLAM)] = np.nan
flam_r = (rmags*u.ABmag).to(su.FLAM, u.spectral_density(lam[3]))
flam_r[flam_r > (1e-11 * su.FLAM)] = np.nan

# Plot the same flux ratios used for UV-excess selection (see
# uv_excess_mask() in candidates_to_csv_w2m.py): NUV/g > 1 & g/r < 1, OR
# FUV/NUV > 1 & NUV/g < 1.
f_fn = (flam_fuv / flam_nuv).value
f_ng = (flam_nuv / flam_g).value
f_gr = (flam_g / flam_r).value



#Only display E(B-V) > 0.2:
#ebv[ebv < 0.2] = np.nan


# Flag which QSOs are in the UV-excess candidate sample.
# TARGETID == 0 is a placeholder for W2M-only rows with no DESI ID, so those
# candidates must be matched via designation instead (see build_control_sample_w2m.py).
candidates = Table.read(candidates_file := str(BASE_DIR / "data/matched/uv_excess_candidates_w2m.csv"))
candidate_ids = np.array(candidates['TARGETID'])
candidate_designations = np.array(candidates['designation'], dtype=str)

matched_by_id = np.isin(targetID, candidate_ids[candidate_ids != 0]) & (np.array(targetID) != 0)
matched_by_designation = np.isin(designation, candidate_designations[candidate_ids == 0]) & (designation != '0')
is_candidate = matched_by_id | matched_by_designation
colors = np.where(is_candidate, 'blue', 'red')


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))

sc1 = ax1.scatter(f_gr, f_ng, c=colors, s=100)
ax1.axhline(y=1)
ax1.axvline(x=1)
ax1.set_xlabel('g/r flux ratio (<1)')
ax1.set_ylabel('NUV/g flux ratio (>1)')
ax1.set_title('Color vs Color for Final Combined Sample (5490 QSOs)')

sc2 = ax2.scatter(f_ng, f_fn, c=colors, s=100)
ax2.axhline(y=1)
ax2.axvline(x=1)
ax2.set_xlabel('NUV/g flux ratio (<1)')
ax2.set_ylabel('FUV/NUV flux ratio (>1)')
ax2.set_title('FUV Upturn Branch')

#Cursor to show each DESI TARGETID
# cursor = mplcursors.cursor(sc1, hover=True)
# @cursor.connect("add")
# def on_add(sel):
#     idx = sel.index
#     sel.annotation.set_text(f"RA: {ra[idx]}")

plt.show()
    



