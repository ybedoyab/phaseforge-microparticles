# AUDIT_REPORT

Regenerated after the scientific-audit corrections (2026-09-08).

This project did **not** physically perform PhaseForge laboratory experiments.

## Environment status

| Item | Status |
|---|---|
| OS | Windows 10.0.26200, AMD Ryzen 7 5800U (8c/16t), 15.4 GB RAM |
| Git | 2.41.0.windows.3 |
| Python | 3.12 via `uv`; lockfile `uv.lock` |
| Docker CLI | Installed |
| Docker engine | **Not reachable** at audit time (`dockerDesktopLinuxEngine` pipe missing). CFD not solved |
| GitHub Actions | Latest `main` commit `383ac11`: python-ci **success** (29 s), https://github.com/ybedoyab/phaseforge-microparticles/actions/runs/34192864866. The previous audit commit `f868426` failed in 0 s because the workflow YAML accidentally duplicated the `jobs:` key; that is fixed. An earlier `main` run `34187273191` also succeeded. Local 44/44 tests are separate from Actions |

Details: `docs/environment_audit.md`.

## Tests

- `uv run pytest`: **44 passed** (includes new audit-correction tests)
- `uv run ruff check phaseforge tests scripts`: **clean**
- Local tests are **not** a substitute for GitHub Actions on the latest commit until that run finishes

## Reproducibility status

```
uv sync --extra dev
uv run python scripts/reproduce_all.py
```

Completed with seed 42. Outputs in `figures/`, `results/tables/`, `results/final_metrics.json`.

## Models completed

1. Challenge requirements YAML + SI units + provenance
2. Arrhenius ROMP delay / conversion (Madbouly 2025; Hu 2018 analogue) — **150 °C Ru/phosphite still FAIL**; no multiplier used to force PASS
3. PhaseForge-HT Mo latent family (Elser 2018; Momin 2021) — **UNKNOWN** (DSC ≠ isothermal 25–75 min)
4. Lumped droplet energy balance
5. Taylor/Pal emulsion viscosity
6. Hinze + Grace droplet size **with sensitivity** (nominal **approximately 270 μm**; p10–p90 **approximately 140–550 μm**)
7. Temperature-qualified mechanics (moderate PASS candidate; 98 °C patent analogue; 150 °C UNKNOWN)
8. Permeability split: A geometry / B analytical k / C unvalidated closure conductivity → **MARGINAL**
9. Agglomeration heuristic **cannot PASS** without validation → **MARGINAL** at moderate T; **UNKNOWN** at high T
10. Coupled envelope + LHS n=400 + Sobol

## Simulations completed

| Simulation | Status |
|---|---|
| Python coupled design space | Done |
| LHS / Sobol UQ | Done |
| GeoChemFoam official tutorial **solve** | **Not run** — Docker engine down. `--check` records the engine error |
| Custom PhaseForge 2D `interFoam` case | Case files present; **not solved**. Fields not fabricated |
| OpenFOAM fallback | Not executed (same Docker limitation) |

## Literature sources

Registry: `data/literature/evidence_registry.csv` (added Momin 2021; Elser T_exo; US11377580B2 Table 3). Bib: `data/literature/references.bib`.

**Liang et al. 2025** DOI verified; full text not retrieved; **no numbers invented**.

## Requirements (YAML nominal ~60 °C, reviewer-facing rounding)

From `results/tables/requirements_traceability.csv` and `results/final_metrics.json`:

- R01 liquid delivery — PASS (by design / analogue)
- R02 viscosity — PASS (μ_eff **approximately 0.64 cP** at 60 °C, φ=0.15)
- R06 controlled activation — PASS (mechanism analogue)
- R08 discrete particles — PASS (φ isolation hypothesis / analogue)
- R09 particle size — PASS (**approximately 270 μm** Hinze/Grace; range ~140–550 μm)
- R12 load-bearing — PASS **candidate** at 60 °C (SF **approximately 1.4** vs 6,000 psi)

## Requirements marginal

- R07 transformation window — **MARGINAL** at YAML nominal (t_solid **approximately 78 min**)
- R10 sphericity — MARGINAL
- R11 agglomeration — **MARGINAL** (heuristic; cannot independently PASS)
- R14 distribution — MARGINAL
- R15 / R16 open pathways — **MARGINAL** (geometry connected; `k_rel` ≈ 0.74 is **relative to assumed k_open**, not measured conductivity)
- R17 no bulk gel — MARGINAL
- **Overall YAML nominal: MARGINAL** (core_overall also MARGINAL because t_solid is slightly above 75 min)

A 70 °C / lower-φ grid point can still be a **core-physics PASS candidate** for viscosity + time + size + moderate-T mechanics. That does **not** upgrade agglomeration or conductivity to PASS.

## Requirements failing

- **150 °C published Ru/phosphite analogue:** t_solid **approximately 1.6 min** — **FAIL** the 25–75 min window. Do not treat DSC T_onset ≤ 142 °C as proof of a 50 min isothermal hold at 150 °C.
- Hypothetical 2000× extra latency remains **ASSUMED_FOR_SENSITIVITY** and is not a published-chemistry PASS.

## Requirements unknown

- **R03** upper-temperature capability of **exact PhaseForge** (a 70 °C candidate does not close “up to ~150 °C”)
- **R04** 10,000 psi effects on ROMP rate
- **R05 / R13** at 150 °C (T near pDCPD Tg). 98 °C analogue only (US11377580B2 Table 3, patent examples)
- **PhaseForge-HT** isothermal 25–75 min at 150 °C
- High-T agglomeration / sticky cure

## Monte Carlo (n=400, 40–90 °C, 2 significant digits)

- P(viscosity PASS) = **1.0**
- P(time window PASS) ≈ **0.30**
- P(core_pass) ≈ **0.18**
- P(overall_pass) = **0.00** (agglomeration and unvalidated k never PASS)
- P(overall not FAIL) ≈ **0.41**

## CFD

Exact `--check` output is in `results/raw/cfd/` after `bash scripts/run_cfd.sh --check`. If the engine is down, that file is the record. **No CFD fields were invented.**

## Claim control

See `docs/final_submission_claims.md`. Keep TRL wording: TRL-3-oriented analytical/computational proof-of-concept; integrated PhaseForge is a TRL 2–3 candidate. Do not claim TRL 3 achieved.
