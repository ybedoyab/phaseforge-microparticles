# GeoChemFoam / OpenFOAM notes

Hydrodynamics only. ROMP chemistry is **not** solved in OpenFOAM.

```
bash scripts/run_cfd.sh --check
bash scripts/run_cfd.sh --solve
python scripts/cfd_postprocess.py
```

`--check` probes the image. A tutorial **directory listing is not a solved case**.

`--solve` attempts:

1. One official two-phase GeoChemFoam or OpenFOAM `interFoam` tutorial, with logs under `results/raw/cfd/`.
2. The custom 2D PhaseForge channel in `simulations/cfd/phaseforge_channel/` (water continuous, organic droplets, IFT 4 mN/m).

If Docker Desktop’s engine is not running, the script records `docker_unavailable.txt` and **does not fabricate fields**.
