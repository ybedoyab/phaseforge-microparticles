"""Arrhenius-type delayed ROMP kinetics for DCPD-rich droplets.

Primary output: t_transform(T, catalyst, inhibitor) and whether it lies
in the 25-75 min window.

Gel time is NOT treated as complete solidification. Two conversion
thresholds are used:
  alpha_gel   ~ 0.4  (Winter-Chambon / G'-G'' crossover analogue)
  alpha_solid ~ 0.80 (load-bearing network; model criterion, not a measured
                      PhaseForge conversion)

Calibration points are published gel times. Extrapolation to 150 C is
far outside the 40-80 C experimental window and is tagged accordingly.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from phaseforge.ht_catalyst import CATALYST_MO_LATENT, evaluate_ht_family
from phaseforge.provenance import (
    EvidenceClass,
    Provenance,
    Quantity,
    RequirementStatus,
    ResultRecord,
    combine_provenance,
)
from phaseforge.requirements import classify_transform_time_s
from phaseforge.units import R_GAS, C_to_K

CATALYST_RU_PHOSPHITE = "ru_phosphite"

# Madbouly et al., ACS Omega 2025, 10, 63359-63368. Open via ACS / PMC.
# tgel = 19.7 min at 55 C, 0.04 wt% Grubbs II. Ea = 79.3 ± 1.0 kJ/mol.
EA_J_MOL = Quantity(
    79300.0,
    "J/mol",
    Provenance.PUBLISHED_EXPERIMENTAL,
    source_id="MADBOULY2025_ACS_OMEGA",
    notes="Ea independent of Grubbs concentration in 0.04-0.30 wt% range.",
    uncertainty_abs=1000.0,
    temperature_C=None,
)
TGEL_REF_S = Quantity(
    19.7 * 60.0,
    "s",
    Provenance.PUBLISHED_EXPERIMENTAL,
    source_id="MADBOULY2025_ACS_OMEGA",
    temperature_C=55.0,
    notes="G'/G'' crossover gel time at 0.04 wt% GC, 55 C, 1 rad/s.",
)
T_REF_C = 55.0
C_REF = 1.0  # catalyst_relative = 1 corresponds to 0.04 wt% GC

# Hu, Zhu, Qu, Robisson, J. Pet. Sci. Eng. 2019 (online 2018): TPP latency.
# 10 g DCPD + 200 uL catalyst: tgel 5.98 min (no TPP), 38.5 min (10 uL TPP) at 50 C.
HU_TGEL_NO_INH_S = Quantity(
    5.98 * 60.0,
    "s",
    Provenance.PUBLISHED_EXPERIMENTAL,
    source_id="HU2018_JPSE",
    temperature_C=50.0,
)
HU_TGEL_INH_S = Quantity(
    38.5 * 60.0,
    "s",
    Provenance.PUBLISHED_EXPERIMENTAL,
    source_id="HU2018_JPSE",
    temperature_C=50.0,
    notes="10 uL tri-isopropyl phosphite in 10 g DCPD.",
)
HU_TGEL_80C_S = Quantity(
    2.0 * 60.0,
    "s",
    Provenance.PUBLISHED_EXPERIMENTAL,
    source_id="HU2018_JPSE",
    temperature_C=80.0,
    notes="Same inhibited formulation; gel time ~2 min at 80 C.",
)

# Patent US11377580B2: time-to-peak, NOT gel time.
PATENT_TTP_30C_S = Quantity(
    60.0 * 60.0,
    "s",
    Provenance.PUBLISHED_EXPERIMENTAL,
    source_id="US11377580B2",
    temperature_C=30.0,
    notes="Time to peak exotherm ~1 h at 30 C with 28 ppm mol M2 / 0.02 wt%. Not complete cure.",
)
PATENT_TTP_50C_S = Quantity(
    10.0 * 60.0,
    "s",
    Provenance.PUBLISHED_EXPERIMENTAL,
    source_id="US11377580B2",
    temperature_C=50.0,
    notes="TtP ~10 min at 50 C; peak temperature ~160 C (bulk exotherm).",
)

ALPHA_GEL = 0.40
ALPHA_SOLID = 0.80
# Approximate ratio t_solid / t_gel for first-order/autocatalytic ROMP after gel.
# Kessler 2002 showed Ea rising after alpha~0.6; solidification is slower than gel.
T_SOLID_OVER_GEL = Quantity(
    1.8,
    "dimensionless",
    Provenance.ASSUMED_FOR_SENSITIVITY,
    notes="t_solid ~ 1.8 t_gel. Not a measured PhaseForge conversion time.",
)

# Heat of ROMP (used by thermal model; stored here for one source of truth).
# Kessler & White, J Polym Sci A, 2002 and subsequent DSC literature commonly
# report ~350-500 J/g. We use 400 J/g as a mid literature value with wide UQ.
HR_J_KG = Quantity(
    4.0e5,
    "J/kg",
    Provenance.ASSUMED_FOR_SENSITIVITY,
    source_id="KESSLER2002_JPSA",
    notes="Order-of-magnitude heat of DCPD ROMP; not digitized from a specific DSC table in this repo.",
)


@dataclass(frozen=True, slots=True)
class KineticsInputs:
    temperature_C: float
    catalyst_relative: float = 1.0
    inhibitor_index: float = 0.0  # 0..1
    inhibitor_factor_max: float = 12.0
    Ea_J_mol: float = EA_J_MOL.value
    tgel_ref_s: float = TGEL_REF_S.value
    catalyst_order_n: float = 1.4
    latency_extra: float = 1.0
    t_solid_over_gel: float = T_SOLID_OVER_GEL.value
    alpha_gel: float = ALPHA_GEL
    alpha_solid: float = ALPHA_SOLID
    catalyst_family: str = CATALYST_RU_PHOSPHITE


@dataclass(frozen=True, slots=True)
class KineticsResult:
    t_gel_s: float
    t_solid_s: float
    t_transform_s: float
    t_transform_min: float
    status: RequirementStatus
    extrapolation_flag: str
    provenance: Provenance
    notes: str
    alpha_gel: float
    alpha_solid: float

    def as_record(self) -> ResultRecord:
        return ResultRecord(
            name="t_transform",
            value=self.t_transform_s,
            unit="s",
            provenance=self.provenance,
            status=self.status,
            evidence_class=EvidenceClass.COMPUTATIONALLY_PREDICTED,
            notes=self.notes,
            extra={
                "t_gel_s": self.t_gel_s,
                "t_solid_s": self.t_solid_s,
                "t_transform_min": self.t_transform_min,
                "extrapolation_flag": self.extrapolation_flag,
            },
        )


def inhibitor_multiplier(inhibitor_index: float, inhibitor_factor_max: float) -> float:
    """Linear interpolation: 0 -> 1x (uninhibited), 1 -> inhibitor_factor_max.

    Calibrated in magnitude to Hu 2018 phosphite delay at 50 C (factor ~6.4
    at a specific TPP loading). The index is an engineering parameter, not a
    molar recipe.
    """
    x = min(max(inhibitor_index, 0.0), 1.0)
    return 1.0 + x * (inhibitor_factor_max - 1.0)


def arrhenius_tgel_s(inp: KineticsInputs) -> float:
    """t_gel(T) = t_ref * (C_ref/C)^n * exp(Ea/R (1/T - 1/Tref)) * inh * latency_extra."""
    T = C_to_K(inp.temperature_C)
    Tref = C_to_K(T_REF_C)
    c = max(inp.catalyst_relative, 1.0e-6)
    cat = (C_REF / c) ** inp.catalyst_order_n
    arrh = np.exp(inp.Ea_J_mol / R_GAS * (1.0 / T - 1.0 / Tref))
    inh = inhibitor_multiplier(inp.inhibitor_index, inp.inhibitor_factor_max)
    return float(inp.tgel_ref_s * cat * arrh * inh * max(inp.latency_extra, 1.0e-12))


def conversion_profile(
    t_s: np.ndarray,
    t_gel_s: float,
    alpha_gel: float = ALPHA_GEL,
    n: float = 1.2,
) -> np.ndarray:
    """Phenomenological conversion. First-order-like with gel at alpha_gel.

    dα/dt = k (1-α)^n with k chosen so α(t_gel)=alpha_gel.
    Closed form for n!=1: (1-α)^{1-n} = 1 - (1-n) k t
    """
    t = np.asarray(t_s, dtype=float)
    # Choose k so that alpha(t_gel) = alpha_gel for nth-order: 
    # k = [1 - (1-alpha_gel)^{1-n}] / [(1-n) t_gel]  if n != 1
    if abs(n - 1.0) < 1e-9:
        k = -np.log(1.0 - alpha_gel) / max(t_gel_s, 1e-12)
        alpha = 1.0 - np.exp(-k * t)
    else:
        k = (1.0 - (1.0 - alpha_gel) ** (1.0 - n)) / ((1.0 - n) * max(t_gel_s, 1e-12))
        inner = 1.0 - (1.0 - n) * k * t
        inner = np.clip(inner, 0.0, None)
        alpha = 1.0 - inner ** (1.0 / (1.0 - n))
    return np.clip(alpha, 0.0, 1.0)


def heat_generation_W(
    alpha: float,
    dadt: float,
    mass_kg: float,
    Hr_J_kg: float = HR_J_KG.value,
) -> float:
    """q = m * Hr * dα/dt."""
    return mass_kg * Hr_J_kg * dadt


def extrapolation_flag(temperature_C: float) -> str:
    if temperature_C <= 60.0:
        return "inside_calibration_window_40_60C"
    if temperature_C <= 80.0:
        return "near_calibration_Hu2018_80C"
    if temperature_C <= 110.0:
        return "moderate_extrapolation"
    return "severe_extrapolation_beyond_published_isothermal_gel_times"


def evaluate_kinetics(inp: KineticsInputs) -> KineticsResult:
    if inp.catalyst_family == CATALYST_MO_LATENT:
        ht = evaluate_ht_family()
        return KineticsResult(
            t_gel_s=float("nan"),
            t_solid_s=float("nan"),
            t_transform_s=float("nan"),
            t_transform_min=float("nan"),
            status=RequirementStatus.UNKNOWN,
            extrapolation_flag="dsc_onset_not_isothermal_latency",
            provenance=ht.provenance,
            notes=ht.notes,
            alpha_gel=inp.alpha_gel,
            alpha_solid=inp.alpha_solid,
        )
    t_gel = arrhenius_tgel_s(inp)
    t_solid = t_gel * inp.t_solid_over_gel
    t_transform = t_solid  # load-bearing criterion
    flag = extrapolation_flag(inp.temperature_C)
    # Severe T-extrapolation: never PASS. If the Arrhenius value is far outside
    # the window, call FAIL for published-chemistry analogues; if it lands inside
    # only by extrapolation, call UNKNOWN.
    if flag == "severe_extrapolation_beyond_published_isothermal_gel_times" and inp.latency_extra <= 1.0 + 1e-12:
        if t_transform < 15.0 * 60.0 or t_transform > 85.0 * 60.0:
            status = RequirementStatus.FAIL
        else:
            status = RequirementStatus.UNKNOWN
    else:
        status = classify_transform_time_s(t_transform, unknown=False)
    tags = [
        Provenance.PUBLISHED_EXPERIMENTAL,
        Provenance.FITTED,
        Provenance.MODEL_PREDICTION,
    ]
    if inp.latency_extra > 1.0 + 1e-9:
        tags.append(Provenance.ASSUMED_FOR_SENSITIVITY)
    if inp.t_solid_over_gel != 1.0:
        tags.append(Provenance.ASSUMED_FOR_SENSITIVITY)
    notes = (
        f"t_gel={t_gel / 60.0:.3g} min; t_solid={t_solid / 60.0:.3g} min; "
        f"flag={flag}; latency_extra={inp.latency_extra:g}. "
        "t_transform uses t_solid, not time-to-peak."
    )
    return KineticsResult(
        t_gel_s=t_gel,
        t_solid_s=t_solid,
        t_transform_s=t_transform,
        t_transform_min=t_transform / 60.0,
        status=status,
        extrapolation_flag=flag,
        provenance=combine_provenance(tags),
        notes=notes,
        alpha_gel=inp.alpha_gel,
        alpha_solid=inp.alpha_solid,
    )


def feasible_activation_map(
    temperatures_C: np.ndarray,
    inhibitor_index: np.ndarray,
    *,
    catalyst_relative: float = 1.0,
    inhibitor_factor_max: float = 12.0,
    latency_extra: float = 1.0,
) -> np.ndarray:
    """Return t_transform in minutes on a T x inhibitor grid."""
    T = np.asarray(temperatures_C, dtype=float)
    inh_grid = np.asarray(inhibitor_index, dtype=float)
    out = np.empty((inh_grid.size, T.size), dtype=float)
    for i, inh in enumerate(inh_grid):
        for j, tC in enumerate(T):
            r = evaluate_kinetics(
                KineticsInputs(
                    temperature_C=float(tC),
                    catalyst_relative=catalyst_relative,
                    inhibitor_index=float(inh),
                    inhibitor_factor_max=inhibitor_factor_max,
                    latency_extra=latency_extra,
                )
            )
            out[i, j] = r.t_transform_min
    return out


def validation_points() -> list[dict[str, float | str]]:
    """Published gel times used for sanity checks (not time-to-peak)."""
    return [
        {
            "source_id": "MADBOULY2025_ACS_OMEGA",
            "T_C": 55.0,
            "catalyst_relative": 1.0,
            "inhibitor_index": 0.0,
            "t_obs_min": 19.7,
            "quantity": "t_gel",
            "provenance": Provenance.PUBLISHED_EXPERIMENTAL.value,
        },
        {
            "source_id": "MADBOULY2025_ACS_OMEGA",
            "T_C": 50.0,
            "catalyst_relative": 1.0,
            "inhibitor_index": 0.0,
            "t_obs_min": 70.0,
            "quantity": "t_gel",
            "provenance": Provenance.PUBLISHED_EXPERIMENTAL.value,
        },
        {
            "source_id": "MADBOULY2025_ACS_OMEGA",
            "T_C": 50.0,
            "catalyst_relative": 3.0,  # 0.12/0.04
            "inhibitor_index": 0.0,
            "t_obs_min": 10.0,
            "quantity": "t_gel",
            "provenance": Provenance.PUBLISHED_EXPERIMENTAL.value,
        },
        {
            "source_id": "MADBOULY2025_ACS_OMEGA",
            "T_C": 40.0,
            "catalyst_relative": 3.0,
            "inhibitor_index": 0.0,
            "t_obs_min": 50.0,
            "quantity": "t_gel",
            "provenance": Provenance.PUBLISHED_EXPERIMENTAL.value,
        },
        {
            "source_id": "MADBOULY2025_ACS_OMEGA",
            "T_C": 60.0,
            "catalyst_relative": 3.0,
            "inhibitor_index": 0.0,
            "t_obs_min": 5.0,
            "quantity": "t_gel",
            "provenance": Provenance.PUBLISHED_EXPERIMENTAL.value,
        },
        {
            "source_id": "HU2018_JPSE",
            "T_C": 50.0,
            "catalyst_relative": 1.0,
            "inhibitor_index": 1.0,
            "inhibitor_factor_max": 6.44,
            "t_obs_min": 38.5,
            "quantity": "t_gel",
            "provenance": Provenance.PUBLISHED_EXPERIMENTAL.value,
            "notes": "Relative to Hu uninhibited 5.98 min, not Madbouly reference.",
        },
    ]


def predicted_vs_observed() -> list[dict[str, float | str]]:
    rows = []
    for p in validation_points():
        if p["source_id"] == "HU2018_JPSE":
            # Separate branch: Hu's uninhibited 5.98 min at 50 C is a different
            # catalyst loading than Madbouly 0.04 wt%. Report factor only.
            pred = 5.98 * inhibitor_multiplier(1.0, 6.44)
            rows.append(
                {
                    **p,
                    "t_pred_min": pred,
                    "rel_error": (pred - float(p["t_obs_min"])) / float(p["t_obs_min"]),
                    "notes": "Hu branch uses published 5.98 min baseline, not Madbouly A-factor.",
                }
            )
            continue
        r = evaluate_kinetics(
            KineticsInputs(
                temperature_C=float(p["T_C"]),
                catalyst_relative=float(p["catalyst_relative"]),
                inhibitor_index=float(p["inhibitor_index"]),
            )
        )
        pred = r.t_gel_s / 60.0
        obs = float(p["t_obs_min"])
        rows.append({**p, "t_pred_min": pred, "rel_error": (pred - obs) / obs})
    return rows
