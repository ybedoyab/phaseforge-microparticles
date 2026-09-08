# Opening PhaseForge 3D cases in ParaView

ParaView CLI (`pvpython`) was **not** installed on the Windows host used for this pass. Scientific 3D figures were generated from the OpenFOAM `foamToVTK` output with PyVista/VTK. Do **not** treat a missing GUI screenshot as a missing solve.

## Files

| Item | Path |
|---|---|
| Moderate-T case | `simulations/cfd/phaseforge_channel_3d/phaseforge_3d.foam` |
| HPHT property analogue | `simulations/cfd/phaseforge_channel_3d_hpht/phaseforge_3d.foam` |
| State (camera / pipeline notes) | `visualization/phaseforge_3d.pvsm` |
| VTK (after `foamToVTK`) | `simulations/cfd/phaseforge_channel_3d/VTK/` |

Time directories and `polyMesh` are gitignored. Reproduce fields with:

```
uv run python scripts/run_cfd_3d.py --only moderate
```

## Open in ParaView GUI

1. Install ParaView 5.11+ from https://www.paraview.org/
2. File → Open → `simulations/cfd/phaseforge_channel_3d/phaseforge_3d.foam`
3. In Pipeline Browser, Apply. Select **alpha.water**.
4. Filters → Alphabetical → Contour. Isosurface value **0.5**.
5. Camera: azimuth ~32°, elevation ~22° (perspective).
6. Optional: File → Load State → `visualization/phaseforge_3d.pvsm` (re-point the case directory if asked).

A GUI screenshot `figures/software_evidence/paraview_phaseforge_3d.png` is created only if a real ParaView window can be captured. It was **not fabricated**.
