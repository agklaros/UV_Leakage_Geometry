from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import yaml

from synphot import SourceSpectrum, units
from synphot import SpectralElement
from synphot import Observation, SourceSpectrum
from synphot.models import Empirical1D
from synphot import units as su

from astropy.io import ascii
from astropy.table import Table
import astropy.units as u

BASE_DIR = Path(__file__).resolve().parents[2]
KAST_TAB_CSV = BASE_DIR / "data/etc_downloads/etc_downloads_auto/J204626.10+002337.6.csv"

with open(BASE_DIR / "config/qso_params.yaml") as f:
    cfg = yaml.safe_load(f)
FILTER_PATH = BASE_DIR / cfg["observing"]["imaging_filter"]

model = Table.read(KAST_TAB_CSV)
wave = model["wave"]
obj = model["obj"]
sky = model["sky"]
noise = model["noise"]

# ### Feed the model spectrum into Synphot so that it turns them into a "SourceSpectrum"
# You need to tell it which array is the wavelength
# (include units as shown below) and which is the 'flux' axis.
# For the object spectrum the flux is just the light from the quasar,
# but the sky and noise get detected too and affect our signal-to-noise so we need to take them into account.

# We also read in the filter transmission curve. These can be downloaded from the SVO filter profile page,
# or directly from Synphot if you follow the directions in the documentation:
# https://synphot.readthedocs.io/en/latest/index.html#installation-and-setup
# scroll down to the green 'Note' box where there are instructions on how to incorporate filter curves.

# read in the spectrum, assign the wavelength and and flux arrays
sp_obj = SourceSpectrum(Empirical1D, points=wave*u.AA, lookup_table=obj*su.PHOTLAM) # object
sp_sky = SourceSpectrum(Empirical1D, points=wave*u.AA, lookup_table=sky*su.PHOTLAM) # skys
sp_noise = SourceSpectrum(Empirical1D, points=wave*u.AA, lookup_table=noise*su.PHOTLAM) # noise

# read in the BANDPASS element
bp = SpectralElement.from_file(str(FILTER_PATH))
bpw = bp.waveset
bpf = bp(bpw)
plt.plot(bpw,bpf) # this plot is just to check things.





# read in the spectrum, assign the wavelength and and flux arrays
sp_obj = SourceSpectrum(Empirical1D, points=wave*u.AA, lookup_table=obj*su.PHOTLAM) # object
sp_sky = SourceSpectrum(Empirical1D, points=wave*u.AA, lookup_table=sky*su.PHOTLAM) # skys
sp_noise = SourceSpectrum(Empirical1D, points=wave*u.AA, lookup_table=noise*su.PHOTLAM) # noise

# read in the BANDPASS element
bp = SpectralElement.from_file(str(FILTER_PATH))
bpw = bp.waveset
bpf = bp(bpw)
plt.plot(bpw,bpf) # this plot is just to check things.


# Observations can do many things,
# but we want is to know what is the total number
# of counts collected through our filter from our simulated object.
# This is done with the effstim() method applied to the object.

# PHOTLAM is a unit that means "counts"

# zero point flux of sdss system
# zero_point_star_equiv = u.zero_point_flux(3631.1 * u.Jy)

qso_obs = Observation(sp_obj, bp, force='extrap')
n_qso = qso_obs.effstim()
print(n_qso) # counts from the QSO through the filter (N*)

sky_obs = Observation(sp_sky, bp, force='extrap')
n_sky = sky_obs.effstim()
print(n_sky) # counts from the sky through the filter

noise_obs = Observation(sp_noise, bp, force='extrap')
n_noise = noise_obs.effstim()
print(n_noise) # counts from the detector itself

#CCD Equation
# snr = n_qso / np.sqrt(n_qso + n_sky + n_noise)
# print(snr)


n_qso_rate = n_qso / 900
n_sky_rate = n_sky / 900


snr_target = float(cfg["observing"]["target_snr"])

A = n_qso_rate.value ** 2
B = (-1) * (snr_target ** 2) * (n_qso_rate.value + n_sky_rate.value)
C = (-1) * (snr_target ** 2) * n_noise.value

roots = np.roots([A, B, C])
real_positive_roots = roots[np.isreal(roots) & (roots.real > 0)].real
if real_positive_roots.size == 0:
    raise ValueError("no real positive root for the required exposure time")
et_output = real_positive_roots[0]

print("To acheive a SNR of " + str(snr_target) + " requires " + str(et_output) + " seconds, or " + str(et_output / 60) + " minutes.")
