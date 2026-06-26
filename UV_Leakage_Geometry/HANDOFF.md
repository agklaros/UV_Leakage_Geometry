# Session Handoff Log

## Session — 2026-06-26

**What we did:**
- Set up UV_Leakage_Geometry project structure from Research_save_6_23 save
- Copied all scripts to scripts/ and updated all hardcoded paths to new locations
- Copied filter .dat files to filters/, QSO template to templates/, figures to figures/
- Organized data into data/raw/ (source catalog), data/matched/ (current outputs), data/archive/ (old iterations)
- Migrated Building_SEDs.ipynb → 02_build_seds.ipynb, unreddened_template.ipynb → 03_unreddened_template.ipynb; created stubs for 01, 04, 05
- Created CLAUDE.md, HANDOFF.md, all 11 slash commands, .claude/settings.json with Stop hook

**Progress state:**

| Stage | Status |
|---|---|
| Crossmatch | Done (in data/matched/; optimal radius TBD) |
| SED construction | In progress (scripts complete; notebook 02 migrated) |
| Unreddened template | In progress (notebook 03 migrated) |
| Color-color plots | In progress (script complete; notebook 04 stub) |
| UV excess sample | Not finalized (<100 target) |

**Open issues:**
- Crossmatch radius not yet optimized (currently 2 arcsec for all catalogs)
- Need to determine which of the four matched CSVs (UKPSAWG, PSAWG, PSG, UKPSGAW) is the primary working sample
- GitHub repository not yet initialized

**Next steps:**
1. Initialize git repository in UV_Leakage_Geometry/ and push to GitHub
2. Run /validate-crossmatch on the four matched CSVs to compare band coverage and decide on primary sample
3. Work through notebook 02 (build_seds) with the primary matched catalog
4. Run /review-uv-excess after notebook 04 to assess candidate sample size

---

## Session — 2026-06-26 (second session)

**What we did:**
- Created `scripts/candidates_to_csv.py`: loads `data/matched/COMBINED_matched.csv`, applies the `UVExcess` function (copied verbatim from `COMBINED_SEDs_unred.py`; criterion: NUV/G > 1 & G/R < 1, OR FUV/NUV > 1 & NUV/G < 1, AND E(B-V) > 0.2), writes passing TARGETIDs to `data/matched/uv_excess_candidates.csv`
- Created `scripts/COMBINED_SEDs_unred_candidates.py`: copy of `COMBINED_SEDs_unred.py` that reads `uv_excess_candidates.csv` and only plots SEDs for TARGETIDs in that list
- Fixed `filtdir` path in candidates SED script to `data/filters/` (filters were moved from `filters/` to `data/filters/`)
- Note: `COMBINED_SEDs_unred.py` and other existing scripts were not modified

**Progress state:**

| Stage | Status |
|---|---|
| Crossmatch | Done (in data/matched/; optimal radius TBD) |
| SED construction | In progress (scripts complete; notebook 02 migrated) |
| Unreddened template | In progress (notebook 03 migrated) |
| Color-color plots | In progress (script complete; notebook 04 stub) |
| UV excess candidate export | Script ready (`candidates_to_csv.py`); not yet run |
| UV excess candidate SEDs | Script ready (`COMBINED_SEDs_unred_candidates.py`); not yet run |

**Open issues:**
- `candidates_to_csv.py` has not been run yet — `uv_excess_candidates.csv` may not exist until first run
- Crossmatch radius not yet optimized (currently 2 arcsec for all catalogs)
- Need to determine which of the four matched CSVs is the primary working sample
- GitHub repository not yet initialized
- CLAUDE.md directory layout still lists `filters/` — should be updated to `data/filters/`

**Next steps:**
1. Run `candidates_to_csv.py` to generate `data/matched/uv_excess_candidates.csv`; check candidate count (target <100)
2. Run `COMBINED_SEDs_unred_candidates.py` to inspect SEDs of UV-excess candidates
3. Update CLAUDE.md to reflect `data/filters/` as the filter location
4. Initialize git and push to GitHub
5. Run /validate-crossmatch to decide on primary matched CSV
