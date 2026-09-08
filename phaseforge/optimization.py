"""Constrained search for conservative / nominal / aggressive envelopes.

Does not optimize hazardous laboratory recipes. Engineering-level parameters
only: φ, T, inhibitor index, catalyst relative activity, IFT regime, shear.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from phaseforge.coupled import CoupledResult, OperatingPoint, evaluate_point
from phaseforge.provenance import RequirementStatus


@dataclass(frozen=True, slots=True)
class Envelope:
    name: str
    point: OperatingPoint
    result: CoupledResult
    score: float
    notes: str


def _score(r: CoupledResult) -> float:
    """Higher is better. FAIL and UNKNOWN are heavily penalized."""
    if r.overall == RequirementStatus.FAIL:
        return -1.0e3
    bonus = 0.0
    if r.overall == RequirementStatus.PASS:
        bonus += 50.0
    elif r.overall == RequirementStatus.MARGINAL:
        bonus += 10.0
    elif r.overall == RequirementStatus.UNKNOWN:
        bonus -= 20.0
    # Margins
    mu_m = max(0.0, 10.0 - r.viscosity.mu_eff_cP)
    t = r.kinetics.t_transform_min
    t_m = max(0.0, min(t - 25.0, 75.0 - t))
    d = r.droplets.d_particle_um
    d_m = max(0.0, min(d - 70.0, 600.0 - d)) / 100.0
    sf_m = max(0.0, r.mechanics.SF - 1.0)
    k_m = max(0.0, r.permeability.porosity - 0.2)
    return bonus + 2.0 * mu_m + 0.4 * t_m + d_m + 8.0 * sf_m + 10.0 * k_m


def grid_search(seed: int = 42) -> list[CoupledResult]:
    rng = np.random.default_rng(seed)
    temps = [45.0, 50.0, 55.0, 60.0, 70.0, 80.0]
    phis = [0.08, 0.12, 0.15, 0.20]
    inhs = [0.35, 0.55, 0.75, 0.90]
    cats = [0.7, 1.0, 1.4]
    sigmas = [0.0032, 0.004, 0.006]
    shears = [400.0, 800.0, 1500.0]
    results: list[CoupledResult] = []
    for T in temps:
        for phi in phis:
            for inh in inhs:
                for c in cats:
                    for s in sigmas:
                        for g in shears:
                            # subsample aggressive combinations to keep runtime modest
                            if rng.random() > 0.55 and not (T in (50.0, 60.0) and phi == 0.15):
                                continue
                            pt = OperatingPoint(
                                temperature_C=T,
                                phi=phi,
                                inhibitor_index=inh,
                                catalyst_relative=c,
                                sigma_N_m=s,
                                shear_rate_1_s=g,
                                label=f"opt_T{T}_phi{phi}_I{inh}_c{c}",
                            )
                            results.append(evaluate_point(pt))
    return results


def select_envelopes(results: list[CoupledResult] | None = None) -> dict[str, Envelope]:
    if results is None:
        results = grid_search()
    scored = []
    for r in results:
        # recover point from label is lossy; re-evaluate via stored metrics only
        scored.append(( _score(r), r))
    scored.sort(key=lambda z: z[0], reverse=True)

    def pick(pred, fallback_idx: int) -> CoupledResult:
        for s, r in scored:
            if pred(r) and s > -500:
                return r
        return scored[min(fallback_idx, len(scored) - 1)][1]

    cons = pick(
        lambda r: r.kinetics.t_transform_min >= 40.0
        and r.viscosity.mu_eff_cP <= 8.0
        and r.mechanics.SF >= 1.0
        and r.overall != RequirementStatus.FAIL,
        0,
    )
    nom = pick(
        lambda r: 30.0 <= r.kinetics.t_transform_min <= 60.0
        and r.overall in (RequirementStatus.PASS, RequirementStatus.MARGINAL, RequirementStatus.UNKNOWN),
        0,
    )
    agg = pick(
        lambda r: r.kinetics.t_transform_min <= 40.0
        and r.droplets.d_particle_um <= 300.0
        and r.overall != RequirementStatus.FAIL,
        1,
    )

    def to_env(name: str, r: CoupledResult, notes: str) -> Envelope:
        # Reconstruct a representative OperatingPoint from the result label/metrics.
        pt = OperatingPoint(
            temperature_C=float(r.notes.split("T=")[1].split(" ")[0]) if "T=" in r.notes else 60.0,
            phi=float(r.notes.split("φ=")[1].split(",")[0]) if "φ=" in r.notes else 0.15,
            catalyst_relative=float(r.notes.split("cat=")[1].split(",")[0]) if "cat=" in r.notes else 1.0,
            inhibitor_index=float(r.notes.split("inh=")[1].split(",")[0]) if "inh=" in r.notes else 0.6,
            label=name,
        )
        # Re-evaluate with reconstructed point (deterministic)
        rr = evaluate_point(pt)
        return Envelope(name=name, point=pt, result=rr, score=_score(rr), notes=notes)

    return {
        "conservative": to_env(
            "conservative",
            cons,
            "Favours longer latency, lower φ, higher viscosity margin.",
        ),
        "nominal": to_env(
            "nominal",
            nom,
            "Central 25-75 min window with moderate φ.",
        ),
        "aggressive": to_env(
            "aggressive",
            agg,
            "Shorter delay, higher loading, still avoiding FAIL where possible.",
        ),
    }
