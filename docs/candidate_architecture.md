# Candidate architecture

Four families. Statuses are **never mixed** into one global PASS. D899, Cu(I) activation, and patented Mo complexes are **prior-art analogues**, not PhaseForge inventions.

| Family | Idea | Moderate T | 150 °C latency | 150 °C trigger | Mechanics 150 °C | Overall 150 °C |
|---|---|---|---|---|---|---|
| `PhaseForge-RuP` | Ru/Grubbs + phosphite | Candidate window | **FAIL** (~1.6 min t_solid) | Too fast | UNKNOWN (near Tg) | **FAIL** |
| `PhaseForge-HT-Thermal` | Hexacoordinated Mo NHC | Not the primary moderate-T case | **SUPPORTED analogue** (Kordes 2024: no DCPD polymerization up to ~150 °C) | UNKNOWN (thermal activation **>150 °C**; full conversion ~175 °C) | UNKNOWN | **UNKNOWN** |
| `PhaseForge-ChemGate` | **Primary high-T architecture.** Two-stage: Stage A latent droplets without available activator; Stage B aqueous activator chase | Compatible with low-μ carrier | Thermal latency **decoupled** from T if activator is withheld (Lee 2024 D899 dormant through ~200 °C FROMP until Cu(I)) | Aqueous→organic activation **demonstrated** by Lee 2025 (ambient). 25–75 min at 150 °C is **modelled**, not measured | UNKNOWN crush; high-Tg pDCPD-family analogues exist | **UNKNOWN / PLAUSIBLE PATHWAY** |
| `PhaseForge-ChemGate-Acid` | Acid-unmasked latent Ru (Samec/Keitz/Grubbs 2010; Monsaert 2010) | Mixing latency analogue | Not shown at 150 °C | Exploratory | UNKNOWN | **UNKNOWN** (exploratory) |

## ChemGate two-stage deployment

**Stage A — placement fluid.** A low-viscosity aqueous carrier transports latent-catalyst DCPD-family droplets. The activator is **not** present in an available form. This is what prevents chemical activation during HPHT transport.

**Stage B — activator chase.** After the reactive-droplet fluid has reached the target region, a low-viscosity aqueous activator-containing chase is introduced. When that fluid reaches the placed droplets:

aqueous activator → liquid–liquid partition → diffusion into organic droplets → latent catalyst activation → surface-to-core ROMP → discrete particles, with continued open pathways.

D899/Cu remains **prior-art analogue only**. Do not claim its formulation as PhaseForge IP.

## Timing split (do not mix clocks)

```
t_trigger_arrival              operational Stage-B arrival
                               tag: ASSUMED_FOR_DEPLOYMENT_SCENARIO
                               not material kinetics

t_post_trigger_particle      = t_partition + t_diffusion + t_activation
                               + t_polymerization

t_total_after_initial_pumping
                             = t_trigger_arrival + t_post_trigger_particle
```

Innocentive ~25–75 min after pumping is **interpretation A** (`t_total_after_initial_pumping`). **Interpretation B** is time from activator contact (`t_post_trigger_particle` only).

Lee ambient D, activity = 1, 70–600 μm (model, not 150 °C experiment):

| Quantity | Modelled value | Provenance |
|---|---|---|
| t_post_trigger_particle | **approximately 27–35 min** (≈29 min at 270 μm) | MODEL_PREDICTION from analogue partition / Lee D / Suslick activation / residual polymerisation |
| Nominal t_trigger_arrival | 30 min scenario | **ASSUMED_FOR_DEPLOYMENT_SCENARIO** |
| Allowable Stage-B arrival (A in 25–75) | **0 to approximately 40–48 min** (≈0–46 min at 270 μm) | MODEL_PREDICTION envelope over 0–60 min search |
| Nominal total from pumping | **approximately 59 min** at 270 μm (30 + 29) | mixed operational + model |

A fixed 30 min delay is **not required**. Post-trigger time already sits near the 25 min floor, so arrival of 0 min still lands interpretation A inside 25–75 min at these analogue rates. The 30 min figure is one engineering placement scenario, not intrinsic chemical latency.

Do **not** write: “ChemGate intrinsically delays cure for 62 min.”

Prefer: “In the nominal deployment scenario, approximately 30 min of controlled Stage-B trigger arrival is followed by a modelled approximately 29 min post-trigger partition/diffusion/activation/cure sequence at 270 μm (Lee ambient D). The 25–75 min window from initial pumping is a design envelope over Stage-B arrival, not a single kinetic delay.”

See `results/tables/trigger_timing_envelope.csv` and figure `31_trigger_timing_envelope`.

Lee 2025 film-growth D ≈ 6×10⁻⁸ cm²/s = 6×10⁻¹² m²/s is **ambient**, not 150 °C. Innocentive sizes 70–600 μm overlap the Lee observation that filaments ≳400 μm can retain an uncured core at ~20 min. Diffusion is only a few minutes at Lee D for volume-average 50%; the post-trigger total is dominated by assumed partition + analogue activation + analogue polymerisation.

## Practical fluid handling (implementation concept, not validated hardware)

Sequential injection is compatible **in principle** with ordinary pumping systems. This is an engineering concept, not an experimentally validated surface spread.

- **Two reservoirs or sequential batches.** Stage A (latent-droplet fluid) and Stage B (aqueous activator chase) can be separate tanks or successive batches through the same high-pressure pump, as with conventional pad / slurry / flush sequences.
- **Same pumping line.** The wellbore and surface iron can carry Stage A then Stage B. Residual Stage A in the line will mix at the interface.
- **Spacer / chase.** A clean aqueous spacer between Stage A and Stage B is a standard oilfield idea to reduce chemical commingling. It is not demonstrated here.
- **Mixing at the Stage A / Stage B interface.** The interface is not a sharp plane. Taylor–Aris dispersion and wellbore holdup smear the activator front. Modelled timing sensitivity uses an assumed ±5 / ±10 / ±15 min front spread (`ASSUMED_FOR_SENSITIVITY`). A ±10 min smear on a ~59 min nominal total still intersects 25–75 min; it does **not** keep the entire ±15 min band inside the window for every diameter.
- **Placement uncertainty.** Stage A must populate the target before Stage B arrives. Too-early chase is equivalent to activator present during transport (nonuniform early activation). Too-late chase pushes interpretation A past 75 min if post-trigger time is already ~30–35 min (600 μm allowable arrival only to ~40 min).
- **Trigger-front dispersion and bypass.** Preferential flow can deliver activator to some droplets and starve others. That increases variance of local t_trigger_arrival and can leave uncured droplets. Not quantified experimentally.
- **Timing variance.** Operational t_trigger_arrival is the dominant controllable clock; post-trigger chemistry is the weakly diameter-dependent add-on at Lee ambient D.

## What we do not claim

- Exact PhaseForge-ChemGate formulation has been demonstrated.
- D899/Cu is our IP.
- 25–75 min at 150 °C has been measured.
- 6000 psi integrity at 150 °C.
- The two-stage pumping sequence has been field- or lab-validated.

See `docs/150C_decision.md` and `docs/high_temperature_ip_review.md`.
