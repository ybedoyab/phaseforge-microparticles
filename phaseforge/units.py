"""SI-internal unit conversions. Mixed units must never be hard-coded silently."""

from __future__ import annotations

from dataclasses import dataclass

import pint

ureg = pint.UnitRegistry()
Q_ = ureg.Quantity

# Convenience aliases used in oilfield / polymer literature
ureg.define("cP = 0.001 * Pa * s")
ureg.define("cp = cP")
ureg.define("psi = 6894.757293168 * Pa")


@dataclass(frozen=True, slots=True)
class SIValue:
    value: float
    unit: str

    def to(self, target: str) -> float:
        return float(Q_(self.value, self.unit).to(target).magnitude)


def to_si(value: float, unit: str, si_unit: str) -> float:
    """Convert *value* in *unit* to *si_unit*."""
    return float(Q_(value, unit).to(si_unit).magnitude)


def from_si(value: float, si_unit: str, display_unit: str) -> float:
    return float(Q_(value, si_unit).to(display_unit).magnitude)


def cP_to_Pa_s(mu_cP: float) -> float:
    return mu_cP * 1.0e-3


def Pa_s_to_cP(mu_Pa_s: float) -> float:
    return mu_Pa_s * 1.0e3


def psi_to_Pa(p_psi: float) -> float:
    return p_psi * 6894.757293168


def Pa_to_psi(p_Pa: float) -> float:
    return p_Pa / 6894.757293168


def psi_to_MPa(p_psi: float) -> float:
    return psi_to_Pa(p_psi) / 1.0e6


def MPa_to_psi(p_MPa: float) -> float:
    return Pa_to_psi(p_MPa * 1.0e6)


def um_to_m(d_um: float) -> float:
    return d_um * 1.0e-6


def m_to_um(d_m: float) -> float:
    return d_m * 1.0e6


def C_to_K(t_C: float) -> float:
    return t_C + 273.15


def K_to_C(t_K: float) -> float:
    return t_K - 273.15


# Challenge stress conversions (explicit, tested)
PSI_4500_MPA = psi_to_MPa(4500.0)  # 31.026 MPa
PSI_6000_MPA = psi_to_MPa(6000.0)  # 41.369 MPa
PSI_10000_MPA = psi_to_MPa(10000.0)  # 68.948 MPa
CP_10_PA_S = cP_to_Pa_s(10.0)  # 0.01 Pa s
UM_70_M = um_to_m(70.0)
UM_600_M = um_to_m(600.0)

R_GAS = 8.314462618  # J / (mol K)
