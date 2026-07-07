from pathlib import Path

from astropy import units as u
from astropy.table import Table, join, unique
from astroquery.xmatch import XMatch

# W2M sample (FIRST/VLASS radio-matched); base catalog already includes
# SDSS ugriz, 2MASS, AllWISE, and EBV. Restricted to spCl == 'redQSO' before matching.
BASE_DIR = Path(__file__).resolve().parents[2]
W2M_CSV  = f"{BASE_DIR}/data/raw/FULL_W2M_SAMPLE_FIRST_VLASS.csv"
W2M_OUT  = f"{BASE_DIR}/data/matched/W2M_COMBINED_matched.csv"
RADIUS   = 2 * u.arcsec

# gmag/rmag/imag/zmag conflict with SDSS cols already in base;
# astropy suffixes them _1 (SDSS) and _2 (PS1) on the join
OUT_FIELDS = [
    'designation', 'ra', 'dec', 'zsp', 'spCl', 'ebv',
    'umag', 'gmag_1', 'rmag_1', 'imag_1', 'zmag_1',
    'jmag', 'hmag', 'kmag',
    'w1mag', 'w2mag', 'w3mag', 'w4mag',
    'FIRST_peak', 'FIRST_int', 'VLASS_peak', 'VLASS_int',
    'broad', 'src',
    'FUVmag', 'NUVmag',
    'gmag_2', 'rmag_2', 'imag_2', 'zmag_2', 'ymag',
    'yAperMag3', 'j_1AperMag3', 'hAperMag3', 'kAperMag3',
]

# Load base catalog, restrict to redQSO
base = Table.read(W2M_CSV, format='csv')
base = base[base['spCl'] == 'redQSO']

# Match to PanSTARRS keeping only double matches
mt_ps1 = XMatch.query(cat1=base, cat2="II/349/ps1", max_distance=RADIUS, colRA1='ra', colDec1='dec')
mt_ps1.sort('angDist')
ps1 = unique(mt_ps1, keys='designation', keep='first')
ps1 = ps1[['designation', 'gmag', 'rmag', 'imag', 'zmag', 'ymag']]
step1 = join(base, ps1, keys='designation', join_type='inner')

# Match PS1 sources to GALEX keeping only double matches
mt_galex = XMatch.query(cat1=step1, cat2="II/335/galex_ais", max_distance=RADIUS, colRA1='ra', colDec1='dec')
mt_galex.sort('angDist')
galex = unique(mt_galex, keys='designation', keep='first')
galex = galex[['designation', 'FUVmag', 'NUVmag']]
step2 = join(step1, galex, keys='designation', join_type='inner')

# UKIDSS: left join against the PS1+GALEX double matches
mt_ukidss = XMatch.query(cat1=step2, cat2="II/319/las9", max_distance=RADIUS, colRA1='ra', colDec1='dec')
mt_ukidss.sort('angDist')
ukidss = unique(mt_ukidss, keys='designation', keep='first')
ukidss = ukidss[['designation', 'yAperMag3', 'j_1AperMag3', 'hAperMag3', 'kAperMag3']]
final = join(step2, ukidss, keys='designation', join_type='left')

final[OUT_FIELDS].write(W2M_OUT, format='csv', overwrite=True)
print(f"  -> {len(final)} sources written to {W2M_OUT}")
