"""High-Tg pDCPD-family material scenarios for 150 C mechanics narrative.

150 C is near Tg of conventional pDCPD but below Tg of several experimentally
demonstrated high-Tg pDCPD-family networks. No 150 C crush of PhaseForge particles.
Modulus is not substituted for compressive strength.
"""

from __future__ import annotations

from dataclasses import dataclass

from phaseforge.provenance import Provenance, RequirementStatus

# Conventional pDCPD Tg 140-165 C (Kovacic 2020). RT compressive 78 MPa (PMC12566568).
# Zhan 2024: sequential ROMP+radical Tg 191 C (200 C cure) / 216 C (250 C).
# US4703098: DCPD + 6.5-22% TCPD oligomer Tg 132-162 C (patent). 80 wt% TCPD Tg ~210 C
# from Zhang 2024 DOI 10.1016/j.mtcomm.2024.109494 was not independently extracted from
# a retrieved full PDF in this session — recorded as bibliographic / task-cited.


@dataclass(frozen=True, slots=True)
class MaterialScenario:
    name: str
    Tg_C_lo: float
    Tg_C_hi: float
    sigma_RT_MPa: float | None
    modulus_note: str
    viscosity_150C: str
    status_150C_crush: RequirementStatus
    provenance: Provenance
    notes: str

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "Tg_C_lo": self.Tg_C_lo,
            "Tg_C_hi": self.Tg_C_hi,
            "sigma_RT_MPa": self.sigma_RT_MPa,
            "modulus_note": self.modulus_note,
            "viscosity_150C": self.viscosity_150C,
            "status_150C_crush": self.status_150C_crush.value,
            "provenance": self.provenance.value,
            "notes": self.notes,
        }


def scenarios() -> list[MaterialScenario]:
    return [
        MaterialScenario(
            name="A_neat_pDCPD",
            Tg_C_lo=140.0,
            Tg_C_hi=165.0,
            sigma_RT_MPa=78.0,
            modulus_note="Do not use flexural modulus as 6000 psi crush.",
            viscosity_150C="DCPD monomer ~1 cP class at 20 C; emulsion modelled PASS",
            status_150C_crush=RequirementStatus.UNKNOWN,
            provenance=Provenance.PUBLISHED_EXPERIMENTAL,
            notes="150 C is near Tg. Retention scenario function only. UNKNOWN crush.",
        ),
        MaterialScenario(
            name="B_DCPD_TCPD_analogue",
            Tg_C_lo=132.0,
            Tg_C_hi=210.0,
            sigma_RT_MPa=None,
            modulus_note=(
                "US4703098 flex modulus ~1.94-2.14 GPa at 6-22% TCPD (patent). "
                "Zhang 2024 DOI 10.1016/j.mtcomm.2024.109494 reports improved thermomechanics "
                "including high-TCPD Tg (full PDF not retrieved; ~80 wt% TCPD Tg ~210 C "
                "and flex modulus increase 1865→2703 MPa are task-cited, not re-digitized)."
            ),
            viscosity_150C="UNKNOWN for high-TCPD liquids; 80 wt% TCPD is not assumed to meet 10 cP",
            status_150C_crush=RequirementStatus.UNKNOWN,
            provenance=Provenance.PUBLISHED_EXPERIMENTAL,
            notes="Low TCPD fractions remain liquid (US4751337/US4703098). High TCPD viscosity UNKNOWN.",
        ),
        MaterialScenario(
            name="C_enhanced_crosslink_pDCPD",
            Tg_C_lo=191.0,
            Tg_C_hi=216.0,
            sigma_RT_MPa=None,
            modulus_note="Zhan 2024 sequential ROMP+radical. Not compressive strength at 150 C.",
            viscosity_150C="Same DCPD delivery; extra peroxide cure is post-ROMP",
            status_150C_crush=RequirementStatus.UNKNOWN,
            provenance=Provenance.PUBLISHED_EXPERIMENTAL,
            notes="Tg above 150 C is experimentally demonstrated in related networks, not PhaseForge particles.",
        ),
    ]
