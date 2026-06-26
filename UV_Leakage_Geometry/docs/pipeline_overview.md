# Pipeline Overview

## Goal

Quantify the UV leakage fraction in dust-reddened quasars as a function of E(B-V)
by fitting photometric SEDs to the patchy obscuration model:

    F(λ)_obs = A·F(λ)_0 + (1-A)·F(λ)_0·e^(-τ(λ))

where A is the leakage fraction, F(λ)_0 is the intrinsic QSO spectrum, and
τ(λ) = k(λ)·E(B-V) / 1.086.

## Stage 1 — Crossmatch (`01_crossmatch.ipynb`)

- Input: `data/raw/QSO_Sample.csv` (subset of Fawcett+2023 DESI red QSO catalog)
- Tool: CDS XMatch via `astroquery.xmatch`
- Catalogs queried: GALEX AIS/MIS, PanSTARRS DR2, UKIDSS LAS/DXS/GCS, AllWISE
- Matching radius: 2 arcsec (optimization pending)
- Filter: retain only QSOs matched to ≥ 3 distinct catalogs
- Output: `data/matched/QSO_SED_Matches.csv`
- Verify: `/validate-crossmatch`

## Stage 2 — Build SEDs (`02_build_seds.ipynb`)

- Convert AB magnitudes to F_λ (erg/s/cm²/Å) using astropy unit conversions
- Apply Vega-to-AB offsets for WISE and UKIDSS bands (see config/qso_params.yaml)
- Set outlier flux values to NaN
- Plot SEDs per QSO in rest-frame wavelength

## Stage 3 — Unreddened Template (`03_unreddened_template.ipynb`)

- Load intrinsic QSO template from `templates/qso_template.txt`
- Redshift template to each QSO's z
- Compute synthetic photometry through each filter using synphot
- Scale template to observed fluxes for overlay

## Stage 4 — Color-Color Plots (`04_color_color.ipynb`)

- Compute flux ratios: NUV/G and G/R
- Color-code by E(B-V)
- V-shaped SED criterion: NUV/G > 1 (UV upturn) and G/R < 1 (red optical)
- Verify: `/review-uv-excess`
