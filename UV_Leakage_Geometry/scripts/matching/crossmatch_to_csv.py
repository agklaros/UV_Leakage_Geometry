from astropy import units as u
from astropy.table import Table as t
from astroquery.xmatch import XMatch


csv_file = "2r_prelim1.csv"
catalog_id = "II/389/ps1_dr2"
input_table = t.read(csv_file, format="csv")
radius = 2



matched_table = XMatch.query(
    cat1=input_table,
    cat2=catalog_id,
    max_distance=radius * u.arcsec,
    colRA1="RA",
    colDec1="DEC"
)

print("Found "+str(len(matched_table))+" matches.")


numpy_data = matched_table.as_array()
matched_table.write("2r_prelim2.csv", format="csv", overwrite=True)
#print("Results saved to 'cross_matched_results.csv'.")

#with open("/home/agklaros/Documents/Match_quantity.txt", "a") as file:
#    file.write("\n" + catalog_id + " has " + str(len(matched_table)) + " matches")
