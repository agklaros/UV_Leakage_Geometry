# Pipeline Overview

## Goal

Quantify the UV leakage fraction in dust-reddened quasars as a function of E(B-V)
by fitting photometric SEDs to the patchy obscuration model:

    F(λ)_obs = A·F(λ)_0 + (1-A)·F(λ)_0·e^(-τ(λ))

where A is the leakage fraction, F(λ)_0 is the intrinsic QSO spectrum, and
τ(λ) = k(λ)·E(B-V) / 1.086. (Not yet implemented — see CLAUDE.md Known Issues; the
current pipeline below produces the vetted sample this model will eventually be fit to.)

Rebuilt 2026-08-02 to describe the current, actual 5-notebook pipeline (the previous
4-stage version described here was itself stale — wrong output filenames and an
outdated, simplified UV-excess criterion).

## Stage 1 — Crossmatch (`01_crossmatch.ipynb`)

- Inputs: `data/raw/COMBINED_QSOS_TAB.csv` (DESI, Fawcett+2023), `data/raw/FULL_W2M_SAMPLE_FIRST_VLASS.csv` (W2M-current), `data/raw/W2M_QSOs.csv` (W2M-legacy, reproducibility only)
- Tool: CDS XMatch via `astroquery.xmatch`
- Catalogs queried: PanSTARRS DR2 + GALEX AIS (required, inner join), then UKIDSS LAS/DXS/GCS + 2MASS + AllWISE (optional, left join)
- Matching radius: 2 arcsec (optimization pending)
- Filter: DESI base catalog restricted to `SPECTYPE == 'QSO'`; W2M restricted to `spCl == 'redQSO'`
- Outputs: `data/matched/DESI_COMBINED_matched.csv`, `W2M_COMBINED_matched.csv`, `data/matched/legacy/W2M_legacy_COMBINED_matched.csv`
- Figure: crossmatch-quality (real vs. false-match separation), validates the 2″ radius
- Verify: `/validate-crossmatch`

## Stage 2 — Merge & Dedupe (`02_merge_and_dedupe.ipynb`)

- Combine DESI + W2M-current matched tables (outer join)
- Remove duplicate rows (unique on GALEX/UKIDSS magnitude columns)
- Output: `data/matched/FINAL_COMBINED_QSOs_W2M.csv` — the canonical combined catalog (~5,489 QSOs)

## Stage 3 — UV-Excess Selection (`03_uv_excess_selection.ipynb`)

- Convert AB magnitudes to F_λ (erg/s/cm²/Å) using astropy unit conversions; set outlier flux values to NaN
- Compute flux ratios: FUV/NUV, NUV/G, G/R
- UV-excess criterion: `(NUV/G > 1 AND G/R < 1) OR (FUV/NUV > 1 AND NUV/G < 1)`, AND E(B-V) > 0.2 (DESI rows only — W2M's own E(B-V) runs much lower by design and is exempt from that half of the cut)
- Output: `data/matched/uv_excess_candidates_w2m.csv` (34 candidates) — the canonical candidate list
- Figures: color-color (full sample, candidates highlighted), E(B-V) histogram, UV-excess fraction per E(B-V) bin, apparent g-mag distribution
- Verify: `/review-uv-excess`

## Stage 4 — Visual Review & Final Sample (`04_visual_review_final_sample.ipynb`)

- Load intrinsic QSO template from `templates/qso_template.txt`, redshift to each candidate's z, compute synthetic photometry through each filter via `synphot`, scale template to observed fluxes for overlay (visual scaling only — E(B-V) fitting via `quasar_unred.find_ebv` is not yet wired in)
- The Accept/Reject decision itself is interactive and made standalone via `scripts/seds/review_uv_excess_sample.py` (a blocking Tkinter GUI — cannot run inside a notebook cell); decisions are logged to `data/matched/UV_EXCESS_SAMPLE_progress.csv`
- Output (already produced by the interactive step, loaded not regenerated): `data/matched/UV_EXCESS_SAMPLE.csv` — the final, vetted 29-QSO sample
- Figure: redshift vs. absolute WISE-W4 magnitude, vetted 29 vs. full sample

## Stage 5 — Control Sample (`05_control_sample.ipynb`)

- For each of the 29 vetted QSOs, find its single nearest neighbor in standardized 3D (z, E(B-V), g-mag) space within the full combined catalog, excluding known sample members and any independently UV-excess-like row
- Output: `data/matched/uv_excess_with_controls_nn.csv` — used as non-UV-excess comparison targets for the follow-up Lick polarimetry program
