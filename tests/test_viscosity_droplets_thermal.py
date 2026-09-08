from phaseforge.droplets import DropletInputs, evaluate_droplets
from phaseforge.provenance import RequirementStatus
from phaseforge.thermal import ThermalInputs, adiabatic_delta_T, simulate_droplet
from phaseforge.units import um_to_m
from phaseforge.viscosity import ViscosityInputs, evaluate_viscosity, water_viscosity_Pa_s


def test_water_viscosity_20C_near_1cP() -> None:
    mu = water_viscosity_Pa_s(20.0)
    assert 0.0008 < mu < 0.0013
    assert water_viscosity_Pa_s(80.0) < water_viscosity_Pa_s(20.0)


def test_emulsion_below_10cP_at_moderate_phi() -> None:
    r = evaluate_viscosity(ViscosityInputs(temperature_C=60.0, phi=0.15))
    assert r.mu_eff_cP < 10.0
    assert r.status is RequirementStatus.PASS


def test_kd_higher_than_taylor_at_finite_phi() -> None:
    r = evaluate_viscosity(ViscosityInputs(temperature_C=20.0, phi=0.25))
    assert r.mu_kd_Pa_s >= r.mu_taylor_Pa_s * 0.99


def test_diameter_decreases_with_shear() -> None:
    a = evaluate_droplets(
        DropletInputs(
            temperature_C=60.0,
            sigma_N_m=0.004,
            shear_rate_1_s=400.0,
            velocity_m_s=1.0,
            length_m=0.003,
            phi=0.15,
        )
    )
    b = evaluate_droplets(
        DropletInputs(
            temperature_C=60.0,
            sigma_N_m=0.004,
            shear_rate_1_s=2000.0,
            velocity_m_s=4.0,
            length_m=0.003,
            phi=0.15,
        )
    )
    assert b.d_particle_um < a.d_particle_um


def test_adiabatic_delta_T_positive() -> None:
    assert adiabatic_delta_T() > 50.0


def test_droplet_self_heating_limited_by_water() -> None:
    r = simulate_droplet(
        ThermalInputs(diameter_m=um_to_m(200.0), T_cont_C=60.0, t_end_s=900.0)
    )
    assert r.dT_max_K < 40.0
