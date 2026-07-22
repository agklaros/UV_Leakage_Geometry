"""Imaging-polarimetry exposure-time math for Lick Kast planning, standalone.

Reproduces E. Glikman's synphot notebook (Downloads/Exposure Time Calc/
exposure_calc.ipynb), the ground-truth source for this math. Config is
loaded directly from config/qso_params.yaml — no other module dependency.
Pipeline: make_etc_inputs.py -> fetch_etc_downloads.py ->
single_kast_etc_imaging.py -> make_obs_plan_pdf.py.

Per-target ETC counts (obj/sky/noise vs. wavelength, from a manually
downloaded Kast ETC "csv table for exposure") are integrated over a filter
bandpass via synphot's Observation.effstim() (a throughput-weighted mean),
then combined with the CCD equation S/N = Nqso / sqrt(Nqso + Nsky + Noise).
Counts scale linearly with exposure time while noise does not, so the
exposure time reaching a target S/N is the exact quadratic solution
(Chromey, "To Measure the Sky", eq. 9.77).
"""

from pathlib import Path

import numpy as np
import yaml

import astropy.units as u
from astropy.table import Table
from synphot import Observation, SourceSpectrum, SpectralElement
from synphot import units as su
from synphot.models import Empirical1D

BASE_DIR = Path(__file__).resolve().parents[2]


def load_config():
    with open(BASE_DIR / "config/qso_params.yaml") as f:
        return yaml.safe_load(f)


def read_etc_table(path):
    """Read a manually downloaded Kast ETC 'csv table for exposure'."""
    model = Table.read(path)
    return model["wave"], model["obj"], model["sky"], model["noise"]


def required_exptime(etc_path, filter_path, etc_exptime_s, snr_target):
    """Exposure time [s] at which imaging-polarimetry S/N reaches snr_target.

    etc_exptime_s is the exposure time that was typed into the ETC form when
    etc_path was downloaded (counts there scale linearly with exposure time).
    """
    wave, obj, sky, noise = read_etc_table(etc_path)

    sp_obj = SourceSpectrum(Empirical1D, points=wave * u.AA, lookup_table=obj * su.PHOTLAM)
    sp_sky = SourceSpectrum(Empirical1D, points=wave * u.AA, lookup_table=sky * su.PHOTLAM)
    sp_noise = SourceSpectrum(Empirical1D, points=wave * u.AA, lookup_table=noise * su.PHOTLAM)

    bp = SpectralElement.from_file(str(filter_path))

    n_qso = Observation(sp_obj, bp, force="extrap").effstim()  # counts from the QSO through the filter
    n_sky = Observation(sp_sky, bp, force="extrap").effstim()  # counts from the sky through the filter
    n_noise = Observation(sp_noise, bp, force="extrap").effstim()  # counts from the detector itself

    print(n_qso)
    print(n_sky)
    print(n_noise)
    n_qso_rate = n_qso / etc_exptime_s
    n_sky_rate = n_sky / etc_exptime_s

    # CCD equation S/N = Nqso / sqrt(Nqso + Nsky + Noise), solved for t.
    A = n_qso_rate.value ** 2
    B = -(snr_target ** 2) * (n_qso_rate.value + n_sky_rate.value)
    C = -(snr_target ** 2) * n_noise.value

    print(A)
    print(B)
    print(C)
    roots = np.roots([A, B, C])
    print(roots)
    real_positive_roots = roots[np.isreal(roots) & (roots.real > 0)].real
    if real_positive_roots.size == 0:
        raise ValueError(f"{etc_path}: no real positive root for the required exposure time")
    return real_positive_roots[0]


if __name__ == "__main__":
    cfg = load_config()
    obs = cfg["observing"]
    etc_path = BASE_DIR / obs["etc_downloads_dir"] / "J204626.10+002337.6.csv"
    filter_path = BASE_DIR / obs["imaging_filter"]
    snr_target = float(obs["target_snr"])

    et_output = required_exptime(etc_path, filter_path, float(obs["etc_exptime_s"]), snr_target)
    print("To acheive a SNR of " + str(snr_target) + " requires " + str(np.round(et_output, out=None))
          + " seconds, or " + str(et_output / 60) + " minutes.")
