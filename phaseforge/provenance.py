"""Provenance tracking for every numerical input and significant result.

Every value used in PhaseForge models must carry exactly one provenance tag.
UNKNOWN results must never be recast as PASS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Provenance(StrEnum):
    """Allowed provenance classes. Do not invent additional labels."""

    PUBLISHED_EXPERIMENTAL = "PUBLISHED_EXPERIMENTAL"
    DIGITIZED_FROM_PUBLICATION = "DIGITIZED_FROM_PUBLICATION"
    MANUFACTURER_DATA = "MANUFACTURER_DATA"
    ASSUMED_FOR_SENSITIVITY = "ASSUMED_FOR_SENSITIVITY"
    FITTED = "FITTED"
    MODEL_PREDICTION = "MODEL_PREDICTION"


class RequirementStatus(StrEnum):
    PASS = "PASS"
    MARGINAL = "MARGINAL"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class EvidenceClass(StrEnum):
    """How a claim is supported. Distinct from numerical provenance."""

    PRIOR_LITERATURE_EXPERIMENTAL = "prior_literature_experimental"
    ANALYTICALLY_CALCULATED = "analytically_calculated"
    COMPUTATIONALLY_PREDICTED = "computationally_predicted"
    UNRESOLVED_NEEDS_LAB = "unresolved_needs_lab"


@dataclass(frozen=True, slots=True)
class Quantity:
    """A scalar with unit, provenance, and optional source identifier."""

    value: float
    unit: str
    provenance: Provenance
    source_id: str | None = None
    notes: str = ""
    uncertainty_abs: float | None = None
    temperature_C: float | None = None
    pressure_MPa: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "unit": self.unit,
            "provenance": self.provenance.value,
            "source_id": self.source_id,
            "notes": self.notes,
            "uncertainty_abs": self.uncertainty_abs,
            "temperature_C": self.temperature_C,
            "pressure_MPa": self.pressure_MPa,
        }


@dataclass
class ResultRecord:
    """A model output that must retain provenance of its inputs."""

    name: str
    value: float | None
    unit: str
    provenance: Provenance
    status: RequirementStatus | None = None
    evidence_class: EvidenceClass = EvidenceClass.COMPUTATIONALLY_PREDICTED
    inputs: tuple[str, ...] = ()
    notes: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "provenance": self.provenance.value,
            "status": None if self.status is None else self.status.value,
            "evidence_class": self.evidence_class.value,
            "inputs": list(self.inputs),
            "notes": self.notes,
            "extra": self.extra,
        }


def combine_provenance(tags: list[Provenance]) -> Provenance:
    """Worst-case combination: fitted/assumed dominate published sources."""
    if not tags:
        return Provenance.ASSUMED_FOR_SENSITIVITY
    priority = [
        Provenance.ASSUMED_FOR_SENSITIVITY,
        Provenance.FITTED,
        Provenance.MODEL_PREDICTION,
        Provenance.DIGITIZED_FROM_PUBLICATION,
        Provenance.MANUFACTURER_DATA,
        Provenance.PUBLISHED_EXPERIMENTAL,
    ]
    for p in priority:
        if p in tags:
            return p
    return tags[0]


def never_upgrade_unknown(status: RequirementStatus) -> RequirementStatus:
    """Guard: UNKNOWN must remain UNKNOWN."""
    return status
