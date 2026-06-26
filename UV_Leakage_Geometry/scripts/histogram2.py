from astropy import units as u
from astropy.table import Table
from astroquery.xmatch import XMatch
import matplotlib.pyplot as plt
import numpy as np

csv_file = "/home/agklaros/Documents/UV_Leakage_Geometry/data/raw/QSO_Sample.csv" 
real_catalog = Table.read(csv_file, format="csv")
ra_col, dec_col = "RA", "DEC"

false_catalog = real_catalog.copy()
false_catalog[dec_col] = false_catalog[dec_col] + 5

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


rCounts, _ = np.histogram(real_separations, bins=bin_edges)
fCounts, _ = np.histogram(false_separations, bins=bin_edges)
diff_counts = rCounts - fCounts


fig, ax = plt.subplots(figsize=(8, 5.5))


ax.stairs(
    rCounts, 
    bin_edges, 
    baseline=0, 
    linewidth=2, 
    color="black", 
    label="Matches"
)


ax.stairs(
    fCounts, 
    bin_edges, 
    baseline=0, 
    fill=True, 
    color="red", 
    alpha=0.3, 
    label="Shifted (False) matches"
)


ax.stairs(
    diff_counts, 
    bin_edges, 
    baseline=0, 
    linewidth=2, 
    color="blue",
    alpha = 0.5, 
    label="Difference (Real - False)"
)


ax.set_xlim(0, 12)
ax.set_xlabel("Separation (arcsec)", fontsize=12)
ax.set_ylabel("Number", fontsize=12)
ax.grid(linestyle=":", alpha=0.5)
ax.legend(loc="upper right")

plt.title(target_catalog_id + " and Fawcett real and false matches")
plt.tight_layout()
plt.show()
