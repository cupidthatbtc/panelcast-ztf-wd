# Cross-dataset synthesis table report

Generated with:

```text
.venv-gen/bin/python scripts/generalization/descriptive/synthesis_table.py --d1-metrics outputs/generalization/metrics_d1 --d3-bundle generalization/results/2026-09-02_d3 --out-dir outputs/generalization/synthesis_dry_run
```

The dry-run directory contains `synthesis_table.csv`, `evidence_map.json`, `synthesis_table.md`, and `manifest.json`. D1/frozen and D3/frozen are present; D2/frozen, D2/v2, and D3/v2 are explicit blank slots with `notes="bundle not available"`. The evidence map covers all 306 nonblank cells in the 40-row CSV and records the source-file SHA-256 for each.

## Real D1 + D3 table

Values are estimate [95% interval] (n).

| Endpoint | D1/frozen | D3/frozen |
| --- | ---: | ---: |
| P1_detection | 0.846 [0.578, 0.957] (13) | 0.536 [0.496, 0.575] (610) |
| P2_recovery | 0.000 [0.000, 0.490] (4) | 0.163 [0.132, 0.201] (441) |
| P3_negative_trigger | 0.000 [0.000, 0.434] (5) | 0.416 [0.396, 0.436] (2314) |
| census_rate | 0.692 [0.424, 0.873] (13) | 0.041 [0.028, 0.060] (610) |
| either_rate | 1.000 [0.772, 1.000] (13) | 0.548 [0.508, 0.587] (610) |
| union_rate | 1.000 [0.772, 1.000] (13) | 0.571 [0.530, 0.610] (585) |
| incremental_census | 0.154 [0.043, 0.422] (13) | 0.012 [0.0058, 0.024] (585) |
| mcnemar_p | 0.688 (13) | 8.95e-82 (585) |
| chance_match_mean | 0.000 (100) | 0.0037 (100) |
| chance_match_p95 | 0.000 (100) | 0.0091 (100) |
| ppv | — | 0.097 [0.094, 0.101] (1290) |

The D1 negative-class row is the five paper-constant stars (transit control excluded): 0 confirmed and 1 candidate. The D3 P3 row's CSV notes retain the post-launch merged-oid breakdown: <=1, 0/46; 2, 107/438; 3–4, 670/1,439; >=5, 186/391.

## D3 README cross-check

PASS — 25 cells for P1, P2, P3, union, incremental census, PPV, and chance-match agree with `generalization/results/2026-09-02_d3/README.md` after three-decimal formatting. The command exited 0 and printed:

```text
[synthesis_table] D3 README cross-check: PASS (25 README CELLS AT THREE DECIMALS)
```

## Tests

Focused synthesis tests:

```text
6 passed in 0.17s
```

Whole-suite command: `.venv-gen/bin/python -m pytest tests -q`.

```text
4 failed, 227 passed in 63.79s (0:01:03)
```

All four failures are pre-existing `tests/test_v2_runner.py` process-pool tests. This managed macOS sandbox raises `PermissionError: [Errno 1] Operation not permitted` while Python queries `os.sysconf("SC_SEM_NSEMS_MAX")`, before the runner executes repository work. The synthesis tests and the other 227 tests passed; no frozen runner file was changed to work around the sandbox restriction.
