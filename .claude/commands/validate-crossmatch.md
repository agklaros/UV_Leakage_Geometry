---
description: Per-band QSO coverage stats across matched CSVs; flag star/galaxy contaminants
---

Run per-band coverage statistics on the crossmatched CSVs and flag any contaminants.

For each CSV in UV_Leakage_Geometry/data/matched/:
1. Load it and count total rows
2. Count non-null detections per photometric band (FUV, NUV, g, r, i, z, y, Y, J, H, K, W1-W4)
3. Check SPECTYPE column — flag any rows where SPECTYPE != 'QSO'
4. Report detection fractions per band as a markdown table

Also check:
- Whether E(B-V) > 0 for all rows (flag zeros)
- Whether redshift Z is in the expected range 0.5 < z < 2.5
- Duplicate TARGETID entries

Print a summary table and a list of any flagged issues.
