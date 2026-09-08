# PhaseForge 3D channel — hydrodynamic demonstration

True 3D `interFoam` case (OpenFOAM v2212 / GeoChemFoam). Not an extrusion of the 2D screening case.

- Domain: 20 × 3 × 2 mm
- Mesh: 160 × 24 × 16 hex cells (61440 cells)
- Cell size: 125.0 μm (isotropic in the nominal dict)
- Cells across 500 μm droplet: 4.0
- Boundaries: inlet/outlet patches; four long faces are **walls** (noSlip). No `empty` patch.
- IC: four `sphereToCell` organic droplets, d = 500 μm, distinct Y and Z.
- Hydrodynamics only. No ChemGate chemistry. 10,000 psi is not a chemical-rate variable.

The 2D case `simulations/cfd/phaseforge_channel` remains **2D screening / baseline CFD**.
