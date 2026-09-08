# Model validation

No model is “validated by us experimentally.” Validation means comparison to **published** measurements or internal sanity checks.

## Kinetics

| Published point | Model | Rel. error target |
|---|---|---|
| Madbouly 19.7 min, 55 °C, 0.04 wt% G2 | t_gel reference (forced match) | ~0 by construction |
| Madbouly 70 min, 50 °C, 0.04 wt% | Arrhenius + n=1.4 | order-of-magnitude (see `results/tables/kinetics_validation.csv`) |
| Madbouly 10 min, 50 °C, 0.12 wt% | catalyst order | fitted compromise |
| Madbouly 50→5 min, 40→60 °C, 0.12 wt% | temperature trend | monotonic PASS |
| Hu 38.5 / 5.98 min at 50 °C | inhibitor factor | separate branch, not Madbouly A-factor |

**Limitation:** calibration window 40–60 °C (Madbouly) and 50–80 °C (Hu). 150 °C is a severe extrapolation. Kessler 2002: Ea rises for α > 0.6, so late-stage solidification may be slower than gel — captured only by the assumed t_solid/t_gel = 1.8.

Time-to-peak in US11377580B2 is **not** used as t_solid.

## Viscosity

- Water μ(T) decreases with T (IAPWS-like). Sanity: μ(20 °C) ≈ 1 cP.
- DCPD 1.0 cP at 20 °C matches Madbouly.
- Chen mixture 33–55 mPa s is an **epoxy analogue** and is above 10 cP — used as a warning, not a PhaseForge measurement.
- Taylor ≤ Einstein ≤ KD at λ~1 and moderate φ (tested).

## Droplets

- Size decreases with shear (Chen 2023 qualitative trend; Hinze/Grace quantitative).
- Yang abstract IFT 3.2–4.5 mN/m used as a nominal σ.
- Absolute d32 is correlation-uncertain (C, ε). UQ spans that.

## Thermal

- Adiabatic ΔT = Hr/Cp is hundreds of K (bulk ROMP runaway is real — patent peak ~160 °C at 50 °C bath).
- For a 200 μm droplet with Nu=2 in water, Bi is small and **computed** ΔT is much smaller than adiabatic. This is a model result, not a droplet calorimetry experiment.
- Sanity: larger d, smaller h, more heating.

## Mechanics

- RT σ_c = 78 MPa vs 41.4 MPa (6000 psi) gives SF > 1 **at room temperature** after a 0.75 particle discount, T ≪ Tg.
- At 150 °C ≈ Tg, status is forced UNKNOWN.
- Chen crush at 69 MPa is epoxy particles, not pDCPD beads.

## Permeability

- Packed-bed KC recovers k ∝ d² and k → 0 as φ_solid → 1.
- Dilute distributed particles keep open pathways at φ = 0.15 (challenge intent).
- Absolute fracture conductivity is **not** claimed.

## CFD

See the CFD section of `AUDIT_REPORT.md` after the Docker attempt. The Python POC does not depend on CFD success. Official GeoChemFoam tutorials are the validation path for the solver, not for ROMP chemistry.

## Coupled envelope

Sanity: raising T at fixed inhibitor shortens t_transform; raising φ raises μ_eff; raising shear reduces d. Tests encode monotonicity.
