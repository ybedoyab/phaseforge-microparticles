"""Four PhaseForge candidate families. Statuses are never mixed into one global PASS.

1. PhaseForge-RuP — Ru/Grubbs + phosphite (control). 150 C kinetics FAIL.
2. PhaseForge-HT-Thermal — Mo latent; stable ~150 C; trigger at exactly 150 C UNKNOWN.
3. PhaseForge-ChemGate — primary high-T architecture (chemical gate). UNKNOWN / plausible pathway.
4. PhaseForge-ChemGate-Acid — secondary acid gate. UNKNOWN; no 150 C evidence.
"""

from __future__ import annotations

from dataclasses import dataclass

from phaseforge.chemgate import (
    FAMILY_CHEMGATE,
    FAMILY_CHEMGATE_ACID,
    ChemGateInputs,
    evaluate_chemgate,
)
from phaseforge.coupled import OperatingPoint, evaluate_point
from phaseforge.ht_catalyst import evaluate_ht_family
from phaseforge.kinetics import CATALYST_RU_PHOSPHITE
from phaseforge.provenance import RequirementStatus

FAMILY_RUP = "PhaseForge-RuP"
FAMILY_HT_THERMAL = "PhaseForge-HT-Thermal"


@dataclass
class FamilyCard:
    family: str
    overall_150C: RequirementStatus
    transport_latency_150C: str
    activation_at_150C: str
    mechanics_150C: str
    pathway: str
    notes: str

    def as_dict(self) -> dict:
        return {
            "family": self.family,
            "overall_150C": self.overall_150C.value,
            "transport_latency_150C": self.transport_latency_150C,
            "activation_at_150C": self.activation_at_150C,
            "mechanics_150C": self.mechanics_150C,
            "pathway": self.pathway,
            "notes": self.notes,
        }


def evaluate_rup() -> FamilyCard:
    r = evaluate_point(
        OperatingPoint(
            temperature_C=150.0,
            phi=0.15,
            inhibitor_index=0.95,
            latency_extra=1.0,
            catalyst_family=CATALYST_RU_PHOSPHITE,
            label="rup_150",
        )
    )
    return FamilyCard(
        family=FAMILY_RUP,
        overall_150C=RequirementStatus.FAIL,
        transport_latency_150C="FAIL (Arrhenius t_solid ~1.6 min)",
        activation_at_150C="too fast; not a usable hold",
        mechanics_150C="UNKNOWN (near conventional pDCPD Tg)",
        pathway="NEGATIVE_CONTROL",
        notes=r.notes,
    )


def evaluate_ht_thermal() -> FamilyCard:
    ht = evaluate_ht_family()
    return FamilyCard(
        family=FAMILY_HT_THERMAL,
        overall_150C=RequirementStatus.UNKNOWN,
        transport_latency_150C=(
            "SUPPORTED analogue: Kordes 2024 hexacoordinated Mo NHC "
            "does not polymerize DCPD up to ~150 C (long pot life)."
        ),
        activation_at_150C=(
            "UNKNOWN at exactly 150 C. Thermal activation reported above 150 C; "
            "full conversion on heating to ~175 C (Kordes 2024). DSC onset ≠ 25-75 min hold."
        ),
        mechanics_150C="UNKNOWN (no 150 C particle crush)",
        pathway="UNKNOWN",
        notes=ht.notes,
    )


def evaluate_chemgate_family() -> FamilyCard:
    cg = evaluate_chemgate(
        ChemGateInputs(diameter_um=270.0, temperature_C=150.0, D_mode="lee_ambient")
    )
    return FamilyCard(
        family=FAMILY_CHEMGATE,
        overall_150C=RequirementStatus.UNKNOWN,
        transport_latency_150C=(
            "SUPPORTED analogue: D899 remains dormant through ~200 C frontal polymerization "
            "until Cu(I) (Lee 2024). Requires delayed activator contact so droplets are not "
            "exposed during transport."
        ),
        activation_at_150C=(
            f"MODELLED: t_transform approximately {cg.t_transform_min:.0f} min at 270 um "
            f"with delayed contact + Lee ambient D ({cg.pathway}). "
            "Aqueous-to-organic activation demonstrated by Lee 2025 (ambient). "
            "25-75 min at 150 C is NOT experimentally demonstrated."
        ),
        mechanics_150C="UNKNOWN crush; high-Tg pDCPD-family analogues exist (Zhan; TCPD patents)",
        pathway=cg.pathway,
        notes=cg.notes,
    )


def evaluate_chemgate_acid() -> FamilyCard:
    cg = evaluate_chemgate(
        ChemGateInputs(diameter_um=270.0, temperature_C=150.0),
        family=FAMILY_CHEMGATE_ACID,
    )
    return FamilyCard(
        family=FAMILY_CHEMGATE_ACID,
        overall_150C=RequirementStatus.UNKNOWN,
        transport_latency_150C=(
            "Samec/Keitz/Grubbs 2010: picolinate Ru latent until HCl; inactive even at "
            "elevated T without acid (not shown at 150 C)."
        ),
        activation_at_150C="UNKNOWN; no 150 C isothermal acid-gate window retrieved.",
        mechanics_150C="UNKNOWN",
        pathway="EXPLORATORY",
        notes=cg.notes + " Acid-gate is secondary. Do not claim it meets 150 C.",
    )


def all_family_cards() -> list[FamilyCard]:
    return [
        evaluate_rup(),
        evaluate_ht_thermal(),
        evaluate_chemgate_family(),
        evaluate_chemgate_acid(),
    ]
