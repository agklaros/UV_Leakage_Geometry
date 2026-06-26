import csv
from astropy import units as u
from astropy.table import Table
from astroquery.xmatch import XMatch

# 1. Define paths (using the exact paths from your environment)
csv_file = "/home/agklaros/Documents/UV_Leakage_Geometry/data/raw/QSO_Sample.csv"
output_file = "/home/agklaros/Documents/UV_Leakage_Geometry/data/matched/QSO_SED_Matches.csv"
radius = 2 * u.arcsec

# 2. Define catalogs and their corresponding magnitude column mappings.
# To ensure robustness, we map standard names to possible VizieR variations.
mag_mapping = {
    'gmag': ['gmag', 'g_mag', 'gmagPSF'],
    'rmag': ['rmag', 'r_mag', 'rmagPSF'],
    'imag': ['imag', 'i_mag', 'imagPSF'],
    'zmag': ['zmag', 'z_mag', 'zmagPSF'],
    'ymag': ['ymag', 'y_mag', 'ymagPSF'],
    'Ymag': ['Ymag', 'Y_mag', 'YmagAper3'],
    'Jmag': ['Jmag', 'J_mag', 'JmagAper3', 'Jmag1'],
    'Hmag': ['Hmag', 'H_mag', 'HmagAper3'],
    'Kmag': ['Kmag', 'K_mag', 'KmagAper3', 'Kmag1'],
    'W1mag': ['W1mag', 'w1mpro', 'W1_mag'],
    'W2mag': ['W2mag', 'w2mpro', 'W2_mag'],
    'W3mag': ['W3mag', 'w3mpro', 'W3_mag'],
    'W4mag': ['W4mag', 'w4mpro', 'W4_mag'],
    'FUVmag': ['FUVmag', 'fuv_mag', 'fuv_mag_best'],
    'NUVmag': ['NUVmag', 'nuv_mag', 'nuv_mag_best']
}

# List of catalogs that yielded matches in your Match_quantity.txt
catalogs_to_query = [
    "II/389/ps1_dr2",     # PanSTARRS
    "II/319/las9",        # UKIDSS LAS
    "II/319/dxs9",        # UKIDSS DXS
    "II/319/gcs9",        # UKIDSS GCS
    "II/311/wise",        # AllWISE
    "II/335/galex_ais",   # GALEX AIS
    "II/312/ais",         # GALEX AIS Alt
    "II/312/mis"          # GALEX MIS
]

print("Reading base QSO sample...")
input_table = Table.read(csv_file, format="csv")

# 3. Initialize data structures using native Python dicts
data_dict = {}
catalog_matches = {}
best_distances = {}

for row in input_table:
    tid = str(row['TARGETID'])
    # Store standard metadata
    data_dict[tid] = {
        'TARGETID': tid,
        'RA': row['RA'],
        'DEC': row['DEC'],
        'Z': row['Z'],
        'SPECTYPE': row['SPECTYPE'],
        'matched_catalogs_count': 0
    }
    # Initialize all magnitude fields with empty strings
    for field in mag_mapping.keys():
        data_dict[tid][field] = ''
        
    catalog_matches[tid] = set()
    best_distances[tid] = {}

# 4. Perform crossmatches sequentially
print("\nStarting multi-catalog crossmatching...")
for cat_id in catalogs_to_query:
    print(f"Querying {cat_id}...")
    try:
        matched_table = XMatch.query(
            cat1=input_table,
            cat2=cat_id,
            max_distance=radius,
            colRA1="RA",
            colDec1="DEC"
        )
        
        print(f" -> Found {len(matched_table)} matches.")
        
        # Process rows from the matched table
        for row in matched_table:
            tid = str(row['TARGETID'])
            dist = row['angDist'] if 'angDist' in matched_table.colnames else 0.0
            
            if tid in data_dict:
                # If this is the first match for this catalog or a closer match, record it
                if cat_id not in best_distances[tid] or dist < best_distances[tid][cat_id]:
                    best_distances[tid][cat_id] = dist
                    catalog_matches[tid].add(cat_id)
                    
                    # Extract the relevant magnitude columns case-insensitively
                    for std_name, possible_names in mag_mapping.items():
                        for colname in matched_table.colnames:
                            if colname.lower() in [p.lower() for p in possible_names]:
                                val = row[colname]
                                # Check for masked values or empty placeholders
                                if hasattr(val, 'mask') and val.mask:
                                    continue
                                if str(val) not in ['', 'nan', 'None', '--']:
                                    data_dict[tid][std_name] = val
                                    break
                                    
    except Exception as e:
        print(f" -> Skipped {cat_id} due to error: {e}")

# 5. Filter for targets that matched $\ge 3$ distinct catalogs
filtered_targets = []
for tid, info in data_dict.items():
    num_matches = len(catalog_matches[tid])
    info['matched_catalogs_count'] = num_matches
    if num_matches >= 3:
        filtered_targets.append(info)

print(f"\nProcessing complete. Found {len(filtered_targets)} QSOs matching >= 3 catalogs.")

# 6. Save results to CSV using built-in csv module
fieldnames = [
    'TARGETID', 'RA', 'DEC', 'Z', 'SPECTYPE', 'matched_catalogs_count',
    'FUVmag', 'NUVmag', 
    'gmag', 'rmag', 'imag', 'zmag', 'ymag',
    'Ymag', 'Jmag', 'Hmag', 'Kmag',
    'W1mag', 'W2mag', 'W3mag', 'W4mag'
]

print(f"Writing results to {output_file}...")
with open(output_file, mode='w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for target in filtered_targets:
        # Keep only the columns specified in fieldnames
        row_data = {k: target.get(k, '') for k in fieldnames}
        writer.writerow(row_data)

print("Done!")