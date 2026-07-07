from pathlib import Path

from astropy import units as u
from astropy.table import Table, join, unique
from astroquery.xmatch import XMatch

BASE_DIR     = Path(__file__).resolve().parents[2]
COMBINED_CSV = str(BASE_DIR / "data/raw/COMBINED_QSOS_TAB.csv")
COMBINED_OUT = str(BASE_DIR / "data/matched/COMBINED_matched.csv")
RADIUS       = 2 * u.arcsec

BASE_COLS  = ['TARGETID', 'RA', 'DEC', 'Z', 'SPECTYPE', 'EBV', 'EBV_ERR']
OUT_FIELDS = BASE_COLS + [
    'FUVmag', 'NUVmag',
    'gmag', 'rmag', 'imag', 'zmag', 'ymag',
    'yAperMag3', 'j_1AperMag3', 'hAperMag3', 'kAperMag3',
    'Jmag', 'Hmag', 'Kmag',
    'W1mag', 'W2mag', 'W3mag', 'W4mag',
]

#Load base catalog
base = Table.read(COMBINED_CSV, format='csv')


#Match to PanSTARRS keeping only double matches

mt_ps1 = XMatch.query(cat1=base, cat2="II/349/ps1", max_distance=RADIUS, colRA1='RA', colDec1='DEC')
mt_ps1.sort('angDist')
ps1 = unique(mt_ps1, keys='TARGETID', keep='first')
ps1 = ps1[['TARGETID', 'gmag', 'rmag', 'imag', 'zmag', 'ymag']]
step1 = join(base, ps1, keys='TARGETID', join_type='inner')


#Match PS1 sources to GALEX keeping only double matches

mt_galex = XMatch.query(cat1=step1, cat2="II/335/galex_ais", max_distance=RADIUS, colRA1='RA', colDec1='DEC')
mt_galex.sort('angDist')
galex = unique(mt_galex, keys='TARGETID', keep='first')
galex = galex[['TARGETID', 'FUVmag', 'NUVmag']]
step2 = join(step1, galex, keys='TARGETID', join_type='inner')

#UKIDSS, 2MASS, AllWISE matched against the PS1+GALEX double matches

mt_ukidss = XMatch.query(cat1=step2, cat2="II/319/las9", max_distance=RADIUS, colRA1='RA', colDec1='DEC')
mt_ukidss.sort('angDist')
ukidss = unique(mt_ukidss, keys='TARGETID', keep='first')
ukidss = ukidss[['TARGETID', 'yAperMag3', 'j_1AperMag3', 'hAperMag3', 'kAperMag3']]


mt_2mass = XMatch.query(cat1=step2, cat2="II/246/out", max_distance=RADIUS, colRA1='RA', colDec1='DEC')
mt_2mass.sort('angDist')
mass2 = unique(mt_2mass, keys='TARGETID', keep='first')
mass2 = mass2[['TARGETID', 'Jmag', 'Hmag', 'Kmag']]


mt_allwise = XMatch.query(cat1=step2, cat2="II/328/allwise", max_distance=RADIUS, colRA1='RA', colDec1='DEC')
mt_allwise.sort('angDist')
allwise = unique(mt_allwise, keys='TARGETID', keep='first')
allwise = allwise[['TARGETID', 'W1mag', 'W2mag', 'W3mag', 'W4mag']]

# UKIDSS/2MASS/AllWISE are optional; left join preserves all PS1+GALEX sources
final = join(step2, ukidss,  keys='TARGETID', join_type='left')
final = join(final, mass2,   keys='TARGETID', join_type='left')
final = join(final, allwise, keys='TARGETID', join_type='left')


final[OUT_FIELDS].write(COMBINED_OUT, format='csv', overwrite=True)


