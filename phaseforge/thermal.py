"""Lumped transient energy balance for an individual DCPD-rich droplet.

    rho Cp V dT/dt = Hr * rho * V * dα/dt  -  h A (T - T_cont)

Studies whether reaction exotherm can cause premature solidification or
neighboring-droplet thermal coupling. Exact droplet-scale h and k are
uncertain; conservative ranges are used and tagged ASSUMED_FOR_SENSITIVITY.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from phaseforge.kinetics import ALPHA_GEL, HR_J_KG, KineticsInputs, arrhenius_tgel_s
from phaseforge.provenance import Provenance, RequirementStatus
from phaseforge.units import C_to_K, um_to_m

# Typical organic-liquid / polymer properties (order of magnitude).
RHO_DISP_KG_M3 = 980.0  # DCPD density ~0.98 g/cm3 at 35 C (manufacturer-range)
CP_J_KG_K = 1700.0  # ASSUMED_FOR_SENSITIVITY, typical organic liquid
K_CONT_W_M_K = 0.64  # water
K_DISP_W_M_K = 0.13  # organic


@dataclass(frozen=True, slots=True)
class ThermalInputs:
    diameter_m: float
    T_cont_C: float
    T_init_C: float | None = None
    kinetics: KineticsInputs | None = None
    rho_kg_m3: float = RHO_DISP_KG_M3
    Cp_J_kg_K: float = CP_J_KG_K
    Hr_J_kg: float = HR_J_KG.value
    Nu: float = 2.0  # spherical droplet in stagnant fluid (lower-bound cooling)
    k_cont_W_m_K: float = K_CONT_W_M_K
    t_end_s: float = 7200.0


@dataclass(frozen=True, slots=True)
class ThermalResult:
    T_max_C: float
    dT_max_K: float
    t_to_Tmax_s: float
    runaway: bool
    premature_vs_isothermal: bool
    t_solid_isothermal_s: float
    t_solid_nonisothermal_s: float | None
    status: RequirementStatus
    provenance: Provenance
    notes: str


def film_h(diameter_m: float, Nu: float, k_cont: float) -> float:
    """h = Nu * k / d. Nu=2 is the conduction limit for a sphere."""
    return Nu * k_cont / max(diameter_m, 1e-12)


def adiabatic_delta_T(Hr_J_kg: float = HR_J_KG.value, Cp: float = CP_J_KG_K) -> float:
    """Upper bound: ΔT_ad = Hr / Cp if all heat stays in the droplet."""
    return Hr_J_kg / Cp


def simulate_droplet(inp: ThermalInputs) -> ThermalResult:
    kin = inp.kinetics or KineticsInputs(temperature_C=inp.T_cont_C)
    d = inp.diameter_m
    R = d / 2.0
    V = 4.0 / 3.0 * np.pi * R**3
    A = 4.0 * np.pi * R**2
    h = film_h(d, inp.Nu, inp.k_cont_W_m_K)
    t_gel_iso = arrhenius_tgel_s(kin)
    t_solid_iso = t_gel_iso * kin.t_solid_over_gel
    T_cont = C_to_K(inp.T_cont_C)
    T0 = C_to_K(inp.T_init_C if inp.T_init_C is not None else inp.T_cont_C)
    n_order = 1.2
    n_steps = 240
    t_end = min(max(inp.t_end_s, 60.0), 3600.0)
    dt = t_end / n_steps
    T = T0
    alpha = 0.0
    T_peak = T0
    t_peak = 0.0
    t_solid_ni = None
    cool = (h * A) / (inp.rho_kg_m3 * inp.Cp_J_kg_K * V)
    for i in range(n_steps):
        t = i * dt
        T_C = float(np.clip(T - 273.15, -20.0, 250.0))
        kin_T = KineticsInputs(
            temperature_C=T_C,
            catalyst_relative=kin.catalyst_relative,
            inhibitor_index=kin.inhibitor_index,
            inhibitor_factor_max=kin.inhibitor_factor_max,
            Ea_J_mol=kin.Ea_J_mol,
            tgel_ref_s=kin.tgel_ref_s,
            catalyst_order_n=kin.catalyst_order_n,
            latency_extra=kin.latency_extra,
            t_solid_over_gel=kin.t_solid_over_gel,
        )
        t_gel = max(arrhenius_tgel_s(kin_T), 1e-3)
        if alpha >= 0.999:
            dadt = 0.0
        else:
            k = (1.0 - (1.0 - ALPHA_GEL) ** (1.0 - n_order)) / ((1.0 - n_order) * t_gel)
            dadt = min(k * (1.0 - alpha) ** n_order, 2.0)
        # Exact integration of dT/dt = Q - cool (T - T_cont)
        Q = (inp.Hr_J_kg / inp.Cp_J_kg_K) * dadt
        decay = float(np.exp(-cool * dt))
        T = T_cont + (T - T_cont) * decay + Q / max(cool, 1e-12) * (1.0 - decay)
        alpha = float(min(1.0, alpha + dadt * dt))
        if t_solid_ni is None and alpha >= 0.80:
            t_solid_ni = t + dt
        if T > T_peak:
            T_peak = T
            t_peak = t + dt

    T_max = float(T_peak - 273.15)
    dT = T_max - inp.T_cont_C
    t_max = float(t_peak)
    # Runaway: temperature rise > 15 K (conservative; droplet Biot is small)
    runaway = dT > 15.0
    premature = False
    if t_solid_ni is not None:
        premature = t_solid_ni < 0.7 * t_solid_iso
    # Acceptable thermal behavior: no runaway and no strong prematurity
    if runaway or premature:
        status = RequirementStatus.FAIL if dT > 40.0 else RequirementStatus.MARGINAL
    else:
        status = RequirementStatus.PASS
    dT_ad = adiabatic_delta_T(inp.Hr_J_kg, inp.Cp_J_kg_K)
    notes = (
        f"Nu={inp.Nu}; h={h:.3g} W/m2K; ΔT_max={dT:.2f} K; "
        f"ΔT_adiabatic={dT_ad:.0f} K; Bi~hR/k_disp={h * R / K_DISP_W_M_K:.2e}. "
        "Cooling to a large aqueous continuous phase strongly limits droplet self-heating."
    )
    return ThermalResult(
        T_max_C=T_max,
        dT_max_K=dT,
        t_to_Tmax_s=t_max,
        runaway=runaway,
        premature_vs_isothermal=premature,
        t_solid_isothermal_s=t_solid_iso,
        t_solid_nonisothermal_s=t_solid_ni,
        status=status,
        provenance=Provenance.MODEL_PREDICTION,
        notes=notes,
    )


def neighbor_coupling_estimate(
    diameter_m: float,
    phi: float,
    dT_single_K: float,
) -> float:
    """Crude estimate of extra heating from neighbors: scale with phi/(1-phi).

    Not a CFD result. ASSUMED_FOR_SENSITIVITY scaling.
    """
    return dT_single_K * phi / max(1.0 - phi, 0.05)


def default_droplet_diameter_m(d_um: float = 200.0) -> float:
    return um_to_m(d_um)
