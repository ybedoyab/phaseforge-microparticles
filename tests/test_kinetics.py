import numpy as np
from phaseforge.kinetics import (
    KineticsInputs,
    arrhenius_tgel_s,
    evaluate_kinetics,
    predicted_vs_observed,
)
from phaseforge.provenance import RequirementStatus


def test_gel_time_decreases_with_temperature() -> None:
    t50 = arrhenius_tgel_s(KineticsInputs(temperature_C=50.0, inhibitor_index=0.0))
    t60 = arrhenius_tgel_s(KineticsInputs(temperature_C=60.0, inhibitor_index=0.0))
    assert t60 < t50


def test_gel_time_decreases_with_catalyst() -> None:
    lo = arrhenius_tgel_s(KineticsInputs(temperature_C=50.0, catalyst_relative=1.0))
    hi = arrhenius_tgel_s(KineticsInputs(temperature_C=50.0, catalyst_relative=3.0))
    assert hi < lo


def test_inhibitor_increases_time() -> None:
    a = arrhenius_tgel_s(KineticsInputs(temperature_C=50.0, inhibitor_index=0.0))
    b = arrhenius_tgel_s(KineticsInputs(temperature_C=50.0, inhibitor_index=1.0))
    assert b > a


def test_madbouly_55C_anchor() -> None:
    t = arrhenius_tgel_s(KineticsInputs(temperature_C=55.0, catalyst_relative=1.0, inhibitor_index=0.0))
    assert abs(t / 60.0 - 19.7) < 0.05


def test_150C_uninhibited_is_far_below_window() -> None:
    r = evaluate_kinetics(KineticsInputs(temperature_C=150.0, inhibitor_index=0.0, latency_extra=1.0))
    assert r.t_transform_min < 5.0
    assert r.status is RequirementStatus.FAIL


def test_validation_rel_error_not_insane() -> None:
    rows = [r for r in predicted_vs_observed() if r["source_id"] == "MADBOULY2025_ACS_OMEGA"]
    for r in rows:
        assert abs(float(r["rel_error"])) < 1.5  # order-of-magnitude, n fitted


def test_conversion_monotonic() -> None:
    from phaseforge.kinetics import conversion_profile

    t = np.linspace(0, 3600, 50)
    a = conversion_profile(t, t_gel_s=600.0)
    assert np.all(np.diff(a) >= -1e-12)
    assert a[0] == 0.0
    assert a[-1] > 0.7
