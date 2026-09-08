# AUDIT_REPORT

Regenerated after true-3D OpenFOAM/GeoChemFoam hydrodynamics (2026-09-08).

This project did **not** physically perform PhaseForge laboratory experiments.

## Environment status

| Item | Status |
|---|---|
| OS | Windows 10.0.26200, AMD Ryzen 7 5800U (8c/16t), 15.4 GB RAM |
| Git | 2.41.0.windows.3 |
| Python | 3.12 via `uv`; lockfile `uv.lock` |
| Docker | Server 27.4.0, ~8 GB assigned to engine, 16 CPUs |
| GeoChemFoam image | `jcmaes/geochemfoam-5.2` (OpenFOAM **v2212**) |
| ParaView / pvpython | **6.1.1** at `D:\ParaView\ParaView-6.1.1-Windows-Python3.12-msvc2017-AMD64\bin` |
| GitHub Actions | success: https://github.com/ybedoyab/phaseforge-microparticles/actions/runs/34258135741 |

Details: `docs/environment_audit.md`, `docs/cfd_3d_validation.md`.

## Tests

- `uv run ruff check phaseforge tests scripts`: clean
- `uv run pytest --cov=phaseforge`: **79 passed**, core coverage **≈82%**

## 3D CFD (this pass)

True 3D `interFoam` (not an extrusion of the 2D case):

| Item | Nominal | Coarse (sensitivity) |
|---|---|---|
| Mesh | 320×48×32 = **491,520** hex | 160×24×16 = 61,440 |
| Δ / cells across 500 μm | 62.5 μm / **8** | 125 μm / 4 |
| checkMesh | **Mesh OK**, AR=1, non-ortho=0 | **Mesh OK** |
| Directions | 3 geometric + 3 solution | same |
| Initialization | 4× `sphereToCell` (~268 cells each) | 4× `sphereToCell` (~34 cells) |
| End | **yes** (moderate + HPHT) | **yes** |
| t | 0.08 s | 0.08 s |
| Final n droplets | **4** (0 coalescence) | 3 (1 event) |

2D `phaseforge_channel` is retained as **2D screening / baseline**. ChemGate 150 °C statuses are unchanged (RuP FAIL; Mo UNKNOWN; ChemGate UNKNOWN/PLAUSIBLE; crush UNKNOWN; 10,000 psi chemistry UNKNOWN).

## Claim control

See `docs/final_submission_claims.md`. Do not claim 3D CFD proves PhaseForge works or validates ChemGate chemistry.
