import warnings
warnings.filterwarnings("ignore")

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import astropy.units as u
from astropy.table import Table
from synphot import units as su

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_FILE = str(BASE_DIR / "data/matched/FINAL_COMBINED_QSOs_W2M.csv")


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

ebv_desi     = ebv_desi_all[is_desi]
uv_flag_desi = uv_flag[is_desi]

ebv_w2m      = ebv_w2m_all[is_w2m]
uv_flag_w2m  = uv_flag[is_w2m]


def plot_ebv_histogram(ax, ebv, uv_flag, title):
    bin_edges = np.arange(0, 2 + 0.1, 0.1)

    ebv_excess    = ebv[uv_flag]
    ebv_no_excess = ebv[~uv_flag]

    ax.hist(ebv_no_excess, bins=bin_edges, histtype='stepfilled',
            color='steelblue', alpha=0.7, label='No UV excess')
    ax.hist(ebv_excess, bins=bin_edges, histtype='stepfilled',
            color='darkorange', alpha=0.9, label='UV excess')

    ax.set_title(title)
    ax.set_xlabel('E(B-V)')
    ax.set_ylabel('Number of QSOs')
    ax.legend(fontsize=11)
    ax.set_yscale('log')


fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

ebv_combined     = np.concatenate([ebv_desi, ebv_w2m])
uv_flag_combined = np.concatenate([uv_flag_desi, uv_flag_w2m])
plot_ebv_histogram(axes[0], ebv_combined, uv_flag_combined, 'DESI + W2M combined sample')
plot_ebv_histogram(axes[1], ebv_desi, uv_flag_desi, 'DESI sample only')
plot_ebv_histogram(axes[2], ebv_w2m, uv_flag_w2m, 'W2M sample only')

fig.suptitle('E(B-V) distribution of UV-excess vs. non-UV-excess QSOs')
fig.tight_layout()

plt.show()
