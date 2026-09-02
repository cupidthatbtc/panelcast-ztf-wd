NOT RESOLVED — `scripts/v2/run_v2_ls.py:251`: the lock omits `scripts/generalization/frozen_api.py`, although v2 imports executable helpers through it. That file is excluded from both `v2_digest` and `frozen_digest`; campaign changes are merely recorded (`run_v2_ls.py:541`). Altering it between launches therefore preserves every locked value, permitting an incomplete/missing result to be rescored under different code. Metrics (`metrics_generalization.py:1590`) and comparison (`compare_engines.py:370`) also accept the unchanged digests.

Required: include `frozen_api.py` in the artifact-validated runtime digest, lock, resume/end checks, metrics/comparison verification, and add a relaunch drift test.

VERDICT: REVISE