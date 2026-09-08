from phaseforge.provenance import (
    Provenance,
    RequirementStatus,
    combine_provenance,
    never_upgrade_unknown,
)
from phaseforge.requirements import (
    classify_diameter_m,
    classify_mechanical_sf,
    classify_transform_time_s,
    classify_viscosity,
    load_challenge_requirements,
    worst_status,
)
from phaseforge.units import cP_to_Pa_s, um_to_m


def test_challenge_yaml_loads() -> None:
    data = load_challenge_requirements()
    assert "requirements" in data
    assert "R02_viscosity" in data["requirements"]
    assert data["requirements"]["R02_viscosity"]["threshold"] == 10.0
    assert data["requirements"]["R07_transformation_window"]["threshold_min"] == 25.0
    assert data["requirements"]["R09_particle_size"]["threshold_max"] == 600.0


def test_viscosity_threshold() -> None:
    assert classify_viscosity(cP_to_Pa_s(9.9)) is RequirementStatus.PASS
    assert classify_viscosity(cP_to_Pa_s(10.0)) is RequirementStatus.PASS
    assert classify_viscosity(cP_to_Pa_s(11.0)) is RequirementStatus.MARGINAL
    assert classify_viscosity(cP_to_Pa_s(20.0)) is RequirementStatus.FAIL


def test_time_window() -> None:
    assert classify_transform_time_s(45 * 60) is RequirementStatus.PASS
    assert classify_transform_time_s(20 * 60) is RequirementStatus.MARGINAL
    assert classify_transform_time_s(5 * 60) is RequirementStatus.FAIL
    assert classify_transform_time_s(45 * 60, unknown=True) is RequirementStatus.UNKNOWN


def test_diameter() -> None:
    assert classify_diameter_m(um_to_m(200)) is RequirementStatus.PASS
    assert classify_diameter_m(um_to_m(60)) is RequirementStatus.MARGINAL
    assert classify_diameter_m(um_to_m(20)) is RequirementStatus.FAIL


def test_sf() -> None:
    assert classify_mechanical_sf(1.5) is RequirementStatus.PASS
    assert classify_mechanical_sf(1.1) is RequirementStatus.MARGINAL
    assert classify_mechanical_sf(0.7) is RequirementStatus.FAIL
    assert classify_mechanical_sf(2.0, unknown=True) is RequirementStatus.UNKNOWN


def test_unknown_never_becomes_pass() -> None:
    assert never_upgrade_unknown(RequirementStatus.UNKNOWN) is RequirementStatus.UNKNOWN
    assert worst_status([RequirementStatus.PASS, RequirementStatus.UNKNOWN]) is RequirementStatus.UNKNOWN
    assert worst_status([RequirementStatus.PASS, RequirementStatus.FAIL]) is RequirementStatus.FAIL
    assert worst_status([RequirementStatus.PASS, RequirementStatus.MARGINAL]) is RequirementStatus.MARGINAL


def test_provenance_priority() -> None:
    assert (
        combine_provenance([Provenance.PUBLISHED_EXPERIMENTAL, Provenance.ASSUMED_FOR_SENSITIVITY])
        is Provenance.ASSUMED_FOR_SENSITIVITY
    )
