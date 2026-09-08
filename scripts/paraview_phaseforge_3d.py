"""ParaView/pvpython renderer for the true-3D PhaseForge interFoam case.

This file is executed by Kitware pvpython, not by the project venv.
It must not import phaseforge.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path


def _log(msg: str) -> None:
    print(msg, flush=True)


def _save_meta(png: Path, **kwargs) -> None:
    payload = {
        "generated_utc": datetime.now(UTC).isoformat(),
        "openfoam": "v2212",
        "image": "jcmaes/geochemfoam-5.2",
        "renderer": "ParaView",
        "file": png.name,
        **kwargs,
    }
    png.with_suffix(".json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _oblique_camera(view, bounds) -> None:
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    cx = 0.5 * (xmin + xmax)
    cy = 0.5 * (ymin + ymax)
    cz = 0.5 * (zmin + zmax)
    dx, dy, dz = xmax - xmin, ymax - ymin, zmax - zmin
    diag = math.sqrt(dx * dx + dy * dy + dz * dz)
    az = math.radians(32.0)
    el = math.radians(22.0)
    dist = 2.35 * max(diag, 1e-6)
    view.CameraParallelProjection = 0
    view.CameraFocalPoint = [cx, cy, cz]
    view.CameraPosition = [
        cx - dist * math.cos(el) * math.cos(az),
        cy - dist * math.cos(el) * math.sin(az),
        cz + dist * math.sin(el),
    ]
    view.CameraViewUp = [0.05, 0.12, 0.99]
    view.CameraViewAngle = 18


def _style_view(view) -> None:
    view.Background = [1.0, 1.0, 1.0]
    view.OrientationAxesVisibility = 1
    view.OrientationAxesLabelColor = [0.1, 0.1, 0.1]
    view.OrientationAxesOutlineColor = [0.2, 0.2, 0.2]
    try:
        view.UseColorPaletteForBackground = 0
    except Exception:
        pass
    grid = view.AxesGrid
    grid.Visibility = 1
    grid.XTitle = "X (m)"
    grid.YTitle = "Y (m)"
    grid.ZTitle = "Z (m)"
    grid.XTitleColor = [0.1, 0.1, 0.1]
    grid.YTitleColor = [0.1, 0.1, 0.1]
    grid.ZTitleColor = [0.1, 0.1, 0.1]
    grid.GridColor = [0.75, 0.75, 0.75]
    grid.ShowGrid = 0
    try:
        grid.XLabelColor = [0.15, 0.15, 0.15]
        grid.YLabelColor = [0.15, 0.15, 0.15]
        grid.ZLabelColor = [0.15, 0.15, 0.15]
        grid.XTitleFontSize = 12
        grid.YTitleFontSize = 12
        grid.ZTitleFontSize = 12
        grid.XLabelFontSize = 10
        grid.YLabelFontSize = 10
        grid.ZLabelFontSize = 10
    except Exception:
        pass


def _compact_bar(lut, view, title: str):
    from paraview.simple import GetScalarBar

    bar = GetScalarBar(lut, view)
    bar.Title = title
    bar.ComponentTitle = ""
    bar.TitleFontSize = 10
    bar.LabelFontSize = 8
    bar.TitleColor = [0.05, 0.05, 0.05]
    bar.LabelColor = [0.05, 0.05, 0.05]
    try:
        bar.BackgroundColor = [1, 1, 1, 1]
    except Exception:
        pass
    try:
        bar.WindowLocation = "LowerRightCorner"
        bar.ScalarBarLength = 0.28
        bar.ScalarBarThickness = 12
    except Exception:
        pass
    return bar


def _set_time(scene, tk, value: float | None, last: bool = False) -> float | None:
    times = []
    try:
        times = list(tk.TimestepValues)
    except Exception:
        try:
            times = list(scene.TimeKeeper.TimestepValues)
        except Exception:
            times = []
    if not times:
        return None
    if last or value is None:
        t = float(times[-1])
    else:
        t = min(times, key=lambda x: abs(float(x) - float(value)))
        t = float(t)
    try:
        tk.Time = t
    except Exception:
        scene.AnimationTime = t
    scene.GoToLast() if last and value is None else None
    try:
        scene.AnimationTime = t
    except Exception:
        pass
    return t


def _load_source(simple, foam: Path, vtk_series: Path | None):
    src = None
    kind = None
    if foam.is_file() or foam.exists():
        try:
            src = simple.OpenFOAMReader(registrationName="phaseforge_channel_3d", FileName=str(foam))
            src.UpdatePipelineInformation()
            try:
                src.CaseType = "Reconstructed Case"
            except Exception:
                pass
            arrays = []
            try:
                arrays = list(src.CellArrays.Available)
            except Exception:
                try:
                    arrays = list(src.CellArrays)
                except Exception:
                    arrays = []
            wanted = [n for n in ("alpha.water", "U", "p", "p_rgh") if n in arrays]
            if wanted:
                src.CellArrays = wanted
            try:
                regions = list(src.MeshRegions.Available)
            except Exception:
                regions = []
            if "internalMesh" in regions:
                src.MeshRegions = ["internalMesh"]
            src.UpdatePipeline()
            kind = "OpenFOAM"
            _log(f"loaded OpenFOAM reader arrays={wanted} regions={regions}")
        except Exception as exc:
            _log(f"OpenFOAMReader failed: {exc}")
            src = None
    if src is None and vtk_series is not None and vtk_series.is_file():
        src = simple.OpenDataFile(str(vtk_series), registrationName="phaseforge_channel_3d_vtk")
        src.UpdatePipeline()
        kind = "VTK"
        _log(f"loaded VTK series {vtk_series}")
    if src is None:
        raise RuntimeError("Could not open OpenFOAM .foam or VTK series for the true-3D case")
    return src, kind


def _point_data(simple, src):
    c2p = simple.CellDatatoPointData(registrationName="PointData", Input=src)
    try:
        c2p.PassCellData = 1
    except Exception:
        pass
    c2p.UpdatePipeline()
    return c2p


def _hide_all(simple, view, objs) -> None:
    for o in objs:
        try:
            simple.Hide(o, view)
        except Exception:
            pass


def _shot(simple, view, path: Path, res) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    simple.SaveScreenshot(
        str(path),
        view,
        ImageResolution=res,
        CompressionLevel="1",
        TransparentBackground=0,
    )
    _log(f"wrote {path}")


def build(args) -> int:
    import paraview.simple as simple
    from paraview.simple import (
        Calculator,
        ColorBy,
        Contour,
        ExtractSurface,
        GetActiveViewOrCreate,
        GetAnimationScene,
        GetColorTransferFunction,
        GetTimeKeeper,
        Hide,
        Outline,
        Render,
        ResetCamera,
        SaveAnimation,
        SaveState,
        Show,
        Slice,
        StreamTracer,
    )

    simple._DisableFirstRenderCameraReset()

    foam = Path(args.foam)
    vtk_series = Path(args.vtk_series) if args.vtk_series else None
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    state_path = Path(args.state)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    res = [int(args.width), int(args.height)]

    src, kind = _load_source(simple, foam, vtk_series)
    scene = GetAnimationScene()
    tk = GetTimeKeeper()
    try:
        scene.UpdateAnimationUsingDataTimeSteps()
    except Exception:
        pass

    view = GetActiveViewOrCreate("RenderView")
    _style_view(view)
    pts = _point_data(simple, src)

    contour = Contour(registrationName="alpha0.5_interface", Input=pts)
    contour.ContourBy = ["POINTS", "alpha.water"]
    contour.Isosurfaces = [0.5]
    contour.PointMergeMethod = "Uniform Binning"

    walls = ExtractSurface(registrationName="channel_surface", Input=pts)
    outline = Outline(registrationName="channel_outline", Input=src)

    umag = Calculator(registrationName="UMagnitude", Input=pts)
    umag.Function = "mag(U)"
    umag.ResultArrayName = "UMag"

    vel_slice = Slice(registrationName="velocity_slice", Input=umag)
    vel_slice.SliceType = "Plane"
    vel_slice.HyperTreeGridSlicer = "Plane"
    vel_slice.SliceType.Origin = [0.01, 0.0015, 0.001]
    vel_slice.SliceType.Normal = [0.0, 0.0, 1.0]

    p_slice = Slice(registrationName="pressure_slice", Input=pts)
    p_slice.SliceType = "Plane"
    p_slice.SliceType.Origin = [0.01, 0.0015, 0.001]
    p_slice.SliceType.Normal = [0.0, 1.0, 0.0]

    streams = None
    stream_ok = False
    try:
        streams = StreamTracer(registrationName="velocity_streamlines", Input=pts, SeedType="Line")
        streams.Vectors = ["POINTS", "U"]
        streams.MaximumStreamlineLength = 0.022
        streams.SeedType.Point1 = [0.0008, 0.0004, 0.0003]
        streams.SeedType.Point2 = [0.0008, 0.0026, 0.0017]
        streams.SeedType.Resolution = 18
        streams.UpdatePipeline()
        stream_ok = True
    except Exception as exc:
        _log(f"StreamTracer skipped: {exc}")
        streams = None

    pipeline = [src, pts, contour, walls, outline, umag, vel_slice, p_slice]
    if streams is not None:
        pipeline.append(streams)

    t_last = _set_time(scene, tk, None, last=True)
    for obj in pipeline:
        try:
            obj.UpdatePipeline(t_last)
        except Exception:
            obj.UpdatePipeline()

    crep = Show(contour, view)
    crep.Representation = "Surface"
    try:
        ColorBy(crep, None)
    except Exception:
        pass
    crep.DiffuseColor = [0.78, 0.32, 0.10]
    crep.AmbientColor = [0.78, 0.32, 0.10]
    crep.Opacity = 1.0
    crep.Specular = 0.15

    wrep = Show(walls, view)
    wrep.Representation = "Surface"
    wrep.Opacity = 0.07
    wrep.DiffuseColor = [0.55, 0.62, 0.72]
    try:
        ColorBy(wrep, None)
    except Exception:
        pass

    orep = Show(outline, view)
    orep.Representation = "Wireframe"
    orep.AmbientColor = [0.15, 0.15, 0.18]
    orep.DiffuseColor = [0.15, 0.15, 0.18]
    orep.LineWidth = 1.5

    srep = Show(vel_slice, view)
    srep.Representation = "Surface"
    ColorBy(srep, ("POINTS", "UMag"))
    lut_u = GetColorTransferFunction("UMag")
    lut_u.ApplyPreset("Cool to Warm (Extended)", True)
    lut_u.RescaleTransferFunction(0.0, 0.08)
    srep.SetScalarBarVisibility(view, True)
    _compact_bar(lut_u, view, "U (m/s)")

    prep = Show(p_slice, view)
    prep.Representation = "Surface"
    ColorBy(prep, ("POINTS", "p"))
    lut_p = GetColorTransferFunction("p")
    lut_p.ApplyPreset("Cool to Warm (Extended)", True)
    prep.SetScalarBarVisibility(view, False)

    strep = None
    if stream_ok and streams is not None:
        strep = Show(streams, view)
        strep.Representation = "Surface"
        ColorBy(strep, ("POINTS", "U"))
        strep.SetScalarBarVisibility(view, False)

    Hide(vel_slice, view)
    Hide(p_slice, view)
    if streams is not None:
        Hide(streams, view)

    ResetCamera(view)
    try:
        bounds = src.GetDataInformation().GetBounds()
    except Exception:
        bounds = (0.0, 0.02, 0.0, 0.003, 0.0, 0.002)
    _oblique_camera(view, bounds)
    Render()

    SaveState(str(state_path))
    _log(f"saved state {state_path}")
    head = state_path.read_text(encoding="utf-8", errors="replace")[:80]
    if "<" not in head:
        raise RuntimeError(f"State file is not XML: {state_path}")

    extras = {
        "dataset": kind,
        "foam": str(foam),
        "paraview_script": Path(__file__).name,
        "timestep_s": t_last,
        "mesh": "320x48x32",
    }

    # 01 initial interface
    t0 = _set_time(scene, tk, 0.0, last=False)
    Hide(vel_slice, view)
    Hide(p_slice, view)
    if streams is not None:
        Hide(streams, view)
    srep.SetScalarBarVisibility(view, False)
    Show(contour, view)
    Show(walls, view)
    Show(outline, view)
    Render()
    p01 = out / "01_phaseforge_3d_interface.png"
    if args.tag == "hpht":
        p01 = out / "01_phaseforge_3d_hpht_interface.png"
    _shot(simple, view, p01, res)
    _save_meta(p01, field="alpha.water=0.5", camera="az32 el22 perspective", time_s=t0, **extras)

    # 02 velocity at late time
    t_mid = _set_time(scene, tk, 0.06 if args.tag != "hpht" else 0.06, last=False)
    Hide(p_slice, view)
    Show(vel_slice, view)
    srep.SetScalarBarVisibility(view, True)
    Render()
    p02 = out / "02_phaseforge_3d_velocity.png"
    if args.tag == "hpht":
        p02 = out / "02_phaseforge_3d_hpht_velocity.png"
    _shot(simple, view, p02, res)
    _save_meta(p02, field="UMag slice + interface", time_s=t_mid, **extras)

    # 03 pressure
    Hide(vel_slice, view)
    srep.SetScalarBarVisibility(view, False)
    Show(p_slice, view)
    prep.SetScalarBarVisibility(view, True)
    _compact_bar(lut_p, view, "p (Pa)")
    Render()
    p03 = out / "03_phaseforge_3d_pressure.png"
    if args.tag == "hpht":
        p03 = out / "03_phaseforge_3d_hpht_pressure.png"
    _shot(simple, view, p03, res)
    _save_meta(p03, field="p slice + interface", time_s=t_mid, **extras)

    # 04 streamlines or velocity fallback
    Hide(p_slice, view)
    prep.SetScalarBarVisibility(view, False)
    p04 = out / "04_phaseforge_3d_streamlines.png"
    if args.tag == "hpht":
        p04 = out / "04_phaseforge_3d_hpht_streamlines.png"
    if stream_ok and streams is not None:
        Show(streams, view)
        ColorBy(strep, ("POINTS", "U"))
        strep.SetScalarBarVisibility(view, True)
        _compact_bar(GetColorTransferFunction("U"), view, "U (m/s)")
        field4 = "streamlines + interface"
    else:
        Show(vel_slice, view)
        srep.SetScalarBarVisibility(view, True)
        field4 = "streamlines omitted; velocity slice shown"
    Render()
    _shot(simple, view, p04, res)
    _save_meta(p04, field=field4, time_s=t_mid, **extras)

    # 05 final
    t_end = _set_time(scene, tk, None, last=True)
    if streams is not None:
        Hide(streams, view)
    Hide(vel_slice, view)
    Hide(p_slice, view)
    srep.SetScalarBarVisibility(view, False)
    Show(contour, view)
    Show(walls, view)
    Show(outline, view)
    Render()
    p05 = out / "05_phaseforge_3d_final.png"
    if args.tag == "hpht":
        p05 = out / "05_phaseforge_3d_hpht_final.png"
    _shot(simple, view, p05, res)
    _save_meta(p05, field="alpha.water=0.5 final", time_s=t_end, **extras)

    # submission: droplets + velocity slice, no extra chrome titles
    Show(vel_slice, view)
    srep.SetScalarBarVisibility(view, True)
    _compact_bar(lut_u, view, "U (m/s)")
    view.OrientationAxesVisibility = 1
    Render()
    psub = out / "phaseforge_paraview_submission.png"
    if args.tag == "hpht":
        psub = out / "phaseforge_paraview_hpht_submission.png"
    _shot(simple, view, psub, res)
    _save_meta(psub, field="interface + U slice", time_s=t_end, **extras)

    if args.tag != "hpht" and args.animation:
        Hide(vel_slice, view)
        srep.SetScalarBarVisibility(view, False)
        Show(contour, view)
        Show(walls, view)
        Show(outline, view)
        _oblique_camera(view, bounds)
        frames_dir = out / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        mp4 = out / "phaseforge_3d_transport_paraview.mp4"
        try:
            scene.GoToFirst()
            SaveAnimation(
                str(mp4),
                view,
                ImageResolution=res,
                FrameRate=4,
                CompressionLevel="1",
            )
            _log(f"wrote {mp4}")
        except Exception as exc:
            _log(f"SaveAnimation mp4 failed ({exc}); writing PNG frames")
            times = []
            try:
                times = list(tk.TimestepValues)
            except Exception:
                times = [0.0, 0.02, 0.04, 0.06, 0.08]
            for i, t in enumerate(times):
                _set_time(scene, tk, float(t), last=False)
                Render()
                fp = frames_dir / f"frame_{i:03d}.png"
                _shot(simple, view, fp, res)
        # Always also dump PNG frames for stitching fallback
        times = []
        try:
            times = list(tk.TimestepValues)
        except Exception:
            times = []
        for i, t in enumerate(times):
            _set_time(scene, tk, float(t), last=False)
            Render()
            fp = frames_dir / f"frame_{i:03d}.png"
            if not fp.exists():
                _shot(simple, view, fp, res)

    _log("pipeline_ok")
    _log(f"source_kind={kind}")
    _log(f"t_end={t_end}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--foam", required=True)
    p.add_argument("--vtk-series", default="")
    p.add_argument("--out", required=True)
    p.add_argument("--state", required=True)
    p.add_argument("--tag", default="moderate")
    p.add_argument("--width", type=int, default=2560)
    p.add_argument("--height", type=int, default=1440)
    p.add_argument("--animation", action="store_true")
    args = p.parse_args()
    try:
        return build(args)
    except Exception as exc:
        _log(f"FATAL: {exc}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
