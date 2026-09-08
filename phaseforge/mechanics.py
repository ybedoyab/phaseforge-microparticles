"""Mechanical survival of pDCPD-family microparticles under closure stress.

Challenge: 4500-6000 psi ≈ 31.0-41.4 MPa.

Room-temperature unreinforced pDCPD compressive strength is 78 MPa
(PMC12566568, ~23 C). That value MUST NOT be used at 150 C without derating
because published pDCPD Tg is typically 140-165 C (Kovacic & Slugovc 2020).

SF_mech(T) = allowable_strength(T) / required_closure_stress
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from phaseforge.provenance import Provenance, RequirementStatus
from phaseforge.requirements import classify_mechanical_sf
from phaseforge.units import PSI_6000_MPA

SIGMA_C_RT_MPA = 78.0  # PMC12566568 unreinforced PDCPD, ~23 C
TG_NOMINAL_C = 155.0  # mid of 140-165 C literature band
SIGMA_YANG_MPA = 95.0  # Yang 2026 DCPD-modified resin compressive, T not specified as 150 C


def strength_retention(T_C: float, Tg_C: float) -> float:
    """Conservative glassy-to-rubbery retention.

    1.0 for T <= Tg-50 C
    linear decline to 0.15 at Tg
    0.05 above Tg (residual rubbery network; not a measured 150 C crush test)

    This is a scenario function, not a DMA master curve for PhaseForge particles.
    """
    t1 = Tg_C - 50.0
    if T_C <= t1:
        return 1.0
    if T_C >= Tg_C:
        return 0.05
    x = (T_C - t1) / 50.0
    return float(1.0 + x * (0.15 - 1.0))


@dataclass(frozen=True, slots=True)
class MechanicsInputs:
    temperature_C: float
    Tg_C: float = TG_NOMINAL_C
    sigma_c_RT_MPa: float = SIGMA_C_RT_MPA
    stress_MPa: float = PSI_6000_MPA
    safety_discount: float = 0.75  # particle vs bulk specimen; ASSUMED_FOR_SENSITIVITY


@dataclass(frozen=True, slots=True)
class MechanicsResult:
    sigma_allow_MPa: float
    stress_MPa: float
    SF: float
    retention: float
    T_minus_Tg_K: float
    status: RequirementStatus
    unknown_high_T: bool
    provenance: Provenance
    notes: str


def evaluate_mechanics(inp: MechanicsInputs) -> MechanicsResult:
    ret = strength_retention(inp.temperature_C, inp.Tg_C)
    sigma = inp.sigma_c_RT_MPa * ret * inp.safety_discount
    sf = sigma / max(inp.stress_MPa, 1e-9)
    near_tg = inp.temperature_C >= inp.Tg_C - 20.0
    # Direct high-T particle crush data for pDCPD beads at 150 C were not retrieved.
    unknown = near_tg
    status = classify_mechanical_sf(sf, unknown=unknown)
    notes = (
        f"σ_RT={inp.sigma_c_RT_MPa:.1f} MPa (PMC12566568); retention={ret:.2f}; "
        f"particle discount={inp.safety_discount:.2f}; σ_allow={sigma:.1f} MPa; "
        f"σ_req={inp.stress_MPa:.2f} MPa (6000 psi); T-Tg={inp.temperature_C - inp.Tg_C:.1f} K. "
        "150 C performance is a major experimental validation requirement."
    )
    prov = Provenance.MODEL_PREDICTION
    if unknown:
        # Keep model prediction but status UNKNOWN overrides PASS.
        pass
    return MechanicsResult(
        sigma_allow_MPa=sigma,
        stress_MPa=inp.stress_MPa,
        SF=sf,
        retention=ret,
        T_minus_Tg_K=inp.temperature_C - inp.Tg_C,
        status=status,
        unknown_high_T=unknown,
        provenance=prov,
        notes=notes,
    )


def sf_vs_temperature(
    temperatures_C: np.ndarray,
    Tg_C: float = TG_NOMINAL_C,
    sigma_c_RT_MPa: float = SIGMA_C_RT_MPA,
) -> np.ndarray:
    out = np.empty_like(temperatures_C, dtype=float)
    for i, t in enumerate(temperatures_C):
        out[i] = evaluate_mechanics(
            MechanicsInputs(temperature_C=float(t), Tg_C=Tg_C, sigma_c_RT_MPa=sigma_c_RT_MPa)
        ).SF
    return out
