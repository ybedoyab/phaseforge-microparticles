# Assumptions

Every significant number is tagged with exactly one provenance class.
This file lists assumptions that affect feasibility conclusions.

## Provenance rules

| Tag | Meaning |
|---|---|
| PUBLISHED_EXPERIMENTAL | Measured in a retrieved paper/patent/manufacturer page |
| DIGITIZED_FROM_PUBLICATION | Read from a figure (none used as primary calibration here) |
| MANUFACTURER_DATA | Vendor specification |
| FITTED | Fit to published points (e.g. catalyst order n, Ca_crit shape) |
| ASSUMED_FOR_SENSITIVITY | Engineering range; not claimed as a measurement |
| MODEL_PREDICTION | Output of a PhaseForge model |

## Kinetics

- Gel time follows Arrhenius with Ea = 79.3 kJ/mol (Madbouly 2025) and reference t_gel = 19.7 min at 55 °C, 0.04 wt% Grubbs II.
- Catalyst order n = 1.4 (FITTED between first-order and the 70 min vs 10 min 50 °C pair).
- Inhibitor index 0–1 scales gel time up to `inhibitor_factor_max` (default 12), bounded by Hu 2018 phosphite factors (~6.4 at 50 °C).
- t_solid / t_gel = 1.8 (ASSUMED). Time-to-peak is **not** treated as solidification (US11377580B2 TtP is recorded separately).
- Extrapolation above ~80 °C, and especially to 150 °C, is outside the isothermal calibration window. With `latency_extra = 1`, 150 °C is UNKNOWN/FAIL, not PASS.

## Thermal

- Droplet Nu = 2 (conduction limit). This **maximizes** self-heating risk relative to flowing convection.
- Cp ≈ 1700 J/kg/K and Hr ≈ 4e5 J/kg are order-of-magnitude (ASSUMED).
- Neighbor coupling is a φ/(1−φ) scaling, not CFD.

## Viscosity

- Continuous phase = water viscosity (IAPWS-like fit) × 1.1 brine factor (ASSUMED).
- Dispersed phase = DCPD 1.0 cP at 20 °C (Madbouly 2025) with Andrade T-slope 15 kJ/mol (ASSUMED).
- Taylor (dilute) / Pal-style (moderate φ). Krieger–Dougherty is comparison only (rigid spheres).

## Droplets

- Hinze C = 0.55 (literature-typical, UQ 0.4–0.8).
- Dissipation = max(shear estimate, **turb_fraction × U³/L**) with turb_fraction = 0.02 (ASSUMED_FOR_SENSITIVITY). Sensitivity spans 0.005–0.10.
- Shrinkage = 3% (ASSUMED).
- Coalescence risk is a 0–1 score, not a measured rate. **Heuristic low risk cannot independently PASS** the agglomeration requirement (MARGINAL unless validated). High-T sticky cure is UNKNOWN.

## Mechanics

- Room-temperature compressive strength 78 MPa (PMC12566568, unreinforced pDCPD).
- Strength retention falls toward 0.05 at Tg. This is a scenario function, **not** a measured 150 °C crush curve.
- Particle vs bulk coupon discount 0.75 (ASSUMED).
- If T ≥ Tg − 20 °C or T ≥ 140 °C, status is UNKNOWN even if SF > 1.
- 98 °C analogue: US11377580B2 Table 3 bulk yields about 33–50 MPa (patent examples, not PhaseForge).

## Permeability

- **A.** Geometric connectivity / continuous-phase availability (1−φ if distributed).
- **B.** Analytical k: Kozeny–Carman (settled) or dilute obstruction vs **assumed** k_open = 1e-8 m² (ASSUMED_FOR_SENSITIVITY). `k_rel` is not experimental conductivity.
- **C.** Conductivity under closure stress is unvalidated for PhaseForge → status **MARGINAL** unless disconnected (FAIL).
- Fracture geometry of the Seeker application is unknown.

## PhaseForge-HT

- Mo latent DSC onsets (Elser 2018, Momin 2021) are **not** converted into isothermal 25–75 min times.
- Status remains UNKNOWN. No latency multiplier is used to force a 150 °C PASS.

## Integrity rule

If an assumption is doing the work of turning FAIL into PASS at 150 °C (for example a 2000× extra latency multiplier), the result is labelled ASSUMED_FOR_SENSITIVITY and is **not** a published-chemistry PASS.
