# Submission evidence pack (technical basis)

This is the concise technical basis for an Innocentive-style write-up. It is **not** a claim that this project ran laboratory experiments on the exact PhaseForge fluid.

## Problem

Deliver a liquid with μ ≤ 10 cP, keep it fluid during transport (up to ~150 °C, ~10,000 psi), then form discrete 70–600 μm load-bearing particles after ~25–75 min, surviving ~4,500–6,000 psi, without making a bulk gel plug so that fluid can still flow around the assembly.

## Proposed mechanism

**PhaseForge — thermally latent fluid-to-microparticle system.** Aqueous carrier + DCPD-rich droplets as isolated ROMP microreactors. Latency expires after placement; each drop becomes a pDCPD-family particle.

## Why it may work

1. **Viscosity:** DCPD is 1.0 cP at 20 °C (Madbouly 2025). Taylor emulsions at φ ~ 0.1–0.2 stay below 10 cP. Epoxy ISP analogues are often 30–80 mPa s.
2. **Particles from drops:** Chen 2023 shows shear-controlled spherical ISP particles; Della Martina 2005 shows DCPD droplets acting as polymerization microreactors.
3. **Latency:** Hu 2018 phosphite delay (minutes at 50 °C); Kordes/Buchmeiser latent precatalysts; patent examples of delayed DCPD ROMP.
4. **Strength at T ≪ Tg:** unreinforced pDCPD ~78 MPa compressive at ~23 °C vs 41 MPa (6000 psi).
5. **Open pathways:** if φ remains well below packing, the continuous phase is the flow path (Chen NPCL analogue).

## Prior experimental evidence (others, not us)

See `data/literature/evidence_registry.csv` and `docs/scientific_basis.md`. Key OA sources: Chen ACS Omega 2023; Madbouly ACS Omega 2025; Kovacic review 2020; PMC12566568.

## Computational architecture

Seven coupled models + LHS/Sobol UQ + constrained envelope search. SI units. Machine-readable challenge YAML. Status ∈ {PASS, MARGINAL, FAIL, UNKNOWN}.

Reproduce: `uv run python scripts/reproduce_all.py`

## Requirement-by-requirement (nominal ~60 °C vs 150 °C)

Exact numbers are in `results/final_metrics.json` after reproduction. Qualitatively:

| Requirement | ~45–70 °C latent emulsion | 150 °C published Ru/phosphite extrapolation |
|---|---|---|
| Liquid, ≤10 cP | PASS (model + DCPD 1 cP) | PASS (water even thinner) |
| 25–75 min transform | PASS/MARGINAL if inhibitor tuned | FAIL or UNKNOWN (seconds–minutes) |
| 70–600 μm discrete | PASS/MARGINAL (Hinze/Grace + analogue) | Size still plausible; isolation at risk if cure is immediate |
| 6000 psi | PASS/MARGINAL if T ≪ Tg | UNKNOWN (near Tg) |
| Open pathways / no bulk gel | PASS if φ moderate and drops isolated | UNKNOWN/FAIL if instantaneous sticky cure |

## Best candidate operating envelope

Engineering ranges, **not a lab recipe**:

- T ≈ 50–65 °C formation/activation (not 150 °C unless a new latent system is proven)
- φ ≈ 0.10–0.18
- σ ≈ 3–6 mN/m
- inhibitor index high enough that t_solid ∈ 25–75 min at that T
- shear during mixing sufficient to place d32 in 70–600 μm

Conservative / nominal / aggressive numeric points: `results/tables/optimization_envelopes.csv`.

## Uncertainty

Dominant drivers of t_transform: temperature, inhibitor index, catalyst activity (Sobol). Simultaneous PASS probability on the 40–90 °C LHS envelope is in `results/processed/uq_mc.json`. It is **not** a field reliability number.

## Key risks

Premature cure at 150 °C; Tg-limited strength; brine poisoning; coalescence; US11377580B2 overlap. See `docs/risk_register.md`.

## TRL

Integrated PhaseForge fluid: **TRL 3 candidate**, not TRL 3 achieved. Analogous epoxy ISPs and pDCPD chemistry are more mature than this specific integration.

## Validation roadmap

Viscosity, droplet latency at temperature, PSD/sphericity, crush at 150 °C, agglomeration, conductivity. Details in `docs/trl_assessment.md`.

## References

`data/literature/references.bib`
