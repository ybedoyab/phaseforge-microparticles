# TRL assessment

NASA/EU-style TRL is applied **separately** to chemistry, analogues, the integrated PhaseForge fluid, and this software. Conservative.

## Definitions used

| TRL | Meaning (abridged) |
|---|---|
| 1–2 | Principles / concept formulated |
| 3 | Analytical and experimental critical-function proof-of-concept |
| 4 | Component validation in laboratory |
| 5 | Relevant-environment breadboard |

The Innocentive statement invites TRL 3–5. This repository is a **computational / literature** package. It does **not** by itself close experimental TRL 3 for the integrated fluid.

## Split assessment

| Object | Conservative TRL | Why |
|---|---|---|
| ROMP of DCPD to a load-bearing thermoset | 6–9 in manufacturing (RIM pDCPD) | Industrial pDCPD exists; not a downhole microparticle product |
| Latent ROMP catalysts | 3–4 laboratory | Kordes/Buchmeiser/Hu isothermal and DSC data |
| Downhole DCPD/TriCPD polymer | Patent examples + Hu rock-reinforcement paper | Not equivalent to 70–600 μm discrete particles remaining un-agglomerated |
| Emulsified resin ISP (epoxy class) | 4–5 lab; some field (Chen 2023 Energy & Fuels field note) | Different chemistry; viscosity often >10 cP |
| **Integrated PhaseForge fluid** | **TRL 2–3 candidate** | Critical functions have analogues, but the exact brine-dispersed latent DCPD particle system is not experimentally shown here |
| This computational model | Software TRL-style 3 for analysis | Units, tests, UQ, traceability; CFD optional |

**Do not state “TRL 3 achieved” for PhaseForge as a material technology based only on these simulations.**

Acceptable phrasing:

- “TRL-3-oriented analytical proof-of-concept”
- “TRL 3 candidate”
- “computationally validated against published experimental analogues”
- “ready for targeted laboratory TRL-3 validation”

## Minimum experiments to legitimately close laboratory TRL 3

Validation plan only. No unsafe procedures are prescribed.

1. **Viscosity:** emulsion μ(T) from 20–150 °C, φ = 0.05–0.25, confirm ≤10 cP at delivery T.
2. **Latency / transformation:** time-sweep rheology or DSC of **dispersed droplets** (not only bulk resin) at 50, 80, 120, 150 °C; report t_gel and a defined solidification time separately.
3. **Size / morphology:** optical/SEM d32, sphericity, after representative shear.
4. **Strength at temperature:** single-particle or pack crush at 23 °C and 150 °C toward 4,500–6,000 psi.
5. **Agglomeration:** cure in a packed droplet state; count doublets/plugs.
6. **Permeability / conductivity:** slot or API conductivity after in-place formation.

Pass/fail of those tests — not this repo — decides whether experimental TRL 3 is earned.
