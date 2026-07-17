"""Spectropolarimetry exposure-time math for Lick Kast planning, standalone.

Unlike single_kast_etc_imaging.py (one S/N number from a synphot-integrated
filter bandpass), spectropolarimetry has no filter to integrate over — the
science product is the spectrum itself, so every wavelength bin ("pixel") in
the ETC download needs its own adequate S/N. This script solves the CCD
equation per pixel and picks the exposure time at which:
  - the median pixel (blue-side only, 3150-5400 A) reaches S/N >= target_snr
  - 90% of pixels (same range) reach S/N >= snr_floor
taking whichever of the two requirements demands more time.
"""

from pathlib import Path

import numpy as np
import yaml

from astropy.table import Table


BASE_DIR = Path(__file__).resolve().parents[2]


def load_config():
    with open(BASE_DIR / "config/qso_params.yaml") as f:
        return yaml.safe_load(f)


def read_etc_table(path):
    """Read a manually downloaded Kast ETC 'csv table for exposure'."""
    model = Table.read(path)
    return model["wave"], model["obj"], model["sky"], model["noise"]


def _positive_root(A, B, C):
    """Positive root of A*t^2 + B*t + C = 0, elementwise; inf where A == 0."""
    disc = B ** 2 - 4 * A * C
    sqrt_disc = np.sqrt(np.maximum(disc, 0.0))
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(A > 0, (-B + sqrt_disc) / (2 * A), np.inf)


def _load_pixel_rates(etc_path, etc_exptime_s, wave_min, wave_max):
    """Per-pixel obj/sky rates and noise, masked to [wave_min, wave_max]."""
    wave, obj, sky, noise = read_etc_table(etc_path)
    wave = np.asarray(wave.value, dtype=float)
    obj = np.asarray(obj.value, dtype=float)
    sky = np.asarray(sky.value, dtype=float)
    noise = np.asarray(noise.value, dtype=float)

    mask = (wave >= wave_min) & (wave <= wave_max)
    obj_rate = obj[mask] / etc_exptime_s
    sky_rate = sky[mask] / etc_exptime_s
    noise_pix = noise[mask]
    return obj_rate, sky_rate, noise_pix


def _t_required(obj_rate, sky_rate, noise_pix, snr_target):
    """Per-pixel exposure time [s] at which that pixel's own S/N reaches snr_target."""
    A = obj_rate ** 2
    B = -(snr_target ** 2) * (obj_rate + sky_rate)
    C = -(snr_target ** 2) * noise_pix
    return _positive_root(A, B, C)


def _snr_at(obj_rate, sky_rate, noise_pix, t):
    return obj_rate * t / np.sqrt(obj_rate * t + sky_rate * t + noise_pix)


def required_exptime(etc_path, etc_exptime_s, snr_good, frac_good,
                      snr_floor, frac_floor, wave_min, wave_max):
    """Exposure time [s] satisfying both per-pixel S/N requirements.

    frac_good of pixels (in [wave_min, wave_max]) must reach S/N >= snr_good,
    and frac_floor of pixels must reach S/N >= snr_floor; the returned time
    is whichever requirement needs more exposure. Also returns the actual
    fraction of pixels clearing each threshold at that exposure time.
    """
    obj_rate, sky_rate, noise_pix = _load_pixel_rates(etc_path, etc_exptime_s, wave_min, wave_max)

    t_good = np.percentile(_t_required(obj_rate, sky_rate, noise_pix, snr_good), frac_good * 100)
    t_floor = np.percentile(_t_required(obj_rate, sky_rate, noise_pix, snr_floor), frac_floor * 100)
    t_final = max(t_good, t_floor)

    snr_at_t = _snr_at(obj_rate, sky_rate, noise_pix, t_final)
    frac_ge_good = np.mean(snr_at_t >= snr_good)
    frac_ge_floor = np.mean(snr_at_t >= snr_floor)

    return t_final, frac_ge_good, frac_ge_floor


def required_exptime_floor_only(etc_path, etc_exptime_s, snr_floor, frac_floor, wave_min, wave_max):
    """Exposure time [s] at which frac_floor of pixels (in [wave_min, wave_max])
    reach S/N >= snr_floor — a single criterion, with no S/N-good requirement.
    Also returns the actual fraction of pixels clearing the threshold.
    """
    obj_rate, sky_rate, noise_pix = _load_pixel_rates(etc_path, etc_exptime_s, wave_min, wave_max)

    t_final = np.percentile(_t_required(obj_rate, sky_rate, noise_pix, snr_floor), frac_floor * 100)

    snr_at_t = _snr_at(obj_rate, sky_rate, noise_pix, t_final)
    frac_ge_floor = np.mean(snr_at_t >= snr_floor)

    return t_final, frac_ge_floor


if __name__ == "__main__":
    cfg = load_config()
    obs = cfg["observing"]
    etc_path = BASE_DIR / obs["etc_downloads_dir"] / "J204626.10+002337.6.csv"
    snr_good = float(obs["target_snr"])
    snr_floor = float(obs["snr_floor"])

    et_output, frac_good, frac_floor = required_exptime(
        etc_path, float(obs["etc_exptime_s"]),
        snr_good=snr_good, frac_good=0.50,
        snr_floor=snr_floor, frac_floor=0.90,
        wave_min=3150.0, wave_max=5400.0,
    )
    print("To achieve a median S/N of " + str(snr_good) + " requires "
          + str(np.round(et_output)) + " seconds, or " + str(et_output / 60) + " minutes.")
    print("At that exposure time: " + str(np.round(frac_good * 100, 1)) + "% of pixels >= S/N "
          + str(snr_good) + ", " + str(np.round(frac_floor * 100, 1)) + "% of pixels >= S/N " + str(snr_floor))

    et_output_95, frac_95 = required_exptime_floor_only(
        etc_path, float(obs["etc_exptime_s"]),
        snr_floor=snr_floor, frac_floor=0.95,
        wave_min=3150.0, wave_max=5400.0,
    )
    print("To get 95% of pixels >= S/N " + str(snr_floor) + " (no S/N " + str(snr_good)
          + " requirement) requires " + str(np.round(et_output_95)) + " seconds, or "
          + str(et_output_95 / 60) + " minutes.")
    print("At that exposure time: " + str(np.round(frac_95 * 100, 1)) + "% of pixels >= S/N " + str(snr_floor))
