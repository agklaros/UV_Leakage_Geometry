import warnings
warnings.filterwarnings("ignore")

import numpy as np
from astropy.table import Table, vstack
import astropy.units as u
from synphot import units as su

FAWCETT_CSV = "/home/agklaros/Documents/UV_Leakage_Geometry-1/UV_Leakage_Geometry/data/matched/Fawcett_COMBINED_matched.csv"
W2M_CSV     = "/home/agklaros/Documents/UV_Leakage_Geometry-1/UV_Leakage_Geometry/data/matched/W2M_COMBINED_matched.csv"
out_file    = "/home/agklaros/Documents/UV_Leakage_Geometry-1/UV_Leakage_Geometry/data/matched/uv_excess_candidates.csv"

lam_fuv = 1549 * u.AA
lam_nuv = 2303 * u.AA
lam_g   = 4810 * u.AA
lam_r   = 6170 * u.AA


def mag_arr(col):
    if hasattr(col, 'filled'):
        return np.array(col.filled(np.nan), dtype=float)
    arr = np.array(col, dtype=str)
    arr[arr == '--'] = 'nan'
    return arr.astype(float)


def uv_excess_mask(tbl, gmag_col, rmag_col, require_ebv=True):
    flam_fuv = (mag_arr(tbl['FUVmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_fuv))
    flam_fuv[flam_fuv > (1e-11 * su.FLAM)] = np.nan
    flam_nuv = (mag_arr(tbl['NUVmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_nuv))
    flam_nuv[flam_nuv > (1e-11 * su.FLAM)] = np.nan
    flam_g = (mag_arr(tbl[gmag_col]) * u.ABmag).to(su.FLAM, u.spectral_density(lam_g))
    flam_g[flam_g > (1e-11 * su.FLAM)] = np.nan
    flam_r = (mag_arr(tbl[rmag_col]) * u.ABmag).to(su.FLAM, u.spectral_density(lam_r))
    flam_r[flam_r > (1e-11 * su.FLAM)] = np.nan

    f_fn = flam_fuv / flam_nuv
    f_ng = flam_nuv / flam_g
    f_gr = flam_g   / flam_r

    # NUV/g > 1 & g/r < 1: NUV excess over optical continuum (NUV upturn)
    # FUV/NUV > 1 & NUV/g < 1: FUV upturn with suppressed NUV (patchy geometry signature)
    flux_criterion = (
        ((f_ng > 1) & (f_gr < 1)) |
        ((f_fn > 1) & (f_ng < 1))
    )

    if require_ebv:
        ebv = mag_arr(tbl['EBV'])
        return flux_criterion & (ebv > 0.2)
    return flux_criterion



fawcett = Table.read(FAWCETT_CSV, format='csv')
fawcett_mask = uv_excess_mask(fawcett, gmag_col='gmag', rmag_col='rmag', require_ebv=True)
fawcett_cands = fawcett[fawcett_mask]



w2m = Table.read(W2M_CSV, format='csv')
w2m_mask = uv_excess_mask(w2m, gmag_col='gmag_2', rmag_col='rmag_2', require_ebv=False)  # W2M catalog lacks Fawcett EBV estimates
w2m_cands = w2m[w2m_mask]



candidates = vstack([fawcett_cands, w2m_cands], join_type='outer')
candidates.write(out_file, format='csv', overwrite=True)

