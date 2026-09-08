"""Mechanical survival of pDCPD-family microparticles under closure stress.

Challenge: 4500-6000 psi ≈ 31.0-41.4 MPa.

Room-temperature unreinforced pDCPD compressive strength is 78 MPa
(PMC12566568, ~23 C). That value MUST NOT be used at 150 C without derating
because published pDCPD Tg is typically 140-165 C (Kovacic & Slugovc 2020).

US11377580B2 Table 3 reports patent experimental compression yield strengths
for delayed DCPD formulations (bulk specimens, not PhaseForge particles):

  At 50 C reaction condition:
    no phosphite: about 88 MPa RT / 47 MPa at 98 C
    phosphite:M2 ≈ 1:1: about 82 MPa RT / 50 MPa at 98 C
  At 80 C:
    about 73 MPa RT / 33 MPa at 98 C for one delayed formulation
    other reported formulations have lower high-temperature strength.
  70/30 DCPD/TriCPD showed greater compression yield strength than pure
  pDCPD at RT and 98 C.

These are analogue validation points only.

Temperature-qualified statuses:
  moderate temperature (T ≪ Tg): PASS candidate if SF >= 1.25
  98 C: published analogue support (MARGINAL / FAIL by formulation)
  150 C: UNKNOWN
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

# US11377580B2 Table 3 — patent examples, not PhaseForge measurements.
PATENT_TABLE3_ANALOGUES = (
    {
        "reaction_C": 50.0,
        "label": "no_phosphite",
        "sigma_RT_MPa": 88.0,
        "sigma_98C_MPa": 47.0,
    },
    {
        "reaction_C": 50.0,
        "label": "phosphite_M2_approx_1_1",
        "sigma_RT_MPa": 82.0,
        "sigma_98C_MPa": 50.0,
    },
    {
        "reaction_C": 80.0,
        "label": "delayed_80C",
        "sigma_RT_MPa": 73.0,
        "sigma_98C_MPa": 33.0,
    },
)


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


def analogue_98C_bulk_MPa() -> tuple[float, float, float]:
    """Min / typical / max patent Table 3 yield at 98 C (bulk)."""
    vals = [float(r["sigma_98C_MPa"]) for r in PATENT_TABLE3_ANALOGUES]
    return min(vals), float(np.median(vals)), max(vals)


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
    status_moderate: RequirementStatus
    status_98C_analogue: RequirementStatus
    status_150C: RequirementStatus
    analogue_98C_MPa_min: float
    analogue_98C_MPa_max: float


def _analogue_98C_status(stress_MPa: float) -> RequirementStatus:
    """Bulk patent examples vs 6000 psi. Not a PhaseForge particle PASS."""
    lo, _, hi = analogue_98C_bulk_MPa()
    # Some formulations (33 MPa) fail 41 MPa; some (47-50 MPa) are near/above.
    if hi < stress_MPa:
        return RequirementStatus.FAIL
    if lo < stress_MPa <= hi:
        return RequirementStatus.MARGINAL
    return RequirementStatus.MARGINAL


def evaluate_mechanics(inp: MechanicsInputs) -> MechanicsResult:
    ret = strength_retention(inp.temperature_C, inp.Tg_C)
    sigma = inp.sigma_c_RT_MPa * ret * inp.safety_discount
    sf = sigma / max(inp.stress_MPa, 1e-9)
    near_tg = inp.temperature_C >= inp.Tg_C - 20.0
    high_T = inp.temperature_C >= 140.0 or near_tg
    unknown = high_T
    status_at_T = classify_mechanical_sf(sf, unknown=unknown)

    sf_moderate = (
        inp.sigma_c_RT_MPa
        * strength_retention(min(inp.temperature_C, 60.0) if inp.temperature_C <= 80.0 else 60.0, inp.Tg_C)
        * inp.safety_discount
        / max(inp.stress_MPa, 1e-9)
    )
    if inp.temperature_C <= 80.0:
        sf_moderate = sf
    moderate = classify_mechanical_sf(sf_moderate, unknown=False)
    lo98, _, hi98 = analogue_98C_bulk_MPa()
    st98 = _analogue_98C_status(inp.stress_MPa)
    st150 = RequirementStatus.UNKNOWN

    notes = (
        f"σ_RT={inp.sigma_c_RT_MPa:.0f} MPa (PMC12566568 analogue); retention={ret:.2f}; "
        f"particle discount={inp.safety_discount:.2f} (ASSUMED); σ_allow={sigma:.0f} MPa; "
        f"σ_req={inp.stress_MPa:.1f} MPa (6000 psi); T-Tg={inp.temperature_C - inp.Tg_C:.0f} K. "
        f"Temperature-qualified: moderate-T status={moderate.value} (PASS candidate if T≪Tg); "
        f"98 C patent Table 3 analogue bulk yield {lo98:.0f}-{hi98:.0f} MPa → {st98.value}; "
        f"150 C={st150.value}. Patent examples are not PhaseForge particle measurements. "
        "70/30 DCPD/TriCPD is reported stronger than pure pDCPD at RT and 98 C (US11377580B2)."
    )
    return MechanicsResult(
        sigma_allow_MPa=sigma,
        stress_MPa=inp.stress_MPa,
        SF=sf,
        retention=ret,
        T_minus_Tg_K=inp.temperature_C - inp.Tg_C,
        status=status_at_T,
        unknown_high_T=unknown,
        provenance=Provenance.MODEL_PREDICTION,
        notes=notes,
        status_moderate=moderate,
        status_98C_analogue=st98,
        status_150C=st150,
        analogue_98C_MPa_min=lo98,
        analogue_98C_MPa_max=hi98,
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
