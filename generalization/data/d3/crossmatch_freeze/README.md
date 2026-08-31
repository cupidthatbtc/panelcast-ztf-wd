# D3 crossmatch freeze — field-density note (data unchanged)

The zero-discretion dispositions are exactly `d3_crossmatch_adjudicate.py`
(rule constants in `freeze_manifest.json`). One property of the realized data
matters for reading `crossmatch_adjudication.csv`: the Kepler field is dense
enough at ZTF depth that essentially every 10″ cone holds more than one ZTF
object, so the `multi_object_cone` component makes `ambiguous` true for ~100%
of crossmatched stars (2,244/2,244 flag0, 585/585 flag1, 72/72 flag2). The
flag remains recorded as defined; the INFORMATIVE crowding lens is the plan's
prespecified crowding-clean subset (separation < 1.0″ AND ≤ 3 objects in the
cone): 228 flag0 + 44 flag1 + 3 flag2 = 275 stars. Headline eligibility is
the frozen chain's `crossmatched` (2,901/3,000: 585/610 positives, 96%);
nothing here overrides it. Attrition by class: `attrition_by_class.csv`.
