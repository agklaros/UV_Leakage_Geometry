---
description: UV excess candidate count, E(B-V) distribution, band coverage, and outlier flags
---

Review the UV-excess candidate sample and flag any outliers.

Load UV_Leakage_Geometry/data/matched/uv_excess_candidates.csv and report:
1. Total candidate count (target: <100; flag and investigate if larger)
2. E(B-V) distribution: min, max, median, and count in bins (0.1-0.3, 0.3-0.5, 0.5-1.0)
3. Redshift distribution: min, max, median
4. Band coverage per candidate: which bands are detected vs missing
5. Any candidates with suspiciously high or low flux in any band

Flag any candidates where:
- SPECTYPE != 'QSO'
- E(B-V) < 0.1 (should have been filtered)
- FUV or NUV is missing (can't confirm UV excess without UV detection)

Print results as a markdown table plus a short summary of concerns.
