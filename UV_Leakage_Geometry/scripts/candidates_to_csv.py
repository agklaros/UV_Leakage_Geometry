import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from astropy.table import Table
import astropy.units as u
from synphot import units as su

BASE_DIR = "/home/agklaros/Documents/UV_Leakage_Geometry-1/UV_Leakage_Geometry"
file     = f"{BASE_DIR}/data/matched/COMBINED_matched.csv"
out_file = f"{BASE_DIR}/data/matched/uv_excess_candidates.csv"

table = Table.read(file)


def mag_arr(col):
    if hasattr(col, 'filled'):
        return np.array(col.filled(np.nan), dtype=float)
    arr = np.array(col, dtype=str)
    arr[arr == '--'] = 'nan'
    return arr.astype(float)


targetID = np.array(table['TARGETID'])
ebv      = mag_arr(table['EBV'])

lam_fuv = 1549 * u.AA
lam_nuv = 2303 * u.AA
lam_g   = 4810 * u.AA
lam_r   = 6170 * u.AA

flam_fuv = (mag_arr(table['FUVmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_fuv))
flam_fuv[flam_fuv > (1e-11 * su.FLAM)] = np.nan
flam_nuv = (mag_arr(table['NUVmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_nuv))
flam_nuv[flam_nuv > (1e-11 * su.FLAM)] = np.nan
flam_g = (mag_arr(table['gmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_g))
flam_g[flam_g > (1e-11 * su.FLAM)] = np.nan
flam_r = (mag_arr(table['rmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_r))
flam_r[flam_r > (1e-11 * su.FLAM)] = np.nan

f_fn = flam_fuv / flam_nuv
f_ng = flam_nuv / flam_g
f_gr = flam_g   / flam_r


def UVExcess(index):
    return (
        (
            (f_ng[index] > 1 and f_gr[index] < 1) or
            (f_fn[index] > 1 and f_ng[index] < 1)
        ) and ebv[index] > 0.2
    )


candidates = [targetID[i] for i in range(len(targetID)) if UVExcess(i)]
pd.DataFrame({'TARGETID': candidates}).to_csv(out_file, index=False)
print(f"Wrote {len(candidates)} UV-excess candidates to {out_file}")
