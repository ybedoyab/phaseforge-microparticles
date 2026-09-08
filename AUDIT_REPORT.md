# AUDIT_REPORT

Regenerated after ChemGate two-stage trigger hardening (2026-09-08).

This project did **not** physically perform PhaseForge laboratory experiments.

## Environment status

| Item | Status |
|---|---|
| OS | Windows 10.0.26200, AMD Ryzen 7 5800U (8c/16t), 15.4 GB RAM |
| Git | 2.41.0.windows.3 |
| Python | 3.12 via `uv`; lockfile `uv.lock` |
| Docker CLI | 27.4.0 |
| Docker engine | Not rerun this pass (existing solved CFD reused) |
| GeoChemFoam image | `jcmaes/geochemfoam-5.2` (OpenFOAM **v2212**) |
| GitHub Actions | Verify after this push; do not substitute local pytest |

Details: `docs/environment_audit.md`.

## Tests

- `uv run ruff check phaseforge tests scripts`: clean
- `uv run pytest --cov=phaseforge`: **71 passed**, core coverage **≈82%** (reporting/figure modules omitted)

## Reproducibility status

```
uv sync --extra dev
uv run python scripts/reproduce_all.py
```

Completed with seed 42. Outputs in `figures/`, `results/tables/`, `results/final_metrics.json`. CFD was **not** rerun; post-processing still reads existing fields.

## Models completed

1. Challenge requirements YAML + SI units + provenance
2. Arrhenius ROMP delay — **150 °C Ru/phosphite still FAIL**; not retuned
3. `PhaseForge-HT-Thermal` — Kordes 2024: no DCPD polymerization up to ~150 °C; trigger at exactly 150 °C **UNKNOWN**
4. `PhaseForge-ChemGate` two-stage deployment + spherical activator diffusion + Damköhler + shell D reduction — **UNKNOWN / PLAUSIBLE_CANDIDATE**, never PASS
5. Timing split: `t_trigger_arrival` (`ASSUMED_FOR_DEPLOYMENT_SCENARIO`) vs `t_post_trigger_particle` (model). Envelope over 0–60 min arrival; **30 min is not a required kinetic delay**
6. `PhaseForge-ChemGate-Acid` exploratory
7. High-Tg material scenarios A/B/C (crush at 150 °C remains UNKNOWN; high-TCPD viscosity UNKNOWN)
8. Coupled envelope + LHS n=400 + Sobol + ChemGate engineering search

## Simulations completed

| Simulation | Status |
|---|---|
| Python coupled design space | Done |
| LHS / Sobol UQ | Done |
| Official two-phase `interFoam` damBreak | Previously **solved** — not rerun this pass |
| PhaseForge 2D multi-droplet (moderate T and HPHT property analogues) | Previously **solved** — hydro only; 0.08 s is **not** a 25–75 min proof |
| foamToVTK | Previously ran on moderate case |
| Data-derived PNG snapshots | `figures/26–28_*` reused; `31–32_*` new this pass |

CFD is incompressible VoF. Absolute hydrostatic pressure is **not** a chemical-rate variable. 10,000 psi chemical-rate effects remain **UNKNOWN**.

## Literature (unchanged this pass)

Lee 2024 (D899/Cu, ~200 °C latency); Lee 2025 (aqueous Cu(I) → organic DCPD, D≈6e-8 cm²/s ambient, ~400 μm / ~20 min); Suslick 2022; Kordes 2024; Samec 2010; Monsaert 2010; Zhan 2024; US12338310 IP flag.

## Requirements (do not hide branch failures)

See `results/tables/candidate_requirements_matrix.csv` and `docs/150C_decision.md`.

- `PhaseForge-RuP` at 150 °C: **FAIL** (kinetics)
- `PhaseForge-HT-Thermal`: **UNKNOWN** (transport analogue supported; 150 °C trigger UNKNOWN)
- `PhaseForge-ChemGate`: **UNKNOWN / PLAUSIBLE PATHWAY** (two-stage envelope; Lee analogues; not PASS)
- 150 °C crush: **UNKNOWN**
- YAML nominal ~60 °C RuP: **MARGINAL** overall (t_solid slightly above 75 min; agglomeration/conductivity MARGINAL)

## ChemGate clocks (do not conflate)

At 270 μm, Lee ambient D, activity 1:

- `t_post_trigger_particle` ≈ **29 min** (model / analogue)
- nominal `t_trigger_arrival` = **30 min** (`ASSUMED_FOR_DEPLOYMENT_SCENARIO`)
- allowable Stage-B arrival for 25–75 min from pumping ≈ **0–46 min**
- a fixed 30 min delay is **not required**

## CFD

Logs: `results/raw/cfd/`. Status: `phaseforge_case_solved`. Metrics: `results/tables/cfd_metrics.csv`.

## Claim control

See `docs/final_submission_claims.md`. D899/Cu and patented Mo complexes are **prior art / analogue only**. Do not claim “PhaseForge works at 150 °C.” Do not claim ChemGate intrinsically delays cure for a fixed ~60 min.
