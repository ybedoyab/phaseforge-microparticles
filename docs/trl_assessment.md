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

Acceptable phrasing (keep both):

- “TRL-3-oriented analytical/computational proof-of-concept”
- “Integrated PhaseForge is a TRL 2–3 candidate requiring targeted experimental confirmation.”

**Do not state “TRL 3 achieved” for PhaseForge as a material technology based only on these simulations.**

## Split assessment

| Object | Conservative TRL | Why |
|---|---|---|
| ROMP of DCPD to a load-bearing thermoset | 6–9 in manufacturing (RIM pDCPD) | Industrial pDCPD exists; not a downhole microparticle product |
| Latent ROMP catalysts (Ru/phosphite) | 3–4 laboratory | Hu isothermal gel times; Kordes latency snippets |
| High-T latent Mo precatalysts (PhaseForge-HT) | laboratory DSC | Elser 2018 / Momin 2021 onsets 52–142 °C; **not** isothermal 25–75 min at 150 °C |
| Downhole DCPD/TriCPD polymer | Patent examples + Hu rock-reinforcement paper | Not equivalent to 70–600 μm discrete particles remaining un-agglomerated |
| Emulsified resin ISP (epoxy class) | 4–5 lab; some field (Chen 2023 Energy & Fuels field note) | Different chemistry; viscosity often >10 cP |
| **Integrated PhaseForge fluid** | **TRL 2–3 candidate** | Critical functions have analogues, but the exact brine-dispersed latent DCPD particle system is not experimentally shown here |
| This computational model | Software TRL-style 3 for analysis | Units, tests, UQ, traceability; CFD optional |

## Published experimental analogues mapped to critical functions

These are **other groups’ experiments**, used as analogues, not PhaseForge measurements.

| Critical function | Analogue (not us) | What it does **not** prove |
|---|---|---|
| Liquid-to-particle ISP morphology | Chen 2022/2023; Bai 2025; Yang 2026 | Exact DCPD/brine PhaseForge recipe; ≤10 cP mixture in those epoxy papers is often missed |
| DCPD droplet polymerization | Della Martina 2005 microreactor beads | HPHT transport, 10,000 psi, dense 70–600 μm crush pack |
| Tunable ROMP latency | Hu 2018 phosphite; Kordes 2024 PPh3; US11377580B2 delayed examples | 25–75 min **isothermal at 150 °C** in brine-dispersed droplets |
| High-temperature latent catalyst onset | Elser 2018 T_onset 65–140 °C; Momin 2021 T_onset 52–142 °C; T_exo,max to ~174–183 °C | DSC ramp ≠ 25–75 min hold at 150 °C. PhaseForge-HT status = **UNKNOWN** |
| RT mechanical strength | PMC12566568 ~78 MPa unreinforced pDCPD; patent Table 3 ~73–88 MPa RT | Particle vs bulk; PhaseForge PSD |
| 98 °C mechanical analogue | US11377580B2 Table 3: ~47 and 50 MPa (50 °C reaction examples); ~33 MPa (one 80 °C delayed example); 70/30 DCPD/TriCPD stronger than pure pDCPD at RT and 98 °C | Not 150 °C; not microparticles; some formulations fail 41 MPa |
| Residual flow / conductivity analogue | Chen conductivity / crush cells on epoxy ISP | **Not** measured PhaseForge fracture conductivity. `k_open = 1e-8 m²` is assumed |

## Minimum experiments to legitimately close laboratory TRL 3

Validation plan only. No unsafe procedures are prescribed.

1. **Viscosity:** emulsion μ(T) from 20–150 °C, φ = 0.05–0.25, confirm ≤10 cP at delivery T.
2. **Latency / transformation:** time-sweep rheology or DSC of **dispersed droplets** (not only bulk resin) at 50, 80, 120, 150 °C; report t_gel and a defined solidification time separately.
3. **Size / morphology:** optical/SEM d32, sphericity, after representative shear.
4. **Strength at temperature:** single-particle or pack crush at 23 °C, 98 °C, and 150 °C toward 4,500–6,000 psi.
5. **Agglomeration:** cure in a packed droplet state; count doublets/plugs. Heuristic risk scores are not a substitute.
6. **Permeability / conductivity:** slot or API conductivity after in-place formation under closure.

Pass/fail of those tests — not this repo — decides whether experimental TRL 3 is earned.
