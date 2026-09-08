# AUDIT_REPORT

Regenerated after ChemGate + CFD continuation (2026-09-08).

This project did **not** physically perform PhaseForge laboratory experiments.

## Environment status

| Item | Status |
|---|---|
| OS | Windows 10.0.26200, AMD Ryzen 7 5800U (8c/16t), 15.4 GB RAM |
| Git | 2.41.0.windows.3 |
| Python | 3.12 via `uv`; lockfile `uv.lock` |
| Docker CLI | 27.4.0 |
| Docker engine | **Running** — Server Version **27.4.0**, Docker Desktop, 16 CPU, 7.44 GiB |
| GeoChemFoam image | `jcmaes/geochemfoam-5.2` (OpenFOAM **v2212**) |
| GitHub Actions | Verify after this push; do not substitute local pytest |

Details: `docs/environment_audit.md`.

## Tests

- `uv run ruff check phaseforge tests scripts`: clean
- `uv run pytest --cov=phaseforge`: **66 passed**, core coverage **≈82%** (reporting/figure modules omitted)

## Reproducibility status

```
uv sync --extra dev
uv run python scripts/reproduce_all.py
```

Completed with seed 42. Outputs in `figures/`, `results/tables/`, `results/final_metrics.json`.

## Models completed

1. Challenge requirements YAML + SI units + provenance
2. Arrhenius ROMP delay — **150 °C Ru/phosphite still FAIL**; not retuned
3. `PhaseForge-HT-Thermal` — Kordes 2024: no DCPD polymerization up to ~150 °C; trigger at exactly 150 °C **UNKNOWN**
4. `PhaseForge-ChemGate` spherical activator diffusion + coupled `t_transform` + Damköhler + shell D reduction — **UNKNOWN / PLAUSIBLE_CANDIDATE**, never PASS
5. `PhaseForge-ChemGate-Acid` exploratory
6. High-Tg material scenarios A/B/C (crush at 150 °C remains UNKNOWN; high-TCPD viscosity UNKNOWN)
7. Coupled envelope + LHS n=400 + Sobol + ChemGate engineering search

## Simulations completed

| Simulation | Status |
|---|---|
| Python coupled design space | Done |
| LHS / Sobol UQ | Done |
| Official two-phase `interFoam` damBreak | **Solved** — End, time dirs 0.05–0.25, residuals captured. Image `jcmaes/geochemfoam-5.2`, OpenFOAM v2212 |
| PhaseForge 2D multi-droplet (moderate T properties) | **Solved** — 4×500 μm drops, 24 cells each, End, time dirs 0.02–0.08. Four interfaces remained separated (`n_droplets=4`, coalescence_events=0 over 0.08 s). `CFD_MODEL_PREDICTION` |
| PhaseForge HPHT thermal-property analogue (~150 °C μ/IFT) | **Solved** — same mesh; hydro only, not 10,000 psi chemistry |
| foamToVTK | Ran on moderate case |
| Data-derived PNG snapshots | `figures/26–28_*` |

CFD is incompressible VoF. Absolute hydrostatic pressure is **not** a chemical-rate variable.

Laminar channel transport of pre-formed drops is **not** the same question as Hinze turbulent breakup diameter. Figure 28 compares them explicitly rather than hiding disagreement.

## Literature (new this round)

Lee 2024 (D899/Cu, ~200 °C latency); Lee 2025 (aqueous Cu(I) → organic DCPD, D≈6e-8 cm²/s ambient, ~400 μm / ~20 min); Suslick 2022 (ambient gel minutes–hours); Kordes 2024 full HTML (Mo no poly to 150 °C / full conversion 175 °C); Samec 2010; Monsaert 2010; Zhan 2024; Zhang 2024 DOI verified (full PDF not extracted); US12338310 IP flag.

## Requirements (do not hide branch failures)

See `results/tables/candidate_requirements_matrix.csv` and `docs/150C_decision.md`.

- `PhaseForge-RuP` at 150 °C: **FAIL** (kinetics)
- `PhaseForge-HT-Thermal`: **UNKNOWN** (transport analogue supported; 150 °C trigger UNKNOWN)
- `PhaseForge-ChemGate`: **UNKNOWN / PLAUSIBLE PATHWAY** (modelled 25–75 min with delayed activator contact; Lee analogues; not PASS)
- YAML nominal ~60 °C RuP: **MARGINAL** overall (t_solid slightly above 75 min; agglomeration/conductivity MARGINAL)

## CFD

Logs: `results/raw/cfd/`. Status: `phaseforge_case_solved`. Metrics: `results/tables/cfd_metrics.csv`.

## Claim control

See `docs/final_submission_claims.md`. D899/Cu and patented Mo complexes are **prior art / analogue only**. Do not claim “PhaseForge works at 150 °C.”
