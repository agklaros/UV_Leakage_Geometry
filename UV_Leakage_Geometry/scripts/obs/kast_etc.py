"""S/N math and ETC-file parsing for Lick Kast polarimetry planning.

Methodology (K. Leighly notes + E. Glikman's synphot notebook, both in
Downloads/Exposure Time Calc/, 2026-07, and Chromey "To Measure the Sky"
sec. 9.5.4):
  - The observer runs each target through the Kast web ETC by hand
    (https://etc.ucolick.org/web_s2n/kast) with the settings in
    config/qso_params.yaml observing.etc_settings, a flat template, and the
    target's g-band AB magnitude + 0.752 (the polarization optics pass half
    the flux), then downloads the "csv table for exposure".
  - The downloaded CSV has columns wave,obj,sky,noise,s2n: per-pixel object
    counts, sky counts, read noise, and S/N versus wavelength [Angstroms]
    for the exposure time typed into the form.
  - Spectropolarimetry uses the per-pixel values directly at the ETC's own
    convention, S/N = Nqso / sqrt(Nqso + Nsky + Noise^2) (verified against
    the ETC's own reported s2n column to ~2%).
  - Imaging polarimetry instead runs obj/sky/noise through the filter
    bandpass the way synphot's Observation.effstim() does for a PHOTLAM
    source: a throughput-weighted *mean*, not a sum. The reference notebook
    then applies the plain CCD equation S/N = Nqso / sqrt(Nqso+Nsky+Noise)
    with the noise term unsquared, taken as-is from the reference code even
    though it differs from the per-pixel convention above.
  - Counts scale linearly with exposure time while read noise does not, so
    one ETC run per target suffices; the time to reach a target S/N is the
    exact quadratic solution (equivalent to Chromey eq. 9.77).
  - To be sensitive to polarization fraction P, multiply the resulting
    "normal" exposure time by 1/P (1% -> x100).
"""

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = BASE_DIR / "config/qso_params.yaml"

ETC_COLUMNS = ["wave", "obj", "sky", "noise", "s2n"]


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def read_etc_csv(path):
    """Read one manually downloaded Kast ETC table (tab_s2n CSV).

    Returns dict of numpy arrays: wave [AA], obj and sky [counts/pixel over
    the exposure time typed into the ETC], rn [read-noise electrons/pixel],
    s2n [per pixel].
    """
    df = pd.read_csv(path)
    missing = [c for c in ETC_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"{path}: missing columns {missing} — expected the ETC's "
            f"'Return csv table for exposure' download with header "
            f"{','.join(ETC_COLUMNS)}"
        )
    return {
        "wave": df["wave"].to_numpy(float),
        "obj": df["obj"].to_numpy(float),
        "sky": df["sky"].to_numpy(float),
        "rn": df["noise"].to_numpy(float),
        "s2n": df["s2n"].to_numpy(float),
    }


def snr_at_time(obj_rate, sky_rate, rn, t):
    """CCD equation S/N for count rates [counts/s] after exposure t [s]."""
    signal = obj_rate * t
    return signal / np.sqrt(signal + sky_rate * t + rn**2)


def required_exptime(target_snr, obj_rate, sky_rate, noise_const):
    """Exposure time [s] at which the CCD-equation S/N reaches target_snr.

    Solves S^2 (O t + K t + C) = (O t)^2 for t — the same quadratic as
    Chromey eq. 9.77 with A = O^2/S^2, B = O + K, C = noise_const. C is
    R^2 for the per-pixel spectropol convention, or the unsquared
    filter-weighted noise mean for the imaging convention — see module
    docstring.
    """
    s2 = target_snr**2
    a = obj_rate**2
    b = -s2 * (obj_rate + sky_rate)
    c = -s2 * noise_const
    return (-b + np.sqrt(b**2 - 4.0 * a * c)) / (2.0 * a)


def load_filter(filter_path):
    """Load a filter transmission curve via synphot; returns (wave_AA, throughput)."""
    from synphot import SpectralElement

    bp = SpectralElement.from_file(str(filter_path))
    wave = bp.waveset.to_value("Angstrom")
    return wave, bp(bp.waveset).value


def filter_band_rates(etc, filter_wave, filter_thru, exptime_s):
    """Filter-weighted rates for the imaging-polarimetry CCD equation.

    Reproduces the reference notebook (Downloads/Exposure Time Calc/
    exposure_calc.ipynb): the ETC's per-pixel obj/sky/noise columns are each
    passed through the filter bandpass as a synphot Observation.effstim()
    would for a PHOTLAM source — a throughput-weighted *mean* over the ETC
    wavelength grid, not a sum. Verified against the notebook's own logged
    effstim/S/N output (obj=251.0, sky=258.8, noise=12.56 -> S/N=10.98 for
    its example target) to within the expected difference from using a
    different filter curve.

    Returns (obj_rate, sky_rate, noise_const) for use with required_exptime,
    where noise_const is the unsquared throughput-weighted noise mean (see
    module docstring — this aggregate convention differs from the per-pixel
    one in spectropol_pixel_rates, but is taken as-is from the reference).
    """
    thru = np.interp(etc["wave"], filter_wave, filter_thru, left=0.0, right=0.0)
    weight = np.sum(thru)
    obj_rate = np.sum(thru * etc["obj"]) / weight / exptime_s
    sky_rate = np.sum(thru * etc["sky"]) / weight / exptime_s
    noise_const = np.sum(thru * etc["rn"]) / weight
    return obj_rate, sky_rate, noise_const


def spectropol_pixel_rates(etc, window_aa, exptime_s):
    """Median per-pixel count rates within the spectropolarimetry window.

    Returns (obj_rate, sky_rate, noise_const) for the representative
    (median-S/N) pixel inside window_aa, for use with required_exptime.
    noise_const here is R^2 (squared read noise), matching the ETC's own
    per-pixel convention — see module docstring.
    """
    lo, hi = window_aa
    sel = (etc["wave"] >= lo) & (etc["wave"] <= hi)
    if not sel.any():
        raise ValueError(f"no ETC pixels in window {window_aa}")
    idx = np.argsort(etc["s2n"][sel])[sel.sum() // 2]
    obj = etc["obj"][sel][idx]
    sky = etc["sky"][sel][idx]
    rn = etc["rn"][sel][idx]
    return obj / exptime_s, sky / exptime_s, rn**2


def target_name(row):
    """Stable per-target identifier: designation if present, else TARGETID."""
    if pd.notna(row.get("designation")):
        return str(row["designation"])
    return f"TARGETID_{row['TARGETID']}"
