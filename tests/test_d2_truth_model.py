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


def test_dedilution_variant():
    on = build_truth_model(5, [400.0], [8.0], cadence_s=120.0, dedilution=0.8)
    off = build_truth_model(5, [400.0], [8.0], cadence_s=120.0)
    assert abs(on.modes[0].amp_g_mag - off.modes[0].amp_g_mag / 0.8) < 1e-15


def test_super_nyquist_sign_flip_carried_into_amplitude():
    model = build_truth_model(3, [118.0], [10.0], cadence_s=20.0)
    mode = model.modes[0]
    assert mode.tess_sinc > 0.9  # 20-s cadence: nearly no attenuation
    model120 = build_truth_model(3, [300.0], [10.0], cadence_s=120.0)
    assert model120.modes[0].tess_sinc > SINC_REJECT_BELOW
