"""Monte Carlo, Latin Hypercube, and Sobol uncertainty quantification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from SALib.analyze import sobol as sobol_analyze
from SALib.sample import saltelli
from scipy.stats import qmc

from phaseforge.coupled import OperatingPoint, evaluate_point
from phaseforge.provenance import RequirementStatus

UQ_SEED = 42

# Independent uniform parameters for simultaneous-compliance UQ around a
# nominal moderate-temperature operating point. 150 C is handled separately.
PROBLEM = {
    "num_vars": 8,
    "names": [
        "temperature_C",
        "phi",
        "catalyst_relative",
        "inhibitor_index",
        "sigma_N_m",
        "Tg_C",
        "sigma_c_RT_MPa",
        "shear_rate_1_s",
    ],
    "bounds": [
        [40.0, 90.0],
        [0.08, 0.25],
        [0.5, 2.0],
        [0.05, 0.45],
        [0.002, 0.012],
        [139.0, 180.0],
        [50.0, 95.0],
        [150.0, 1200.0],
    ],
}


def _point_from_vector(x: np.ndarray, label: str = "uq") -> OperatingPoint:
    return OperatingPoint(
        temperature_C=float(x[0]),
        phi=float(x[1]),
        catalyst_relative=float(x[2]),
        inhibitor_index=float(x[3]),
        sigma_N_m=float(x[4]),
        Tg_C=float(x[5]),
        sigma_c_RT_MPa=float(x[6]),
        shear_rate_1_s=float(x[7]),
        label=label,
    )


def _pass_flags(pt: OperatingPoint) -> dict[str, int]:
    r = evaluate_point(pt)
    flags = {
        "viscosity": int(r.viscosity.status == RequirementStatus.PASS),
        "transform_time": int(r.kinetics.status == RequirementStatus.PASS),
        "diameter": int(r.droplets.status == RequirementStatus.PASS),
        "mechanics": int(r.mechanics.status == RequirementStatus.PASS),
        "open_pathways": int(r.permeability.status == RequirementStatus.PASS),
        "thermal": int(r.thermal.status == RequirementStatus.PASS),
        "agglomeration": int(r.agglomeration == RequirementStatus.PASS),
        "overall_pass": int(r.overall == RequirementStatus.PASS),
        "overall_not_fail": int(r.overall != RequirementStatus.FAIL),
    }
    return flags


def latin_hypercube(n: int, seed: int = UQ_SEED) -> np.ndarray:
    sampler = qmc.LatinHypercube(d=PROBLEM["num_vars"], seed=seed)
    u = sampler.random(n)
    bounds = np.asarray(PROBLEM["bounds"], dtype=float)
    return qmc.scale(u, bounds[:, 0], bounds[:, 1])


def monte_carlo_compliance(n: int = 800, seed: int = UQ_SEED) -> dict[str, Any]:
    X = latin_hypercube(n, seed)
    keys = [
        "viscosity",
        "transform_time",
        "diameter",
        "mechanics",
        "open_pathways",
        "thermal",
        "agglomeration",
        "overall_pass",
        "overall_not_fail",
    ]
    acc = {k: 0 for k in keys}
    for i, row in enumerate(X):
        flags = _pass_flags(_point_from_vector(row, label=f"mc{i}"))
        for k in keys:
            acc[k] += flags[k]
    probs = {k: acc[k] / n for k in keys}
    return {"n": n, "seed": seed, "probabilities": probs, "method": "latin_hypercube"}


def tornado(nominal: OperatingPoint, deltas: dict[str, tuple[float, float]] | None = None) -> list[dict[str, Any]]:
    """One-at-a-time sensitivity of overall PASS (0/1) and SF, t_transform, mu."""
    base = evaluate_point(nominal)
    if deltas is None:
        deltas = {
            "temperature_C": (40.0, 90.0),
            "phi": (0.08, 0.25),
            "inhibitor_index": (0.05, 0.45),
            "catalyst_relative": (0.5, 2.0),
            "sigma_N_m": (0.002, 0.012),
            "Tg_C": (139.0, 180.0),
            "sigma_c_RT_MPa": (50.0, 95.0),
            "shear_rate_1_s": (150.0, 1200.0),
        }
    rows = []
    for name, (lo, hi) in deltas.items():
        pts = []
        for val in (lo, hi):
            kwargs = nominal.__dict__.copy()
            kwargs[name] = val
            kwargs["label"] = f"{name}_{val}"
            pts.append(evaluate_point(OperatingPoint(**kwargs)))
        rows.append(
            {
                "parameter": name,
                "low": lo,
                "high": hi,
                "t_min_low": pts[0].kinetics.t_transform_min,
                "t_min_high": pts[1].kinetics.t_transform_min,
                "mu_low": pts[0].viscosity.mu_eff_cP,
                "mu_high": pts[1].viscosity.mu_eff_cP,
                "SF_low": pts[0].mechanics.SF,
                "SF_high": pts[1].mechanics.SF,
                "d_um_low": pts[0].droplets.d_particle_um,
                "d_um_high": pts[1].droplets.d_particle_um,
                "overall_low": pts[0].overall.value,
                "overall_high": pts[1].overall.value,
                "delta_t": abs(pts[1].kinetics.t_transform_min - pts[0].kinetics.t_transform_min),
            }
        )
    rows.sort(key=lambda r: r["delta_t"], reverse=True)
    rows.insert(
        0,
        {
            "parameter": "nominal",
            "t_min_low": base.kinetics.t_transform_min,
            "mu_low": base.viscosity.mu_eff_cP,
            "SF_low": base.mechanics.SF,
            "d_um_low": base.droplets.d_particle_um,
            "overall_low": base.overall.value,
        },
    )
    return rows


def sobol_transform_time(n: int = 256, seed: int = UQ_SEED) -> dict[str, Any]:
    """Sobol indices for log10(t_transform_min) on the 40-90 C envelope."""
    problem = PROBLEM
    np.random.seed(seed)
    X = saltelli.sample(problem, n, calc_second_order=False)
    Y = np.empty(X.shape[0])
    for i, row in enumerate(X):
        r = evaluate_point(_point_from_vector(row, label=f"sobol{i}"))
        Y[i] = np.log10(max(r.kinetics.t_transform_min, 1e-6))
    Si = sobol_analyze.analyze(problem, Y, calc_second_order=False, print_to_console=False)
    return {
        "n": n,
        "seed": seed,
        "names": problem["names"],
        "S1": Si["S1"].tolist(),
        "ST": Si["ST"].tolist(),
        "S1_conf": Si["S1_conf"].tolist(),
        "ST_conf": Si["ST_conf"].tolist(),
        "output": "log10(t_transform_min)",
    }


@dataclass
class UQBundle:
    mc: dict[str, Any]
    tornado: list[dict[str, Any]]
    sobol: dict[str, Any] | None
