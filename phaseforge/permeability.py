"""Packed / distributed microparticles and residual flow pathways.

Three separate claims (do not conflate):

  A. Geometric connectivity / continuous-phase availability
  B. Analytical permeability estimate (Kozeny-Carman or dilute obstruction)
  C. Experimentally unvalidated conductivity under closure stress

k_open = 1e-8 m2 is a relative reference assumption, not measured fracture
conductivity. k_rel must not be presented as experimental or field conductivity.

For the exact PhaseForge system, open-pathway status is MARGINAL until
CFD or experimental evidence strengthens it (unless geometry is disconnected,
which is FAIL).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from phaseforge.provenance import Provenance, RequirementStatus

K_OPEN_ASSUMED_M2 = 1.0e-8  # ASSUMED_FOR_SENSITIVITY relative reference


def kozeny_carman(d_m: float, porosity: float, k0: float = 180.0) -> float:
    """k = φ^3 d^2 / [k0 (1-φ)^2]   (SI: m^2)

    Carman (1937) / Kozeny-Carman packed-bed permeability. k0=180 is the
    common spherical-particle coefficient.
    """
    phi = min(max(porosity, 1e-6), 0.99)
    return (phi**3) * d_m**2 / (k0 * (1.0 - phi) ** 2)


def darcy_pressure_drop(k_m2: float, mu: float, U: float, L: float) -> float:
    """ΔP = μ U L / k."""
    return mu * U * L / max(k_m2, 1e-30)


def relative_conductivity(k: float, k_ref: float) -> float:
    return k / max(k_ref, 1e-30)


@dataclass(frozen=True, slots=True)
class PermeabilityInputs:
    d_m: float
    phi_particles: float  # particle volume fraction in the fracture
    packing_fraction: float = 0.60
    settled: bool = False
    mu_Pa_s: float = 1.0e-3
    U_m_s: float = 0.01
    L_m: float = 1.0
    polydispersity: float = 1.0  # d90/d10 analogue scale
    validated_conductivity: bool = False  # True only with measured PhaseForge k


@dataclass(frozen=True, slots=True)
class PermeabilityResult:
    porosity: float
    k_m2: float
    k_mD: float
    dP_Pa: float
    connected: bool
    k_rel: float
    status: RequirementStatus
    provenance: Provenance
    notes: str
    geometric_connectivity: bool
    k_analytical_m2: float
    k_open_assumed_m2: float
    conductivity_under_closure: str


def millidarcy(k_m2: float) -> float:
    return k_m2 / 9.869233e-16


def evaluate_permeability(inp: PermeabilityInputs) -> PermeabilityResult:
    if inp.settled:
        porosity = 1.0 - inp.packing_fraction
        porosity *= 1.0 / (1.0 + 0.15 * max(inp.polydispersity - 1.0, 0.0))
    else:
        porosity = 1.0 - inp.phi_particles
    k_pack = kozeny_carman(inp.d_m, porosity)
    k_open = K_OPEN_ASSUMED_M2
    if not inp.settled:
        k_dilute = k_open * (1.0 - inp.phi_particles) / (1.0 + inp.phi_particles)
        k_use = k_dilute
        k_ref = k_open
    else:
        k_use = k_pack
        k_ref = kozeny_carman(inp.d_m, 0.40)
    dP = darcy_pressure_drop(k_use if inp.settled else max(k_use, k_pack), inp.mu_Pa_s, inp.U_m_s, inp.L_m)
    connected = porosity > 0.18 and inp.phi_particles < 0.64
    k_rel = k_use / max(k_ref, 1e-30)

    # A: geometry; B: analytical k; C: closure-stress conductivity unvalidated.
    if not connected or porosity < 0.12:
        status = RequirementStatus.FAIL
        cond_tag = "UNVALIDATED_DISCONNECTED"
    elif inp.validated_conductivity:
        status = RequirementStatus.PASS if k_rel >= 0.05 else RequirementStatus.MARGINAL
        cond_tag = "MEASURED"
    else:
        status = RequirementStatus.MARGINAL
        cond_tag = "UNVALIDATED_UNDER_CLOSURE"

    notes = (
        f"A_geometric_connected={connected}; porosity={porosity:.2f}; "
        f"B_analytical_k={k_use:.1e} m2 ({millidarcy(k_use):.3g} mD); "
        f"k_rel={k_rel:.2f} is relative to assumed k_open={k_open:.0e} m2 "
        f"(ASSUMED_FOR_SENSITIVITY, not measured fracture conductivity); "
        f"C_conductivity_under_closure={cond_tag}. "
        "Do not present k_rel as experimental or field conductivity. "
        f"settled={inp.settled}; φ_particles={inp.phi_particles:.3f}."
    )
    return PermeabilityResult(
        porosity=porosity,
        k_m2=k_use,
        k_mD=millidarcy(k_use),
        dP_Pa=dP,
        connected=connected,
        k_rel=float(k_rel),
        status=status,
        provenance=Provenance.ASSUMED_FOR_SENSITIVITY,
        notes=notes,
        geometric_connectivity=connected,
        k_analytical_m2=k_use,
        k_open_assumed_m2=k_open,
        conductivity_under_closure=cond_tag,
    )


def random_disk_pack(
    n: int,
    d_m: float,
    width_m: float,
    height_m: float,
    rng: np.random.Generator | None = None,
    max_tries: int = 50,
) -> tuple[np.ndarray, float]:
    """2D random sequential addition. Returns centres (x,y) and void fraction.

    Overlap is rejected. If n cannot be placed, returns as many as fit.
    """
    rng = rng or np.random.default_rng(42)
    r = d_m / 2.0
    pts: list[tuple[float, float]] = []
    for _ in range(n * max_tries):
        if len(pts) >= n:
            break
        x = rng.uniform(r, width_m - r)
        y = rng.uniform(r, height_m - r)
        ok = True
        for px, py in pts:
            if (x - px) ** 2 + (y - py) ** 2 < (2.0 * r) ** 2:
                ok = False
                break
        if ok:
            pts.append((x, y))
    arr = np.asarray(pts, dtype=float) if pts else np.zeros((0, 2))
    area_frac = len(pts) * np.pi * r**2 / (width_m * height_m)
    void = 1.0 - area_frac
    return arr, float(void)


def connectivity_metric(points: np.ndarray, d_m: float, cutoff: float = 1.5) -> float:
    """Fraction of particles with at least one neighbor within cutoff*d.

    High values indicate a contacting cluster (agglomeration / percolating solids).
    """
    if points.shape[0] < 2:
        return 0.0
    thresh = (cutoff * d_m) ** 2
    n = points.shape[0]
    has = np.zeros(n, dtype=bool)
    for i in range(n):
        d2 = np.sum((points - points[i]) ** 2, axis=1)
        d2[i] = np.inf
        has[i] = np.any(d2 < thresh)
    return float(np.mean(has))


def diameter_sweep_um() -> list[float]:
    return [70.0, 100.0, 200.0, 400.0, 600.0]
