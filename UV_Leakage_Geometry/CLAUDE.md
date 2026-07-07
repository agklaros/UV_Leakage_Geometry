# UV Leakage Geometry

## Session Start — Do This Before Anything Else

At the start of every session, ask the user:
> "Would you like me to read HANDOFF.md to catch up on the project state?
> Recommended if you are continuing work. Say no for advisory mode only."

If yes (editing mode): read HANDOFF.md, summarize state, check heartbeat vs
last HANDOFF entry — if heartbeat is newer, flag unsaved work and ask user
whether to run /reconstruct-session or check for a concurrent session.

If no (advisory mode): answer questions and explain code only — no file edits.
User runs /resume-editing to switch modes.

## Project Overview

Study of UV-excess ("V-shaped" SED) red quasars from the Fawcett+2023 DESI catalog
(34,293 sources, 0.5 < z < 2.5, E(B-V) up to 1). The goal is to crossmatch these
to GALEX, PanSTARRS, UKIDSS, and AllWISE, construct photometric SEDs, and fit the
patchy obscuration model F(λ)_obs = A·F(λ)_0 + (1-A)·F(λ)_0·e^(-τ(λ)) to quantify
the UV leakage fraction as a function of E(B-V). A follow-up polarimetry campaign
(Lick, Palomar) will distinguish scattered vs. leaked UV emission.

## Data Source

- Source: Fawcett+2023 DESI red QSO catalog
- Cross-matched to: GALEX AIS/MIS, PanSTARRS DR2, UKIDSS LAS/DXS/GCS, AllWISE
- Base catalog: `data/raw/COMBINED_QSOS_TAB.csv` (34,293 QSOs; never modify)
- Working input: `data/raw/QSO_Sample.csv`
- Current best matched outputs: `data/matched/` (see /pipeline-status for counts)
- Number of targets: ~30,000 initially; ~5,000 after crossmatching; <100 UV-excess candidates

## Pipeline Steps

1. `01_crossmatch.ipynb` — Crossmatch QSO catalog to all survey catalogs via CDS XMatch
2. `02_build_seds.ipynb` — Convert magnitudes to F_λ, construct SEDs for matched QSOs
3. `03_unreddened_template.ipynb` — Set up and validate the intrinsic QSO spectral template
4. `04_color_color.ipynb` — Color-color plots (NUV/G vs G/R) to identify UV-excess candidates

## Key Parameters

- Matching radius: 2 arcsec (current; optimization pending)
- Minimum catalog matches to retain a QSO: 3
- FLAM outlier threshold: > 1e-11 FLAM → set to NaN (GALEX/PanSTARRS); > 1e-10 FLAM (UKIDSS)
- WISE Vega-to-AB offsets: W1 +2.699, W2 +3.339, W3 +5.174, W4 +6.620
- UKIDSS Vega-to-AB offsets: Y +0.634, J +0.938, H +1.379, K +1.900
- UV-excess criterion: FUV > NUV AND (NUV/G upturn OR FUV/NUV upturn) AND E(B-V) > 0.1

## Directory Layout

- `data/raw/` — Original catalogs; never modified after download
- `data/matched/` — Current canonical crossmatched outputs
- `data/archive/` — Old iterations; kept for reference, not canonical
- `data/processed/` — SED outputs and UV-excess candidate lists (future)
- `scripts/` — Reference .py scripts; notebooks are the primary working environment
- `filters/` — Filter transmission curves (.dat) from SVO Filter Profile Service
- `templates/` — Intrinsic QSO spectral template (qso_template.txt)
- `figures/` — Output plots

## Conventions

- Notebooks are numbered and must be run in order
- Raw data in data/raw/ is immutable — never overwrite or modify
- data/archive/ files are kept for reproducibility but not used in current analysis
- Always read HANDOFF.md before starting any work

## Available Commands

| Command | Purpose |
|---|---|
| `/end-session` | Write session summary to HANDOFF.md |
| `/checkpoint` | Mid-session save state |
| `/reconstruct-session` | Rebuild HANDOFF.md after a crash |
| `/advisory-mode` | Switch to read-only mode |
| `/resume-editing` | Switch to editing mode with safety checks |
| `/log-issue` | Log a recurring mistake permanently |
| `/push-to-github` | Stage, commit, and push |
| `/sync-from-github` | Safely pull from remote with conflict diagnostics |
| `/validate-crossmatch` | Per-band QSO coverage stats, flag star/galaxy contaminants |
| `/pipeline-status` | Table of QSO counts, GALEX detection rates, pipeline progress |
| `/review-uv-excess` | UV excess candidate count, E(B-V) distribution, flag outliers |

## Known Issues — Always Check Before Acting

- [ ] Issue logged 2026-06-26: Do not match quasars to stars or galaxies — always verify SPECTYPE == QSO before analysis
- [ ] Issue logged 2026-06-26: Verify unit consistency when combining bands — magnitudes must be converted to AB system before flux conversion (WISE and UKIDSS require Vega-to-AB offsets listed above)
- [ ] Issue logged 2026-06-26: UV-excess candidate sample target is <100 QSOs — flag and investigate if the sample grows significantly larger
- [x] Issue logged 2026-07-06, fixed 2026-07-07: `scripts/seds/unred.py`, `PSG_SEDs_unred.py`, `PSAWG_SEDs_unred.py`, and `DESI_SEDs_unred.py` hardcoded `filtdir` as `UV_Leakage_Geometry/filters/` instead of the real `UV_Leakage_Geometry/data/filters/` — corrected when all scripts were switched to `Path(__file__)`-relative paths
- [ ] Issue logged 2026-07-06: `scripts/seds/W2M_legacy_SEDs.py` references `data/archive/W2M_QSOs.csv`, which does not exist — only `W2M_multi_2arc.csv` is present in `data/archive/`
