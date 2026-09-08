"""Spherical chemical-activator diffusion into an organic droplet.

Lee et al., Adv. Mater. 2025, DOI 10.1002/adma.202508568:
  D_Cu(I) ≈ 6e-8 cm2/s = 6e-12 m2/s from 20-30 min film-growth (ambient).
That coefficient is NOT a 150 C measurement.

Analytic Dirichlet sphere (Crank): C(R,t)=C_s, C(r,0)=0.

t_transform is NOT diffusion alone. See phaseforge.chemgate.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from phaseforge.provenance import Provenance
from phaseforge.units import C_to_K, um_to_m
from phaseforge.viscosity import dcpd_viscosity_Pa_s

# Lee 2025, ambient film-growth estimate.
D_LEE2025_M2_S = 6.0e-12
D_LEE_T_C = 25.0  # room-temperature analogue; not stated as 150 C
DIAMETERS_UM = (70.0, 100.0, 150.0, 200.0, 270.0, 300.0, 400.0, 500.0, 600.0)


def d_lee_m2_s() -> float:
    return D_LEE2025_M2_S


def stokes_einstein_scale(T_C: float, T_ref_C: float = D_LEE_T_C) -> float:
    """D ~ T/μ using DCPD Andrade viscosity (organic-phase analogue).

    ASSUMED_FOR_SENSITIVITY: Lee D is in a DCPD-family ink, not calibrated μ(T).
    """
    T = C_to_K(T_C)
    Tref = C_to_K(T_ref_C)
    mu = dcpd_viscosity_Pa_s(T_C)
    mu_ref = dcpd_viscosity_Pa_s(T_ref_C)
    return float((T / Tref) * (mu_ref / max(mu, 1e-12)))


def arrhenius_D_scale(T_C: float, Ea_J_mol: float, T_ref_C: float = D_LEE_T_C) -> float:
    R = 8.314462618
    T = C_to_K(T_C)
    Tref = C_to_K(T_ref_C)
    return float(np.exp(-Ea_J_mol / R * (1.0 / T - 1.0 / Tref)))


def diffusivity_m2_s(
    T_C: float,
    *,
    mode: str = "lee_ambient",
    empirical_factor: float = 1.0,
    Ea_J_mol: float = 25000.0,
) -> tuple[float, str, Provenance]:
    """Return (D, notes, provenance). lee_ambient ignores T (conservative vs 150 C speed-up)."""
    D0 = D_LEE2025_M2_S
    if mode == "lee_ambient":
        D = D0 * empirical_factor
        notes = (
            f"D={D:.3g} m2/s = Lee 2025 ambient {D0:.3g} × empirical_factor={empirical_factor:g}. "
            "Not a 150 C measurement."
        )
        return D, notes, Provenance.PUBLISHED_EXPERIMENTAL if abs(empirical_factor - 1.0) < 1e-12 else Provenance.ASSUMED_FOR_SENSITIVITY
    if mode == "stokes_einstein":
        s = stokes_einstein_scale(T_C)
        D = D0 * s * empirical_factor
        notes = f"Stokes-Einstein D_ref×T/μ scale={s:.2f} at {T_C:g} C (ASSUMED). D={D:.3g} m2/s."
        return D, notes, Provenance.ASSUMED_FOR_SENSITIVITY
    if mode == "arrhenius":
        s = arrhenius_D_scale(T_C, Ea_J_mol)
        D = D0 * s * empirical_factor
        notes = f"Arrhenius Ea={Ea_J_mol/1000:.0f} kJ/mol (ASSUMED) scale={s:.2f}. D={D:.3g} m2/s."
        return D, notes, Provenance.ASSUMED_FOR_SENSITIVITY
    raise ValueError(f"unknown diffusivity mode {mode}")


def _series_avg(Fo: np.ndarray, n_terms: int = 80) -> np.ndarray:
    """C_avg/C_s = 1 - (6/π²) Σ n^{-2} exp(-n² π² Fo)."""
    Fo = np.asarray(Fo, dtype=float)
    s = np.zeros_like(Fo)
    for n in range(1, n_terms + 1):
        s += np.exp(-(n**2) * np.pi**2 * Fo) / (n**2)
    return 1.0 - (6.0 / np.pi**2) * s


def _series_center(Fo: np.ndarray, n_terms: int = 80) -> np.ndarray:
    """C(0)/C_s = 1 + 2 Σ (-1)^n exp(-n² π² Fo)."""
    Fo = np.asarray(Fo, dtype=float)
    s = np.zeros_like(Fo)
    for n in range(1, n_terms + 1):
        s += ((-1.0) ** n) * np.exp(-(n**2) * np.pi**2 * Fo)
    return 1.0 + 2.0 * s


def _series_profile(r_over_R: np.ndarray, Fo: float, n_terms: int = 80) -> np.ndarray:
    """C(r)/C_s for Dirichlet sphere. r=0 uses center limit."""
    x = np.asarray(r_over_R, dtype=float)
    out = np.ones_like(x)
    Fo = max(float(Fo), 0.0)
    for i, ri in enumerate(x):
        if ri < 1e-12:
            out[i] = float(_series_center(np.array([Fo]))[0])
            continue
        acc = 0.0
        for n in range(1, n_terms + 1):
            acc += ((-1.0) ** n / n) * np.sin(n * np.pi * ri) * np.exp(-(n**2) * np.pi**2 * Fo)
        out[i] = 1.0 + (2.0 / (np.pi * ri)) * acc
    return np.clip(out, 0.0, 1.0)


def fourier_number(D: float, t_s: float, R_m: float) -> float:
    return D * t_s / max(R_m, 1e-18) ** 2


def time_to_avg_threshold(D: float, R_m: float, threshold: float = 0.5) -> float:
    """t such that C_avg/C_s = threshold. Infinite D → 0; D=0 → inf."""
    if D <= 0.0:
        return float("inf")
    if threshold <= 0.0:
        return 0.0
    Fo_grid = np.logspace(-4, 1.5, 400)
    avg = _series_avg(Fo_grid)
    if avg[-1] < threshold:
        return float("inf")
    Fo = float(np.interp(threshold, avg, Fo_grid))
    return Fo * R_m**2 / D


def time_to_center_threshold(D: float, R_m: float, threshold: float = 0.5) -> float:
    if D <= 0.0:
        return float("inf")
    Fo_grid = np.logspace(-4, 1.5, 400)
    c = np.clip(_series_center(Fo_grid), 0.0, 1.0)
    if c[-1] < threshold:
        return float("inf")
    Fo = float(np.interp(threshold, c, Fo_grid))
    return Fo * R_m**2 / D


def activation_front_radius_m(R_m: float, Fo: float, threshold: float = 0.5) -> float:
    """Largest r where C(r) >= threshold, else 0 if none. Surface is always C_s."""
    if Fo <= 0.0:
        return 0.0
    rs = np.linspace(0.0, 1.0, 201)
    c = _series_profile(rs, Fo)
    hit = np.where(c >= threshold)[0]
    if hit.size == 0:
        return 0.0
    return float(rs[hit[0]] * R_m)


@dataclass(frozen=True, slots=True)
class SphereDiffusionResult:
    diameter_um: float
    R_m: float
    D_m2_s: float
    t_avg_50_s: float
    t_center_50_s: float
    t_avg_80_s: float
    Fo_avg_50: float
    notes: str
    provenance: Provenance

    def as_dict(self) -> dict:
        return {
            "diameter_um": self.diameter_um,
            "D_m2_s": self.D_m2_s,
            "t_avg_50_min": self.t_avg_50_s / 60.0,
            "t_center_50_min": self.t_center_50_s / 60.0,
            "t_avg_80_min": self.t_avg_80_s / 60.0,
            "notes": self.notes,
            "provenance": self.provenance.value,
        }


def evaluate_sphere(
    diameter_um: float,
    *,
    T_C: float = 25.0,
    mode: str = "lee_ambient",
    empirical_factor: float = 1.0,
    partition_K: float = 1.0,
    biot: float | None = None,
) -> SphereDiffusionResult:
    """partition_K scales effective surface concentration (K=C_org/C_aq). Biot unused in analytic Dirichlet.

    External mass-transfer: if biot is small, we inflate t by (1 + 2/Bi) heuristic (ASSUMED).
    """
    R = um_to_m(diameter_um) / 2.0
    D, dnotes, prov = diffusivity_m2_s(T_C, mode=mode, empirical_factor=empirical_factor)
    # Finite K: lower organic surface concentration slows the clock ~ 1/K if K<1.
    D_eff = D * min(max(partition_K, 0.05), 5.0)
    if biot is not None and biot > 0.0:
        D_eff = D_eff / (1.0 + 2.0 / biot)
        prov = Provenance.ASSUMED_FOR_SENSITIVITY
    t50 = time_to_avg_threshold(D_eff, R, 0.5)
    t80 = time_to_avg_threshold(D_eff, R, 0.8)
    tc = time_to_center_threshold(D_eff, R, 0.5)
    notes = (
        f"{dnotes} diameter={diameter_um:g} um; K={partition_K:g}; "
        f"t_avg50={t50/60.0:.3g} min. Dirichlet analytic sphere (Crank)."
    )
    return SphereDiffusionResult(
        diameter_um=diameter_um,
        R_m=R,
        D_m2_s=D_eff,
        t_avg_50_s=t50,
        t_center_50_s=tc,
        t_avg_80_s=t80,
        Fo_avg_50=fourier_number(D_eff, t50, R) if np.isfinite(t50) else float("nan"),
        notes=notes,
        provenance=prov,
    )


def diameter_sweep(
    T_C: float = 25.0,
    mode: str = "lee_ambient",
    empirical_factor: float = 1.0,
) -> list[SphereDiffusionResult]:
    return [
        evaluate_sphere(d, T_C=T_C, mode=mode, empirical_factor=empirical_factor)
        for d in DIAMETERS_UM
    ]


def profile_snapshot(diameter_um: float, t_s: float, D: float = D_LEE2025_M2_S, n_r: int = 81) -> tuple[np.ndarray, np.ndarray]:
    R = um_to_m(diameter_um) / 2.0
    r = np.linspace(0.0, R, n_r)
    Fo = fourier_number(D, t_s, R)
    c = _series_profile(r / R, Fo)
    return r, c


def volume_average_from_profile(r: np.ndarray, c: np.ndarray) -> float:
    """3/R³ ∫ c r² dr."""
    R = float(r[-1])
    if R <= 0.0:
        return float(c[-1])
    integ = np.trapezoid(c * r**2, r)
    return float(3.0 * integ / R**3)


def solve_sphere_fv(
    R_m: float,
    D: float,
    t_end_s: float,
    *,
    Cs: float = 1.0,
    n_r: int = 81,
    n_t: int = 400,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Explicit finite-volume solution of ∂C/∂t = D ∇²C in spherical coordinates.

    Dirichlet C(R)=Cs, Neumann ∂C/∂r(0)=0, C(r,0)=0.
    Returns (r, C(r,t_end), times unused except last).
    """
    r = np.linspace(0.0, R_m, n_r)
    dr = r[1] - r[0]
    dt = t_end_s / max(n_t, 1)
    Fo_cell = D * dt / max(dr, 1e-18) ** 2
    if Fo_cell > 0.4:
        n_t = int(np.ceil(t_end_s * D / (0.35 * dr**2))) + 2
        dt = t_end_s / n_t
    C = np.zeros(n_r)
    C[-1] = Cs
    for _ in range(n_t):
        Cnew = C.copy()
        for i in range(1, n_r - 1):
            ri = r[i]
            d2 = (C[i + 1] - 2.0 * C[i] + C[i - 1]) / dr**2
            d1 = (C[i + 1] - C[i - 1]) / (2.0 * dr)
            lap = d2 + 2.0 * d1 / max(ri, 0.5 * dr)
            Cnew[i] = C[i] + dt * D * lap
        Cnew[0] = Cnew[1]
        Cnew[-1] = Cs
        C = np.clip(Cnew, 0.0, Cs)
    return r, C, np.array([t_end_s])


def fraction_activated(c_over_cs: np.ndarray, r: np.ndarray, threshold: float = 0.5) -> float:
    """Volume fraction where C/Cs >= threshold."""
    mask = np.asarray(c_over_cs) >= threshold
    if not np.any(mask):
        return 0.0
    w = r**2
    return float(np.trapezoid(mask.astype(float) * w, r) / max(np.trapezoid(w, r), 1e-30))


def shell_reduced_D_times(
    diameter_um: float,
    D: float = D_LEE2025_M2_S,
) -> dict[str, float]:
    """Compare constant D, 10× reduction after surface gel, and continuously declining D.

    Continuous model: D_eff = D / (1 + 9 Fo) analogue of growing resistance (ASSUMED).
    """
    base = evaluate_sphere(diameter_um, T_C=25.0, mode="lee_ambient")
    slow = evaluate_sphere(diameter_um, T_C=25.0, mode="lee_ambient", empirical_factor=0.1)
    # Continuous: solve t from Fo_eff with D/(1+k Fo) ≈ implicit. Use 4× slower as mid.
    mid = evaluate_sphere(diameter_um, T_C=25.0, mode="lee_ambient", empirical_factor=0.25)
    return {
        "diameter_um": diameter_um,
        "t_const_D_min": base.t_avg_50_s / 60.0,
        "t_D_x0.1_min": slow.t_avg_50_s / 60.0,
        "t_D_x0.25_min": mid.t_avg_50_s / 60.0,
    }
