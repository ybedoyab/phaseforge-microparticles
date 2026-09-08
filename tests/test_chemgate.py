"""ChemGate diffusion, status logic, and literature-analogue guards."""

from __future__ import annotations

import math

import numpy as np
from phaseforge.activation_diffusion import (
    D_LEE2025_M2_S,
    evaluate_sphere,
    fraction_activated,
    profile_snapshot,
    solve_sphere_fv,
    stokes_einstein_scale,
    time_to_avg_threshold,
    volume_average_from_profile,
)
from phaseforge.candidates import (
    FAMILY_HT_THERMAL,
    FAMILY_RUP,
    all_family_cards,
    evaluate_chemgate_family,
    evaluate_rup,
)
from phaseforge.chemgate import ChemGateInputs, evaluate_chemgate
from phaseforge.ht_catalyst import FAMILY_NAME, KORDES_NO_POLY_UP_TO_C, evaluate_ht_family
from phaseforge.kinetics import KineticsInputs, evaluate_kinetics
from phaseforge.provenance import Provenance, RequirementStatus
from phaseforge.rounding import round_cP, round_sf, round_um
from phaseforge.units import um_to_m


def test_lee_d_conversion() -> None:
    assert abs(D_LEE2025_M2_S - 6e-12) < 1e-18


def test_zero_diffusion_infinite_time() -> None:
    R = um_to_m(270.0) / 2.0
    assert math.isinf(time_to_avg_threshold(0.0, R, 0.5))


def test_large_diffusion_fast_time() -> None:
    R = um_to_m(270.0) / 2.0
    t = time_to_avg_threshold(1.0, R, 0.5)
    assert t < 1e-6


def test_analytic_profile_mass_and_bounds() -> None:
    r, c = profile_snapshot(270.0, 30 * 60.0)
    assert np.all(c >= -1e-6)
    assert np.all(c <= 1.0 + 1e-6)
    avg = volume_average_from_profile(r, c)
    assert 0.0 < avg < 1.0
    sph = evaluate_sphere(270.0, T_C=25.0, mode="lee_ambient")
    assert sph.t_avg_50_s > 0
    frac = fraction_activated(c, r, 0.5)
    assert 0.0 <= frac <= 1.0


def test_fv_matches_analytic_order() -> None:
    R = um_to_m(200.0) / 2.0
    t = 20 * 60.0
    r, c_fv, _ = solve_sphere_fv(R, D_LEE2025_M2_S, t, n_r=61, n_t=800)
    r2, c_an = profile_snapshot(200.0, t)
    avg_fv = volume_average_from_profile(r, c_fv)
    avg_an = volume_average_from_profile(r2, c_an)
    assert abs(avg_fv - avg_an) < 0.12


def test_stokes_einstein_hotter_is_faster() -> None:
    assert stokes_einstein_scale(150.0) > 1.0


def test_chemgate_never_pass() -> None:
    r = evaluate_chemgate(ChemGateInputs(diameter_um=270.0, temperature_C=150.0))
    assert r.status is RequirementStatus.UNKNOWN
    assert r.status is not RequirementStatus.PASS
    r2 = evaluate_chemgate(
        ChemGateInputs(diameter_um=150.0, t_trigger_arrival_s=30 * 60.0, D_mode="lee_ambient")
    )
    if 25.0 <= r2.t_from_pumping_min <= 75.0:
        assert r2.pathway in ("PLAUSIBLE_CANDIDATE", "PLAUSIBLE_WITH_EXTRAPOLATED_D")
    assert r2.status is RequirementStatus.UNKNOWN


def test_missing_data_cannot_create_pass() -> None:
    r = evaluate_chemgate(ChemGateInputs(diameter_um=600.0, t_trigger_arrival_s=0.0, D_mode="arrhenius"))
    assert r.status is not RequirementStatus.PASS


def test_rup_150_still_fail() -> None:
    k = evaluate_kinetics(KineticsInputs(temperature_C=150.0, inhibitor_index=0.95, latency_extra=1.0))
    assert k.status is RequirementStatus.FAIL
    card = evaluate_rup()
    assert card.family == FAMILY_RUP
    assert card.overall_150C is RequirementStatus.FAIL


def test_mo_150_unknown_not_pass() -> None:
    ht = evaluate_ht_family()
    assert ht.family == FAMILY_NAME == FAMILY_HT_THERMAL
    assert ht.status is RequirementStatus.UNKNOWN
    assert KORDES_NO_POLY_UP_TO_C == 150.0
    assert ht.isothermal_150C_evidence is False
    assert "150" in ht.notes


def test_chemgate_family_unknown() -> None:
    c = evaluate_chemgate_family()
    assert c.overall_150C is RequirementStatus.UNKNOWN
    assert "D899" in c.activation_at_150C or "Lee" in c.activation_at_150C


def test_d899_is_analogue_not_invention() -> None:
    notes = evaluate_chemgate().notes.lower()
    assert "analogue" in notes or "prior art" in notes
    assert "not a phaseforge invention" in notes


def test_families_do_not_hide_rup_fail() -> None:
    cards = all_family_cards()
    by = {c.family: c.overall_150C for c in cards}
    assert by[FAMILY_RUP] is RequirementStatus.FAIL
    assert RequirementStatus.FAIL in by.values()
    assert all(s is not RequirementStatus.PASS for s in by.values())


def test_reviewer_rounding() -> None:
    assert round_cP(0.5011236538896975) == 0.50
    assert round_um(273.0466868420546) == 270
    assert round_sf(1.414117942869614) == 1.4


def test_cfd_provenance_tag() -> None:
    assert Provenance.CFD_MODEL_PREDICTION.value == "CFD_MODEL_PREDICTION"
    assert Provenance.CFD_3D_MODEL_PREDICTION.value == "CFD_3D_MODEL_PREDICTION"


def test_high_tg_scenarios_unknown_crush() -> None:
    from phaseforge.high_tg import scenarios

    sc = scenarios()
    assert len(sc) == 3
    assert all(s.status_150C_crush is RequirementStatus.UNKNOWN for s in sc)
    visc = next(s for s in sc if s.name.startswith("B_")).viscosity_150C
    assert "UNKNOWN" in visc


def test_chemgate_search_never_pass() -> None:
    from phaseforge.optimization import chemgate_engineering_search

    out = chemgate_engineering_search(seed=1)
    assert "UNKNOWN" in out["verdict"]
    for h in out["example_hits"]:
        assert h["status"] != "PASS"


def test_shell_and_feasibility_shapes() -> None:
    from phaseforge.activation_diffusion import shell_reduced_D_times
    from phaseforge.chemgate import feasibility_map, t_shell_vs_coalescence

    z = feasibility_map(diameters_um=(70.0, 270.0), activities=(1.0,))
    assert z.shape == (1, 2)
    sh = shell_reduced_D_times(270.0)
    assert sh["t_D_x0.1_min"] > sh["t_const_D_min"]
    hyp = t_shell_vs_coalescence(270.0, 10.0)
    assert "Hypothesis" in hyp["notes"]


def test_post_trigger_excludes_operational_arrival() -> None:
    from phaseforge.chemgate import TRIGGER_ARRIVAL_TAG, allowable_trigger_arrival_min

    delayed = evaluate_chemgate(
        ChemGateInputs(diameter_um=270.0, t_trigger_arrival_s=30 * 60.0, D_mode="lee_ambient")
    )
    contact = evaluate_chemgate(
        ChemGateInputs(diameter_um=270.0, t_trigger_arrival_s=0.0, D_mode="lee_ambient")
    )
    assert delayed.t_trigger_arrival_tag == TRIGGER_ARRIVAL_TAG
    assert abs(delayed.t_post_trigger_particle_s - contact.t_post_trigger_particle_s) < 1e-9
    assert abs(delayed.t_from_pumping_min - delayed.t_from_contact_min - 30.0) < 1e-6
    assert delayed.t_post_trigger_particle_min == delayed.t_from_contact_min
    assert delayed.t_from_pumping_min == delayed.t_total_after_initial_pumping_s / 60.0
    # Operational arrival is not chemical latency.
    assert delayed.t_post_trigger_particle_min < delayed.t_from_pumping_min
    env = allowable_trigger_arrival_min(delayed.t_post_trigger_particle_min)
    assert env["requires_arbitrary_fixed_30_min"] is False
    if env["feasible"]:
        lo, hi = env["t_trigger_arrival_min_allowable"], env["t_trigger_arrival_max_allowable"]
        assert 25.0 <= lo + delayed.t_post_trigger_particle_min + 1e-9
        assert hi + delayed.t_post_trigger_particle_min <= 75.0 + 1e-9
        assert abs(hi - lo) > 1.0  # a window, not a single forced 30 min


def test_trigger_envelope_is_a_range_not_a_fixed_30() -> None:
    from phaseforge.chemgate import envelope_summary, trigger_timing_envelope_rows

    rows = trigger_timing_envelope_rows(diameters_um=(270.0,), D_modes=("lee_ambient",))
    assert any(abs(r["t_trigger_arrival_min"] - 0.0) < 1e-9 for r in rows)
    assert any(abs(r["t_trigger_arrival_min"] - 60.0) < 1e-9 for r in rows)
    summ = envelope_summary(diameters_um=(70.0, 270.0, 400.0))
    assert summ["requires_arbitrary_fixed_30_min"] is False
    nom = summ["nominal_270um"]
    assert nom["t_post_trigger_particle_min"] > 0
    lo, hi = nom["t_arr_min_allowable_min"], nom["t_arr_max_allowable_min"]
    assert lo is not None and hi is not None
    assert hi - lo >= 10.0
    in_window = [r for r in rows if r["in_challenge_window_from_pumping"]]
    arrivals = {r["t_trigger_arrival_min"] for r in in_window}
    assert len(arrivals) >= 2


def test_stage_a_activator_is_not_intrinsic_delay() -> None:
    r = evaluate_chemgate(ChemGateInputs(diameter_um=70.0, t_trigger_arrival_s=0.0))
    assert r.stage_a_activator_present is True
    if r.t_post_trigger_particle_min < 25.0:
        assert r.pathway == "NEEDS_TWO_STAGE_DEPLOYMENT"
    assert r.status is RequirementStatus.UNKNOWN
    assert "not material kinetics" in r.notes


def test_notes_do_not_claim_intrinsic_62_min() -> None:
    notes = evaluate_chemgate().notes.lower()
    assert "intrinsically delays" not in notes
    assert "assumed_for_deployment_scenario" in notes
    assert "t_post_trigger_particle" in notes
    assert "t_trigger_arrival" in notes


def test_envelope_json_serializable() -> None:
    import json

    from phaseforge.chemgate import envelope_summary

    json.dumps(envelope_summary(diameters_um=(70.0, 270.0)))
