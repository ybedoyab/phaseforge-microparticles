"""Figures, tables, traceability, and final metrics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from phaseforge.coupled import (
    CoupledResult,
    OperatingPoint,
    design_space,
    evaluate_point,
    from_yaml_point,
)
from phaseforge.droplets import DropletInputs, diameter_sensitivity, evaluate_droplets
from phaseforge.ht_catalyst import CATALYST_MO_LATENT, evaluate_ht_family
from phaseforge.kinetics import (
    KineticsInputs,
    conversion_profile,
    evaluate_kinetics,
    feasible_activation_map,
    predicted_vs_observed,
)
from phaseforge.mechanics import sf_vs_temperature
from phaseforge.optimization import select_envelopes
from phaseforge.permeability import PermeabilityInputs, diameter_sweep_um, evaluate_permeability
from phaseforge.provenance import RequirementStatus
from phaseforge.requirements import load_baseline, repo_root
from phaseforge.rounding import round_cP, round_krel, round_min, round_prob, round_sf, round_um
from phaseforge.uncertainty import monte_carlo_compliance, sobol_transform_time, tornado
from phaseforge.units import PSI_6000_MPA, um_to_m
from phaseforge.viscosity import viscosity_design_map

plt.rcParams.update(
    {
        "figure.dpi": 140,
        "savefig.dpi": 300,
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "legend.fontsize": 8,
        "figure.facecolor": "white",
        "axes.grid": True,
        "grid.alpha": 0.3,
    }
)


def _ensure_dirs() -> tuple[Path, Path, Path]:
    root = repo_root()
    fig = root / "figures"
    tab = root / "results" / "tables"
    proc = root / "results" / "processed"
    fig.mkdir(parents=True, exist_ok=True)
    tab.mkdir(parents=True, exist_ok=True)
    proc.mkdir(parents=True, exist_ok=True)
    return fig, tab, proc


def _save(fig: plt.Figure, name: str, figdir: Path) -> None:
    fig.tight_layout()
    fig.savefig(figdir / f"{name}.png", dpi=300)
    fig.savefig(figdir / f"{name}.svg")
    fig.savefig(figdir / f"{name}.pdf")
    plt.close(fig)


def figure_mechanism_schematic(figdir: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 3.2))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 3)
    ax.axis("off")
    stages = [
        (1.0, "Low-viscosity\naqueous carrier"),
        (3.2, "Stabilized\nDCPD-rich droplets"),
        (5.5, "HPHT transport\n(latency holds)"),
        (7.8, "Latency expires\nROMP in droplets"),
        (10.1, "Discrete solid\nmicroparticles"),
        (12.4, "Packed assembly\nopen flow paths"),
    ]
    for x, text in stages:
        circ = plt.Circle((x, 1.6), 0.85, fill=False, lw=1.5, color="#1f4e79")
        ax.add_patch(circ)
        ax.text(x, 1.6, text, ha="center", va="center", fontsize=7.5)
    for i in range(len(stages) - 1):
        ax.annotate(
            "",
            xy=(stages[i + 1][0] - 0.9, 1.6),
            xytext=(stages[i][0] + 0.9, 1.6),
            arrowprops=dict(arrowstyle="->", color="#c45911", lw=1.6),
        )
    ax.set_title(
        "PhaseForge proposed mechanism (schematic, not experimental photography)",
        loc="left",
    )
    ax.text(
        0.2,
        0.25,
        "Isolated-droplet microreactors: polymerization is intended to remain inside each droplet, avoiding a bulk gel plug.",
        fontsize=8,
    )
    _save(fig, "01_mechanism_schematic", figdir)


def figure_requirement_architecture(figdir: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.axis("off")
    boxes = [
        (0.05, 0.70, 0.28, 0.22, "Delivery\nliquid, ≤10 cP\n≤150 °C, ≤10,000 psi"),
        (0.36, 0.70, 0.28, 0.22, "Transformation\ncontrolled activation\n25–75 min"),
        (0.67, 0.70, 0.28, 0.22, "Particles\n70–600 μm\nspherical, discrete"),
        (0.20, 0.38, 0.28, 0.22, "Mechanics\n4,500–6,000 psi\nload-bearing"),
        (0.52, 0.38, 0.28, 0.22, "System flow\nopen pathways\nno bulk plug"),
        (0.20, 0.08, 0.60, 0.20, "Coupled envelope + UQ\nPASS / MARGINAL / FAIL / UNKNOWN\nUNKNOWN is never recast as PASS"),
    ]
    for x, y, w, h, t in boxes:
        ax.add_patch(plt.Rectangle((x, y), w, h, fill=True, facecolor="#deebf7", edgecolor="#1f4e79", lw=1.4))
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=9)
    ax.set_title("Challenge requirement architecture (Innocentive public statement)")
    _save(fig, "02_requirement_architecture", figdir)


def figure_activation_map(figdir: Path, tab: Path) -> None:
    T = np.linspace(40.0, 150.0, 45)
    inh = np.linspace(0.0, 1.0, 21)
    Z = feasible_activation_map(T, inh)
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    im = ax.pcolormesh(T, inh, Z, shading="auto", cmap="viridis", vmin=0, vmax=120)
    cs = ax.contour(T, inh, Z, levels=[25, 75], colors="white", linewidths=1.5)
    ax.clabel(cs, fmt="%g min", fontsize=8)
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel("Inhibitor index (0 = uninhibited Grubbs-II analogue)")
    ax.set_title("Predicted t_solid (min). White contours = 25 and 75 min.")
    fig.colorbar(im, ax=ax, label="t_transform (min)")
    ax.text(
        0.02,
        -0.18,
        "Arrhenius calibrated to Madbouly 2025 gel times (40–60 °C). T>110 °C is a severe extrapolation; "
        "status at 150 °C for published Ru/phosphite is FAIL (too fast), not a forced PASS.",
        transform=ax.transAxes,
        fontsize=7.5,
        wrap=True,
    )
    _save(fig, "04_activation_time_map", figdir)
    pd.DataFrame(Z, index=np.round(inh, 3), columns=np.round(T, 2)).to_csv(tab / "activation_map.csv")


def figure_conversion(figdir: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.2))
    t = np.linspace(0, 120 * 60, 400)
    for T, ls in [(50, "-"), (60, "--"), (80, ":")]:
        r = evaluate_kinetics(KineticsInputs(temperature_C=T, inhibitor_index=0.6))
        a = conversion_profile(t, r.t_gel_s)
        ax.plot(t / 60.0, a, ls, label=f"{T} °C, t_gel={r.t_gel_s/60:.1f} min")
    ax.axhline(0.4, color="gray", lw=0.8, label="α_gel criterion")
    ax.axhline(0.8, color="black", lw=0.8, label="α_solid criterion")
    ax.axvspan(25, 75, color="#c6dbef", alpha=0.4, label="25–75 min window")
    ax.set_xlabel("Time (min)")
    ax.set_ylabel("Conversion α")
    ax.set_ylim(0, 1.05)
    ax.set_xlim(0, 120)
    ax.legend(loc="lower right")
    ax.set_title("Phenomenological conversion vs time (inhibitor index = 0.6)")
    _save(fig, "05_conversion_vs_time", figdir)


def figure_viscosity_map(figdir: Path, tab: Path) -> None:
    T = np.linspace(20, 150, 40)
    P = np.linspace(0.02, 0.35, 30)
    Z = viscosity_design_map(T, P)
    fig, ax = plt.subplots(figsize=(7.2, 5))
    im = ax.pcolormesh(T, P, Z, shading="auto", cmap="YlOrRd", vmin=0.2, vmax=12)
    cs = ax.contour(T, P, Z, levels=[10], colors="navy", linewidths=1.8)
    ax.clabel(cs, fmt="10 cP")
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel("Dispersed-phase volume fraction φ")
    ax.set_title("Effective emulsion viscosity (Taylor/Pal), DCPD-in-brine analogue")
    fig.colorbar(im, ax=ax, label="μ_eff (cP)")
    _save(fig, "06_viscosity_design_map", figdir)
    pd.DataFrame(Z, index=np.round(P, 3), columns=np.round(T, 1)).to_csv(tab / "viscosity_map.csv")


def figure_diameter_map(figdir: Path) -> None:
    shears = np.logspace(2, 3.5, 40)
    sigmas = np.array([0.002, 0.004, 0.008, 0.015])
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for s in sigmas:
        ds = []
        for g in shears:
            r = evaluate_droplets(
                DropletInputs(
                    temperature_C=60.0,
                    sigma_N_m=float(s),
                    shear_rate_1_s=float(g),
                    velocity_m_s=2.0,
                    length_m=0.003,
                    phi=0.15,
                )
            )
            ds.append(r.d_particle_um)
        ax.plot(shears, ds, label=f"σ = {s*1e3:.1f} mN/m")
    ax.axhspan(70, 600, color="#c7e9c0", alpha=0.45, label="70–600 μm target")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Shear rate (1/s)")
    ax.set_ylabel("Predicted particle diameter (μm)")
    ax.set_title("Hinze/Grace characteristic diameter vs shear and IFT (order-of-magnitude)")
    ax.legend()
    _save(fig, "07_droplet_diameter_map", figdir)


def figure_diameter_uncertainty(figdir: Path, tab: Path) -> dict:
    sens = diameter_sensitivity()
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    labels = ["p10", "nominal", "p50", "p90"]
    vals = [
        sens["d_p10_um"],
        sens["nominal_raw_um"],
        sens["d_p50_um"],
        sens["d_p90_um"],
    ]
    ax.bar(labels, vals, color="#3182bd")
    ax.axhspan(70, 600, color="#c7e9c0", alpha=0.35, label="70–600 μm target")
    ax.set_ylabel("Cured diameter (μm)")
    ax.set_title(
        f"Hinze/Grace sensitivity: {sens['reviewer_range_um']}. "
        "Do not quote 273.046 μm precision."
    )
    ax.legend()
    _save(fig, "15_diameter_uncertainty", figdir)
    pd.DataFrame([sens]).to_csv(tab / "diameter_sensitivity.csv", index=False)
    return sens


def figure_ht_onset(figdir: Path) -> None:
    ht = evaluate_ht_family()
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    ax.barh(
        ["Elser 2018 T_onset", "Momin 2021 T_onset", "Elser T_exo,max", "Momin T_exo,max"],
        [
            140.0 - 65.0,
            142.0 - 52.0,
            183.0 - 98.0,
            174.0 - 99.0,
        ],
        left=[65.0, 52.0, 98.0, 99.0],
        color=["#3182bd", "#6baed6", "#fd8d3c", "#fdae6b"],
        height=0.55,
    )
    ax.axvline(150.0, color="crimson", lw=1.2, label="150 °C challenge wording")
    ax.set_xlabel("Temperature (°C)")
    ax.set_xlim(40, 200)
    ax.set_title(
        "PhaseForge-HT published DSC windows (not isothermal 25–75 min at 150 °C). "
        f"Status: {ht.status.value}."
    )
    ax.legend(loc="lower right")
    ax.text(
        0.02,
        -0.22,
        "A heating-ramp onset is a pathway toward high-T latency, not a PASS for the Innocentive hold window.",
        transform=ax.transAxes,
        fontsize=8,
    )
    _save(fig, "16_phaseforge_ht_onset", figdir)


def figure_mechanics(figdir: Path) -> None:
    T = np.linspace(20, 180, 80)
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for Tg, ls in [(140, "-"), (155, "--"), (200, ":")]:
        sf = sf_vs_temperature(T, Tg_C=Tg)
        ax.plot(T, sf, ls, label=f"Tg = {Tg} °C scenario")
    ax.axhline(1.0, color="crimson", lw=1.0, label="SF = 1")
    ax.axvline(150, color="gray", lw=0.8)
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel("SF_mech vs 6,000 psi")
    ax.set_title("Mechanical safety factor. 150 °C near typical pDCPD Tg is UNKNOWN.")
    ax.legend()
    ax.set_ylim(0, 3.5)
    _save(fig, "08_mechanical_sf_vs_T", figdir)


def figure_permeability(figdir: Path, tab: Path) -> None:
    ds = diameter_sweep_um()
    rows = []
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for settled, marker, label in [(False, "o", "distributed φ=0.15"), (True, "s", "settled pack")]:
        ks = []
        for d in ds:
            r = evaluate_permeability(
                PermeabilityInputs(d_m=um_to_m(d), phi_particles=0.15, settled=settled)
            )
            ks.append(r.k_mD)
            rows.append({"d_um": d, "settled": settled, "k_mD" : r.k_mD, "porosity": r.porosity})
        ax.plot(ds, ks, marker=marker, label=label)
    ax.set_xlabel("Particle diameter (μm)")
    ax.set_ylabel("Permeability estimate (mD)")
    ax.set_yscale("log")
    ax.set_title(
        "Residual permeability: distributed vs settled (analytical estimate). "
        "k_open is assumed; not measured fracture conductivity."
    )
    ax.legend()
    _save(fig, "09_residual_permeability", figdir)
    pd.DataFrame(rows).to_csv(tab / "permeability_sweep.csv", index=False)


def figure_feasible_window(figdir: Path, tab: Path, results: list[CoupledResult]) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 5))
    colors = {
        RequirementStatus.PASS: "#238b45",
        RequirementStatus.MARGINAL: "#fec44f",
        RequirementStatus.FAIL: "#d7301f",
        RequirementStatus.UNKNOWN: "#737373",
    }
    for r in results:
        T = float(r.notes.split("T=")[1].split(" ")[0])
        phi = float(r.notes.split("φ=")[1].split(",")[0])
        ax.scatter(T, phi, c=colors[r.core_overall], s=48, edgecolors="k", linewidths=0.3)
    for lab, c in colors.items():
        ax.scatter([], [], c=c, label=lab.value, edgecolors="k")
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel("Dispersed volume fraction φ")
    ax.set_title(
        "Core physics envelope (viscosity, time, size, mechanics, thermal). "
        "Agglomeration heuristic and unvalidated conductivity remain MARGINAL."
    )
    ax.legend(title="Overall")
    _save(fig, "10_coupled_feasible_window", figdir)
    pd.DataFrame([r.as_dict() for r in results]).to_csv(tab / "coupled_design_space.csv", index=False)


def figure_mc(figdir: Path, mc: dict[str, Any]) -> None:
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    labels = list(mc["probabilities"].keys())
    vals = [round_prob(mc["probabilities"][k]) for k in labels]
    ax.barh(labels, vals, color="#2b8cbe")
    ax.set_xlim(0, 1)
    ax.set_xlabel("Estimated probability (LHS, 40–90 °C; 2 significant digits, n=400)")
    ax.set_title(f"Monte Carlo simultaneous compliance (n={mc['n']}, seed={mc['seed']})")
    _save(fig, "11_monte_carlo_compliance", figdir)


def figure_sobol(figdir: Path, sob: dict[str, Any]) -> None:
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    y = np.arange(len(sob["names"]))
    ax.barh(y - 0.18, sob["S1"], height=0.35, label="S1", color="#3182bd")
    ax.barh(y + 0.18, sob["ST"], height=0.35, label="ST", color="#fd8d3c")
    ax.set_yticks(y)
    ax.set_yticklabels(sob["names"])
    ax.set_xlabel("Sobol index")
    ax.set_title("Global sensitivity of log10(t_transform) (40–90 °C envelope)")
    ax.legend()
    _save(fig, "12_sobol_sensitivity", figdir)


def figure_validation(figdir: Path, tab: Path) -> None:
    rows = predicted_vs_observed()
    fig, ax = plt.subplots(figsize=(5.4, 5.0))
    obs = [float(r["t_obs_min"]) for r in rows]
    pred = [float(r["t_pred_min"]) for r in rows]
    ax.scatter(obs, pred, c="#1f4e79")
    lim = [0, max(max(obs), max(pred)) * 1.1]
    ax.plot(lim, lim, "k--", lw=0.8)
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("Published t_gel (min)")
    ax.set_ylabel("Model t_gel (min)")
    ax.set_title("Kinetics validation against published gel times")
    _save(fig, "03_literature_validation_kinetics", figdir)
    pd.DataFrame(rows).to_csv(tab / "kinetics_validation.csv", index=False)


def figure_evidence_matrix(figdir: Path, trace: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.axis("off")
    ax.table(
        cellText=trace[["requirement_id", "status", "confidence", "predicted"]].values.tolist(),
        colLabels=["ID", "status", "confidence", "predicted"],
        loc="center",
        cellLoc="left",
    )
    ax.set_title("Requirement evidence snapshot (see CSV for full matrix)")
    _save(fig, "14_evidence_uncertainty_matrix", figdir)


def write_schematic_svg(figdir: Path) -> None:
    svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="320" viewBox="0 0 1100 320">
  <rect width="1100" height="320" fill="white"/>
  <text x="24" y="28" font-size="16" font-family="Segoe UI, Arial">PhaseForge proposed mechanism — not experimental photography</text>
  <g font-family="Segoe UI, Arial" font-size="12" text-anchor="middle">
    <circle cx="90" cy="160" r="62" fill="#deebf7" stroke="#1f4e79" stroke-width="2"/>
    <text x="90" y="156">Aqueous</text><text x="90" y="172">carrier ≤10 cP</text>
    <circle cx="270" cy="160" r="62" fill="#fff2cc" stroke="#1f4e79" stroke-width="2"/>
    <text x="270" y="148">DCPD-rich</text><text x="270" y="164">droplets</text><text x="270" y="180">microreactors</text>
    <circle cx="450" cy="160" r="62" fill="#fce4d6" stroke="#1f4e79" stroke-width="2"/>
    <text x="450" y="148">HPHT</text><text x="450" y="164">transport</text><text x="450" y="180">latent ROMP</text>
    <circle cx="630" cy="160" r="62" fill="#f8cbad" stroke="#1f4e79" stroke-width="2"/>
    <text x="630" y="148">Latency</text><text x="630" y="164">expires</text><text x="630" y="180">in-drop ROMP</text>
    <circle cx="810" cy="160" r="62" fill="#c6efce" stroke="#1f4e79" stroke-width="2"/>
    <text x="810" y="148">Discrete</text><text x="810" y="164">70–600 μm</text><text x="810" y="180">particles</text>
    <circle cx="990" cy="160" r="62" fill="#c5e0b4" stroke="#1f4e79" stroke-width="2"/>
    <text x="990" y="148">Open</text><text x="990" y="164">flow paths</text><text x="990" y="180">around pack</text>
    <path d="M152 160 H208" stroke="#c45911" stroke-width="3" marker-end="url(#a)"/>
    <path d="M332 160 H388" stroke="#c45911" stroke-width="3" marker-end="url(#a)"/>
    <path d="M512 160 H568" stroke="#c45911" stroke-width="3" marker-end="url(#a)"/>
    <path d="M692 160 H748" stroke="#c45911" stroke-width="3" marker-end="url(#a)"/>
    <path d="M872 160 H928" stroke="#c45911" stroke-width="3" marker-end="url(#a)"/>
  </g>
  <defs><marker id="a" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#c45911"/></marker></defs>
  <text x="24" y="300" font-size="11" font-family="Segoe UI, Arial">Original schematic. No copyrighted figures were copied.</text>
</svg>
"""
    (figdir / "01_mechanism_schematic_vector.svg").write_text(svg, encoding="utf-8")


def build_traceability(
    nom: CoupledResult,
    hpht: CoupledResult,
) -> pd.DataFrame:
    rows = []

    def add(rid, model, predicted, unit, status, conf, lit, remain):
        rows.append(
            {
                "requirement_id": rid,
                "model_or_evidence": model,
                "literature_support": lit,
                "predicted": predicted,
                "unit": unit,
                "confidence": conf,
                "status": status if isinstance(status, str) else status.value,
                "remaining_validation": remain,
            }
        )

    add(
        "R01_liquid_delivery",
        "baseline concept + viscosity",
        "liquid emulsion, no solids injected",
        "-",
        RequirementStatus.PASS,
        "high (by design; analogue Chen 2023)",
        "CHEN2023_OMEGA; DELLA2005_JAPS",
        "Confirm no premature solids at mix temperature.",
    )
    add(
        "R02_viscosity",
        "Taylor/Pal emulsion viscosity",
        f"approximately {round_cP(nom.viscosity.mu_eff_cP)} (nominal 60 C)",
        "cP",
        nom.viscosity.status,
        "medium-high at 20-80 C; DCPD 1 cP is published",
        "MADBOULY2025_ACS_OMEGA; CHEN2023_OMEGA (analogue mixture is higher)",
        "Measure emulsion viscosity of the actual stabilizer package.",
    )
    add(
        "R03_transport_temperature",
        "upper-T capability of exact PhaseForge",
        "moderate-T branch shows mechanism feasibility; PhaseForge-HT is the proposed 150 C pathway; DSC onset is not isothermal 25-75 min",
        "degC",
        RequirementStatus.UNKNOWN,
        "low at 150 C for exact PhaseForge; published Mo DSC onsets 52-142 C are not a hold-time proof",
        "Madbouly 40-60 C; Hu 50-80 C; Elser 2018; Momin 2021 (DSC, not isothermal 150 C)",
        "Isothermal latency of the exact brine-dispersed fluid at 150 C.",
    )
    add(
        "R04_transport_pressure",
        "literature liquids + coupled notes",
        "10000 psi = 68.95 MPa; liquids remain liquid",
        "psi",
        RequirementStatus.UNKNOWN,
        "low (pressure effect on ROMP not retrieved as a quantitative rate law)",
        "US11377580B2 HPHT polymer claims (not a particle-size study)",
        "HPHT rheology and cure under 10,000 psi.",
    )
    add(
        "R05_post_transform_pressure",
        "mechanics (temperature-qualified)",
        f"6000 psi = {PSI_6000_MPA:.1f} MPa; moderate-T {nom.mechanics.status_moderate.value}; 150 C UNKNOWN",
        "psi",
        RequirementStatus.UNKNOWN,
        "medium at 60 C; UNKNOWN at 150 C",
        "PMC12566568; US11377580B2 Table 3 analogue at 98 C; CHEN2023 crush at 52-69 MPa (epoxy analogue)",
        "Particle crush at temperature and 6000 psi.",
    )
    add(
        "R06_controlled_activation",
        "latent ROMP kinetics",
        "temperature + inhibitor index",
        "-",
        RequirementStatus.PASS if nom.kinetics.status != RequirementStatus.FAIL else nom.kinetics.status,
        "medium (published latency analogues)",
        "KORDES2024_MME; HU2018_JPSE; US11377580B2",
        "Programmed delay in brine-dispersed droplets.",
    )
    add(
        "R07_transformation_window",
        "Arrhenius t_solid (Ru/phosphite)",
        f"approximately {round_min(nom.kinetics.t_transform_min)} min nominal; HPHT approximately {round_min(hpht.kinetics.t_transform_min)} min FAIL",
        "min",
        nom.kinetics.status,
        "medium in 40-80 C; FAIL at 150 C for published Ru/phosphite",
        "MADBOULY2025; HU2018",
        "Droplet-scale conversion in water at target T.",
    )
    add(
        "R08_discrete_particles",
        "phi isolation + Della Martina analogue",
        f"phi={nom.as_dict().get('porosity', '')} continuous; discrete if phi<0.55",
        "-",
        RequirementStatus.PASS,
        "medium (analogue beads; not PhaseForge experiments)",
        "DELLA2005_JAPS; CHEN2023_OMEGA",
        "Morphology after cure in brine.",
    )
    add(
        "R09_particle_size",
        "Hinze/Grace with dissipation sensitivity",
        f"approximately {round_um(nom.droplets.d_particle_um)} um nominal (robust range in diameter_sensitivity.csv)",
        "um",
        nom.droplets.status,
        "medium (order-of-magnitude; assumed dissipation structure)",
        "Hinze 1955; Grace 1982; CHEN2023 shear-size trend",
        "Measure d32 vs shear for the actual IFT.",
    )
    add(
        "R10_sphericity",
        "interfacial energy + analogue",
        "near-spherical expected if IFT-stabilized",
        "-",
        RequirementStatus.MARGINAL,
        "medium analogue, not measured here",
        "CHEN2023 sphericity vs sand; BAI2025 sphericity >=0.9; YANG2026 0.9",
        "Image analysis of cured particles.",
    )
    add(
        "R11_minimal_adhesion",
        "coalescence_risk_score heuristic (ASSUMED_FOR_SENSITIVITY)",
        f"score approximately {nom.droplets.coalescence_risk:.2f}; heuristic cannot independently PASS",
        "risk 0-1",
        nom.agglomeration,
        "low (no PhaseForge adhesion test)",
        "Chen interfacial-film discussion; no PhaseForge adhesion test",
        "Cure in contact; sticky-window mapping.",
    )
    add(
        "R12_load_bearing",
        "mechanics SF at moderate T (PASS candidate)",
        f"SF approximately {round_sf(nom.mechanics.SF)} at nominal T",
        "-",
        nom.mechanics.status_moderate,
        "medium at T≪Tg; UNKNOWN near Tg",
        "PMC12566568 78 MPa RT compression",
        "Single-particle crush vs T.",
    )
    add(
        "R13_compressive_integrity",
        "temperature-qualified SF vs 4500-6000 psi",
        (
            f"moderate T: {nom.mechanics.status_moderate.value} candidate "
            f"(SF approximately {round_sf(nom.mechanics.SF)}); "
            f"98 C analogue bulk {nom.mechanics.analogue_98C_MPa_min:.0f}-"
            f"{nom.mechanics.analogue_98C_MPa_max:.0f} MPa → {nom.mechanics.status_98C_analogue.value}; "
            f"150 C: {nom.mechanics.status_150C.value}"
        ),
        "dimensionless",
        RequirementStatus.UNKNOWN,
        "low at 150 C; analogue only at 98 C",
        "PMC12566568; US11377580B2 Table 3 (patent examples, not PhaseForge); pDCPD Tg 140-165 C",
        "6000 psi crush at 150 C on actual particles.",
    )
    add(
        "R14_remain_distributed",
        "liquid-liquid placement analogue",
        "liquids can enter branches (Chen analogue)",
        "-",
        RequirementStatus.MARGINAL,
        "low-medium",
        "CHEN2023 complex-fracture fill; settling after cure unresolved",
        "Flow-loop placement and post-cure distribution.",
    )
    add(
        "R15_open_pathways",
        "A geometric connectivity; B analytical k; C unvalidated conductivity",
        f"A connected={nom.permeability.geometric_connectivity}; porosity approximately {nom.permeability.porosity:.2f}; C={nom.permeability.conductivity_under_closure}",
        "-",
        nom.permeability.status,
        "MARGINAL until CFD/experiment; FAIL if disconnected",
        "Chen conductivity 10-30 MPa analogue (not PhaseForge k)",
        "Conductivity cell after in-situ formation under closure.",
    )
    add(
        "R16_flow_through_around",
        "k_rel vs assumed k_open (not measured conductivity)",
        f"k_rel approximately {round_krel(nom.permeability.k_rel)} relative to assumed k_open=1e-8 m2",
        "relative",
        nom.permeability.status,
        "low (assumption tagged)",
        "Kozeny-Carman / dilute obstruction; Chen conductivity comparison is analogue",
        "Measured conductivity vs closure.",
    )
    add(
        "R17_no_bulk_gel",
        "isolated droplet hypothesis",
        "PASS only if droplets remain isolated until solid",
        "-",
        RequirementStatus.MARGINAL,
        "low-medium",
        "Della Martina microreactors; coalescence risk remains",
        "Visual bulk-gel vs bead formation tests.",
    )
    return pd.DataFrame(rows)


def write_traceability_md(df: pd.DataFrame, docs: Path) -> None:
    lines = [
        "# Requirements traceability matrix",
        "",
        "Machine-generated from `scripts/reproduce_all.py`. Status is computational",
        "and analogue-based. This project did **not** physically perform experiments.",
        "",
        "| ID | Model/evidence | Predicted | Status | Confidence | Remaining validation |",
        "|---|---|---|---|---|---|",
    ]
    for _, r in df.iterrows():
        lines.append(
            f"| {r['requirement_id']} | {r['model_or_evidence']} | {r['predicted']} {r['unit']} | "
            f"**{r['status']}** | {r['confidence']} | {r['remaining_validation']} |"
        )
    (docs / "requirements_traceability.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_final_metrics(nom: CoupledResult, hpht: CoupledResult, mc: dict[str, Any], path: Path) -> None:
    ht = evaluate_ht_family()
    ht_pt = OperatingPoint(
        temperature_C=150.0,
        phi=0.15,
        inhibitor_index=0.5,
        catalyst_family=CATALYST_MO_LATENT,
        label="phaseforge_ht",
    )
    ht_eval = evaluate_point(ht_pt)
    dsens = diameter_sensitivity(
        DropletInputs(
            temperature_C=70.0,
            sigma_N_m=0.004,
            shear_rate_1_s=400.0,
            velocity_m_s=1.5,
            length_m=0.05,
            phi=0.15,
        )
    )
    mc_rounded = dict(mc)
    if mc.get("probabilities"):
        mc_rounded = {
            **mc,
            "probabilities_reviewer": {k: round_prob(v) for k, v in mc["probabilities"].items()},
        }
    payload = {
        "disclaimer": "Computational predictions and literature analogues. No PhaseForge laboratory experiments were performed in this repository.",
        "nominal": nom.as_dict(),
        "hpht_150C": hpht.as_dict(),
        "phaseforge_ht": {
            **ht.as_dict(),
            "coupled": ht_eval.as_dict(),
        },
        "diameter_sensitivity": dsens,
        "uq_40_90C": mc_rounded,
        "units": {
            "6000_psi_MPa": PSI_6000_MPA,
            "10_cP_Pa_s": 0.01,
        },
        "headline": {
            "question": "Is there a physically plausible operating window?",
            "answer_40_80C": nom.core_overall.value,
            "answer_40_80C_with_unvalidated_system_claims": nom.overall.value,
            "answer_150C_ru_phosphite": hpht.overall.value,
            "answer_150C_phaseforge_ht": ht.status.value,
            "notes": (
                "A computationally plausible core-physics window exists at moderate temperature "
                "(approximately 50-70 C) with latent Ru/phosphite ROMP and φ~0.1-0.2. "
                "Agglomeration and fracture conductivity remain MARGINAL (heuristics / unvalidated). "
                "At 150 C, published Ru/phosphite gel times extrapolate far below 25 min (FAIL). "
                "Mechanical strength at 150 C is near Tg and remains UNKNOWN. "
                "PhaseForge-HT (Mo latent precatalysts) is a separate UNKNOWN pathway based on "
                "DSC onsets approximately 52-142 C, not a fabricated isothermal PASS."
            ),
        },
        "reviewer_facing_nominal": {
            "mu_eff_cP": round_cP(nom.viscosity.mu_eff_cP),
            "d_particle_um": round_um(nom.droplets.d_particle_um),
            "SF_mech": round_sf(nom.mechanics.SF),
            "t_transform_min": round_min(nom.kinetics.t_transform_min),
            "k_rel_assumed": round_krel(nom.permeability.k_rel),
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def generate_all_figures(*, skip_uq: bool = False) -> dict[str, Any]:
    figdir, tab, proc = _ensure_dirs()
    docs = repo_root() / "docs"
    docs.mkdir(exist_ok=True)
    baseline = load_baseline()

    nom_pt = from_yaml_point(baseline["operating_point_nominal"], "nominal")
    hpht_raw = baseline["operating_point_hpht"]
    hpht_pt = from_yaml_point(hpht_raw, "hpht")
    # Explicit: without assumed extra latency, 150 C is a published-chemistry extrapolation
    hpht_pt_no_extra = OperatingPoint(
        temperature_C=150.0,
        phi=0.15,
        catalyst_relative=0.5,
        inhibitor_index=0.95,
        latency_extra=1.0,
        label="hpht_no_extra_latency",
    )

    nom = evaluate_point(nom_pt)
    hpht = evaluate_point(hpht_pt_no_extra)
    hpht_assumed = evaluate_point(hpht_pt)
    ht_pt = OperatingPoint(
        temperature_C=150.0,
        phi=0.15,
        inhibitor_index=0.5,
        catalyst_family=CATALYST_MO_LATENT,
        label="phaseforge_ht",
    )
    ht = evaluate_point(ht_pt)

    figure_mechanism_schematic(figdir)
    write_schematic_svg(figdir)
    figure_requirement_architecture(figdir)
    figure_validation(figdir, tab)
    figure_activation_map(figdir, tab)
    figure_conversion(figdir)
    figure_viscosity_map(figdir, tab)
    figure_diameter_map(figdir)
    figure_diameter_uncertainty(figdir, tab)
    figure_ht_onset(figdir)
    figure_mechanics(figdir)
    figure_permeability(figdir, tab)

    space = design_space(
        temperatures_C=[40, 50, 60, 70, 80, 100, 120, 150],
        phis=[0.08, 0.12, 0.15, 0.22, 0.30],
        inhibitors=[0.12, 0.22, 0.35],
    )
    figure_feasible_window(figdir, tab, space)

    if skip_uq:
        mc = {"n": 0, "seed": 42, "probabilities": {}, "method": "skipped"}
        sob = None
        torn = []
    else:
        mc = monte_carlo_compliance(n=400, seed=42)
        torn = tornado(nom_pt)
        sob = sobol_transform_time(n=64, seed=42)
        figure_mc(figdir, mc)
        figure_sobol(figdir, sob)
        pd.DataFrame(torn).to_csv(tab / "tornado.csv", index=False)
        pd.DataFrame({"name": sob["names"], "S1": sob["S1"], "ST": sob["ST"]}).to_csv(
            tab / "sobol.csv", index=False
        )

    pd.DataFrame([nom.as_dict(), hpht.as_dict(), hpht_assumed.as_dict(), ht.as_dict()]).to_csv(
        tab / "baseline_points.csv", index=False
    )
    json.dumps(mc, indent=2)
    (proc / "uq_mc.json").write_text(json.dumps(mc, indent=2), encoding="utf-8")
    if sob:
        (proc / "uq_sobol.json").write_text(json.dumps(sob, indent=2), encoding="utf-8")

    envs = select_envelopes(space)
    env_rows = []
    for name, e in envs.items():
        d = e.result.as_dict()
        d["envelope"] = name
        d["score"] = e.score
        env_rows.append(d)
    pd.DataFrame(env_rows).to_csv(tab / "optimization_envelopes.csv", index=False)

    trace = build_traceability(nom, hpht)
    trace.to_csv(tab / "requirements_traceability.csv", index=False)
    write_traceability_md(trace, docs)
    figure_evidence_matrix(figdir, trace)
    write_final_metrics(nom, hpht, mc, repo_root() / "results" / "final_metrics.json")
    return {
        "nominal": nom.as_dict(),
        "hpht": hpht.as_dict(),
        "hpht_assumed_latency": hpht_assumed.as_dict(),
        "phaseforge_ht": ht.as_dict(),
        "mc": mc,
        "envelopes": env_rows,
    }
