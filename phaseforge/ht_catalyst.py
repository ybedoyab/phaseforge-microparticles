"""PhaseForge-HT: thermally latent molybdenum ROMP precatalysts.

Separate candidate family from Ru/Grubbs + phosphite. Published DSC onset
temperatures are NOT equivalent to 25-75 min isothermal latency at 150 C.

Literature (abstracts retrieved; isothermal gel times at 150 C were not
retrieved):

* Elser et al., Chem. Eur. J. 2018, DOI 10.1002/chem.201801862
  T_onset approximately 65-140 C; T_exo,max approximately 98-183 C.
* Momin / Musso / Frey / Buchmeiser, Organometallics 2021,
  DOI 10.1021/acs.organomet.0c00740
  T_onset approximately 52-142 C; T_exo,max approximately 99-174 C.

Status is UNKNOWN unless sufficient isothermal evidence exists.
This module does not invent isothermal 25-75 min times from DSC ramps.
"""

from __future__ import annotations

from dataclasses import dataclass

from phaseforge.provenance import EvidenceClass, Provenance, RequirementStatus, ResultRecord

FAMILY_NAME = "PhaseForge-HT"
CATALYST_MO_LATENT = "mo_latent"

# Combined published DSC windows (two papers; overlapping but not identical).
ELSER_TONSET_C = (65.0, 140.0)
ELSER_TEXO_MAX_C = (98.0, 183.0)
MOMIN_TONSET_C = (52.0, 142.0)
MOMIN_TEXO_MAX_C = (99.0, 174.0)


@dataclass(frozen=True, slots=True)
class HTCatalystResult:
    family: str
    status: RequirementStatus
    T_onset_span_C: tuple[float, float]
    T_exo_max_span_C: tuple[float, float]
    isothermal_150C_evidence: bool
    notes: str
    provenance: Provenance

    def as_record(self) -> ResultRecord:
        return ResultRecord(
            name="phaseforge_ht_latency",
            value=None,
            unit="degC_onset_span",
            provenance=self.provenance,
            status=self.status,
            evidence_class=EvidenceClass.PRIOR_LITERATURE_EXPERIMENTAL,
            notes=self.notes,
            extra={
                "T_onset_span_C": list(self.T_onset_span_C),
                "T_exo_max_span_C": list(self.T_exo_max_span_C),
                "isothermal_150C_evidence": self.isothermal_150C_evidence,
            },
        )

    def as_dict(self) -> dict:
        return {
            "family": self.family,
            "status": self.status.value,
            "T_onset_min_C": self.T_onset_span_C[0],
            "T_onset_max_C": self.T_onset_span_C[1],
            "T_exo_max_min_C": self.T_exo_max_span_C[0],
            "T_exo_max_max_C": self.T_exo_max_span_C[1],
            "isothermal_150C_evidence": self.isothermal_150C_evidence,
            "notes": self.notes,
        }


def evaluate_ht_family() -> HTCatalystResult:
    """Conservative literature map. Never PASS the 25-75 min / 150 C window."""
    onset = (min(ELSER_TONSET_C[0], MOMIN_TONSET_C[0]), max(ELSER_TONSET_C[1], MOMIN_TONSET_C[1]))
    texo = (min(ELSER_TEXO_MAX_C[0], MOMIN_TEXO_MAX_C[0]), max(ELSER_TEXO_MAX_C[1], MOMIN_TEXO_MAX_C[1]))
    notes = (
        f"{FAMILY_NAME} uses published Mo imido alkylidene NHC precatalysts. "
        f"DSC T_onset approximately {onset[0]:.0f}-{onset[1]:.0f} C "
        f"(Elser 2018 {ELSER_TONSET_C[0]:.0f}-{ELSER_TONSET_C[1]:.0f} C; "
        f"Momin 2021 {MOMIN_TONSET_C[0]:.0f}-{MOMIN_TONSET_C[1]:.0f} C). "
        f"Exotherm maxima approximately {texo[0]:.0f}-{texo[1]:.0f} C "
        f"(Elser to {ELSER_TEXO_MAX_C[1]:.0f} C; Momin to {MOMIN_TEXO_MAX_C[1]:.0f} C). "
        "A DSC heating-ramp onset is not an isothermal 25-75 min latency at 150 C. "
        "No retrieved isothermal hold at 150 C for these complexes in this repository. "
        "Status remains UNKNOWN: a credible pathway toward the upper-temperature "
        "requirement, not a fabricated PASS."
    )
    return HTCatalystResult(
        family=FAMILY_NAME,
        status=RequirementStatus.UNKNOWN,
        T_onset_span_C=onset,
        T_exo_max_span_C=texo,
        isothermal_150C_evidence=False,
        notes=notes,
        provenance=Provenance.PUBLISHED_EXPERIMENTAL,
    )
