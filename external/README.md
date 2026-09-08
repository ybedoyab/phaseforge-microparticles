# External software (not vendored)

Clone with `scripts/bootstrap_external.sh`. This directory is gitignored except this README.

| Project | URL | Why | License (inspect upstream) |
|---|---|---|---|
| GeoChemFoam | https://github.com/GeoChemFoam/GeoChemFoam | Pore/channel multiphase OpenFOAM | OpenFOAM-related GPL |
| GeoChemFoam-5.2 | https://github.com/GeoChemFoam/GeoChemFoam-5.2 | Pinned major version | same |
| polykin | https://github.com/HugoMVale/polykin | Polymerization kinetics library (optional) | inspect repo |
| PyFrac | https://github.com/GeoEnergyLab-EPFL/PyFrac | Optional fracture mechanics | inspect repo |

Prefer Docker image `jcmaes/geochemfoam-5.2` over compiling OpenFOAM.

Pin the commit hash in `docs/environment_audit.md` / `AUDIT_REPORT.md` when a clone succeeds.
