"""Unit tests for the D2 truth model (G3 reviews the algebra independently)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "generalization"))

from d2_truth_model import (  # noqa: E402
    SINC_REJECT_BELOW,
    blackbody_amplitude_ratios,
    build_truth_model,
    integration_sinc,
    retained_modes,
    scenario_code,
)


def test_sinc_limits():
    assert integration_sinc(1000.0, 0.0) == 1.0
    # P = 2 T: x = pi/2, sinc = 2/pi
    assert abs(integration_sinc(240.0, 120.0) - 2.0 / math.pi) < 1e-12
    # first null at P = T
    assert abs(integration_sinc(120.0, 120.0)) < 1e-12
    # past the null the sign flips
    assert integration_sinc(70.0, 120.0) < 0.0


def test_sinc_rejection_boundary():
    # |sinc| = 0.3 at x ~ 2.3556 -> P ~ 160.05 s for 120-s cadence
    model = build_truth_model(1, [150.0, 170.0], [10.0, 10.0], cadence_s=120.0)
    assert len(model.modes) == 1 and len(model.rejected) == 1
    assert model.rejected[0]["period_s"] == 150.0
    # 20-s cadence keeps everything in the DAV range
    model20 = build_truth_model(1, [116.0, 150.0], [10.0, 10.0], cadence_s=20.0)
    assert len(model20.modes) == 2 and not model20.rejected


def test_amplitude_chain_nominal():
    model = build_truth_model(42, [240.0], [10.0], cadence_s=120.0)
    mode = model.modes[0]
    intrinsic_mag = (10.0 * 1e-3 / (2.0 / math.pi)) * 1.0857
    assert abs(mode.amp_g_mag - intrinsic_mag * 1.7) < 1e-12
    assert abs(mode.amp_r_mag - intrinsic_mag * 1.7 * 0.80) < 1e-12
    # ZTF 30-s integration barely attenuates a 240-s mode
    assert 0.97 < mode.ztf_sinc < 1.0


def test_blackbody_ratios_anchor_ladder_low_rung():
    ratio_g, ratio_rg = blackbody_amplitude_ratios(11500.0)
    assert abs(ratio_g - 1.43) < 0.03
    assert abs(ratio_rg - 0.80) < 0.02


def test_phase_determinism_and_band_coherence():
    a = build_truth_model(777, [300.0, 500.0], [5.0, 3.0], cadence_s=120.0)
    b = build_truth_model(777, [300.0, 500.0], [5.0, 3.0], cadence_s=120.0)
    assert [m.phase_rad for m in a.modes] == [m.phase_rad for m in b.modes]
    # ladder variants share phases (variant-stable)
    c = build_truth_model(777, [300.0, 500.0], [5.0, 3.0], cadence_s=120.0,
                          ratio_g=2.1, ratio_rg=0.70)
    assert [m.phase_rad for m in a.modes] == [m.phase_rad for m in c.modes]
    time = np.linspace(0.0, 2.0, 501)
    zg = a.evaluate(time, "zg", t_ref=0.0)
    zr = a.evaluate(time, "zr", t_ref=0.0)
    # same phases, amplitude ratio 0.8 mode-by-mode -> zr = 0.8 * zg exactly
    assert np.allclose(zr, 0.80 * zg, atol=1e-12)


def test_phase_draw_variants():
    base = build_truth_model(777, [300.0, 500.0], [5.0, 3.0], cadence_s=120.0)
    d1 = build_truth_model(777, [300.0, 500.0], [5.0, 3.0], cadence_s=120.0,
                           phase_draw=1)
    d1b = build_truth_model(777, [300.0, 500.0], [5.0, 3.0], cadence_s=120.0,
                            phase_draw=1)
    assert [m.phase_rad for m in d1.modes] == [m.phase_rad for m in d1b.modes]
    assert [m.phase_rad for m in base.modes] != [m.phase_rad for m in d1.modes]
    # amplitudes identical across phase draws
    assert [m.amp_g_mag for m in base.modes] == [m.amp_g_mag for m in d1.modes]


def test_zero_amplitude_null():
    null = build_truth_model(9, [300.0], [5.0], cadence_s=120.0, amplitude_scale=0.0)
    time = np.linspace(0.0, 1.0, 100)
    assert np.all(null.evaluate(time, "zg", t_ref=0.0) == 0.0)
    assert np.all(null.evaluate(time, "zr", t_ref=0.0) == 0.0)


def test_redilution_variant_multiplies_by_crowdsap():
    # PDCSAP is already crowding-corrected: the prespecified sensitivity is the
    # SAP-equivalent RE-dilution A x CROWDSAP (G3 numerics finding 4), never A / CROWDSAP
    on = build_truth_model(5, [400.0], [8.0], cadence_s=120.0, crowdsap=0.19)
    off = build_truth_model(5, [400.0], [8.0], cadence_s=120.0)
    assert abs(on.modes[0].amp_g_mag - off.modes[0].amp_g_mag * 0.19) < 1e-15
    assert on.modes[0].phase_rad == off.modes[0].phase_rad
    import pytest
    with pytest.raises(ValueError):
        build_truth_model(5, [400.0], [8.0], cadence_s=120.0, crowdsap=1.5)


def test_dropout_removes_largest_retained_mode_and_preserves_survivor_phases():
    # table order: 150 s (rejected at 120-s cadence), 300 s (5 ppt), 500 s (9 ppt), 700 s (2 ppt)
    periods, amps = [150.0, 300.0, 500.0, 700.0], [20.0, 5.0, 9.0, 2.0]
    assert retained_modes(periods, amps, 120.0) == [1, 2, 3]
    nominal = build_truth_model(11, periods, amps, cadence_s=120.0)
    dropped = build_truth_model(11, periods, amps, cadence_s=120.0, drop_dominant=True)
    # the 20-ppt mode is REJECTED, so the dominant RETAINED mode (500 s) is dropped
    assert dropped.dominant_dropped and dropped.dropped_period_s == 500.0
    assert [m.period_s for m in dropped.modes] == [300.0, 700.0]
    phase_nominal = {m.period_s: m.phase_rad for m in nominal.modes}
    for mode in dropped.modes:
        assert mode.phase_rad == phase_nominal[mode.period_s]
        assert mode.amp_g_mag == {m.period_s: m.amp_g_mag for m in nominal.modes}[mode.period_s]
    assert len(dropped.rejected) == 1 and dropped.rejected[0]["period_s"] == 150.0


def test_dropout_requires_two_retained_modes():
    import pytest
    with pytest.raises(ValueError):
        build_truth_model(12, [150.0, 300.0], [9.0, 5.0], cadence_s=120.0, drop_dominant=True)


def test_phase_is_a_function_of_table_position_only():
    # sinc rejection of an earlier mode must not shift later modes' phases
    with_short = build_truth_model(13, [150.0, 300.0, 500.0], [9.0, 5.0, 3.0], cadence_s=120.0)
    phases_by_period = {m.period_s: m.phase_rad for m in with_short.modes}
    # the same TIC with the identical table evaluated at 20-s cadence retains the 150-s mode
    at_20s = build_truth_model(13, [150.0, 300.0, 500.0], [9.0, 5.0, 3.0], cadence_s=20.0)
    for mode in at_20s.modes:
        if mode.period_s in phases_by_period:
            assert mode.phase_rad == phases_by_period[mode.period_s]


def test_scenario_codes_are_explicit_and_disjoint():
    assert scenario_code(1.7, 0.80, 0, 1.0, False) == "nominal"
    assert scenario_code(1.7, 0.80, 0, 1.0, True) == "dropout"
    assert scenario_code(1.7, 0.80, 1, 1.0, False) == "phase_1"
    assert scenario_code(1.7, 0.80, 0, 0.7, False) == "ampscale_0.7"
    assert scenario_code(2.1, 0.70, 0, 1.0, False) == "ladder_g3r1"
    assert scenario_code(1.7, 0.80, 0, 1.0, False, crowd_code=1) == "redilution"


def test_super_nyquist_sign_flip_carried_into_amplitude():
    model = build_truth_model(3, [118.0], [10.0], cadence_s=20.0)
    mode = model.modes[0]
    assert mode.tess_sinc > 0.9  # 20-s cadence: nearly no attenuation
    model120 = build_truth_model(3, [300.0], [10.0], cadence_s=120.0)
    assert model120.modes[0].tess_sinc > SINC_REJECT_BELOW
