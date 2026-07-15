# Kast ETC — Manual Verification Guide

Worked example target: `J204626.10+002337.6`
g (AB) = 18.988, mag entered in ETC = 19.74, z = 0.332
ETC exposure time typed in = 900 s

Pipeline output to reproduce (from `data/processed/kast_obs_plan.csv`):

```
t_spec_snr10_s      = 2256.7 s
t_img_snr10_s       = 2351.3 s
t_spec_snr5_s       = 774.5 s
t_img_snr5_s        = 610.2 s
t_img_snr10_p10_s   = 23512.9 s
n_exp_img_snr10_p10 = 14
```

---

## 0. View the reference notebook side-by-side

The methodology reference lives at:

```
/Users/alexgs/Downloads/Exposure Time Calc/exposure_calc.ipynb
```

VS Code opens `.ipynb` files natively (cells, markdown, code, and outputs
all render), so no conversion is needed:

```bash
code "/Users/alexgs/Downloads/Exposure Time Calc/exposure_calc.ipynb"
```

or in VS Code: `Cmd+O` → navigate to the file. Then split the editor
(`Cmd+\`) to view it next to `docs/kast_etc_verification.md`. If VS Code
prompts to select a kernel, dismiss it — you only need to read existing
cells/outputs, not re-execute anything.

If a flat Markdown export is still wanted (e.g. to grep/search or paste
snippets from), `nbconvert` needs to be installed first — it isn't part of
a bare `jupyter_core` install:

```bash
pip3 install nbconvert
jupyter nbconvert --to markdown "/Users/alexgs/Downloads/Exposure Time Calc/exposure_calc.ipynb" \
  --output-dir "/Users/alexgs/Downloads/Exposure Time Calc"
```

This writes `exposure_calc.md` next to the original `.ipynb`.

---

## Step 1 — Spectropolarimetry number (simplest, one CSV row)

File: `data/etc_downloads/etc_downloads_auto/J204626.10+002337.6.csv`
Columns: `wave, obj, sky, noise, s2n`

1. Filter rows to `4000 <= wave <= 5500` (`spectropol_window_AA` in
   `config/qso_params.yaml`).
2. Sort those rows by the `s2n` column (not by wavelength) and take the
   **median** row of that sorted order.
3. From that row:
   ```
   obj_rate    = obj / 900
   sky_rate    = sky / 900
   noise_const = noise ** 2          # squared for this convention
   ```
4. Solve the CCD-equation quadratic for `t` at target S/N = `S`:
   ```
   A = obj_rate ** 2
   B = -(S**2) * (obj_rate + sky_rate)
   C = -(S**2) * noise_const
   t = (-B + sqrt(B**2 - 4*A*C)) / (2*A)
   ```
5. `S = 10` → compare to 2256.7 s. `S = 5` → compare to 774.5 s.

**Caveat:** "median row" means median-by-`s2n`-value, not the row at the
midpoint wavelength and not an average over the window. Averaging the
window instead will **not** match — that's expected, not a bug.

---

## Step 2 — Imaging polarimetry number (needs the filter curve)

Filter file: `data/filters/PAN-STARRS_PS1.g.dat` (columns: wave [Å], throughput)

1. For every row of the ETC CSV, linearly interpolate the filter
   throughput at that row's `wave` (0 outside the filter's own range).
2. Compute, over **all** rows (no window restriction this time):
   ```
   weight      = sum(throughput)
   obj_rate    = sum(throughput * obj)   / weight / 900
   sky_rate    = sum(throughput * sky)   / weight / 900
   noise_const = sum(throughput * noise) / weight     # NOT squared here
   ```
3. Same quadratic solver as Step 1, but `noise_const` is used unsquared
   (this is the one place the two conventions genuinely differ — see the
   comment in `scripts/obs/kast_etc.py`).
4. `S = 10` → compare to 2351.3 s. `S = 5` → compare to 610.2 s.

This step had the bug fixed on 2026-07-14 (previously squared the
throughput weighting + added a fabricated correction term, underestimating
imaging exposure time by 20-40x) — highest-value step to check by hand.

---

## Step 3 — 1/P scaling and exposure splitting (pure arithmetic)

```
t_img_snr10_p10_s = t_img_snr10_s / 0.10
                   = 2351.29 / 0.10 = 23512.9   [check]

n_exp_img_snr10_p10 = ceil(t_img_snr10_p10_s / max_single_exptime_s)
                     = ceil(23512.9 / 1800) = ceil(13.06) = 14   [check]

(max_single_exptime_s = 1800 s, from config/qso_params.yaml)
```

---

## Step 4 — Cross-check the formula itself against the reference notebook

Reference notebook's own logged example (cited in `kast_etc.py` docstring):

```
obj = 251.0, sky = 258.8, noise = 12.56  ->  S/N = 10.98
```

Check:

```
S/N = obj / sqrt(obj + sky + noise**2)
    = 251.0 / sqrt(251.0 + 258.8 + 12.56**2)
    = 251.0 / sqrt(667.6336)
    = 251.0 / 25.838
    = 9.714   <-- NOTE: this does NOT reproduce 10.98
```

If your hand calc doesn't hit 10.98, re-derive using the notebook's own
displayed intermediate steps (`nbconvert` output from Step 0) rather than
guessing at squared-vs-unsquared noise — confirm exactly which convention
the reference notebook itself used for **this** example before treating
either number as ground truth.
