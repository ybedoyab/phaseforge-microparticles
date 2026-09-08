"""Coupled feasibility envelope for PhaseForge operating points.

Evaluates simultaneously:
  1. viscosity <= 10 cP
  2. transformation time 25-75 min
  3. particle diameter 70-600 um
  4. mechanical safety factor >= 1
  5. agglomeration / coalescence risk (heuristic; cannot independently PASS)
  6. open flow pathways (geometric + analytical k; conductivity unvalidated)
  7. acceptable thermal behavior

UNKNOWN is never converted into PASS.
Heuristic low agglomeration risk without direct validation is MARGINAL, not PASS.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from phaseforge.droplets import DropletInputs, DropletResult, evaluate_droplets
from phaseforge.ht_catalyst import CATALYST_MO_LATENT, evaluate_ht_family
from phaseforge.kinetics import (
    CATALYST_RU_PHOSPHITE,
    KineticsInputs,
    KineticsResult,
    evaluate_kinetics,
)
from phaseforge.mechanics import MechanicsInputs, MechanicsResult, evaluate_mechanics
from phaseforge.permeability import PermeabilityInputs, PermeabilityResult, evaluate_permeability
from phaseforge.provenance import RequirementStatus
from phaseforge.requirements import worst_status
from phaseforge.rounding import round_cP, round_krel, round_sf, round_um


def _json_float(x: float) -> float | None:
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return x
from phaseforge.thermal import ThermalInputs, ThermalResult, simulate_droplet
from phaseforge.viscosity import ViscosityInputs, ViscosityResult, evaluate_viscosity


@dataclass
class OperatingPoint:
    temperature_C: float
    phi: float
    catalyst_relative: float = 1.0
    inhibitor_index: float = 0.6
    inhibitor_factor_max: float = 12.0
    latency_extra: float = 1.0
    sigma_N_m: float = 0.004
    shear_rate_1_s: float = 800.0
    velocity_m_s: float = 1.5
    length_m: float = 0.05
    Tg_C: float = 155.0
    sigma_c_RT_MPa: float = 78.0
    packing_fraction: float = 0.60
    shrinkage: float = 0.03
    hinze_C: float = 0.55
    coalescence_scale: float = 1.0
    settled: bool = False
    label: str = "point"
    catalyst_family: str = CATALYST_RU_PHOSPHITE
    agglomeration_validated: bool = False


@dataclass
class CoupledResult:
    label: str
    overall: RequirementStatus
    core_overall: RequirementStatus
    viscosity: ViscosityResult
    kinetics: KineticsResult
    droplets: DropletResult
    mechanics: MechanicsResult
    permeability: PermeabilityResult
    thermal: ThermalResult
    agglomeration: RequirementStatus
    components: dict[str, str] = field(default_factory=dict)
    notes: str = ""
    catalyst_family: str = CATALYST_RU_PHOSPHITE

    def as_dict(self) -> dict[str, Any]:
        tmin = self.kinetics.t_transform_min
        tgel = self.kinetics.t_gel_s / 60.0 if math.isfinite(self.kinetics.t_gel_s) else float("nan")
        return {
            "label": self.label,
            "catalyst_family": self.catalyst_family,
            "overall": self.overall.value,
            "core_overall": self.core_overall.value,
            "mu_eff_cP": self.viscosity.mu_eff_cP,
            "t_transform_min": _json_float(tmin),
            "t_gel_min": _json_float(tgel),
            "d_particle_um": self.droplets.d_particle_um,
            "d_particle_um_nominal": self.droplets.d_particle_um_nominal,
            "SF_mech": self.mechanics.SF,
            "porosity": self.permeability.porosity,
            "k_rel": self.permeability.k_rel,
            "k_rel_note": "relative to assumed k_open; not measured fracture conductivity",
            "dT_max_K": _json_float(self.thermal.dT_max_K),
            "coalescence_risk": self.droplets.coalescence_risk,
            "coalescence_risk_note": "ASSUMED_FOR_SENSITIVITY heuristic; not a hard agglomeration PASS",
            "status_viscosity": self.viscosity.status.value,
            "status_kinetics": self.kinetics.status.value,
            "status_diameter": self.droplets.status.value,
            "status_mechanics": self.mechanics.status.value,
            "status_mechanics_moderate": self.mechanics.status_moderate.value,
            "status_mechanics_98C_analogue": self.mechanics.status_98C_analogue.value,
            "status_mechanics_150C": self.mechanics.status_150C.value,
            "status_permeability": self.permeability.status.value,
            "status_thermal": self.thermal.status.value,
            "status_agglomeration": self.agglomeration.value,
            "geometric_connectivity": self.permeability.geometric_connectivity,
            "conductivity_under_closure": self.permeability.conductivity_under_closure,
            "kinetics_flag": self.kinetics.extrapolation_flag,
            "mechanics_unknown": self.mechanics.unknown_high_T,
            "reviewer_facing": {
                "mu_eff_cP": round_cP(self.viscosity.mu_eff_cP),
                "d_particle_um": round_um(self.droplets.d_particle_um),
                "SF_mech": round_sf(self.mechanics.SF),
                "k_rel": round_krel(self.permeability.k_rel),
            },
            "notes": self.notes,
        }


def _agglomeration_status(
    risk: float,
    discrete: bool,
    temperature_C: float,
    *,
    validated: bool = False,
) -> RequirementStatus:
    """Heuristic coalescence_risk_score cannot independently generate a hard PASS.

    measured/validated evidence may PASS
    heuristic low risk without direct validation = MARGINAL
    uncertain high-temperature sticky cure = UNKNOWN
    non-discrete / bulk = FAIL
    """
    if not discrete:
        return RequirementStatus.FAIL
    if validated:
        if risk <= 0.35:
            return RequirementStatus.PASS
        if risk <= 0.60:
            return RequirementStatus.MARGINAL
        return RequirementStatus.FAIL
    if temperature_C >= 110.0:
        return RequirementStatus.UNKNOWN
    if risk <= 0.60:
        return RequirementStatus.MARGINAL
    return RequirementStatus.FAIL


def evaluate_point(pt: OperatingPoint) -> CoupledResult:
    visc = evaluate_viscosity(ViscosityInputs(pt.temperature_C, pt.phi))
    kin = evaluate_kinetics(
        KineticsInputs(
            temperature_C=pt.temperature_C,
            catalyst_relative=pt.catalyst_relative,
            inhibitor_index=pt.inhibitor_index,
            inhibitor_factor_max=pt.inhibitor_factor_max,
            latency_extra=pt.latency_extra,
            catalyst_family=pt.catalyst_family,
        )
    )
    drop = evaluate_droplets(
        DropletInputs(
            temperature_C=pt.temperature_C,
            sigma_N_m=pt.sigma_N_m,
            shear_rate_1_s=pt.shear_rate_1_s,
            velocity_m_s=pt.velocity_m_s,
            length_m=pt.length_m,
            phi=pt.phi,
            hinze_C=pt.hinze_C,
            shrinkage=pt.shrinkage,
            coalescence_scale=pt.coalescence_scale,
        )
    )
    mech = evaluate_mechanics(
        MechanicsInputs(
            temperature_C=pt.temperature_C,
            Tg_C=pt.Tg_C,
            sigma_c_RT_MPa=pt.sigma_c_RT_MPa,
        )
    )
    perm = evaluate_permeability(
        PermeabilityInputs(
            d_m=drop.d_particle_m,
            phi_particles=pt.phi,
            packing_fraction=pt.packing_fraction,
            settled=pt.settled,
        )
    )
    therm = simulate_droplet(
        ThermalInputs(
            diameter_m=drop.d_particle_m,
            T_cont_C=pt.temperature_C,
            kinetics=KineticsInputs(
                temperature_C=pt.temperature_C,
                catalyst_relative=pt.catalyst_relative,
                inhibitor_index=pt.inhibitor_index,
                inhibitor_factor_max=pt.inhibitor_factor_max,
                latency_extra=pt.latency_extra,
                catalyst_family=pt.catalyst_family,
            ),
            t_end_s=min(max(kin.t_solid_s * 1.2 if math.isfinite(kin.t_solid_s) else 1800.0, 300.0), 1800.0),
        )
    )
    discrete = pt.phi < 0.55
    agg = _agglomeration_status(
        drop.coalescence_risk,
        discrete,
        pt.temperature_C,
        validated=pt.agglomeration_validated,
    )
    bulk_gel = kin.status == RequirementStatus.FAIL and pt.phi > 0.45
    if not discrete or bulk_gel:
        discrete_status = RequirementStatus.FAIL
    else:
        discrete_status = RequirementStatus.PASS

    components = {
        "viscosity": visc.status.value,
        "transform_time": kin.status.value,
        "diameter": drop.status.value,
        "mechanics": mech.status.value,
        "agglomeration": agg.value,
        "open_pathways": perm.status.value,
        "thermal": therm.status.value,
        "discrete_particles": discrete_status.value,
    }
    core_overall = worst_status(
        [
            visc.status,
            kin.status,
            drop.status,
            mech.status,
            therm.status,
            discrete_status,
        ]
    )
    overall = worst_status(
        [
            core_overall,
            agg,
            perm.status,
        ]
    )
    notes = (
        f"T={pt.temperature_C} C, φ={pt.phi}, cat={pt.catalyst_relative}, "
        f"inh={pt.inhibitor_index}, latency_extra={pt.latency_extra}, "
        f"family={pt.catalyst_family}. "
        f"UNKNOWN never upgraded. kinetics_flag={kin.extrapolation_flag}. "
        "Agglomeration heuristic cannot PASS without validation. "
        "k_rel is not measured fracture conductivity."
    )
    if pt.catalyst_family == CATALYST_MO_LATENT:
        notes += " " + evaluate_ht_family().notes
    return CoupledResult(
        label=pt.label,
        overall=overall,
        core_overall=core_overall,
        viscosity=visc,
        kinetics=kin,
        droplets=drop,
        mechanics=mech,
        permeability=perm,
        thermal=therm,
        agglomeration=agg,
        components=components,
        notes=notes,
        catalyst_family=pt.catalyst_family,
    )


def from_yaml_point(data: dict[str, Any], label: str) -> OperatingPoint:
    family = str(data.get("catalyst_family", CATALYST_RU_PHOSPHITE))
    extra = 1.0
    if label == "hpht":
        extra = float(data.get("latency_multiplier_assumed", 1.0))
    return OperatingPoint(
        temperature_C=float(data["temperature_C"]),
        phi=float(data["dispersed_volume_fraction"]),
        catalyst_relative=float(data.get("catalyst_relative", 1.0)),
        inhibitor_index=float(data.get("inhibitor_index", 0.22)),
        latency_extra=extra,
        sigma_N_m=float(data.get("interfacial_tension_N_m", 0.004)),
        shear_rate_1_s=float(data.get("shear_rate_1_s", 400.0)),
        velocity_m_s=float(data.get("characteristic_velocity_m_s", 1.5)),
        length_m=float(data.get("channel_width_m", 0.05)),
        label=label,
        catalyst_family=family,
    )


def design_space(
    temperatures_C: list[float],
    phis: list[float],
    inhibitors: list[float],
    shear_rate_1_s: float = 400.0,
    velocity_m_s: float = 1.5,
    length_m: float = 0.05,
    **kwargs: Any,
) -> list[CoupledResult]:
    out: list[CoupledResult] = []
    for t in temperatures_C:
        for phi in phis:
            for inh in inhibitors:
                pt = OperatingPoint(
                    temperature_C=t,
                    phi=phi,
                    inhibitor_index=inh,
                    shear_rate_1_s=shear_rate_1_s,
                    velocity_m_s=velocity_m_s,
                    length_m=length_m,
                    label=f"T{t:g}_phi{phi:g}_I{inh:g}",
                    **kwargs,
                )
                out.append(evaluate_point(pt))
    return out
