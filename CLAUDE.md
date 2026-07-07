# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Session Start — Do This Before Anything Else

At the start of every session, ask the user:
> "Would you like me to read HANDOFF.md to catch up on the project state?
> Recommended if you are continuing work. Say no for advisory mode only."

If yes (editing mode): read `UV_Leakage_Geometry/HANDOFF.md`, summarize state, check heartbeat vs last HANDOFF entry — if heartbeat is newer, flag unsaved work and ask whether to run `/reconstruct-session` or check for a concurrent session.

If no (advisory mode): answer questions and explain code only — no file edits. User runs `/resume-editing` to switch modes.

## Project

Study of UV-excess ("V-shaped" SED) red quasars from the Fawcett+2023 DESI catalog (34,293 sources, 0.5 < z < 2.5, E(B-V) up to 1). Goal: crossmatch to GALEX, PanSTARRS, UKIDSS, and AllWISE; construct photometric SEDs; fit the patchy obscuration model to quantify UV leakage fraction A as a function of E(B-V). A follow-up polarimetry campaign (Lick, Palomar) will distinguish scattered vs. leaked UV.

Model: `F(λ)_obs = A·F(λ)_0 + (1-A)·F(λ)_0·e^(-τ(λ))` where τ(λ) = k(λ)·E(B-V) / 1.086.

## Running the Project

All primary work is in Jupyter notebooks, run in order from `UV_Leakage_Geometry/`:

```bash
cd UV_Leakage_Geometry
jupyter notebook   # or: jupyter lab
```

Required packages: `astropy`, `astroquery`, `synphot`, `numpy`, `pandas`, `matplotlib`, `pyyaml`.

**Scripts in `scripts/` are reference implementations only.** They contain hardcoded absolute paths (currently `/home/agklaros/Documents/UV_Leakage_Geometry-1/UV_Leakage_Geometry/`) and must not be run directly. Use the notebooks.

## Pipeline

Notebooks must be run in order:

1. `notebooks/01_crossmatch.ipynb` — CDS XMatch (via `astroquery.xmatch`) to GALEX/PS1/UKIDSS/WISE → `data/matched/QSO_SED_Matches.csv`
2. `notebooks/02_build_seds.ipynb` — Convert AB mags to F_λ (erg/s/cm²/Å), apply Vega→AB offsets, outlier-clip, plot SEDs
3. `notebooks/03_unreddened_template.ipynb` — Load `templates/qso_template.txt`, redshift to each QSO's z, compute synthetic photometry via `synphot`
4. `notebooks/04_color_color.ipynb` — NUV/G vs G/R color-color plot; UV-excess selection criterion: FUV > NUV AND (NUV/G upturn OR FUV/NUV upturn) AND E(B-V) > 0.1

## Parameters — Single Source of Truth

All tunable parameters live in `config/qso_params.yaml`. Notebooks must load from it; do not hardcode values.

Key values:
- Matching radius: 2 arcsec (optimization pending)
- Min distinct catalogs to retain a QSO: 3
- FLAM outlier thresholds: >1×10⁻¹¹ (GALEX/PanSTARRS), >1×10⁻¹⁰ (UKIDSS) → set to NaN
- WISE Vega→AB: W1 +2.699, W2 +3.339, W3 +5.174, W4 +6.620
- UKIDSS Vega→AB: Y +0.634, J +0.938, H +1.379, K +1.900
- UV-excess target: <100 QSOs; flag and investigate if larger

## Survey & Column Notes

- **GALEX / PanSTARRS**: AB system, no offset needed
- **UKIDSS**: Vega system; column names are `yAperMag3`, `j_1AperMag3`, `hAperMag3`, `kAperMag3`
- **AllWISE**: Vega system; columns are `w1mpro`, `w2mpro`, `w3mpro`, `w4mpro`
- Filter curves in `filters/` are loaded via `synphot.SpectralElement.from_file()`; see `docs/filters.md` for the full table

## Data Layout

- `data/raw/` — **Immutable**; never modify after download
  - `COMBINED_QSOS_TAB.csv` — Full Fawcett+2023 catalog (34,293 QSOs)
  - `QSO_Sample.csv` — Working input to crossmatch
- `data/matched/` — Current canonical crossmatched CSVs (four variants: UKPSAWG, PSAWG, PSG, UKPSGAW; primary not yet determined)
- `data/archive/` — Old iterations; kept for reproducibility, not used in current analysis
- `filters/` — Filter transmission curves (.dat) from SVO Filter Profile Service
- `templates/qso_template.txt` — Intrinsic QSO spectral template

## Known Issues — Always Check Before Acting

- [ ] Always verify `SPECTYPE == QSO` before analysis — do not match to stars or galaxies
- [ ] Convert all bands to AB before flux conversion — WISE and UKIDSS require Vega→AB offsets (see config)
- [ ] UV-excess candidate sample target is <100 — flag and investigate if it grows larger
- [ ] Crossmatch radius (2 arcsec) not yet optimized across catalogs
- [ ] Primary working matched CSV not yet determined — run `/validate-crossmatch` on the four variants in `data/matched/` to compare band coverage
- [ ] GitHub remote not yet initialized — `/push-to-github` and `/sync-from-github` will not work until `git remote` is set up

## Slash Commands

| Command | Purpose |
|---|---|
| `/end-session` | Write session summary to HANDOFF.md |
| `/checkpoint` | Mid-session save state |
| `/reconstruct-session` | Rebuild HANDOFF.md after a crash |
| `/advisory-mode` | Switch to read-only mode |
| `/resume-editing` | Switch to editing mode with safety checks |
| `/log-issue` | Log a recurring mistake permanently |
| `/push-to-github` | Stage, commit, and push (requires remote to be initialized) |
| `/sync-from-github` | Safely pull from remote with conflict diagnostics |
| `/validate-crossmatch` | Per-band QSO coverage stats, flag star/galaxy contaminants |
| `/pipeline-status` | Table of QSO counts, GALEX detection rates, pipeline progress |
| `/review-uv-excess` | UV excess candidate count, E(B-V) distribution, flag outliers |
