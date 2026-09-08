"""Unit conversion tests. Mixed units must never be silent."""

from phaseforge.units import (
    PSI_4500_MPA,
    PSI_6000_MPA,
    PSI_10000_MPA,
    C_to_K,
    K_to_C,
    MPa_to_psi,
    Pa_s_to_cP,
    Pa_to_psi,
    cP_to_Pa_s,
    m_to_um,
    psi_to_MPa,
    psi_to_Pa,
    to_si,
    um_to_m,
)


def test_cP_roundtrip() -> None:
    assert abs(Pa_s_to_cP(cP_to_Pa_s(10.0)) - 10.0) < 1e-12
    assert abs(cP_to_Pa_s(10.0) - 0.01) < 1e-15


def test_psi_to_MPa() -> None:
    assert abs(psi_to_MPa(6000.0) - 41.368543759) < 1e-6
    assert abs(psi_to_MPa(4500.0) - 31.026407819) < 1e-6
    assert abs(psi_to_MPa(10000.0) - 68.947572932) < 1e-6
    assert abs(PSI_6000_MPA - psi_to_MPa(6000.0)) < 1e-12
    assert abs(PSI_4500_MPA - psi_to_MPa(4500.0)) < 1e-12
    assert abs(PSI_10000_MPA - psi_to_MPa(10000.0)) < 1e-12


def test_psi_roundtrip() -> None:
    assert abs(Pa_to_psi(psi_to_Pa(6000.0)) - 6000.0) < 1e-8
    assert abs(MPa_to_psi(psi_to_MPa(4500.0)) - 4500.0) < 1e-6


def test_length_temp() -> None:
    assert abs(m_to_um(um_to_m(250.0)) - 250.0) < 1e-9
    assert abs(C_to_K(150.0) - 423.15) < 1e-12
    assert abs(K_to_C(423.15) - 150.0) < 1e-12


def test_pint_to_si() -> None:
    assert abs(to_si(10.0, "cP", "Pa*s") - 0.01) < 1e-12
    assert abs(to_si(6000.0, "psi", "MPa") - 41.368543759) < 1e-5
