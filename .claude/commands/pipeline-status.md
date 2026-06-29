---
description: Show a status table of QSO counts and pipeline progress across all stages
---

Show a status table of the current pipeline progress.

Run the following to gather data:
1. `wc -l UV_Leakage_Geometry/data/raw/QSO_Sample.csv` — input QSO count
2. `wc -l UV_Leakage_Geometry/data/matched/*.csv` — row counts for all matched files
3. `head -1 UV_Leakage_Geometry/data/matched/FINAL_COMBINED_QSOs.csv` — column coverage
4. Check which notebooks exist in UV_Leakage_Geometry/notebooks/

Then print a markdown table with columns: Stage | File | QSO Count | Status

Also report:
- Which bands are present in FINAL_COMBINED_QSOs.csv (GALEX/PS1/UKIDSS/2MASS/WISE)
- UV-excess candidate count from uv_excess_candidates.csv
- Any pipeline steps not yet completed
