"""Figures 17-30 for ChemGate, high-Tg analogues, and CFD coupling."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from phaseforge.activation_diffusion import (
    D_LEE2025_M2_S,
    DIAMETERS_UM,
    activation_front_radius_m,
    diameter_sweep,
    fourier_number,
    profile_snapshot,
    shell_reduced_D_times,
)
from phaseforge.candidates import all_family_cards
from phaseforge.cfd_postprocess import intended_dimensionless, write_metrics_csv
from phaseforge.chemgate import (
    ChemGateInputs,
    evaluate_chemgate,
    feasibility_map,
    search_plausible_150C,
    t_shell_vs_coalescence,
)
from phaseforge.high_tg import scenarios
from phaseforge.provenance import RequirementStatus
from phaseforge.requirements import repo_root
from phaseforge.units import um_to_m


def _save(fig: plt.Figure, name: str, figdir: Path) -> None:
    fig.tight_layout()
    fig.savefig(figdir / f"{name}.png", dpi=300)
    fig.savefig(figdir / f"{name}.svg")
    fig.savefig(figdir / f"{name}.pdf")
    plt.close(fig)


def figure_17_candidate_comparison(figdir: Path, tab: Path) -> None:
    cards = all_family_cards()
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    colors = {
        RequirementStatus.FAIL: "#d7301f",
        RequirementStatus.UNKNOWN: "#737373",
        RequirementStatus.MARGINAL: "#fec44f",
        RequirementStatus.PASS: "#238b45",
    }
    y = np.arange(len(cards))
    ax.barh(y, [1] * len(cards), color=[colors[c.overall_150C] for c in cards], edgecolor="k")
    ax.set_yticks(y)
    ax.set_yticklabels([c.family for c in cards])
    ax.set_xlim(0, 1.35)
    ax.set_xticks([])
    ax.set_title("150 °C overall status by candidate family (never mixed into one global PASS)")
    for i, c in enumerate(cards):
        ax.text(1.02, i, c.overall_150C.value, va="center", fontsize=9)
    _save(fig, "17_high_temperature_candidate_comparison", figdir)
    pd.DataFrame([c.as_dict() for c in cards]).to_csv(tab / "candidate_family_cards.csv", index=False)


def figure_18_chemgate_schematic(figdir: Path) -> None:
    fig, ax = plt.subplots(figsize=(11.2, 3.4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3.2)
    ax.axis("off")
    stages = [
        (1.0, "Aqueous carrier\n+ organic droplets\nlatent catalyst"),
        (3.3, "HPHT transport\ncatalyst masked\nno 150 °C trigger"),
        (5.6, "Activator access\nafter placement"),
        (7.9, "Diffusion across\nL–L interface"),
        (10.3, "Surface-to-core\nROMP → particles"),
    ]
    for x, text in stages:
        ax.add_patch(plt.Circle((x, 1.7), 0.95, fill=True, facecolor="#deebf7", edgecolor="#1f4e79", lw=1.4))
        ax.text(x, 1.7, text, ha="center", va="center", fontsize=7.5)
    for i in range(len(stages) - 1):
        ax.annotate(
            "",
            xy=(stages[i + 1][0] - 1.0, 1.7),
            xytext=(stages[i][0] + 1.0, 1.7),
            arrowprops=dict(arrowstyle="->", color="#c45911", lw=1.5),
        )
    ax.set_title(
        "PhaseForge-ChemGate architecture (redrawn). D899/Cu is prior-art analogue, not our recipe.",
        loc="left",
    )
    ax.text(
        0.2,
        0.25,
        "Lee 2025 demonstrates aqueous Cu(I) → organic DCPD ink by interfacial diffusion. Not a 150 °C experiment.",
        fontsize=8,
    )
    _save(fig, "18_chemgate_prior_art_architecture", figdir)


def figure_19_profiles(figdir: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for tmin in (5, 15, 30, 60):
        r, c = profile_snapshot(270.0, tmin * 60.0)
        ax.plot(r * 1e6, c, label=f"{tmin} min")
    ax.set_xlabel("Radius (μm)")
    ax.set_ylabel("C / C_s")
    ax.set_title("Spherical activator profiles, 270 μm drop, Lee ambient D (not 150 °C)")
    ax.legend()
    _save(fig, "19_spherical_activator_profiles", figdir)


def figure_20_front(figdir: Path) -> None:
    R = um_to_m(270.0) / 2.0
    t = np.linspace(0, 90 * 60, 80)
    rf = [activation_front_radius_m(R, fourier_number(D_LEE2025_M2_S, ti, R)) * 1e6 for ti in t]
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.plot(t / 60.0, rf)
    ax.axhline(R * 1e6, color="gray", ls="--", label="drop radius")
    ax.set_xlabel("Time (min)")
    ax.set_ylabel("Activation-front radius (μm)")
    ax.set_title("Front radius vs time (C/Cs=0.5), 270 μm, Lee D")
    ax.legend()
    _save(fig, "20_activation_front_radius", figdir)


def figure_21_diameter_diffusion(figdir: Path, tab: Path) -> None:
    rows = [r.as_dict() for r in diameter_sweep()]
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    d = [r["diameter_um"] for r in rows]
    ax.plot(d, [r["t_avg_50_min"] for r in rows], "o-", label="volume-avg 50%")
    ax.plot(d, [r["t_center_50_min"] for r in rows], "s--", label="center 50%")
    ax.axhspan(25, 75, color="#9ecae1", alpha=0.35, label="25–75 min band")
    ax.set_xlabel("Droplet diameter (μm)")
    ax.set_ylabel("Diffusion time (min)")
    ax.set_title("Diameter vs activator diffusion time (Lee ambient D)")
    ax.legend()
    _save(fig, "21_diameter_vs_diffusion_time", figdir)
    pd.DataFrame(rows).to_csv(tab / "chemgate_diffusion_sweep.csv", index=False)


def figure_22_feasibility_map(figdir: Path, tab: Path) -> None:
    acts = (0.2, 0.5, 1.0, 2.0, 5.0)
    Z = feasibility_map(activities=acts)
    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    im = ax.pcolormesh(DIAMETERS_UM, acts, Z, shading="auto", cmap="viridis")
    cs = ax.contour(DIAMETERS_UM, acts, Z, levels=[25, 75], colors="white")
    ax.clabel(cs, fmt="%g min")
    ax.set_xlabel("Droplet diameter (μm)")
    ax.set_ylabel("Activator activity (relative)")
    ax.set_title("t_transform (min) including 30 min delayed contact. Model, not 150 °C experiment.")
    fig.colorbar(im, ax=ax, label="t_transform (min)")
    _save(fig, "22_diameter_activity_feasibility_map", figdir)
    pd.DataFrame(Z, index=acts, columns=DIAMETERS_UM).to_csv(tab / "chemgate_feasibility_map.csv")


def figure_23_damkohler(figdir: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    for d in DIAMETERS_UM:
        r = evaluate_chemgate(ChemGateInputs(diameter_um=d))
        ax.scatter(d, r.Da_diff_act, c="#3182bd")
    ax.axhline(3.0, color="crimson", ls="--", label="diffusion-limited ~Da≥3")
    ax.axhline(0.3, color="gray", ls=":", label="reaction-limited ~Da≤0.3")
    ax.set_xlabel("Diameter (μm)")
    ax.set_ylabel("Da = t_diff / t_activation")
    ax.set_title("Damköhler regime map (Lee ambient D, analogue t_act)")
    ax.legend()
    _save(fig, "23_damkohler_regime_map", figdir)


def figure_24_shell(figdir: Path) -> None:
    rows = [shell_reduced_D_times(d) for d in DIAMETERS_UM]
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    d = [r["diameter_um"] for r in rows]
    ax.plot(d, [r["t_const_D_min"] for r in rows], label="constant D")
    ax.plot(d, [r["t_D_x0.25_min"] for r in rows], label="D×0.25 (growing resistance)")
    ax.plot(d, [r["t_D_x0.1_min"] for r in rows], label="D×0.1 after surface gel")
    ax.axhspan(25, 75, color="#9ecae1", alpha=0.3)
    ax.set_xlabel("Diameter (μm)")
    ax.set_ylabel("t_avg50 (min)")
    ax.set_title("Shell / self-limiting diffusion comparison (hypothesis, not measured shell)")
    ax.legend()
    _save(fig, "24_shell_self_limiting_diffusion", figdir)


def figure_25_high_tg(figdir: Path, tab: Path) -> None:
    sc = scenarios()
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    names = [s.name for s in sc]
    lo = [s.Tg_C_lo for s in sc]
    hi = [s.Tg_C_hi for s in sc]
    y = np.arange(len(sc))
    ax.barh(y, np.array(hi) - np.array(lo), left=lo, color="#9ecae1", edgecolor="#1f4e79")
    ax.axvline(150.0, color="crimson", label="150 °C")
    ax.set_yticks(y)
    ax.set_yticklabels(names)
    ax.set_xlabel("Tg (°C)")
    ax.set_title("High-Tg pDCPD-family analogues. Not PhaseForge crush data.")
    ax.legend()
    _save(fig, "25_high_tg_material_analogues", figdir)
    pd.DataFrame([s.as_dict() for s in sc]).to_csv(tab / "high_tg_scenarios.csv", index=False)


def figure_26_30_cfd_and_decision(figdir: Path, tab: Path) -> None:
    """CFD snapshots if fields exist; always write decision matrix and coupling figure."""
    write_metrics_csv(tab / "cfd_metrics.csv")
    csvp = tab / "cfd_metrics.csv"
    df = pd.read_csv(csvp)
    # 29 coupling from model diameters even without CFD
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    tdiff = []
    ttot = []
    for d in DIAMETERS_UM:
        r = evaluate_chemgate(ChemGateInputs(diameter_um=d, D_mode="lee_ambient"))
        tdiff.append(r.t_diff_s / 60.0)
        ttot.append(r.t_transform_min)
    ax.plot(DIAMETERS_UM, tdiff, "o-", label="t_diff (Lee D)")
    ax.plot(DIAMETERS_UM, ttot, "s-", label="t_transform (delay+diff+act+poly)")
    ax.axhspan(25, 75, color="#9ecae1", alpha=0.3, label="25–75 min")
    ax.set_xlabel("Hydrodynamic / droplet diameter (μm)")
    ax.set_ylabel("Time (min)")
    ax.set_title("Hydrodynamic diameter → activator delay coupling")
    ax.legend()
    _save(fig, "29_hydrodynamic_diameter_to_activation_time", figdir)

    cards = all_family_cards()
    fig, ax = plt.subplots(figsize=(10.5, 3.6))
    ax.axis("off")
    cell = [[c.family, c.overall_150C.value, c.pathway] for c in cards]
    ax.table(cellText=cell, colLabels=["family", "150 C overall", "pathway"], loc="center")
    ax.set_title("Final candidate decision matrix (computational / analogue)")
    _save(fig, "30_candidate_decision_matrix", figdir)

    # 26-28: CFD if we have droplet rows
    if "d_eq_um" in df.columns and df["d_eq_um"].notna().any():
        from phaseforge.cfd_postprocess import plot_phase_snapshots

        plot_phase_snapshots(repo_root() / "simulations" / "cfd" / "phaseforge_channel", figdir)
        sub = df.dropna(subset=["d_eq_um"])
        fig, ax = plt.subplots(figsize=(7.2, 4.6))
        for tid, g in sub.groupby("time_s"):
            ax.scatter(g["centroid_x_m"] * 1e3, g["centroid_y_m"] * 1e3, label=f"t={tid:g}s", s=40)
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("y (mm)")
        ax.set_title("CFD droplet centroids (model prediction)")
        ax.legend(fontsize=7)
        _save(fig, "27_cfd_droplet_trajectories", figdir)

        fig, ax = plt.subplots(figsize=(7.2, 4.6))
        ax.plot(sub["time_s"], sub["d_eq_um"], "o")
        dim = intended_dimensionless(65.0)
        ax.axhline(dim["d_hinze_um"], color="crimson", ls="--", label=f"Hinze analogue {dim['d_hinze_um']:.0f} μm")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Equivalent diameter (μm)")
        ax.set_title("CFD d_eq vs Hinze/Grace-scale estimate")
        ax.legend()
        _save(fig, "28_cfd_vs_hinze_diameter", figdir)
    else:
        fig, ax = plt.subplots(figsize=(7.2, 3.2))
        ax.axis("off")
        ax.text(0.5, 0.5, "CFD phase-fraction snapshots: no solved fields yet.\nFields were not fabricated.", ha="center", va="center")
        _save(fig, "26_cfd_phase_fraction_snapshots", figdir)
        fig, ax = plt.subplots(figsize=(7.2, 3.2))
        ax.axis("off")
        ax.text(0.5, 0.5, "CFD trajectories unavailable until interFoam writes time directories.", ha="center")
        _save(fig, "27_cfd_droplet_trajectories", figdir)
        dim = intended_dimensionless(65.0)
        fig, ax = plt.subplots(figsize=(7.2, 4.2))
        ax.bar(["CFD d (unsolved)", "Hinze analogue"], [np.nan, dim["d_hinze_um"]])
        ax.set_ylabel("μm")
        ax.set_title(f"Hinze analogue {dim['d_hinze_um']:.0f} μm; CFD d not extracted")
        _save(fig, "28_cfd_vs_hinze_diameter", figdir)

    search = search_plausible_150C()
    (tab / "chemgate_search.json").write_text(json.dumps(search, indent=2), encoding="utf-8")
    # shell vs coalescence sensitivity
    rows = [t_shell_vs_coalescence(d, coalescence_time_s=5.0) for d in (70, 270, 600)]
    pd.DataFrame(rows).to_csv(tab / "shell_vs_coalescence.csv", index=False)


def generate_chemgate_figures(figdir: Path, tab: Path) -> None:
    figure_17_candidate_comparison(figdir, tab)
    figure_18_chemgate_schematic(figdir)
    figure_19_profiles(figdir)
    figure_20_front(figdir)
    figure_21_diameter_diffusion(figdir, tab)
    figure_22_feasibility_map(figdir, tab)
    figure_23_damkohler(figdir)
    figure_24_shell(figdir)
    figure_25_high_tg(figdir, tab)
    figure_26_30_cfd_and_decision(figdir, tab)
