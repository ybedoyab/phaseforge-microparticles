# Architecture

PhaseForge is a **TRL-3-oriented analytical / computational proof-of-concept**. It does not contain laboratory experiments performed by this project.

## Question the software is built to answer

Is there a physically plausible operating window in which a thermally latent DCPD-rich droplet system can:

1. remain a liquid with μ_eff ≤ 10 cP during delivery,
2. delay transformation for approximately 25–75 min,
3. form discrete ~70–600 μm particles,
4. survive ~4,500–6,000 psi closure,
5. preserve interconnected fluid pathways?

Answers are `PASS`, `MARGINAL`, `FAIL`, or `UNKNOWN`. `UNKNOWN` is never recast as `PASS`.

## Layers

```
config/          machine-readable requirements, baseline, UQ ranges
data/literature/ evidence registry (provenance-tagged numbers)
phaseforge/      SI models (kinetics, thermal, viscosity, droplets,
                 mechanics, permeability, coupled, UQ, optimization)
scripts/         reproduce_all.py, CFD helpers, external bootstrap
results/         tables, processed JSON, final_metrics.json
figures/         SVG/PDF/PNG
docs/            scientific narrative, TRL, risks, evidence pack
simulations/cfd/ GeoChemFoam / OpenFOAM cases (not vendored binaries)
external/        gitignored clones
```

## Model coupling

One-way:

1. viscosity(T, φ)
2. t_transform(T, catalyst, inhibitor) from Arrhenius gel-time model; t_solid = 1.8 t_gel (assumed)
3. droplet size from Hinze + Grace; particle size = (1 − shrinkage) d32
4. lumped droplet energy balance (exotherm vs water cooling)
5. temperature-derated compressive SF vs 6,000 psi
6. Kozeny–Carman / dilute obstruction permeability
7. coupled status = worst of the component statuses

CFD, if available, supplies hydrodynamics only. Chemistry is **not** solved inside OpenFOAM in this POC.

## Determinism

Default seed = 42 (`phaseforge.SEED`). LHS/Sobol use that seed.

## What is intentionally not in the repo

- Laboratory recipes with hazardous catalyst/inhibitor dosages as “the formulation”
- Downloaded copyrighted PDFs
- Docker images and OpenFOAM processor directories
- Claims of TRL 3 achieved for the integrated PhaseForge fluid
