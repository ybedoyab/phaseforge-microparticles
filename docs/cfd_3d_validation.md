# PhaseForge 3D CFD validation

**2D screening / baseline:** `simulations/cfd/phaseforge_channel` (one cell in Z, `empty` frontAndBack, cylinder initialization).

**3D hydrodynamic demonstration:** `simulations/cfd/phaseforge_channel_3d` (multiple cells in X, Y, and Z; `sphereToCell` droplets; no `empty` patch).

This is incompressible volume-of-fluid hydrodynamics. It does **not** prove ChemGate chemistry, 150 °C kinetics, 25–75 min cure, or 6000 psi particle strength.

## Solver

- Docker image: `jcmaes/geochemfoam-5.2`
- OpenFOAM: **v2212**
- Application: `interFoam` (laminar VoF)
- Official environment check remains `simulations/cfd/official_damBreak`

## Geometry

Rectangular duct:

- X = 20 mm (streamwise)
- Y = 3 mm (height)
- Z = 2 mm (span)

Inlet and outlet are patches. The four long faces are **walls** with `noSlip`. Walls are the physically appropriate confinement for a millimetre-scale channel; slip/symmetry would hide wall interaction. Gravity is off (`g = 0`) so settling is not mixed into the transport test.

## Mesh

Nominal structured hex mesh:

- 320 × 48 × 32 = **491,520** cells
- Δ ≈ 62.5 μm (isotropic)
- **8 cells** across the 500 μm droplet diameter
- Coarse sensitivity mesh: 160 × 24 × 16 = 61,440 cells (4 cells across diameter)

`checkMesh` on the solved coarse case: **Mesh OK**, max aspect ratio 1, non-orthogonality 0, skewness ~0. See `results/raw/cfd/cfd3d_*_checkMesh.log`.

This is **mesh sensitivity**, not mesh independence.

## Phases

Continuous: aqueous (`alpha.water = 1`). Dispersed: organic microreactor analogue (`alpha.water = 0`).

| Case | ρ_w | ν_w | ρ_oil | ν_oil | σ |
|---|---|---|---|---|---|
| Moderate-T (~60–70 °C) | 983 kg/m³ | 4.1×10⁻⁷ m²/s | 960 | 5.1×10⁻⁷ | 4.0 mN/m |
| HPHT property analogue (~150 °C) | 917 | 2.0×10⁻⁷ | 880 | 3.2×10⁻⁷ | 3.2 mN/m |

The 150 °C case uses temperature-dependent **liquid properties**. It is not a 10,000 psi chemical-rate model.

## Initial condition

Four non-overlapping **spheres**, diameter 500 μm, at distinct X, Y, and Z (`sphereToCell`, not `cylinderToCell`).

## Solver settings

- `endTime` 0.08 s (droplet displacement ~4 mm at U = 0.05 m/s)
- adaptive Δt, `maxCo` = 0.4, `maxAlphaCo` = 0.4
- Euler / vanLeer MULES VoF
- optional 4-way `simple` decomposition

## Results

See `results/tables/cfd_3d_metrics.csv` (`CFD_3D_MODEL_PREDICTION`).

**Nominal 491,520-cell mesh (solved to End, 0.08 s):**

- Initial droplets: 4 spheres (`sphereToCell`, ~264–276 cells each)
- Final droplets: **4** (no coalescence events on this mesh)
- Volume-equivalent diameter: approximately **472–485 μm** at t = 0.08 s
- Wadell sphericity (from volume and ∫|∇α|dV area): approximately **0.97–0.98**
- Deformation (1 − √(λ_min/λ_max) of cell-cloud covariance): up to about **0.09**
- Mean streamwise displacement consistent with U = 0.05 m/s × 0.08 s ≈ 4 mm
- Pressure drop: approximately **4 Pa**

**150 °C property analogue (same mesh, End at 0.08 s):** four droplets remain discrete; pressure drop ≈ **2.3 Pa** (lower viscosity) vs ≈ **4.0 Pa** moderate-T. This is a hydrodynamic property difference, not a chemistry result.

**Coarse 61,440-cell mesh (mesh sensitivity, not independence):** final connected-component count **3** (one coalescence or wall-interaction event). Four cells across the diameter is not equivalent to the nominal result.

## Dimensionless groups (U = 0.05 m/s, d = 500 μm, H = 3 mm)

## Limitations

- No chemistry / no ChemGate activation in CFD
- No compressible 10,000 psi model
- Short hydrodynamic window (0.08 s)
- VOF interface thickness and mass loss on coarse meshes
- No experimental PIV/CFD validation
- Sphericity uses ∫|∇α|dV for area; values slightly above 1 mean the area estimator is biased on smeared interfaces, not a super-spherical particle

## Claim language

A full three-dimensional multiphase OpenFOAM/GeoChemFoam model was solved to examine hydrodynamic transport of four initially spherical dispersed droplets. The model tracks volumetric phase fraction, velocity and pressure fields and is post-processed from VTK (PyVista; ParaView-compatible `.foam`). In the simulated hydrodynamic interval, see the metrics table for the actual droplet count, deformation and pressure drop.

Do **not** say the 3D simulation proves PhaseForge works or validates ChemGate chemistry.
