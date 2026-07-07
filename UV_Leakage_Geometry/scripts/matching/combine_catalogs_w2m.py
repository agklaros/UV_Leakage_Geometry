from pathlib import Path

import numpy as np
from astropy.table import Table, vstack, unique

BASE_DIR    = Path(__file__).resolve().parents[2]
DESI_CSV    = str(BASE_DIR / "data/matched/DESI_COMBINED_matched.csv")
W2M_CSV     = str(BASE_DIR / "data/matched/W2M_COMBINED_matched.csv")
FINAL_OUT   = str(BASE_DIR / "data/matched/FINAL_COMBINED_QSOs_W2M.csv")

Column_Keys = ['FUVmag', 'NUVmag', 'ymag', 'yAperMag3', 'j_1AperMag3', 'hAperMag3', 'kAperMag3']

desi = Table.read(DESI_CSV, format='csv')
w2m  = Table.read(W2M_CSV,  format='csv')

combined = vstack([desi, w2m], join_type='outer')
n_before = len(combined)

# unique() requires no masked values; fill with 0.0 temporarily,
# then recover original (unmasked) rows by index to avoid propagating fills
copy = combined.filled(0.0)
copy['_copy'] = np.arange(len(copy))
copy = unique(copy, keys=Column_Keys)
combined = combined[copy['_copy']]

n_dupes = n_before - len(combined)
combined.write(FINAL_OUT, format='csv', overwrite=True)
print(f"  -> {len(combined)} rows written to {FINAL_OUT} ({n_dupes} duplicates removed)")
