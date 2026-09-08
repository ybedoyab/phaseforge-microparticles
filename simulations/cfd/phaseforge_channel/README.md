# PhaseForge 2D channel — hydrodynamics only

This case is a simplified aqueous-continuous / organic-dispersed VoF
transport setup for `interFoam`.

- Geometry: 2D channel, 20 mm × 3 mm
- Continuous: water-like (ρ = 1000 kg/m3, μ ≈ 1 cP)
- Dispersed: DCPD-like organic (ρ = 980 kg/m3, μ ≈ 1 cP)
- Interfacial tension: 4 mN/m (within 3–6 mN/m analogue range)
- **No ROMP chemistry in the solver.** Couple cure time only in postprocessing.

Do not treat this folder as experimental evidence. If Docker/OpenFOAM
cannot run, leave logs in `results/raw/cfd/` and do not invent fields.
