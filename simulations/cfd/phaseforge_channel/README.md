# PhaseForge 2D channel — 2D screening / baseline CFD

This case is a **2D** `interFoam` calculation (one cell in Z, `frontAndBack` type `empty`, droplets initialized as cylinders). It is **not** full 3D CFD.

Use it as the screening / baseline hydrodynamic model.

The true 3D demonstration is:

`simulations/cfd/phaseforge_channel_3d/`

See `docs/cfd_3d_validation.md`.

- Geometry: 2D channel, 20 mm × 3 mm, mesh 200×40×1
- Four initially separated 500 μm **cylindrical** droplets
- Moderate-T and HPHT property analogues
- **No ROMP chemistry.** 10,000 psi is not a chemical-rate variable.

Logs: `results/raw/cfd/`. Metrics: `results/tables/cfd_metrics.csv` (`CFD_MODEL_PREDICTION`).
