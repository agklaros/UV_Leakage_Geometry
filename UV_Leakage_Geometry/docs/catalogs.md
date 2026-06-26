# Survey Catalogs

## GALEX

- **VizieR IDs:** `II/335/galex_ais` (AIS), `II/312/ais` (alt), `II/312/mis` (MIS)
- **Bands:** FUV (1549 Å), NUV (2303 Å)
- **System:** AB
- **Notes:** Primary UV coverage; ~4000 initial matches to Fawcett+2023. Optimal cross-matching radius TBD.
- **Filter files:** `filters/GALEX_GALEX.FUV.dat`, `filters/GALEX_GALEX.NUV.dat`

## PanSTARRS DR2

- **VizieR ID:** `II/389/ps1_dr2`
- **Bands:** g (4810 Å), r (6170 Å), i (7520 Å), z (8660 Å), y (9620 Å)
- **System:** AB
- **Filter files:** `filters/PAN-STARRS_PS1.{g,r,i,z,y,w}.dat`

## UKIDSS

- **VizieR IDs:** `II/319/las9` (LAS), `II/319/dxs9` (DXS), `II/319/gcs9` (GCS)
- **Bands:** Y (10305 Å), J (12483 Å), H (16313 Å), K (22010 Å)
- **System:** Vega — apply AB offsets: Y +0.634, J +0.938, H +1.379, K +1.900
- **Column names:** `yAperMag3`, `j_1AperMag3`, `hAperMag3`, `kAperMag3`
- **Filter files:** `filters/UKIRT_UKIDSS.{Y,Z,J,H,K}.dat`

## AllWISE

- **VizieR ID:** `II/311/wise`
- **Bands:** W1 (33680 Å), W2 (46180 Å), W3 (120820 Å), W4 (221940 Å)
- **System:** Vega — apply AB offsets: W1 +2.699, W2 +3.339, W3 +5.174, W4 +6.620
- **Filter files:** `filters/WISE_WISE.{W1,W2,W3,W4}.dat`

## Filter Profile Source

All filter transmission curves downloaded from the SVO Filter Profile Service:
http://svo2.cab.inta-csic.es/svo/theory/fps/
