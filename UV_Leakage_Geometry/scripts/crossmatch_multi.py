import csv
import numpy as np
from astropy import units as u
from astropy.table import Table
from astroquery.xmatch import XMatch

BASE_DIR     = "/home/agklaros/Documents/UV_Leakage_Geometry-1/UV_Leakage_Geometry"
COMBINED_CSV = f"{BASE_DIR}/data/raw/COMBINED_QSOS_TAB.csv"
W2M_CSV      = f"{BASE_DIR}/data/raw/W2M_QSOs.csv"
COMBINED_OUT = f"{BASE_DIR}/data/matched/COMBINED_matched.csv"
W2M_OUT      = f"{BASE_DIR}/data/matched/W2M_matched.csv"
RADIUS       = 2 * u.arcsec

# Column name candidate maps (first match wins, case-insensitive)
PS1_COL_MAP = {
    'gmag': ['gmag', 'gMeanPSFMag'],
    'rmag': ['rmag', 'rMeanPSFMag'],
    'imag': ['imag', 'iMeanPSFMag'],
    'zmag': ['zmag', 'zMeanPSFMag'],
    'ymag': ['ymag', 'yMeanPSFMag'],
}
# W2M already has gmag/rmag/imag/zmag; prefix PS1 columns to avoid collision
PS1_W2M_COL_MAP = {
    'PS1_gmag': ['gmag', 'gMeanPSFMag'],
    'PS1_rmag': ['rmag', 'rMeanPSFMag'],
    'PS1_imag': ['imag', 'iMeanPSFMag'],
    'PS1_zmag': ['zmag', 'zMeanPSFMag'],
    'PS1_ymag': ['ymag', 'yMeanPSFMag'],
}
GALEX_COL_MAP = {
    'FUVmag': ['FUVmag', 'fuv_mag'],
    'NUVmag': ['NUVmag', 'nuv_mag'],
}
UKIDSS_COL_MAP = {
    'yAperMag3':   ['yAperMag3'],
    'j_1AperMag3': ['j_1AperMag3', 'jAperMag3'],
    'hAperMag3':   ['hAperMag3'],
    'kAperMag3':   ['kAperMag3'],
}
TWOMASS_COL_MAP = {
    'Jmag_2mass': ['Jmag', 'j_m'],
    'Hmag_2mass': ['Hmag', 'h_m'],
    'Kmag_2mass': ['Kmag', 'k_m'],
}

# Helpers
_SENTINELS = {'', 'nan', 'none', '--', '99', '99.0', '-99', '-99.0', '-9999'}


def _safe_float(val):
    """Return float or nan for masked/sentinel catalog values."""
    if isinstance(val, np.ma.core.MaskedConstant):
        return float('nan')
    if hasattr(val, 'mask') and bool(val.mask):
        return float('nan')
    try:
        fval = float(val)
    except (TypeError, ValueError):
        return float('nan')
    if str(val).strip().lower() in _SENTINELS:
        return float('nan')
    return fval


def _extract_col(row, candidates, colnames):
    """Return the first finite float matching any candidate column name."""
    lower_map = {c.lower(): c for c in colnames}
    for cand in candidates:
        actual = lower_map.get(cand.lower())
        if actual is None:
            continue
        fval = _safe_float(row[actual])
        if np.isfinite(fval):
            return fval
    return float('nan')


def run_xmatch(base_table, catalog_id, id_col, ra_col, dec_col, col_map):
    """
    XMatch base_table against a VizieR catalog.
    Returns {source_id: {out_col: value}} keeping only the closest match per source.
    """
    print(f"  Querying {catalog_id} ...", end=' ', flush=True)
    try:
        mt = XMatch.query(
            cat1=base_table,
            cat2=catalog_id,
            max_distance=RADIUS,
            colRA1=ra_col,
            colDec1=dec_col,
        )
        print(f"{len(mt)} raw matches")
    except Exception as exc:
        print(f"FAILED ({exc})")
        return {}

    dist_col = 'angDist' if 'angDist' in mt.colnames else None
    result = {}
    for row in mt:
        tid = str(row[id_col])
        dist = float(row[dist_col]) if dist_col else 0.0
        if tid in result and dist >= result[tid]['_dist']:
            continue
        extracted = {'_dist': dist}
        for out_name, candidates in col_map.items():
            extracted[out_name] = _extract_col(row, candidates, mt.colnames)
        result[tid] = extracted
    return result


def write_matched_csv(base_table, id_col, base_cols, xmatch_list, out_fields, out_path):
    """
    Merge base catalog with xmatch results and write CSV.
    Photometry columns absent from all catalogs are written as 'nan'.
    """
    phot_fields = [f for f in out_fields if f not in base_cols]
    print(f"  Writing {out_path} ...")
    with open(out_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        for row in base_table:
            tid = str(row[id_col])
            rec = {col: row[col] for col in base_cols}
            for field in phot_fields:
                rec[field] = float('nan')
            for xm in xmatch_list:
                if tid in xm:
                    for field, val in xm[tid].items():
                        if not field.startswith('_') and field in out_fields:
                            rec[field] = val
            row_out = {
                k: ('nan' if isinstance(v, float) and np.isnan(v) else v)
                for k, v in rec.items()
            }
            writer.writerow(row_out)
    print(f"    -> {len(base_table)} rows written to {out_path}")


print("\n=== COMBINED_QSOS_TAB ===")
combined_base = Table.read(COMBINED_CSV, format='csv')
print(f"  Loaded {len(combined_base)} sources")

ps1_c    = run_xmatch(combined_base, "II/349/ps1",       "TARGETID", "RA", "DEC", PS1_COL_MAP)
galex_c  = run_xmatch(combined_base, "II/335/galex_ais", "TARGETID", "RA", "DEC", GALEX_COL_MAP)
ukidss_c = run_xmatch(combined_base, "II/319/las9",      "TARGETID", "RA", "DEC", UKIDSS_COL_MAP)
mass2_c  = run_xmatch(combined_base, "II/246/out",       "TARGETID", "RA", "DEC", TWOMASS_COL_MAP)

COMBINED_BASE_COLS = ['TARGETID', 'RA', 'DEC', 'Z', 'SPECTYPE', 'EBV', 'EBV_ERR']
COMBINED_FIELDS = COMBINED_BASE_COLS + [
    'FUVmag', 'NUVmag',
    'gmag', 'rmag', 'imag', 'zmag', 'ymag',
    'yAperMag3', 'j_1AperMag3', 'hAperMag3', 'kAperMag3',
    'Jmag_2mass', 'Hmag_2mass', 'Kmag_2mass',
]
write_matched_csv(
    combined_base, 'TARGETID', COMBINED_BASE_COLS,
    [galex_c, ps1_c, ukidss_c, mass2_c],
    COMBINED_FIELDS, COMBINED_OUT,
)

print("\n=== W2M_QSOs ===")
w2m_base = Table.read(W2M_CSV, format='csv')
print(f"  Loaded {len(w2m_base)} sources")

ps1_w   = run_xmatch(w2m_base, "II/349/ps1",       "designation", "ra", "dec", PS1_W2M_COL_MAP)
galex_w = run_xmatch(w2m_base, "II/335/galex_ais", "designation", "ra", "dec", GALEX_COL_MAP)

W2M_BASE_COLS = [
    'designation', 'ra', 'dec', 'zsp',
    'umag', 'gmag', 'rmag', 'imag', 'zmag',
    'j_m_2mass', 'h_m_2mass', 'k_m_2mass',
    'w1mpro', 'w2mpro', 'w3mpro', 'w4mpro',
    'broad', 'src',
]
W2M_FIELDS = W2M_BASE_COLS + [
    'FUVmag', 'NUVmag',
    'PS1_gmag', 'PS1_rmag', 'PS1_imag', 'PS1_zmag', 'PS1_ymag',
]
write_matched_csv(
    w2m_base, 'designation', W2M_BASE_COLS,
    [galex_w, ps1_w],
    W2M_FIELDS, W2M_OUT,
)

print("\nDone.")
