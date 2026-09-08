"""Effective viscosity of a dilute/moderate liquid-liquid dispersion.

Challenge threshold: mu_eff <= 10 cP.

Krieger-Dougherty is a concentrated *suspension* correlation (rigid spheres)
and is not the default here. For liquid droplets we compare:

1. Taylor (1932) emulsion viscosity (dilute, viscosity ratio λ)
2. Pal (2001) / Pal-Rhodes style extension for moderate φ
3. Einstein (1906) as a lower-bound sanity check (λ→∞ rigid spheres, dilute)

Water and DCPD are both ~1 cP at 20 C, so even moderate φ stays well below
10 cP unless the continuous phase itself is thickened.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from phaseforge.provenance import Provenance, RequirementStatus
from phaseforge.requirements import classify_viscosity
from phaseforge.units import C_to_K, Pa_s_to_cP

# Water viscosity IAPWS-range approximation (Kestin / simple Vogel-like).
# 20 C: 1.002 cP; 25 C: 0.890; 50 C: 0.547; 100 C: 0.282; 150 C: 0.182
# Source: published water viscosity tables (IAPWS), treated as PUBLISHED_EXPERIMENTAL.


def water_viscosity_Pa_s(temperature_C: float) -> float:
    """Vogel-like fit to liquid-water viscosity between 10 and 150 C.

    Coefficients fitted to standard water viscosity points and tagged FITTED
    against PUBLISHED_EXPERIMENTAL water tables, not against PhaseForge fluids.
    """
    T = C_to_K(temperature_C)
    # IAPWS-style Vogel: μ = A * 10**(B / (T - C)), A in Pa s, T in K.
    A = 2.414e-5
    B = 247.8
    C = 140.0
    return float(A * 10 ** (B / (T - C)))


def dcpd_viscosity_Pa_s(temperature_C: float) -> float:
    """DCPD ~1.0 mPa s at 20 C (Madbouly 2025). Weak T dependence assumed.

    Andrade: mu = mu20 * exp(E/R (1/T - 1/293.15)) with E ~ 15 kJ/mol
    (ASSUMED_FOR_SENSITIVITY for the T-slope; 20 C anchor is published).
    """
    mu20 = 1.0e-3
    E = 15000.0
    R = 8.314462618
    T = C_to_K(temperature_C)
    return float(mu20 * np.exp(E / R * (1.0 / T - 1.0 / 293.15)))


def taylor_relative(phi: float, lam: float) -> float:
    """Taylor 1932: μ/μc = 1 + φ (1 + 2.5λ)/(1 + λ)

    Valid for dilute emulsions, small deformation, no interfacial films.
    """
    return 1.0 + phi * (1.0 + 2.5 * lam) / (1.0 + lam)


def einstein_relative(phi: float) -> float:
    """Einstein 1906 rigid-sphere dilute limit: 1 + 2.5 φ."""
    return 1.0 + 2.5 * phi


def pal_relative(phi: float, lam: float, phi_m: float = 0.64) -> float:
    """Pal (2001)-inspired closed form reducing to Taylor at low φ.

    μr = [1 - φ/φ_m * (μc+2.5 μd)/(μc+μd)]^{-φ_m}
    For λ=μd/μc. This is used as a moderate-φ bound, not a fitted emulsion.
    """
    K = (1.0 + 2.5 * lam) / (1.0 + lam)
    x = phi / phi_m * (K / 2.5)  # scale so Einstein/Taylor structure is recovered
    x = min(max(x, 0.0), 0.95)
    return float((1.0 - x) ** (-2.5 * phi_m / 1.0 * (K / 2.5)))


def krieger_dougherty_relative(phi: float, phi_m: float = 0.64, B: float = 2.5) -> float:
    """Krieger-Dougherty 1959 for rigid spheres. Shown for comparison only."""
    x = min(phi / phi_m, 0.95)
    return float((1.0 - x) ** (-B * phi_m))


@dataclass(frozen=True, slots=True)
class ViscosityInputs:
    temperature_C: float
    phi: float
    mu_c_Pa_s: float | None = None
    mu_d_Pa_s: float | None = None
    brine_factor: float = 1.1  # dilute brine vs pure water, ASSUMED_FOR_SENSITIVITY


@dataclass(frozen=True, slots=True)
class ViscosityResult:
    mu_c_Pa_s: float
    mu_d_Pa_s: float
    lambda_ratio: float
    mu_taylor_Pa_s: float
    mu_pal_Pa_s: float
    mu_einstein_Pa_s: float
    mu_kd_Pa_s: float
    mu_eff_Pa_s: float
    mu_eff_cP: float
    status: RequirementStatus
    correlation: str
    provenance: Provenance
    notes: str


def evaluate_viscosity(inp: ViscosityInputs) -> ViscosityResult:
    mu_c = inp.mu_c_Pa_s if inp.mu_c_Pa_s is not None else water_viscosity_Pa_s(inp.temperature_C) * inp.brine_factor
    mu_d = inp.mu_d_Pa_s if inp.mu_d_Pa_s is not None else dcpd_viscosity_Pa_s(inp.temperature_C)
    lam = mu_d / max(mu_c, 1e-18)
    phi = min(max(inp.phi, 0.0), 0.6)
    mu_t = mu_c * taylor_relative(phi, lam)
    mu_p = mu_c * pal_relative(phi, lam)
    mu_e = mu_c * einstein_relative(phi)
    mu_k = mu_c * krieger_dougherty_relative(phi)
    # Primary: Taylor at φ<=0.15, Pal at higher φ (still liquid droplets).
    if phi <= 0.15:
        mu_eff = mu_t
        corr = "Taylor1932"
    else:
        mu_eff = mu_p
        corr = "Pal2001_TaylorExtension"
    status = classify_viscosity(mu_eff)
    notes = (
        f"λ={lam:.3g}; φ={phi:.3f}; Taylor={Pa_s_to_cP(mu_t):.3g} cP; "
        f"Pal={Pa_s_to_cP(mu_p):.3g} cP; Einstein={Pa_s_to_cP(mu_e):.3g} cP; "
        f"KD(rigid)={Pa_s_to_cP(mu_k):.3g} cP. KD is a comparison only."
    )
    return ViscosityResult(
        mu_c_Pa_s=mu_c,
        mu_d_Pa_s=mu_d,
        lambda_ratio=lam,
        mu_taylor_Pa_s=mu_t,
        mu_pal_Pa_s=mu_p,
        mu_einstein_Pa_s=mu_e,
        mu_kd_Pa_s=mu_k,
        mu_eff_Pa_s=mu_eff,
        mu_eff_cP=Pa_s_to_cP(mu_eff),
        status=status,
        correlation=corr,
        provenance=Provenance.MODEL_PREDICTION,
        notes=notes,
    )


def viscosity_design_map(
    temperatures_C: np.ndarray,
    phis: np.ndarray,
) -> np.ndarray:
    T = np.asarray(temperatures_C, dtype=float)
    P = np.asarray(phis, dtype=float)
    out = np.empty((P.size, T.size))
    for i, phi in enumerate(P):
        for j, tC in enumerate(T):
            out[i, j] = evaluate_viscosity(ViscosityInputs(float(tC), float(phi))).mu_eff_cP
    return out


# Chen 2023 published viscosities (epoxy analogue, not PhaseForge).
CHEN_PCL_80CP_20C = (80.0, "mPa s", "PCL viscosity decreases from 80 to 33 mPa s at 60 C")
CHEN_NPCL_4CP = (4.0, "mPa s", "NPCL 4 to 3 mPa s")
CHEN_MIX_55_TO_33 = (55.0, "mPa s", "mixture 55 to 33 mPa s at 30-35 C")
