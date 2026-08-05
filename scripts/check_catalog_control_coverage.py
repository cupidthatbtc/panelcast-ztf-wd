#!/usr/bin/env python3
"""Verify ZTF coverage for the catalog's unavailable southern RR Lyrae control."""

import argparse
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "6555925496084361344"
RA = 349.01224480468346
DEC = -32.77824769403533
BASE_URL = "https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves"


def query(radius_arcsec: float) -> dict[str, object]:
    params = {
        "POS": f"CIRCLE {RA} {DEC} {radius_arcsec / 3600.0:.10f}",
        "BANDNAME": "g,r",
        "FORMAT": "CSV",
        "BAD_CATFLAGS_MASK": "32768",
    }
    url = BASE_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "panelcast-ztf-wd-catalog/1.0"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        text = response.read().decode("utf-8", errors="replace")
    lines = [
        line
        for line in text.splitlines()
        if line.strip() and not line.startswith("\\") and not line.startswith("|")
    ]
    return {
        "radius_arcsec": radius_arcsec,
        "rows": max(0, len(lines) - 1),
        "response_bytes": len(text.encode("utf-8")),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "outputs/catalog/2026-08-01_full/control_coverage.json",
    )
    args = parser.parse_args()

    checks = []
    for radius in (10.0, 30.0):
        checks.append(query(radius))
        time.sleep(1.25)
    payload = {
        "source_id": SOURCE_ID,
        "ra": RA,
        "dec": DEC,
        "endpoint": BASE_URL,
        "bands": ["zg", "zr"],
        "checks": checks,
        "ztf_available": any(check["rows"] > 0 for check in checks),
        "verdict": "unavailable_no_ztf_rows" if all(check["rows"] == 0 for check in checks) else "available",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
