# G5 — independent re-derivation of every frozen D3 headline number (read-only)

Repository: /Users/jackneo/Documents/vonhippel-base9/astro-wd (branch generalization/campaign-1).
Python: `.venv-gen/bin/python` (numpy, pandas, scipy). You may read anything and run read-only
Python; do NOT modify tracked files. Write your report ONLY to
`generalization/reviews/G5/verifier_d3.md`.

You are a fresh verifier with no attachment to the campaign. The authoritative frozen D3 bundle
is `generalization/results/2026-09-02_d3/` (README.md states the headline numbers; metrics/ holds
per_star.csv, completeness_by_class_pass_rule.csv, trigger_rates.csv, contingency_complementarity.json,
chance_match.json, ppv.csv, fp_frequency_distribution.csv, sensitivity.csv, attrition.csv,
attrition_summary.csv, surfaces/; descriptive_postlaunch/ holds the nine admitted descriptive
outputs with their README/manifest sidecars). The per-star JSONs of the run are at
`outputs/generalization/d3_sync/d3_run/stars/<sid>.json` (+ .prov.json) and the truth sources
at `generalization/data/d3/roster_d3.csv` and `generalization/data/d3/raw/mo2026_table2.csv`.
The estimand definitions are in `generalization/METRICS_SPEC.md` (P1, P2, P3 and the rules; the
frequency-match taxonomy `classify_match` and `pass_eligible` in
`scripts/generalization/metrics_generalization.py`).

Task — re-derive INDEPENDENTLY (your own code, not by calling the campaign's aggregation
functions; you may use `classify_match`/`pass_eligible`/`wilson` only after reading them and
stating that you did) from per_star.csv AND, for at least the P1/P3 counts and 50 randomly
chosen stars' statuses/frequencies, from the raw JSONs via the frozen `overall_result`:

1. P1 detection completeness (rule 1, best pass; eligible roster 610; and the usable frame),
   with Wilson 95 % interval.
2. P2 dominant-frequency recovery on the Mo-joined, freq-scorable, eligible, usable frame
   (report n = ? — the README says 441 scorable), the correct-frequency fraction among detected,
   and the chance-match rate.
3. P3 negative-class trigger rate (2,314), census rate, either-rule rate.
4. The contingency table (LS-only / census-only / both / neither; union; McNemar).
5. PPV.
6. Every number quoted in README.md and in the nine descriptive READMEs under
   descriptive_postlaunch/ (P3 by merged-oid count, by pass, sky cells, magnitude/Teff strata,
   positive partition counts, P2 by regime, fR rescoring, a95 medians, coverage): re-derive
   each from its stated inputs and mark MATCH / MISMATCH (with your value and the file's value).
7. Provenance spot-check: 20 random stars — sidecar shard SHA equals the shard on disk
   (`outputs/generalization/d3_sync/d3_panels/exposure_stars/<sid>.csv.gz`), result SHA equals
   the JSON, completion.csv agrees.

Report format: a table per item (quantity | README/file value | re-derived value | MATCH/MISMATCH
| your one-line derivation), then a list of every MISMATCH with the likely cause, then the exact
commands/code you ran (so the lead can reproduce), then `VERDICT: NUMBERS REPRODUCE` or
`VERDICT: DISCREPANCIES` with the list. Be terse and precise; no prose beyond that.
