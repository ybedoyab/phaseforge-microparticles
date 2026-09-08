# PhaseForge

Computational proof-of-concept for a **thermally latent fluid-to-microparticle** system aimed at the Innocentive challenge [*Controlled Formation of Mechanically Functional Microparticles from a Fluid System*](https://www.innocentive.com/challenges/controlled-formation-of-mechanically-functional-microparticles-from-a-fluid-system/).

This repository does **not** contain laboratory experiments performed by us. Results are analytical predictions, uncertainty estimates, and comparisons to **published** experimental analogues.

## Objective

Answer, quantitatively and with provenance:

> Can a DCPD-rich droplet system stay ≤10 cP, delay solidification ~25–75 min, form discrete ~70–600 μm particles, survive ~4,500–6,000 psi, and keep flow pathways open?

## Challenge requirements (encoded in `config/challenge_requirements.yaml`)

- Liquid delivery, μ ≤ 10 cP
- Transport up to ~150 °C and ~10,000 psi; ~6,000 psi after transformation
- Controlled activation; ~25–75 min after pumping
- Discrete 70–600 μm near-spherical particles, minimal agglomeration
- Load-bearing under ~4,500–6,000 psi
- Remain distributed; interconnected flow paths; **no bulk gel plug**

## Mechanism (proposed)

Aqueous/brine carrier → stabilized DCPD or DCPD/TriCPD droplets (microreactors) → HPHT transport while ROMP is latent → latency expires → discrete pDCPD-family particles → assembly with open channels.

## Architecture

See `docs/architecture.md`. Core package: `phaseforge/` (kinetics, thermal, viscosity, droplets, mechanics, permeability, coupled, UQ).

## Quick start

Python 3.12 and [uv](https://github.com/astral-sh/uv):

```bash
uv sync --extra dev
uv run pytest
uv run python scripts/reproduce_all.py
```

`make reproduce` wraps the same command if GNU make is available.

## Current evidence status (read after running reproduce)

Headline files:

- `results/final_metrics.json`
- `results/tables/requirements_traceability.csv`
- `docs/requirements_traceability.md`
- `AUDIT_REPORT.md`

**Expected qualitative outcome (models, not experiments):**

- A plausible **core-physics** window exists at **moderate temperature (~50–70 °C)** with latent Ru/phosphite ROMP and φ ~ 0.1–0.2: viscosity PASS, delay tunable into 25–75 min, size **approximately 270 μm** (range, not 273.046 μm), RT-derated mechanics PASS candidate.
- Agglomeration and fracture conductivity are **MARGINAL** (heuristics / unvalidated). They do not independently PASS.
- At **150 °C**, published Ru/phosphite gel times extrapolate **far below** 25 min (**FAIL**). Mechanical integrity is **UNKNOWN** (near pDCPD Tg).
- **PhaseForge-HT** (Mo latent precatalysts) is a separate **UNKNOWN** pathway (DSC onsets ~52–142 °C ≠ isothermal 25–75 min at 150 °C).
- R03 upper-temperature capability of exact PhaseForge remains **UNKNOWN**; a 70 °C candidate does not close “up to ~150 °C.”

Do not read this as “TRL 3 achieved.” See `docs/final_submission_claims.md`.

## Representative figures

Generated under `figures/` (PNG ≥300 dpi, SVG, PDF):

- `01_mechanism_schematic*`
- `04_activation_time_map*`
- `06_viscosity_design_map*`
- `10_coupled_feasible_window*`
- `11_monte_carlo_compliance*`
- `15_diameter_uncertainty*`
- `16_phaseforge_ht_onset*`

## Limitations

- Arrhenius extrapolation beyond 80 °C is not a measurement.
- No PhaseForge brine-droplet cure data.
- Hinze/Grace diameters are characteristic, not a full population balance.
- Strength derating near Tg is a scenario, not a 150 °C crush test.
- US11377580B2 is a major IP overlap on downhole DCPD/TriCPD ROMP (not legal advice).
- CFD is optional (`scripts/run_cfd.sh`); Python POC does not depend on it.

## References

`data/literature/references.bib` and `data/literature/evidence_registry.csv`.

Primary OA anchors: Chen et al., ACS Omega 2023, DOI 10.1021/acsomega.2c04853; Madbouly et al., ACS Omega 2025, DOI 10.1021/acsomega.5c09864.
