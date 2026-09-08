# Simplified PhaseForge 2D channel case (reduced-order coupling)

Hydrodynamics only. ROMP chemistry is **not** solved in OpenFOAM.
Use GeoChemFoam Docker if available:

    bash scripts/run_cfd.sh --check
    bash scripts/run_cfd.sh

If the image cannot be pulled, this folder documents the intended case:

- Geometry: 2D channel / fracture analogue, width ~3 mm, length ~20 mm
- Fluids: water (continuous) + DCPD-like oil (dispersed), μ ~ 1 cP each
- Goal: discrete droplet transport visualization, capillary/Weber regime
- Coupling: one-way — CFD hydrodynamics, Python kinetics/thermal post-process

Do not commit large time directories or processor* folders.
