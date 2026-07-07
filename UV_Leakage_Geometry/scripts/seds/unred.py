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


filtdir = '/home/agklaros/Documents/UV_Leakage_Geometry-1/UV_Leakage_Geometry/filters/'
templateQSO = '/home/agklaros/Documents/UV_Leakage_Geometry-1/UV_Leakage_Geometry/templates/qso_template.txt'
spec = ascii.read(str(templateQSO))
templateWave = spec['col1']
templateFlux = spec['col2']

# and array of the effective wavelengths
lam = [1549, 2303, 4810, 6170, 7520, 8660, 9620,10305, 12483, 16313, 22010] * u.AA
#,33680, 46180, 120820, 221940

# this is the redshift of the quasar you are comparing to -- change it for each object, e.g. in a loop
zsp = 0.5

# create a spectrum object from the template
sp = SourceSpectrum(Empirical1D, points=templateWave*u.AA, lookup_table=templateFlux*su.FLAM, z=zsp)

#sp.plot() # sanity check -- notice the figure shifts when chaning zsp; comment out if all looks good

wphot = lam.value/(1+zsp)
# replace these with the filter files for your data
filt_files = [
    "GALEX_GALEX.FUV.dat",       # 1549 AA
    "GALEX_GALEX.NUV.dat",       # 2303 AA
    "PAN-STARRS_PS1.g.dat",      # 4810 AA
    "PAN-STARRS_PS1.r.dat",      # 6170 AA
    "PAN-STARRS_PS1.i.dat",      # 7520 AA
    "PAN-STARRS_PS1.z.dat",      # 8660 AA
    "PAN-STARRS_PS1.y.dat",      # 9620 AA
    "UKIRT_UKIDSS.Y.dat",        # 10305 AA
    "UKIRT_UKIDSS.J.dat",        # 12483 AA
    "UKIRT_UKIDSS.H.dat",        # 16313 AA
    "UKIRT_UKIDSS.K.dat",        # 22010 AA
]
    # "WISE_WISE.W1.dat",          # 33680 AA
    # "WISE_WISE.W2.dat",          # 46180 AA
    # "WISE_WISE.W3.dat",          # 120820 AA
    # "WISE_WISE.W4.dat",          # 221940 AA
synth_flx = [] # this will be populated by the spectrophotometry in each filter

###Uncomment this.
## this code does a quick scaling to shift the template to the same y-scale as your data
## Here wphot is the wavelengths for your filters that you have been plotting
## and flam are your fluxes for each quasar
# srat = fit_composite(lam.value, np.array(synth_flx), wphot, np.array(flam))

for filt_file in filt_files:           
    bp = SpectralElement.from_file(filtdir+filt_file) # bp stands for bandpass -- it is the filter transmission curve
    observation = Observation(sp, bp, force='extrap') # this command applies the filter to the data to get a flux for that filter
    synth_flx.append(observation.effstim('flam').value) # this adds that value to the synth_flx table as it loops through the filtrs

    # plot the results -- in the rest frame

    
## once you have a value for 'srat' above, you will edit these commands to multiply
## srat*templateFlux and srat*synth_flx
plt.figure()
plt.plot(templateWave,templateFlux,label='template spectrum') 
plt.scatter(lam.value, synth_flx, color='y') # plot the synthetic photometry        
plt.show()
#plt.ylim(0,2e-16)