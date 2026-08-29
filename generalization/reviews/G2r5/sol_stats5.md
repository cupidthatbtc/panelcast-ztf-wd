- P5 completed-trials — **RESOLVED**: only non-missing nulls count as completed, and acceptance requires exactly 1,000 ([code](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:639)).
- Dominant headline + binding columns + correct-frequency fraction — **UNRESOLVED**: dominant matching and the conditional fraction are implemented, but emitted columns remain `best_match_primary`, `best_match`, and `matched_any_mode_diagnostic`, not the binding estimator names ([code](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:170)).
- P4 denominators + clustered paired contrasts — **RESOLVED**: eligible/usable variants and target-clustered census-minus-LS bootstrap are emitted ([code](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:498)).
- PPV all-2314 preservation — **RESOLVED**: missing negatives remain in the frame and the complete negative frame is resampled before trigger filtering ([code](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:668)).
- Surface coordinates — **UNRESOLVED**: no detection exposure surface is emitted, and `freq_recovery_exposure_amplitude` uses a one-dimensional helper that emits only `exp_per_night_bin`, not `amp_bin` ([code](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:554), [call](/Users/jackneo/Documents/vonhippel-base9/astro-wd/scripts/generalization/metrics_generalization.py:618)).

**FREEZABLE: NO**

Execution blockers: emit the exact binding estimator columns; complete the detection exposure and frequency-recovery exposure×amplitude surface coordinates.
