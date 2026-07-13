"""S/N math and ETC-file parsing for Lick Kast polarimetry planning.

Methodology (K. Leighly notes, 2026-07, and Chromey "To Measure the Sky"
sec. 9.5.4):
  - The observer runs each target through the Kast web ETC by hand
    (https://etc.ucolick.org/web_s2n/kast) with the settings in
    config/qso_params.yaml observing.etc_settings, a flat template, and the
    target's g-band AB magnitude + 0.752 (the polarization optics pass half
    the flux), then downloads the "csv table for exposure".
  - The downloaded CSV has columns wave,obj,sky,noise,s2n: per-pixel object
    counts, sky counts, read noise, and S/N versus wavelength [Angstroms]
    for the exposure time typed into the form.
  - Spectropolarimetry uses the per-pixel S/N directly; imaging polarimetry
    integrates the counts over a filter profile (synphot) and applies the
    CCD equation  S/N = Nqso / sqrt(Nqso + Nsky + Noise).
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


def required_exptime(target_snr, obj_rate, sky_rate, rn_sq):
    """Exposure time [s] at which the CCD-equation S/N reaches target_snr.

    Solves S^2 (O t + K t + R^2) = (O t)^2 for t — the same quadratic as
    Chromey eq. 9.77 with A = O^2/S^2, B = O + K, C = R^2.
    """
    s2 = target_snr**2
    a = obj_rate**2
    b = -s2 * (obj_rate + sky_rate)
    c = -s2 * rn_sq
    return (-b + np.sqrt(b**2 - 4.0 * a * c)) / (2.0 * a)


def load_filter(filter_path):
    """Load a filter transmission curve via synphot; returns (wave_AA, throughput)."""
    from synphot import SpectralElement

    bp = SpectralElement.from_file(str(filter_path))
    wave = bp.waveset.to_value("Angstrom")
    return wave, bp(bp.waveset).value


def filter_band_rates(etc, filter_wave, filter_thru, exptime_s):
    """Filter-weighted count rates for the imaging-polarimetry CCD equation.

    Weights the ETC per-pixel object/sky counts by the filter throughput
    interpolated onto the ETC wavelength grid. Returns (obj_rate, sky_rate,
    rn_sq) where the rates are counts/s summed over the band and rn_sq is the
    throughput-weighted summed squared read noise, i.e. the variance of the
    weighted sum is obj_rate*t + sky_rate*t + rn_sq.
    """
    thru = np.interp(etc["wave"], filter_wave, filter_thru, left=0.0, right=0.0)
    obj_rate = np.sum(thru * etc["obj"]) / exptime_s
    sky_rate = np.sum(thru**2 * etc["sky"]) / exptime_s
    # Poisson variance of a weighted sum carries w^2; fold the object's extra
    # (thru^2 - thru) variance term into the sky rate so the CCD-equation
    # solver (which assumes var = signal + sky*t + rn^2) stays exact.
    sky_rate += np.sum((thru**2 - thru) * etc["obj"]) / exptime_s
    rn_sq = np.sum((thru * etc["rn"]) ** 2)
    return obj_rate, sky_rate, rn_sq


def spectropol_pixel_rates(etc, window_aa, exptime_s):
    """Median per-pixel count rates within the spectropolarimetry window.

    Returns (obj_rate, sky_rate, rn_sq) for the representative (median-S/N)
    pixel inside window_aa, for use with required_exptime.
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
