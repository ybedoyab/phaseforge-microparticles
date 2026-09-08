# PhaseForge 2D channel — hydrodynamics only

Aqueous-continuous / organic-dispersed VoF transport for `interFoam` (OpenFOAM v2212).

- Geometry: 2D channel, 20 mm × 3 mm, mesh 200×40
- Four initially separated 500 μm droplets (`setFields` uses **metres**)
- Moderate-T properties: `constant/transportProperties` / `.moderate` (~60–70 °C analogue)
- HPHT thermal-property analogue: `constant/transportProperties.hpht` (~150 °C liquid viscosities/IFT)
- IFT 3.2–4 mN/m
- **No ROMP chemistry.** 10,000 psi is not a chemical-rate variable in this incompressible solver.

Logs: `results/raw/cfd/`. Metrics: `results/tables/cfd_metrics.csv` (`CFD_MODEL_PREDICTION`).
Time directories and `polyMesh` are gitignored.
