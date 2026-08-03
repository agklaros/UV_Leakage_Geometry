# UV Leakage Geometry

> This file lives inside the project directory itself. The canonical, most detailed project
> instructions are at the repo root (`../CLAUDE.md`, one level up) — read that one first if you
> have access to it. This copy is kept in sync with it on points of fact (pipeline stages,
> canonical files, thresholds) for sessions that start from inside this directory.

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
the UV leakage fraction as a function of E(B-V) (not yet implemented — see Known Issues).
A follow-up polarimetry campaign (Lick, Palomar) will distinguish scattered vs. leaked UV
emission; ETC/SNR planning for the Lick Kast leg lives in `scripts/obs/` and
`config/qso_params.yaml`'s `observing:` section.

## Data Source

- Source: Fawcett+2023 DESI red QSO catalog
- Cross-matched to: GALEX AIS/MIS, PanSTARRS DR2, UKIDSS LAS/DXS/GCS, AllWISE, 2MASS
- Base catalog: `data/raw/COMBINED_QSOS_TAB.csv` (34,293 QSOs; never modify)
- Current canonical crossmatched/derived outputs: `data/matched/` (see /pipeline-status for counts)
- Number of targets: ~5,489 after crossmatching + merge/dedupe; 34 UV-excess candidates;
  **29 QSOs** in the final visually-vetted sample

## Pipeline Steps

Rebuilt 2026-08-02 to mirror the current `scripts/` pipeline end-to-end. Run in order:

1. `notebooks/01_crossmatch.ipynb` — CDS XMatch to GALEX/PS1/UKIDSS/AllWISE/2MASS for DESI, W2M-current, and W2M-legacy (legacy kept for reproducibility only); crossmatch-quality figure
2. `notebooks/02_merge_and_dedupe.ipynb` — Combine DESI + W2M-current, remove duplicates → `FINAL_COMBINED_QSOs_W2M.csv`
3. `notebooks/03_uv_excess_selection.ipynb` — UV-excess color-color + E(B-V) selection → `uv_excess_candidates_w2m.csv` (34 candidates); color-color, E(B-V) histogram, UV-excess-fraction, g-mag figures
4. `notebooks/04_visual_review_final_sample.ipynb` — Documents the SED + template-overlay visual-review methodology (the Accept/Reject step itself is interactive and run standalone via `scripts/seds/review_uv_excess_sample.py`, not in-notebook); loads the final `UV_EXCESS_SAMPLE.csv` (29 QSOs); z vs. absolute-W4 diagnostic
5. `notebooks/05_control_sample.ipynb` — Nearest-neighbor control sample (3D standardized z/E(B-V)/g-mag match) → `uv_excess_with_controls_nn.csv`

## Key Parameters

All tunable parameters live in `config/qso_params.yaml` (single source of truth — scripts and
notebooks should load from it, not hardcode values):

- Matching radius: 2 arcsec (current; optimization pending)
- Minimum catalog matches to retain a QSO: 3 (not currently enforced as an explicit post-hoc
  filter by any script — actual floor is 2 required catalogs [PS1+GALEX] + optional UKIDSS/2MASS/WISE)
- FLAM outlier threshold: > 1e-11 FLAM → set to NaN (GALEX/PanSTARRS); > 1e-10 FLAM (UKIDSS, 2MASS, WISE)
- WISE Vega-to-AB offsets: W1 +2.699, W2 +3.339, W3 +5.174, W4 +6.620
- UKIDSS Vega-to-AB offsets: Y +0.634, J +0.938, H +1.379, K +1.900
- 2MASS Vega-to-AB offsets (added 2026-08-02): J +0.894, H +1.374, K +1.839
- **UV-excess criterion: FUV > NUV AND (NUV/G upturn OR FUV/NUV upturn) AND E(B-V) > 0.2** (DESI rows only — W2M's own E(B-V) runs much lower by design, ~0.03 median, and is exempt from the E(B-V) half of the cut)

## Directory Layout

- `data/raw/` — Original catalogs; never modified after download
- `data/matched/` — Current canonical crossmatched/derived outputs
- `data/matched/legacy/` — Superseded matched-CSV variants (UKPSAWG/PSAWG/PSG/UKPSGAW and others); kept for reference, not used by the current pipeline
- `data/archive/` — Old iterations; kept for reference, not canonical
- `data/filters/` — Filter transmission curves (.dat) from SVO Filter Profile Service (**not** a top-level `filters/` — that was a stale path in an earlier version of this file)
- `scripts/` — Primary working code; changes and updates are normally made here. Takes precedence over the notebooks (policy set 2026-07-12)
- `templates/` — Intrinsic QSO spectral template (qso_template.txt)
- `figures/` — Output plots

## UV-Excess Sample & Control Sample

- `data/matched/UV_EXCESS_SAMPLE.csv` — **canonical, final** UV-excess sample (29 QSOs): the 34 candidates in `uv_excess_candidates_w2m.csv` after manual visual SED inspection via `scripts/seds/review_uv_excess_sample.py` (Accept/Reject against the unreddened template overlay). Decisions logged incrementally in `data/matched/UV_EXCESS_SAMPLE_progress.csv`.
- `data/matched/uv_excess_with_controls_nn.csv` — **canonical** control sample: for each of the 29 vetted candidates, the single nearest neighbor in standardized 3D (z, E(B-V), g-mag) space from `FINAL_COMBINED_QSOs_W2M.csv`, built by `scripts/matching/build_control_sample_nn.py`. Controls may be reused across candidates (true 1-NN).
- `data/matched/legacy/uv_excess_with_controls.csv` — **superseded**; older binned E(B-V) + Δz-tolerance control match. Do not use for analysis.

## Conventions

- Scripts in `scripts/` are more important than the notebooks: develop and update in the scripts; notebooks hold fully completed code only, ported over once stable (policy set 2026-07-12)
- Notebooks are numbered and must be run in order
- Raw data in data/raw/ is immutable — never overwrite or modify
- data/archive/ and data/matched/legacy/ files are kept for reference but not used in current analysis
- Always ask about reading HANDOFF.md before starting any work

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

- [x] Issue logged 2026-06-26, fixed 2026-08-02: Do not match quasars to stars or galaxies — `desi_crossmatch_multi.py` now filters `SPECTYPE == 'QSO'` before matching (previously only the notebook did this)
- [ ] Issue logged 2026-06-26: Verify unit consistency when combining bands — magnitudes must be converted to AB system before flux conversion (WISE, UKIDSS, and 2MASS all require Vega-to-AB offsets, listed above)
- [ ] Issue logged 2026-06-26: UV-excess candidate sample target is <100 QSOs — flag and investigate if the sample grows significantly larger (currently 34 candidates / 29 final)
- [x] Issue logged 2026-07-06, fixed 2026-07-07: filter-directory path corrected to `data/filters/` across all scripts
- [ ] Issue logged 2026-07-06: `scripts/seds/W2M_legacy_SEDs.py` references `data/archive/W2M_QSOs.csv`, which does not exist (real file is `data/raw/W2M_QSOs.csv`) — not ported to the current notebooks
- [ ] Issue logged 2026-07-07: no script/notebook fits E(B-V) via `quasar_unred.find_ebv` — all "unred" scripts and `04_visual_review_final_sample.ipynb` only do template overlay + median-flux scaling for visual comparison. The patchy-obscuration model equation above is a stated goal, not yet implemented.
- [ ] Issue logged 2026-07-07: `scripts/seds/COMBINED_SEDs_unred.py` references `data/matched/COMBINED_matched.csv` (does not exist) and `Jmag_2mass`/`Hmag_2mass`/`Kmag_2mass` columns (not present in any current matched CSV) — broken/aspirational, not ported to the current notebooks
- [x] Issue logged 2026-08-02, fixed 2026-08-02: `desi_crossmatch_multi.py` wrote to `data/matched/COMBINED_matched.csv` while every downstream script/notebook read `DESI_COMBINED_matched.csv` — output path corrected
