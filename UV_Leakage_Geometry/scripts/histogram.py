from astropy import units as u
from astropy.table import Table
from astroquery.xmatch import XMatch
import matplotlib.pyplot as plt
import numpy as np


csv_file = "/home/agklaros/Documents/UV_Leakage_Geometry/data/raw/COMBINED_QSOS_TAB.csv" 
real_catalog = Table.read(csv_file, format="csv")
ra_col, dec_col = "RA", "DEC"


false_catalog = real_catalog.copy()
false_catalog[dec_col] = false_catalog[dec_col] + (5)


target_catalog_id = "II/311/wise"
max_radius = 12 * u.arcsec

real_matches = XMatch.query(
    cat1=real_catalog,
    cat2=target_catalog_id,
    max_distance=max_radius,
    colRA1=ra_col,
    colDec1=dec_col,
)

false_matches = XMatch.query(
    cat1=false_catalog,
    cat2=target_catalog_id,
    max_distance=max_radius,
    colRA1=ra_col,
    colDec1=dec_col,
)




real_separations = np.array(real_matches["angDist"])
false_separations = np.array(false_matches["angDist"])
bin_edges = np.arange(0, 12 + 0.25, 0.25)


fig, ax = plt.subplots(figsize=(8, 5.5))



rCounts, rBins, rPatches = ax.hist(
    real_separations,
    bins=bin_edges,
    histtype="step",
    linewidth=2,
    color="black",
    label="Matches"
)



fCounts, fBins, fPatches = ax.hist(
    false_separations,
    bins=bin_edges,
    histtype="stepfilled",
    linewidth=2,
    color="red",
    label="Shifted (False) matches"
)




ax.set_xlim(0, 12)
ax.set_xlabel("Separation", fontsize=12)
ax.set_ylabel("Number", fontsize=12)





ax.grid(True, linestyle=":", alpha=0.5)


plt.title(target_catalog_id + " and Fawcett real and false matches")
plt.tight_layout()
plt.show()

