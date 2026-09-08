# Submission evidence pack (technical basis)

This is the concise technical basis for an Innocentive-style write-up. It is **not** a claim that this project ran laboratory experiments on the exact PhaseForge fluid.

Claim control: `docs/final_submission_claims.md`.

## Problem

Deliver a liquid with μ ≤ 10 cP, keep it fluid during transport (up to ~150 °C, ~10,000 psi), then form discrete 70–600 μm load-bearing particles after ~25–75 min, surviving ~4,500–6,000 psi, without making a bulk gel plug so that fluid can still flow around the assembly.

## Proposed mechanism

**PhaseForge — thermally latent fluid-to-microparticle system.** Aqueous carrier + DCPD-rich droplets as isolated ROMP microreactors. Latency expires after placement; each drop becomes a pDCPD-family particle.

Two catalyst families:

1. **Ru/Grubbs + phosphite (primary modelled branch).** Moderate temperature: feasible **candidate** window. 150 °C: kinetics **FAIL** / mechanics **UNKNOWN**. Do not force a 150 °C PASS.
2. **PhaseForge-HT (Mo imido alkylidene NHC, Elser 2018 / Momin 2021).** DSC onsets approximately 52–142 °C; exotherm maxima to approximately 174–183 °C. Status **UNKNOWN**. A pathway toward the upper-temperature requirement, not a fabricated isothermal PASS.

## Why it may work

1. **Viscosity:** DCPD is 1.0 cP at 20 °C (Madbouly 2025). Taylor emulsions at φ ~ 0.1–0.2 stay below 10 cP. Epoxy ISP analogues are often 30–80 mPa s.
2. **Particles from drops:** Chen 2023 shows shear-controlled spherical ISP particles; Della Martina 2005 shows DCPD droplets acting as polymerization microreactors.
3. **Latency:** Hu 2018 phosphite delay (minutes at 50 °C); Kordes/Buchmeiser latent precatalysts; patent examples of delayed DCPD ROMP.
4. **Strength at T ≪ Tg:** unreinforced pDCPD ~78 MPa compressive at ~23 °C vs 41 MPa (6000 psi). 98 °C analogue: US11377580B2 Table 3 bulk yield about 33–50 MPa.
5. **Open pathways:** if φ remains well below packing, the continuous phase is geometrically available (claim A). Analytical k (claim B) uses assumed `k_open`. Conductivity under closure (claim C) is **unvalidated** for PhaseForge → requirement status **MARGINAL**.

## Prior experimental evidence (others, not us)

See `data/literature/evidence_registry.csv` and `docs/scientific_basis.md`. Key OA sources: Chen ACS Omega 2023; Madbouly ACS Omega 2025; Kovacic review 2020; PMC12566568. Mo latent: Elser 2018; Momin 2021 (abstracts).

## Computational architecture

Seven coupled models + LHS/Sobol UQ + constrained envelope search. SI units. Machine-readable challenge YAML. Status ∈ {PASS, MARGINAL, FAIL, UNKNOWN}.

Reproduce: `uv run python scripts/reproduce_all.py`

## Requirement-by-requirement (nominal ~60 °C vs 150 °C)

Exact raw numbers are in `results/final_metrics.json`. Reviewer-facing values are rounded.

| Requirement | ~50–70 °C latent emulsion | 150 °C Ru/phosphite | PhaseForge-HT |
|---|---|---|---|
| Liquid, ≤10 cP | PASS (model + DCPD 1 cP) | PASS (water even thinner) | PASS (delivery viscosity) |
| 25–75 min transform | PASS/MARGINAL if inhibitor tuned | **FAIL** (seconds–minutes) | **UNKNOWN** (DSC ≠ isothermal) |
| 70–600 μm discrete | PASS size **candidate** (~270 μm nominal); isolation analogue | Size still plausible; sticky cure **UNKNOWN** | UNKNOWN latency |
| 6000 psi | PASS **candidate** if T ≪ Tg | **UNKNOWN** (near Tg) | UNKNOWN |
| Open pathways / agglomeration | **MARGINAL** (heuristics / unvalidated k) | UNKNOWN/FAIL if instantaneous sticky cure | UNKNOWN |
| R03 upper-T capability | Does **not** satisfy “up to ~150 °C” by itself | FAIL kinetics | UNKNOWN pathway |

## Best candidate operating envelope

Engineering ranges, **not a lab recipe**:

- T ≈ 50–70 °C formation/activation for the Ru/phosphite branch
- φ ≈ 0.10–0.18
- σ ≈ 3–6 mN/m
- inhibitor index high enough that t_solid ∈ 25–75 min at that T
- shear during mixing sufficient to place d32 in 70–600 μm
- PhaseForge-HT only as the **proposed route** toward 150 °C, status UNKNOWN

Conservative / nominal / aggressive numeric points: `results/tables/optimization_envelopes.csv` (core physics). Overall system claims remain MARGINAL because agglomeration and conductivity are unvalidated.

## Uncertainty

Dominant drivers of t_transform: temperature, inhibitor index, catalyst activity (Sobol). Simultaneous **core** PASS probability on the 40–90 °C LHS envelope is in `results/processed/uq_mc.json`. Quote probabilities to about 2 significant digits (n=400). It is **not** a field reliability number. `overall_pass` is expected near zero after the agglomeration/permeability honesty fix.

## Key risks

Premature cure at 150 °C; Tg-limited strength; brine poisoning; coalescence; US11377580B2 overlap. See `docs/risk_register.md`.

## TRL

Keep: **TRL-3-oriented analytical/computational proof-of-concept**.

Keep: **Integrated PhaseForge is a TRL 2–3 candidate requiring targeted experimental confirmation.**

Do not claim TRL 3 achieved. Analogue mapping: `docs/trl_assessment.md`.

## Validation roadmap

Viscosity, droplet latency at temperature, PSD/sphericity, crush at 98 °C and 150 °C, agglomeration, conductivity. Details in `docs/trl_assessment.md`.

## References

`data/literature/references.bib`
