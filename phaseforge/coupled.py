"""Coupled feasibility envelope for PhaseForge operating points.

Evaluates simultaneously:
  1. viscosity <= 10 cP
  2. transformation time 25-75 min
  3. particle diameter 70-600 um
  4. mechanical safety factor >= 1
  5. agglomeration / coalescence risk
  6. open flow pathways
  7. acceptable thermal behavior

UNKNOWN is never converted into PASS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from phaseforge.droplets import DropletInputs, DropletResult, evaluate_droplets
from phaseforge.kinetics import KineticsInputs, KineticsResult, evaluate_kinetics
from phaseforge.mechanics import MechanicsInputs, MechanicsResult, evaluate_mechanics
from phaseforge.permeability import PermeabilityInputs, PermeabilityResult, evaluate_permeability
from phaseforge.provenance import RequirementStatus
from phaseforge.requirements import worst_status
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


@dataclass
class CoupledResult:
    label: str
    overall: RequirementStatus
    viscosity: ViscosityResult
    kinetics: KineticsResult
    droplets: DropletResult
    mechanics: MechanicsResult
    permeability: PermeabilityResult
    thermal: ThermalResult
    agglomeration: RequirementStatus
    components: dict[str, str] = field(default_factory=dict)
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "overall": self.overall.value,
            "mu_eff_cP": self.viscosity.mu_eff_cP,
            "t_transform_min": self.kinetics.t_transform_min,
            "t_gel_min": self.kinetics.t_gel_s / 60.0,
            "d_particle_um": self.droplets.d_particle_um,
            "SF_mech": self.mechanics.SF,
            "porosity": self.permeability.porosity,
            "k_rel": self.permeability.k_rel,
            "dT_max_K": self.thermal.dT_max_K,
            "coalescence_risk": self.droplets.coalescence_risk,
            "status_viscosity": self.viscosity.status.value,
            "status_kinetics": self.kinetics.status.value,
            "status_diameter": self.droplets.status.value,
            "status_mechanics": self.mechanics.status.value,
            "status_permeability": self.permeability.status.value,
            "status_thermal": self.thermal.status.value,
            "status_agglomeration": self.agglomeration.value,
            "kinetics_flag": self.kinetics.extrapolation_flag,
            "mechanics_unknown": self.mechanics.unknown_high_T,
            "notes": self.notes,
        }


def _agglomeration_status(risk: float, discrete: bool) -> RequirementStatus:
    if not discrete:
        return RequirementStatus.FAIL
    if risk <= 0.35:
        return RequirementStatus.PASS
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
            ),
            t_end_s=min(max(kin.t_solid_s * 1.2, 300.0), 1800.0),
        )
    )
    discrete = pt.phi < 0.55
    agg = _agglomeration_status(drop.coalescence_risk, discrete)
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
    overall = worst_status(
        [
            visc.status,
            kin.status,
            drop.status,
            mech.status,
            agg,
            perm.status,
            therm.status,
            discrete_status,
        ]
    )
    notes = (
        f"T={pt.temperature_C} C, φ={pt.phi}, cat={pt.catalyst_relative}, "
        f"inh={pt.inhibitor_index}, latency_extra={pt.latency_extra}. "
        f"UNKNOWN never upgraded. kinetics_flag={kin.extrapolation_flag}."
    )
    return CoupledResult(
        label=pt.label,
        overall=overall,
        viscosity=visc,
        kinetics=kin,
        droplets=drop,
        mechanics=mech,
        permeability=perm,
        thermal=therm,
        agglomeration=agg,
        components=components,
        notes=notes,
    )


def from_yaml_point(data: dict[str, Any], label: str) -> OperatingPoint:
    return OperatingPoint(
        temperature_C=float(data["temperature_C"]),
        phi=float(data["dispersed_volume_fraction"]),
        catalyst_relative=float(data.get("catalyst_relative", 1.0)),
        inhibitor_index=float(data.get("inhibitor_index", 0.22)),
        latency_extra=float(data.get("latency_multiplier_assumed", 1.0))
        if label == "hpht"
        else 1.0,
        sigma_N_m=float(data.get("interfacial_tension_N_m", 0.004)),
        shear_rate_1_s=float(data.get("shear_rate_1_s", 400.0)),
        velocity_m_s=float(data.get("characteristic_velocity_m_s", 1.5)),
        length_m=float(data.get("channel_width_m", 0.05)),
        label=label,
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
