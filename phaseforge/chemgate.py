"""PhaseForge-ChemGate: chemically gated latent ROMP in organic droplets.

t_transform = t_delay + t_partition + t_diff + t_activation + t_polymerization

D899/Cu literature is an ANALOGUE, not a PhaseForge recipe and not our IP.

Lee 2024: D899 dormant through ~200 C frontal polymerization until Cu(I).
Lee 2025: aqueous Cu(I) → organic DCPD ink via interfacial diffusion; D≈6e-12 m2/s
          ambient; filaments <~400 um fully cured in ≥~20 min.
Suslick 2022: ambient gel times ~5 min (CuX) to 12 h (Cu(PPh3)3X); 8 week storage
              without activator + phosphite.

None of that is an isothermal 25-75 min measurement at 150 C. Status cannot be PASS.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from phaseforge.activation_diffusion import (
    D_LEE2025_M2_S,
    DIAMETERS_UM,
    evaluate_sphere,
)
from phaseforge.provenance import Provenance, RequirementStatus
from phaseforge.requirements import classify_transform_time_s
from phaseforge.units import um_to_m

FAMILY_CHEMGATE = "PhaseForge-ChemGate"
FAMILY_CHEMGATE_ACID = "PhaseForge-ChemGate-Acid"

# Ambient analogue gel/activation windows (Suslick 2022 / Lee 2024). Not 150 C.
T_ACT_CUCL_S = 10.0 * 60.0  # "within minutes" simple CuX
T_ACT_SLOW_S = 12.0 * 3600.0  # coordinatively saturated Cu
T_POLY_AFTER_S = 15.0 * 60.0  # Lee color/film ~20 min includes diffusion; residual polymerisation analogue
T_PARTITION_S = 2.0 * 60.0  # ASSUMED interfacial transfer lag


@dataclass(frozen=True, slots=True)
class ChemGateInputs:
    diameter_um: float = 270.0
    temperature_C: float = 150.0
    t_delay_s: float = 30.0 * 60.0  # external trigger / delayed activator contact
    t_partition_s: float = T_PARTITION_S
    t_activation_s: float = T_ACT_CUCL_S
    t_polymerization_s: float = T_POLY_AFTER_S
    D_mode: str = "lee_ambient"
    empirical_D_factor: float = 1.0
    partition_K: float = 1.0
    activator_activity: float = 1.0  # scales t_activation as 1/activity


@dataclass(frozen=True, slots=True)
class ChemGateResult:
    family: str
    t_delay_s: float
    t_partition_s: float
    t_diff_s: float
    t_activation_s: float
    t_polymerization_s: float
    t_transform_s: float
    t_transform_min: float
    t_transport_leak_s: float
    Da_diff_act: float
    Da_diff_poly: float
    regime: str
    status: RequirementStatus
    pathway: str
    premature_during_transport: bool
    notes: str
    provenance: Provenance

    def as_dict(self) -> dict:
        return {
            "family": self.family,
            "t_delay_min": self.t_delay_s / 60.0,
            "t_partition_min": self.t_partition_s / 60.0,
            "t_diff_min": self.t_diff_s / 60.0 if np.isfinite(self.t_diff_s) else None,
            "t_activation_min": self.t_activation_s / 60.0,
            "t_polymerization_min": self.t_polymerization_s / 60.0,
            "t_transform_min": self.t_transform_min if np.isfinite(self.t_transform_min) else None,
            "Da_diff_act": self.Da_diff_act,
            "Da_diff_poly": self.Da_diff_poly,
            "regime": self.regime,
            "status": self.status.value,
            "pathway": self.pathway,
            "premature_during_transport": self.premature_during_transport,
            "notes": self.notes,
        }


def damkohler(t_diff_s: float, t_react_s: float) -> float:
    """Da = t_diff / t_react. >>1 diffusion-limited; <<1 reaction-limited."""
    if not np.isfinite(t_diff_s) or t_react_s <= 0.0:
        return float("nan")
    return t_diff_s / t_react_s


def _regime(da_act: float, da_poly: float) -> str:
    da = max(da_act, da_poly) if np.isfinite(da_act) else da_poly
    if not np.isfinite(da):
        return "unknown"
    if da >= 3.0:
        return "diffusion_limited"
    if da <= 0.3:
        return "activation_or_reaction_limited"
    return "mixed"


def evaluate_chemgate(inp: ChemGateInputs | None = None, *, family: str = FAMILY_CHEMGATE) -> ChemGateResult:
    inp = inp or ChemGateInputs()
    sph = evaluate_sphere(
        inp.diameter_um,
        T_C=inp.temperature_C,
        mode=inp.D_mode,
        empirical_factor=inp.empirical_D_factor,
        partition_K=inp.partition_K,
    )
    t_diff = sph.t_avg_50_s
    t_act = inp.t_activation_s / max(inp.activator_activity, 1e-6)
    t_poly = inp.t_polymerization_s
    t_tot = inp.t_delay_s + inp.t_partition_s + t_diff + t_act + t_poly
    # Leak during transport: if activator is already in the continuous phase, t_delay=0
    # and droplets begin curing immediately. Architecture requires delayed contact.
    leak = inp.t_partition_s + t_diff + t_act
    premature = inp.t_delay_s < 15.0 * 60.0 and leak < 25.0 * 60.0
    da_a = damkohler(t_diff, t_act)
    da_p = damkohler(t_diff, t_poly)
    # Never PASS: no 150 C isothermal ChemGate experiment in this repo.
    window_status = classify_transform_time_s(t_tot, unknown=True)
    in_window = 25.0 * 60.0 <= t_tot <= 75.0 * 60.0
    if premature:
        pathway = "NEEDS_DELAYED_ACTIVATOR_CONTACT"
        status = RequirementStatus.UNKNOWN
    elif in_window and inp.D_mode == "lee_ambient":
        pathway = "PLAUSIBLE_CANDIDATE"
        status = RequirementStatus.UNKNOWN
    elif in_window:
        pathway = "PLAUSIBLE_WITH_EXTRAPOLATED_D"
        status = RequirementStatus.UNKNOWN
    else:
        pathway = "OUTSIDE_WINDOW_OR_UNCONSTRAINED"
        status = RequirementStatus.UNKNOWN
    notes = (
        f"{family}: t_tot={t_tot/60.0:.3g} min = delay {inp.t_delay_s/60.0:.3g} + partition "
        f"{inp.t_partition_s/60.0:.3g} + diff {t_diff/60.0:.3g} + act {t_act/60.0:.3g} + poly "
        f"{t_poly/60.0:.3g}. D mode={inp.D_mode}. Lee 2025 D is ambient. "
        "D899/Cu is analogue/prior art, not a PhaseForge invention. "
        f"pathway={pathway}. NEVER upgraded to PASS without 150 C isothermal data. "
        f"{sph.notes}"
    )
    _ = window_status
    return ChemGateResult(
        family=family,
        t_delay_s=inp.t_delay_s,
        t_partition_s=inp.t_partition_s,
        t_diff_s=t_diff,
        t_activation_s=t_act,
        t_polymerization_s=t_poly,
        t_transform_s=t_tot,
        t_transform_min=t_tot / 60.0,
        t_transport_leak_s=leak,
        Da_diff_act=da_a,
        Da_diff_poly=da_p,
        regime=_regime(da_a, da_p),
        status=status,
        pathway=pathway,
        premature_during_transport=premature,
        notes=notes,
        provenance=Provenance.MODEL_PREDICTION,
    )


def feasibility_map(
    diameters_um: tuple[float, ...] = DIAMETERS_UM,
    activities: tuple[float, ...] = (0.2, 0.5, 1.0, 2.0, 5.0),
    *,
    T_C: float = 150.0,
    D_mode: str = "lee_ambient",
    t_delay_s: float = 30.0 * 60.0,
) -> np.ndarray:
    """t_transform in minutes, shape (n_activity, n_diameter)."""
    Z = np.empty((len(activities), len(diameters_um)), dtype=float)
    for i, a in enumerate(activities):
        for j, d in enumerate(diameters_um):
            r = evaluate_chemgate(
                ChemGateInputs(
                    diameter_um=d,
                    temperature_C=T_C,
                    D_mode=D_mode,
                    t_delay_s=t_delay_s,
                    activator_activity=a,
                )
            )
            Z[i, j] = r.t_transform_min
    return Z


def search_plausible_150C(*, n: int = 80, seed: int = 42) -> dict:
    """Engineering-level search. Does not invent a PASS."""
    rng = np.random.default_rng(seed)
    hits_ambient = 0
    hits_se = 0
    examples: list[dict] = []
    for _ in range(n):
        d = float(rng.choice(DIAMETERS_UM))
        delay = float(rng.uniform(20.0, 50.0) * 60.0)
        act = float(rng.choice([0.3, 1.0, 3.0]))
        K = float(rng.choice([0.3, 1.0, 2.0]))
        for mode, _counter in (("lee_ambient", "amb"), ("stokes_einstein", "se")):
            r = evaluate_chemgate(
                ChemGateInputs(
                    diameter_um=d,
                    temperature_C=150.0,
                    t_delay_s=delay,
                    activator_activity=act,
                    partition_K=K,
                    D_mode=mode,
                )
            )
            ok = 25.0 <= r.t_transform_min <= 75.0
            if mode == "lee_ambient" and ok:
                hits_ambient += 1
            if mode == "stokes_einstein" and ok:
                hits_se += 1
            if ok and len(examples) < 8:
                examples.append(
                    {
                        "mode": mode,
                        "d_um": d,
                        "t_min": r.t_transform_min,
                        "pathway": r.pathway,
                        "regime": r.regime,
                    }
                )
    return {
        "n": n,
        "fraction_in_window_lee_ambient_D": hits_ambient / n,
        "fraction_in_window_stokes_einstein_D": hits_se / n,
        "examples": examples,
        "verdict": (
            "PLAUSIBLE_PATHWAY if delayed activator contact is engineered; "
            "150 C window is modelled not measured; status UNKNOWN not PASS."
        ),
    }


def t_shell_vs_coalescence(
    diameter_um: float,
    coalescence_time_s: float,
    D: float = D_LEE2025_M2_S,
) -> dict:
    """Hypothesis: surface gel vs collision time. Not a proven non-agglomeration claim."""
    R = um_to_m(diameter_um) / 2.0
    # Fo~0.01: thin surface layer (order 0.1 R).
    t_shell = 0.01 * R**2 / max(D, 1e-30)
    return {
        "diameter_um": diameter_um,
        "t_shell_s": t_shell,
        "t_coalescence_s": coalescence_time_s,
        "shell_faster": t_shell < coalescence_time_s,
        "notes": (
            "Hypothesis only: if t_shell < t_collision after activator contact, "
            "surface-first cure may reduce coalescence. Not experimental proof."
        ),
    }
