# Frozen environment — 2026-08-01 production run

Captured 2026-08-28 from the machine and virtualenv that executed the published
2026-08-01_full catalog run (`jacks-7i-5090`, `C:\Users\jcwen\Projects\astro-wd\.venv`,
22 workers per `lomb-scargle/manifest.json`).

- Python 3.12.12 (CPython, win_amd64)
- numpy==2.3.5 (pip metadata in the venv claimed 2.3.3; the interpreter
  imports 2.3.5, and the 2026-08-28 replay gate PASSED under 2.3.5 — the
  runtime import is the authority)
- scipy==1.16.3
- astropy==8.0.1
- astropy-iers-data==0.2026.7.27.0.56.29
- pyerfa==2.0.1.5
- pandas==2.3.3
- matplotlib==3.10.8
- psutil==7.2.1

`requirements-frozen.txt` pins the numerics-bearing subset. The replay gate
(`scripts/generalization/replay_gate.py`) is the acceptance test for any
env/platform combination: campaign L-S runs are only valid on an env that has
passed the replay gate byte-identically on that machine.
