"""Fetch the Kast ETC CSV table for every target on the input sheet.

Automates exactly the manual step documented in make_etc_inputs.py: for each
target it requests the ETC's "Return csv table for exposure" download
(tab_s2n endpoint, same query the web form sends) and saves it to
data/etc_downloads/<save_download_as>. Existing files are kept, so manually
downloaded tables are never overwritten and reruns only fill gaps.
"""

import time
from pathlib import Path

import pandas as pd
import requests
import urllib3
import yaml

BASE_DIR = Path(__file__).resolve().parents[2]
INPUTS_CSV = BASE_DIR / "data/processed/kast_etc_inputs.csv"
ETC_COLUMNS = ["wave", "obj", "sky", "noise", "s2n"]

# etc.ucolick.org serves an incomplete certificate chain that this host's CA
# bundle cannot validate; the payload is public read-only data.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Form codes behind the human-readable settings in config observing.etc_settings
GRISM_CODES = {"600/4310": "G2", "830/3460": "G3"}
FILTER_CODES = {"g": "sdss_g.dat", "r": "sdss_r.dat", "i": "sdss_i.dat",
                "u": "sdss_u.dat", "z": "sdss_z.dat"}
MAG_SYSTEM_CODES = {"AB": "2", "Vega": "1"}


def main():
    with open(BASE_DIR / "config/qso_params.yaml") as f:
        cfg = yaml.safe_load(f)
    obs = cfg["observing"]
    s = obs["etc_settings"]
    tab_url = obs["etc_page"].rsplit("/", 1)[0] + "/tab_s2n"
    downloads = BASE_DIR / obs["etc_downloads_dir"]
    downloads.mkdir(parents=True, exist_ok=True)

    fixed = {
        "inst": "kast",
        "dichroic": s["dichroic"],
        "slitwidth": s["slitwidth"].split()[0],
        "binning": s["binning"].split()[0],
        "grism": GRISM_CODES[s["grism"]],
        "grating": s["grating"],
        "seeing": f"{s['seeing']}",
        "airmass": f"{s['airmass']}",
        "template": "" if s["template"] == "flat" else s["template"],
        "ffilter": FILTER_CODES[s["norm_filter"]],
        "mtype": MAG_SYSTEM_CODES[s["mag_system"]],
        "exptime": f"{float(obs['etc_exptime_s']):.1f}",
        "redshift": "0.0",
    }

    inputs = pd.read_csv(INPUTS_CSV)
    n_fetched = n_kept = 0
    for _, tgt in inputs.iterrows():
        if pd.isna(tgt["mag_to_enter"]):
            print(f"{tgt['target']}: no g magnitude — skipped")
            continue
        dest = downloads / str(tgt["save_download_as"])
        if dest.exists():
            n_kept += 1
            continue
        resp = requests.get(tab_url, timeout=120, verify=False,
                            params={**fixed, "mag": f"{tgt['mag_to_enter']:.2f}"})
        resp.raise_for_status()
        # Validate before saving so a server error page never poisons the dir
        header = resp.text.splitlines()[0].strip()
        if header != ",".join(ETC_COLUMNS):
            raise RuntimeError(f"{tgt['target']}: unexpected ETC response "
                               f"starting with {header!r}")
        dest.write_text(resp.text)
        n_fetched += 1
        print(f"{tgt['target']}: saved {dest.name} (mag {tgt['mag_to_enter']:.2f})")
        time.sleep(0.5)  # be polite to the ETC server

    print(f"\n{n_fetched} fetched, {n_kept} already present, "
          f"{len(inputs) - n_fetched - n_kept} skipped")


if __name__ == "__main__":
    main()
