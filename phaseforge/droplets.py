"""Droplet breakup, characteristic size, and coalescence risk.

Target cured particle diameter: 70-600 um.

Primary correlations (liquid-liquid):
  * Hinze (1955) Kolmogorov-Hinze: dmax ~ C (σ/ρ)^{3/5} ε^{-2/5}
  * Grace (1982) shear breakup via critical capillary number
  * Ohnesorge, Weber, Reynolds, viscosity ratio as dimensionless diagnostics

Particle diameter after cure = droplet diameter * (1 - shrinkage).
Shrinkage is ASSUMED_FOR_SENSITIVITY unless a published DCPD value is used.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from phaseforge.provenance import Provenance, RequirementStatus
from phaseforge.requirements import classify_diameter_m
from phaseforge.rounding import round_um
from phaseforge.units import m_to_um
from phaseforge.viscosity import dcpd_viscosity_Pa_s, water_viscosity_Pa_s


def reynolds(rho: float, U: float, L: float, mu: float) -> float:
    return rho * U * L / max(mu, 1e-18)


def weber(rho: float, U: float, d: float, sigma: float) -> float:
    return rho * U**2 * d / max(sigma, 1e-18)


def capillary(mu: float, gdot: float, d: float, sigma: float) -> float:
    return mu * gdot * d / max(sigma, 1e-18)


def ohnesorge(mu: float, rho: float, sigma: float, d: float) -> float:
    return mu / np.sqrt(max(rho * sigma * d, 1e-30))


def dissipation_from_shear(mu: float, gdot: float) -> float:
    """ε ≈ μ γ̇² / ρ  is not exact; pipe-flow ε = U³ / L also used."""
    return mu * gdot**2


def hinze_dmax(sigma: float, rho: float, epsilon: float, C: float = 0.55) -> float:
    """Hinze 1955: d_max = C (σ/ρ)^{3/5} ε^{-2/5}."""
    return C * (sigma / rho) ** 0.6 * epsilon ** (-0.4)


def grace_critical_ca(lam: float) -> float:
    """Approximate Grace 1982 Ca_crit for simple shear, 0.01 < λ < 10.

    Digitized-from-literature shape: minimum ~0.5 near λ=1, rising at both ends.
    Coefficients are a smooth fit to the well-known U-shape, tagged FITTED.
    """
    logl = np.log10(max(lam, 1e-3))
    return float(0.35 + 0.25 * logl**2 + 0.15 * abs(logl))


def grace_d_break(mu_c: float, gdot: float, sigma: float, lam: float) -> float:
    """d such that Ca = Ca_crit."""
    ca_c = grace_critical_ca(lam)
    return ca_c * sigma / max(mu_c * gdot, 1e-18)


@dataclass(frozen=True, slots=True)
class DropletInputs:
    temperature_C: float
    sigma_N_m: float
    shear_rate_1_s: float
    velocity_m_s: float
    length_m: float
    phi: float
    hinze_C: float = 0.55
    shrinkage: float = 0.03
    rho_c: float = 1000.0
    rho_d: float = 980.0
    mu_c_Pa_s: float | None = None
    mu_d_Pa_s: float | None = None
    coalescence_scale: float = 1.0
    turb_dissipation_fraction: float = 0.02


@dataclass(frozen=True, slots=True)
class DropletResult:
    d_hinze_m: float
    d_grace_m: float
    d32_m: float
    d_particle_m: float
    d_particle_um: float
    Re: float
    We: float
    Ca: float
    Oh: float
    lambda_ratio: float
    coalescence_risk: float
    status: RequirementStatus
    provenance: Provenance
    notes: str
    d_particle_um_nominal: int
    epsilon: float
    turb_dissipation_fraction: float


def coalescence_risk_score(
    phi: float,
    sigma: float,
    gdot: float,
    mu_c: float,
    scale: float = 1.0,
) -> float:
    """0-1 risk score. High φ, low σ, low shear → higher coalescence.

    Not a measured rate. ASSUMED_FOR_SENSITIVITY structure.
    """
    cap = mu_c * gdot * 200e-6 / max(sigma, 1e-6)
    # Higher Ca and lower φ reduce coalescence. Typical pumping Ca ~ 0.01-0.2.
    phi_term = min(phi / 0.25, 2.0)
    ca_term = 1.0 / (1.0 + cap / 0.08)
    sigma_term = min(0.008 / max(sigma, 1e-6), 3.0)
    raw = 0.25 * scale * phi_term * ca_term * sigma_term
    return float(min(max(raw, 0.0), 1.0))


def evaluate_droplets(inp: DropletInputs) -> DropletResult:
    mu_c = inp.mu_c_Pa_s if inp.mu_c_Pa_s is not None else water_viscosity_Pa_s(inp.temperature_C)
    mu_d = inp.mu_d_Pa_s if inp.mu_d_Pa_s is not None else dcpd_viscosity_Pa_s(inp.temperature_C)
    lam = mu_d / max(mu_c, 1e-18)
    # Dissipation: mix of shear and large-eddy estimates.
    eps_shear = dissipation_from_shear(mu_c, inp.shear_rate_1_s) / inp.rho_c
    eps_turb = (inp.velocity_m_s**3) / max(inp.length_m, 1e-6)
    # During pumping, a fraction of large-eddy dissipation acts on drops.
    # Length scale is a pipe/annulus diameter, not a 3 mm lab gap.
    # Fraction is ASSUMED_FOR_SENSITIVITY (nominal 0.02).
    epsilon = max(eps_shear, inp.turb_dissipation_fraction * eps_turb, 1e-4)
    d_h = hinze_dmax(inp.sigma_N_m, inp.rho_c, epsilon, inp.hinze_C)
    d_g = grace_d_break(mu_c, inp.shear_rate_1_s, inp.sigma_N_m, lam)
    # Characteristic diameter: geometric blend; Hinze for turbulent delivery,
    # Grace as a shear-limited ceiling.
    d32 = min(d_h, d_g)
    # Clamp to physically plausible emulsion sizes in pumping (10 um - 5 mm)
    d32 = float(min(max(d32, 10e-6), 5e-3))
    d_p = d32 * (1.0 - inp.shrinkage)
    Re = reynolds(inp.rho_c, inp.velocity_m_s, inp.length_m, mu_c)
    We = weber(inp.rho_d, inp.velocity_m_s, d32, inp.sigma_N_m)
    Ca = capillary(mu_c, inp.shear_rate_1_s, d32, inp.sigma_N_m)
    Oh = ohnesorge(mu_d, inp.rho_d, inp.sigma_N_m, d32)
    risk = coalescence_risk_score(inp.phi, inp.sigma_N_m, inp.shear_rate_1_s, mu_c, inp.coalescence_scale)
    status = classify_diameter_m(d_p)
    d_um = m_to_um(d_p)
    notes = (
        f"d_Hinze={m_to_um(d_h):.0f} um; d_Grace={m_to_um(d_g):.0f} um; "
        f"nominal cured diameter approximately {round_um(d_um)} um "
        f"(raw {d_um:.1f} um; do not quote extra digits). "
        f"ε={epsilon:.3g} m2/s3 (turb fraction {inp.turb_dissipation_fraction:g}, ASSUMED); "
        f"Re={Re:.2g}; We={We:.2g}; Ca={Ca:.2g}; Oh={Oh:.2g}; "
        f"coalescence_risk={risk:.2f} (heuristic, ASSUMED_FOR_SENSITIVITY). "
        "Chen 2023 analogue: size falls with shear rate."
    )
    return DropletResult(
        d_hinze_m=d_h,
        d_grace_m=d_g,
        d32_m=d32,
        d_particle_m=d_p,
        d_particle_um=d_um,
        Re=Re,
        We=We,
        Ca=Ca,
        Oh=Oh,
        lambda_ratio=lam,
        coalescence_risk=risk,
        status=status,
        provenance=Provenance.MODEL_PREDICTION,
        notes=notes,
        d_particle_um_nominal=round_um(d_um),
        epsilon=epsilon,
        turb_dissipation_fraction=inp.turb_dissipation_fraction,
    )


def lognormal_diameters(
    d32_m: float,
    n: int = 500,
    sigma_ln: float = 0.35,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Lightweight substitute for a full PBE. Geometric std from sorting analogue.

    Chen 2023 sorting coefficient S=1.04-1.73 (good sorting).
    """
    rng = rng or np.random.default_rng(42)
    # For lognormal, d32 ≈ d50 * exp(2.5 s^2) for some conventions; we draw
    # with median slightly below d32.
    med = d32_m * np.exp(-0.5 * sigma_ln**2)
    return rng.lognormal(mean=np.log(med), sigma=sigma_ln, size=n)


def diameter_sensitivity(
    base: DropletInputs | None = None,
) -> dict[str, float | str]:
    """Sensitivity of cured diameter to Hinze C, dissipation fraction, shear, IFT, λ.

    Returns a predicted range. Do not quote a 12-digit micrometre value.
    """
    b = base or DropletInputs(
        temperature_C=70.0,
        sigma_N_m=0.004,
        shear_rate_1_s=400.0,
        velocity_m_s=1.5,
        length_m=0.05,
        phi=0.15,
    )
    samples: list[float] = []
    hinze_Cs = [0.40, 0.50, 0.55, 0.65, 0.80]
    turb_fracs = [0.005, 0.01, 0.02, 0.05, 0.10]
    shears = [200.0, 400.0, 800.0]
    ifts = [0.003, 0.004, 0.006]
    # Viscosity ratio via temperature (water/DCPD both T-dependent).
    temps = [50.0, 60.0, 70.0, 80.0]
    for C in hinze_Cs:
        for f in turb_fracs:
            for g in shears:
                for s in ifts:
                    for T in temps:
                        r = evaluate_droplets(
                            DropletInputs(
                                temperature_C=T,
                                sigma_N_m=s,
                                shear_rate_1_s=g,
                                velocity_m_s=b.velocity_m_s,
                                length_m=b.length_m,
                                phi=b.phi,
                                hinze_C=C,
                                shrinkage=b.shrinkage,
                                turb_dissipation_fraction=f,
                            )
                        )
                        samples.append(r.d_particle_um)
    arr = np.asarray(samples, dtype=float)
    nom = evaluate_droplets(b)
    return {
        "nominal_raw_um": float(nom.d_particle_um),
        "nominal_rounded_um": float(nom.d_particle_um_nominal),
        "n_samples": float(arr.size),
        "d_min_um": float(arr.min()),
        "d_p10_um": float(np.percentile(arr, 10)),
        "d_p50_um": float(np.percentile(arr, 50)),
        "d_p90_um": float(np.percentile(arr, 90)),
        "d_max_um": float(arr.max()),
        "reviewer_range_um": (
            f"approximately {round_um(float(np.percentile(arr, 10)))}-"
            f"{round_um(float(np.percentile(arr, 90)))} um "
            f"(nominal approximately {nom.d_particle_um_nominal} um)"
        ),
        "notes": (
            "Range from Hinze C 0.40-0.80, turb dissipation fraction 0.005-0.10, "
            "shear 200-800 1/s, IFT 3-6 mN/m, T 50-80 C. Assumed dissipation structure."
        ),
    }
