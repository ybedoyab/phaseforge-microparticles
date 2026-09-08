"""Scientific-audit corrections: HT branch, agglomeration, rounding, 150 C FAIL."""

from phaseforge.coupled import OperatingPoint, evaluate_point
from phaseforge.droplets import DropletInputs, diameter_sensitivity, evaluate_droplets
from phaseforge.ht_catalyst import CATALYST_MO_LATENT, evaluate_ht_family
from phaseforge.kinetics import KineticsInputs, evaluate_kinetics
from phaseforge.mechanics import MechanicsInputs, evaluate_mechanics
from phaseforge.provenance import RequirementStatus
from phaseforge.rounding import round_cP, round_sf, round_um


def test_150C_ru_phosphite_still_fails() -> None:
    r = evaluate_kinetics(KineticsInputs(temperature_C=150.0, inhibitor_index=0.95, latency_extra=1.0))
    assert r.t_transform_min < 25.0
    assert r.status is RequirementStatus.FAIL


def test_latency_multiplier_not_used_to_pass_150C() -> None:
    """Do not treat assumed extra latency as a published 150 C PASS."""
    r = evaluate_point(
        OperatingPoint(
            temperature_C=150.0,
            phi=0.15,
            inhibitor_index=0.95,
            latency_extra=1.0,
            label="hpht",
        )
    )
    assert r.kinetics.status is RequirementStatus.FAIL
    assert r.mechanics.status is RequirementStatus.UNKNOWN
    assert r.mechanics.status_150C is RequirementStatus.UNKNOWN


def test_phaseforge_ht_unknown_not_pass() -> None:
    ht = evaluate_ht_family()
    assert ht.status is RequirementStatus.UNKNOWN
    assert ht.isothermal_150C_evidence is False
    r = evaluate_point(
        OperatingPoint(
            temperature_C=150.0,
            phi=0.15,
            catalyst_family=CATALYST_MO_LATENT,
            label="ht",
        )
    )
    assert r.kinetics.status is RequirementStatus.UNKNOWN
    assert r.overall is not RequirementStatus.PASS
    assert r.catalyst_family == CATALYST_MO_LATENT


def test_agglomeration_heuristic_cannot_pass() -> None:
    r = evaluate_point(
        OperatingPoint(temperature_C=60.0, phi=0.10, inhibitor_index=0.35, label="agg")
    )
    assert r.agglomeration is not RequirementStatus.PASS
    assert r.agglomeration in (RequirementStatus.MARGINAL, RequirementStatus.FAIL)


def test_high_T_agglomeration_unknown() -> None:
    r = evaluate_point(
        OperatingPoint(temperature_C=150.0, phi=0.15, inhibitor_index=0.95, label="hot")
    )
    assert r.agglomeration is RequirementStatus.UNKNOWN


def test_mechanics_temperature_qualified() -> None:
    m60 = evaluate_mechanics(MechanicsInputs(temperature_C=60.0))
    assert m60.status in (RequirementStatus.PASS, RequirementStatus.MARGINAL)
    assert m60.status_moderate in (RequirementStatus.PASS, RequirementStatus.MARGINAL)
    assert m60.status_150C is RequirementStatus.UNKNOWN
    assert m60.analogue_98C_MPa_min <= 33.0
    assert m60.analogue_98C_MPa_max >= 50.0
    m150 = evaluate_mechanics(MechanicsInputs(temperature_C=150.0))
    assert m150.status is RequirementStatus.UNKNOWN
    assert m150.status_150C is RequirementStatus.UNKNOWN


def test_diameter_rounding_and_range() -> None:
    d = evaluate_droplets(
        DropletInputs(
            temperature_C=70.0,
            sigma_N_m=0.004,
            shear_rate_1_s=400.0,
            velocity_m_s=1.5,
            length_m=0.05,
            phi=0.15,
        )
    )
    assert d.d_particle_um_nominal == round_um(d.d_particle_um)
    assert d.d_particle_um_nominal % 10 == 0
    sens = diameter_sensitivity()
    assert sens["d_p10_um"] < sens["d_p90_um"]
    assert 70.0 <= sens["d_p50_um"] <= 800.0


def test_reviewer_rounding_examples() -> None:
    assert round_cP(0.5011236538896975) == 0.50
    assert round_um(273.0466868420546) == 270
    assert round_sf(1.414117942869614) == 1.4
