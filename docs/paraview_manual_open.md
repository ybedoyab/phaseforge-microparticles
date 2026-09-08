# Opening PhaseForge 3D cases in ParaView

ParaView **6.1.1** was used on this Windows host (`pvpython` + GUI). Scientific figures in `figures/paraview/` were generated with `pvpython`. The GUI screenshot is `figures/software_evidence/paraview_phaseforge_3d_gui.png`.

## One command

If drive `P:` is mapped to this repository (`subst P: "<repo>"`), open the configured state with:

```
"D:\ParaView\ParaView-6.1.1-Windows-Python3.12-msvc2017-AMD64\bin\paraview.exe" --state "P:\visualization\phaseforge_3d.pvsm"
```

Otherwise, from ParaView: File → Load State → `visualization/phaseforge_3d.pvsm` and re-point the case directory if asked.

HPHT analogue: `visualization/phaseforge_3d_hpht.pvsm`

## Files

| Item | Path |
|---|---|
| Moderate-T OpenFOAM case | `simulations/cfd/phaseforge_channel_3d/phaseforge_3d.foam` |
| HPHT property analogue | `simulations/cfd/phaseforge_channel_3d_hpht/phaseforge_3d.foam` |
| ParaView XML state | `visualization/phaseforge_3d.pvsm` |
| HPHT XML state | `visualization/phaseforge_3d_hpht.pvsm` |
| pvpython renderer | `scripts/paraview_phaseforge_3d.py` |

Time directories and `polyMesh` are gitignored. If fields are missing locally, reproduce with `uv run python scripts/run_cfd_3d.py --only moderate` (this reruns hydrodynamics).
