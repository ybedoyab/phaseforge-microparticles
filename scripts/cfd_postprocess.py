"""Dimensionless diagnostics for the PhaseForge 2D channel (analytic, not a fake solve).

Re, We, Ca from the intended case properties. Field snapshots are produced
only if OpenFOAM actually wrote time directories.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGDIR = ROOT / "results" / "raw" / "cfd"


def diagnostics() -> dict[str, float]:
    rho = 1000.0
    mu = 1.0e-3
    U = 0.05
    L = 0.003
    d = 6.0e-4
    sigma = 0.004
    return {
        "Re": rho * U * L / mu,
        "We": rho * U**2 * d / sigma,
        "Ca": mu * U / sigma,
        "U_m_s": U,
        "L_m": L,
        "d_drop_m": d,
        "sigma_N_m": sigma,
        "mu_cP": 1.0,
        "ift_mN_m": 4.0,
    }


def main() -> int:
    LOGDIR.mkdir(parents=True, exist_ok=True)
    d = diagnostics()
    lines = [
        "PhaseForge 2D channel intended dimensionless groups (from case properties).",
        "These are NOT experimental measurements and are NOT a substitute for a solved field.",
        *(f"{k}={v:.4g}" for k, v in d.items()),
    ]
    (LOGDIR / "phaseforge_dimensionless.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    case = ROOT / "simulations" / "cfd" / "phaseforge_channel"
    times = [
        p.name
        for p in case.iterdir()
        if p.is_dir() and p.name.replace(".", "", 1).isdigit() and p.name != "0"
    ]
    note = "No solved OpenFOAM time directories (folder 0/ is initial conditions only). Fields were not fabricated."
    if times:
        note = f"Time directories found: {sorted(times)}"
    (LOGDIR / "phaseforge_fields_note.txt").write_text(note + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(note)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
