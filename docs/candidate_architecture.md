# Candidate architecture

Four families. Statuses are **never mixed** into one global PASS. D899, Cu(I) activation, and patented Mo complexes are **prior-art analogues**, not PhaseForge inventions.

| Family | Idea | Moderate T | 150 °C latency | 150 °C trigger | Mechanics 150 °C | Overall 150 °C |
|---|---|---|---|---|---|---|
| `PhaseForge-RuP` | Ru/Grubbs + phosphite | Candidate window | **FAIL** (~1.6 min t_solid) | Too fast | UNKNOWN (near Tg) | **FAIL** |
| `PhaseForge-HT-Thermal` | Hexacoordinated Mo NHC | Not the primary moderate-T case | **SUPPORTED analogue** (Kordes 2024: no DCPD polymerization up to ~150 °C) | UNKNOWN (thermal activation **>150 °C**; full conversion ~175 °C) | UNKNOWN | **UNKNOWN** |
| `PhaseForge-ChemGate` | **Primary high-T architecture.** Latent catalyst in organic droplets; aqueous chemical activator after placement | Compatible with low-μ carrier | Thermal latency **decoupled** from T if activator is withheld (Lee 2024 D899 dormant through ~200 °C FROMP until Cu(I)) | Aqueous→organic activation **demonstrated** by Lee 2025 (ambient). 25–75 min at 150 °C is **modelled**, not measured | UNKNOWN crush; high-Tg pDCPD-family analogues exist | **UNKNOWN / PLAUSIBLE PATHWAY** |
| `PhaseForge-ChemGate-Acid` | Acid-unmasked latent Ru (Samec/Keitz/Grubbs 2010; Monsaert 2010) | Mixing latency analogue | Not shown at 150 °C | Exploratory | UNKNOWN | **UNKNOWN** (exploratory) |

## ChemGate timing

```
t_transform = t_delay + t_partition + t_diff + t_activation + t_polymerization
```

This is **not** an Arrhenius gel-time extrapolation of Ru/phosphite. If the activator is already in the brine during transport, small droplets can cure too fast; the architecture **requires delayed activator contact** (placement / target-contact / staged chemical).

Lee 2025 film-growth D ≈ 6×10⁻⁸ cm²/s = 6×10⁻¹² m²/s is **ambient**, not 150 °C. Innocentive sizes 70–600 μm overlap the Lee observation that filaments ≳400 μm can retain an uncured core at ~20 min.

## What we do not claim

- Exact PhaseForge-ChemGate formulation has been demonstrated.
- D899/Cu is our IP.
- 25–75 min at 150 °C has been measured.
- 6000 psi integrity at 150 °C.

See `docs/150C_decision.md` and `docs/high_temperature_ip_review.md`.
