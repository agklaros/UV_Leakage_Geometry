import warnings
warnings.filterwarnings("ignore")

import numpy as np
import matplotlib.pyplot as plt
import astropy.units as u
from astropy.table import Table
from synphot import units as su

DATA_FILE = "/Users/alexgs/Documents/UV_Leakage_Geometry/UV_Leakage_Geometry/data/matched/FINAL_COMBINED_QSOs_W2M.csv"


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


def uv_excess_mask(table, gmag_col, rmag_col, require_ebv=True):
    flam_fuv = (mag_arr(table['FUVmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_fuv))
    flam_fuv[flam_fuv > (1e-11 * su.FLAM)] = np.nan
    flam_nuv = (mag_arr(table['NUVmag']) * u.ABmag).to(su.FLAM, u.spectral_density(lam_nuv))
    flam_nuv[flam_nuv > (1e-11 * su.FLAM)] = np.nan
    flam_g = (mag_arr(table[gmag_col]) * u.ABmag).to(su.FLAM, u.spectral_density(lam_g))
    flam_g[flam_g > (1e-11 * su.FLAM)] = np.nan
    flam_r = (mag_arr(table[rmag_col]) * u.ABmag).to(su.FLAM, u.spectral_density(lam_r))
    flam_r[flam_r > (1e-11 * su.FLAM)] = np.nan

    f_fn = flam_fuv / flam_nuv
    f_ng = flam_nuv / flam_g
    f_gr = flam_g   / flam_r

    # NUV/g > 1 & g/r < 1: NUV excess over optical continuum
    # FUV/NUV > 1 & NUV/g < 1: FUV upturn with suppressed NUV
    flux_criterion = (
        ((f_ng > 1) & (f_gr < 1)) |
        ((f_fn > 1) & (f_ng < 1))
    )

    if require_ebv:
        ebv = mag_arr(table['EBV'])
        return flux_criterion & (ebv > 0.2)
    return flux_criterion


table = Table.read(DATA_FILE, format='csv')

# DESI rows have EBV; W2M rows (src == 'w2m') use gmag_2/rmag_2 and their own lowercase ebv column
src = np.array(table['src'], dtype=str)
is_desi = src != 'w2m'
is_w2m = ~is_desi

uv_flag = np.zeros(len(table), dtype=bool)
if np.any(is_desi):
    uv_flag[is_desi] = uv_excess_mask(table[is_desi], gmag_col='gmag', rmag_col='rmag', require_ebv=True)
if np.any(is_w2m):
    uv_flag[is_w2m] = uv_excess_mask(table[is_w2m], gmag_col='gmag_2', rmag_col='rmag_2', require_ebv=False)

ebv_desi_all = mag_arr(table['EBV'])
ebv_w2m_all  = mag_arr(table['ebv'])

ebv_combined     = np.concatenate([ebv_desi_all[is_desi], ebv_w2m_all[is_w2m]])
uv_flag_combined = np.concatenate([uv_flag[is_desi], uv_flag[is_w2m]])

bin_edges   = np.arange(0, 2 + 0.1, 0.1)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

total_counts, _  = np.histogram(ebv_combined, bins=bin_edges)
excess_counts, _ = np.histogram(ebv_combined[uv_flag_combined], bins=bin_edges)

with np.errstate(invalid='ignore', divide='ignore'):
    fraction = np.where(total_counts > 0, excess_counts / total_counts, np.nan)

fig, ax = plt.subplots(figsize=(8, 5.5))
ax.bar(bin_centers, fraction, width=0.09, color='darkorange', edgecolor='black')

ax.set_xlabel('E(B-V)')
ax.set_ylabel('Fraction of QSOs with UV excess')
ax.set_title('UV-excess fraction per E(B-V) bin (DESI + W2M combined sample)')
ax.set_ylim(0, 1)

fig.tight_layout()
plt.show()
