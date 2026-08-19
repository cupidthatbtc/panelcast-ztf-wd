# Pilot Lomb–Scargle run — 2026-08-01_full (19-star roster)

The committed results of the blind, alias-vetted Lomb–Scargle cross-check on the
19-star pilot panel, exactly as produced by the run:

- **`RESULTS.md`** — the full report: executive result, controls, 19/19 master
  table, directed searches at the paper's tabulated pulsator frequencies, period
  accuracy, injection–recovery sensitivity, attenuation loop, and the oddball
  verdict. Preserved verbatim.
- **`master_table.csv`** — machine-readable master table (both bands, all three
  cadences, BLS, bootstrap FAPs, A95 upper limits).
- **`acceptance.json`** — the run's acceptance checklist, all gates passed.
- **`figures/`** — census (3 cadences × 2 bands), injection–recovery grid,
  attenuation closure, plus per-star `periodograms/` (both passes, vetted
  aliases marked) and `phase_folds/` for every blind-confirmed detection.

Intermediate CSVs referenced by `RESULTS.md` (QC tables, upper-limit and
attenuation tables, directed-search aliases) are regenerable with the scripts
in `../../../scripts/` — see the Reproduce section of the top-level README for
the exact command sequence.
