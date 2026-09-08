import numpy as np
from phaseforge.coupled import OperatingPoint, evaluate_point
from phaseforge.mechanics import MechanicsInputs, evaluate_mechanics, strength_retention
from phaseforge.permeability import PermeabilityInputs, evaluate_permeability, random_disk_pack
from phaseforge.provenance import RequirementStatus
from phaseforge.uncertainty import latin_hypercube
from phaseforge.units import um_to_m


def test_retention_drops_near_tg() -> None:
    assert strength_retention(50.0, 155.0) == 1.0
    assert strength_retention(155.0, 155.0) == 0.05
    assert strength_retention(140.0, 155.0) < 1.0


def test_mechanics_unknown_near_tg() -> None:
    r = evaluate_mechanics(MechanicsInputs(temperature_C=150.0, Tg_C=155.0))
    assert r.unknown_high_T is True
    assert r.status is RequirementStatus.UNKNOWN


def test_mechanics_pass_well_below_tg() -> None:
    r = evaluate_mechanics(MechanicsInputs(temperature_C=60.0, Tg_C=155.0))
    assert r.SF > 1.0
    assert r.status in (RequirementStatus.PASS, RequirementStatus.MARGINAL)


def test_distributed_pathways_open() -> None:
    r = evaluate_permeability(PermeabilityInputs(d_m=um_to_m(200), phi_particles=0.15, settled=False))
    assert r.connected is True
    assert r.geometric_connectivity is True
    # Unvalidated conductivity must not independently PASS.
    assert r.status is RequirementStatus.MARGINAL
    assert "ASSUMED" in r.notes or "assumed" in r.notes.lower()


def test_bulk_phi_fails_pathways() -> None:
    r = evaluate_permeability(PermeabilityInputs(d_m=um_to_m(200), phi_particles=0.70, settled=True))
    assert r.status in (RequirementStatus.FAIL, RequirementStatus.MARGINAL)


def test_random_pack_deterministic() -> None:
    a, va = random_disk_pack(40, um_to_m(200), 0.005, 0.003, rng=np.random.default_rng(42))
    b, vb = random_disk_pack(40, um_to_m(200), 0.005, 0.003, rng=np.random.default_rng(42))
    assert a.shape == b.shape
    assert abs(va - vb) < 1e-15


def test_lhs_deterministic() -> None:
    x1 = latin_hypercube(20, seed=42)
    x2 = latin_hypercube(20, seed=42)
    assert np.allclose(x1, x2)


def test_nominal_not_fail_viscosity() -> None:
    r = evaluate_point(
        OperatingPoint(temperature_C=60.0, phi=0.15, inhibitor_index=0.6, label="t")
    )
    assert r.viscosity.status is RequirementStatus.PASS
    assert r.overall is not RequirementStatus.PASS or r.kinetics.status is RequirementStatus.PASS
