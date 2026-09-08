# AUDIT_REPORT

Generated after `uv run pytest` and `uv run python scripts/reproduce_all.py` on 2026-09-08.

This project did **not** physically perform PhaseForge laboratory experiments.

## Environment status

| Item | Status |
|---|---|
| OS | Windows 10.0.26200, AMD Ryzen 7 5800U (8c/16t), 15.4 GB RAM |
| Disk | D: ~209 GB free (project); C: ~24 GB free |
| Git | 2.41.0.windows.3 |
| Python | 3.12.3 via `uv` 0.12.5; lockfile `uv.lock` |
| Docker CLI | 27.4.0 installed |
| Docker engine | **Not running** (Desktop pipe missing). CFD not executed |
| WSL | docker-desktop default, unused for modeling |

Details: `docs/environment_audit.md`.

## Tests

- `uv run pytest`: **36 passed**
- `uv run ruff check phaseforge tests scripts`: **clean**
- Coverage of `phaseforge/` (reporting omitted): **~80%**

## Reproducibility status

```
uv sync --extra dev
uv run python scripts/reproduce_all.py
```

Completed successfully with seed 42. Outputs in `figures/`, `results/tables/`, `results/final_metrics.json`.

## Models completed

1. Challenge requirements YAML + SI units + provenance
2. Arrhenius ROMP delay / conversion (Madbouly 2025 calibration; Hu 2018 inhibitor analogue)
3. Lumped droplet energy balance (implicit cooling)
4. Taylor/Pal emulsion viscosity (Krieger–Dougherty comparison only)
5. Hinze + Grace droplet size
6. Tg-derated mechanics vs 6,000 psi
7. Kozeny–Carman / dilute permeability + 2D disk placement
8. Coupled PASS/MARGINAL/FAIL/UNKNOWN envelope
9. LHS Monte Carlo (n=400) + Sobol (n=64) + tornado
10. Constrained envelope search (conservative/nominal/aggressive)

## Simulations completed

| Simulation | Status |
|---|---|
| Python coupled design space | Done |
| LHS / Sobol UQ | Done |
| GeoChemFoam official tutorial | **Not run** — Docker engine down |
| Custom PhaseForge CFD | **Not run** |
| OpenFOAM interFoam fallback | **Not run** |

## Literature sources

Registry: `data/literature/evidence_registry.csv` (provenance-tagged). Bib: `data/literature/references.bib`.

Retrieved as open/full or abstract/snippet as tagged. **Liang et al. 2025** DOI verified; full text not retrieved; **no numbers invented**. Energy & Fuels Chen 2023 and several Wiley papers: abstract/snippet only.

## Requirements passing (nominal ~60 °C computational)

From `results/tables/requirements_traceability.csv` and `results/final_metrics.json`:

- R01 liquid delivery — PASS (by design / analogue)
- R02 viscosity — PASS (μ_eff ≈ **0.64 cP** at 60 °C, φ=0.15)
- R06 controlled activation — PASS (mechanism analogue)
- R08 discrete particles — PASS (φ isolation hypothesis)
- R09 particle size — PASS (d ≈ **273 μm** Hinze/Grace)
- R11 agglomeration risk score — PASS (score ≈ 0.27; analogue only)
- R12 load-bearing — PASS at 60 °C (SF ≈ **1.41** vs 6,000 psi)
- R13 compressive integrity — PASS at 60 °C only
- R15 / R16 open pathways — PASS at φ=0.15 distributed

## Requirements marginal

- R07 transformation window — **MARGINAL** at YAML nominal (t_solid ≈ **78 min**, slightly above 75)
- R10 sphericity — MARGINAL (analogue, not measured)
- R14 distribution — MARGINAL
- R17 no bulk gel — MARGINAL (isolation not experimentally shown)
- **Overall YAML nominal: MARGINAL**

Grid search found **PASS** points near **70 °C, φ≈0.08, inhibitor index 0.22–0.35**, t_solid ≈ 34–48 min (`results/tables/optimization_envelopes.csv`).

LHS 40–90 °C: P(all PASS) ≈ **0.16**; P(not FAIL) ≈ **0.41**; P(viscosity PASS)=1.0; P(time window PASS)≈0.30.

## Requirements failing

- **150 °C published Ru/phosphite analogue:** t_solid ≈ **1.6 min** (Arrhenius from 40–60 °C data) — **FAIL** the 25–75 min window. Do not treat DSC T_onset ≤ 140 °C as proof of a 50 min isothermal hold at 150 °C.
- Hypothetical 2000× extra latency at 150 °C is **ASSUMED_FOR_SENSITIVITY** and overshoots to thousands of minutes (FAIL too slow) in the tagged sensitivity case.

## Requirements unknown

- R03 150 °C as a **closed** operating point for the integrated fluid
- R04 10,000 psi effects on ROMP rate
- R13 at 150 °C (T near pDCPD Tg 140–165 °C; SF derated ≈ 0.33 and status UNKNOWN for high-T crush)
- Catalyst survival in brine/surfactant droplets
- Liang 2025 quantitative properties (paper not retrieved)

## Biggest scientific uncertainty

**Isothermal transformation time and particle strength at ~150 °C in a water-dispersed droplet**, including whether any latent precatalyst can place t_solid in 25–75 min without poisoning, and whether Tg of a DCPD/TriCPD network stays far enough above 150 °C for SF≥1 at 41 MPa. Room-temperature 78 MPa (PMC12566568) must not be used as 150 °C strength.

## Biggest IP risk

**US11377580B2** (Schlumberger): in-situ DCPD/TriCPD ROMP, delayed phosphite systems, fracturing polymer **pillars**. PhaseForge’s droplet-microreactor / 70–600 μm / ≤10 cP coupling is a possible technical distinction, **not** a legal non-infringement conclusion. Get counsel before claiming novelty. See `docs/prior_art.md`.

## Exact files to inspect manually

1. `docs/submission_evidence_pack.md`
2. `results/final_metrics.json`
3. `results/tables/requirements_traceability.csv`
4. `docs/prior_art.md` (US11377580B2 overlap)
5. `docs/trl_assessment.md`
6. `data/literature/evidence_registry.csv`
7. `figures/04_activation_time_map.png`
8. `figures/10_coupled_feasible_window.png`
9. `figures/11_monte_carlo_compliance.png`
10. `config/challenge_requirements.yaml`
11. `AUDIT_REPORT.md` (this file)

## Manual action still required

1. **Start Docker Desktop** if GeoChemFoam tutorials are desired; then `bash scripts/run_cfd.sh --check`.
2. Laboratory TRL-3 validation plan in `docs/trl_assessment.md` (not performed here).
3. Innocentive submission form / Challenge Agreement — human, not this repo.
4. Optional: retrieve paywalled full texts (Liang 2025; Chen Energy & Fuels; Kordes full PDF) and add only values actually read.

## Headline answer

**Yes, a physically plausible window exists at moderate temperature (~50–70 °C)** for μ≤10 cP, 25–75 min delay (with inhibitor tuned), ~70–600 μm drops, SF>1 vs 6,000 psi **if T is well below Tg**, and open pathways at φ~0.1–0.2. That window is a **computational / analogue TRL-3 candidate**, not an experimental demonstration.

**No (for published Ru/phosphite kinetics) at 150 °C:** transformation is predicted far too fast, and mechanics are unresolved near Tg. A highly latent Mo/Ru system that is isothermal-slow at 150 °C remains **unproven** in the retrieved literature.
