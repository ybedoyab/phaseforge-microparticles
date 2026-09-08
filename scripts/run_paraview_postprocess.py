"""Run ParaView post-processing on the already-solved true-3D PhaseForge case.

Does not rerun interFoam. Requires Kitware pvpython.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from phaseforge.paraview_locate import locate_paraview
from phaseforge.requirements import repo_root


def _run_pvpython(pvpython: Path, script: Path, args: list[str]) -> int:
    cmd = [str(pvpython), str(script), *args]
    print(">>", " ".join(cmd[:6]), "...")
    return subprocess.call(cmd)


def _stitch_mp4(out: Path) -> Path | None:
    frames = sorted((out / "frames").glob("frame_*.png"))
    target = out / "phaseforge_3d_transport_paraview.mp4"
    if len(frames) < 2:
        return target if target.exists() and target.stat().st_size > 200_000 else None
    try:
        import imageio.v2 as imageio
    except ImportError:
        print("imageio not available; leaving PNG frames")
        return None
    imgs = [imageio.imread(f) for f in frames]
    imageio.mimsave(target, imgs, fps=2)
    print("stitched", target, target.stat().st_size)
    return target


def improve_openfoam_log_figure() -> Path | None:
    import matplotlib.pyplot as plt

    root = repo_root()
    log = root / "results/raw/cfd/cfd3d_moderate_interFoam.log"
    if not log.exists():
        return None
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    header = [
        ln
        for ln in lines[:25]
        if any(k in ln for k in ("OpenFOAM", "Version", "Exec", "Case", "Build"))
    ]
    end_idx = None
    for i, ln in enumerate(lines):
        if ln.strip() == "End":
            end_idx = i
    tail = lines[end_idx - 18 : end_idx + 2] if end_idx is not None else lines[-22:]
    body = "\n".join(header + ["", *tail])
    fig, ax = plt.subplots(figsize=(11.2, 6.4))
    ax.axis("off")
    caption = (
        "OpenFOAM v2212  |  interFoam  |  true 3D case phaseforge_channel_3d\n"
        "GeoChemFoam image jcmaes/geochemfoam-5.2  |  solver reached End\n\n"
    )
    ax.text(0.02, 0.98, caption + body, va="top", ha="left", family="monospace", fontsize=7.2)
    dest = root / "figures/software_evidence"
    dest.mkdir(parents=True, exist_ok=True)
    p = dest / "openfoam_solver_end.png"
    fig.savefig(p, dpi=200, bbox_inches="tight", facecolor="#f7f7f4")
    plt.close(fig)
    return p


def _printwindow_capture(hwnd: int, dest: Path) -> bool:
    import ctypes
    from ctypes import wintypes

    from PIL import Image

    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    user32.SetProcessDPIAware()
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    if width < 200 or height < 200:
        return False
    hwnd_dc = user32.GetWindowDC(hwnd)
    mem_dc = gdi32.CreateCompatibleDC(hwnd_dc)
    bmp = gdi32.CreateCompatibleBitmap(hwnd_dc, width, height)
    gdi32.SelectObject(mem_dc, bmp)
    ok = user32.PrintWindow(hwnd, mem_dc, 2)  # PW_RENDERFULLCONTENT

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", wintypes.DWORD),
            ("biWidth", ctypes.c_long),
            ("biHeight", ctypes.c_long),
            ("biPlanes", wintypes.WORD),
            ("biBitCount", wintypes.WORD),
            ("biCompression", wintypes.DWORD),
            ("biSizeImage", wintypes.DWORD),
            ("biXPelsPerMeter", ctypes.c_long),
            ("biYPelsPerMeter", ctypes.c_long),
            ("biClrUsed", wintypes.DWORD),
            ("biClrImportant", wintypes.DWORD),
        ]

    class BITMAPINFO(ctypes.Structure):
        _fields_ = [("bmiHeader", BITMAPINFOHEADER)]

    info = BITMAPINFO()
    info.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    info.bmiHeader.biWidth = width
    info.bmiHeader.biHeight = -height
    info.bmiHeader.biPlanes = 1
    info.bmiHeader.biBitCount = 32
    buf = (ctypes.c_char * (width * height * 4))()
    gdi32.GetDIBits(mem_dc, bmp, 0, height, buf, ctypes.byref(info), 0)
    img = Image.frombuffer("RGB", (width, height), buf, "raw", "BGRX", 0, 1)
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem_dc)
    user32.ReleaseDC(hwnd, hwnd_dc)
    return bool(ok) and dest.is_file() and dest.stat().st_size > 20000


def capture_paraview_gui(paraview: Path, state: Path, dest: Path) -> bool:
    """Launch the real ParaView GUI and capture the window. Never synthesize a UI."""
    import ctypes
    from ctypes import wintypes

    dest.parent.mkdir(parents=True, exist_ok=True)
    # Two-argument --state avoids comma-splitting on Windows paths such as "Code, 3D, Audio".
    cmd = [str(paraview), "--state", str(state)]
    print(">>", cmd)
    subprocess.Popen(cmd)
    user32 = ctypes.windll.user32
    hwnd = None
    for i in range(90):
        time.sleep(1.0)
        found: list[tuple[int, str]] = []
        titles: list[str] = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        def _enum(h, _lp, found=found, titles=titles):
            if not user32.IsWindowVisible(h):
                return True
            buf = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(h, buf, 512)
            title = buf.value.strip()
            if title:
                titles.append(title)
            if title.startswith("ParaView ") or title == "Welcome to ParaView":
                found.append((h, title))
            return True

        user32.EnumWindows(_enum, 0)
        if i in (5, 15, 30, 60) and titles:
            print("visible windows sample:", titles[:12])
        mains = [x for x in found if x[1].startswith("ParaView ")]
        if mains:
            hwnd = mains[0][0]
            print("ParaView window:", mains[0][1])
            break
    if hwnd is None:
        print("ParaView GUI window not found; leaving process running for a manual screenshot")
        return False
    ok = _printwindow_capture(hwnd, dest)
    print("captured", dest, ok)
    return ok


def software_composite(gui: Path, of_log: Path, dest: Path) -> Path | None:
    if not gui.is_file() or not of_log.is_file():
        return None
    import matplotlib.image as mpimg
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(14.4, 6.6))
    for ax, path, lab in (
        (axes[0], gui, "A  ParaView GUI"),
        (axes[1], of_log, "B  OpenFOAM solver log"),
    ):
        ax.imshow(mpimg.imread(path))
        ax.set_title(lab, loc="left", fontsize=11)
        ax.axis("off")
    fig.text(
        0.03,
        0.02,
        "Software and computational workflow evidence   |   "
        "3D multiphase CFD: OpenFOAM v2212 / GeoChemFoam 5.2   |   "
        "Post-processing: ParaView   |   Nominal mesh: 491,520 cells\n"
        "Not experimental validation. Hydrodynamics only.",
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    dest.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(dest, dpi=180, facecolor="white")
    plt.close(fig)
    return dest


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--gui-only", action="store_true")
    p.add_argument("--skip-gui", action="store_true")
    args = p.parse_args(argv)
    root = repo_root()
    info = locate_paraview()
    print("ParaView locate:", info)
    (root / "results" / "raw" / "cfd").mkdir(parents=True, exist_ok=True)
    loc_txt = root / "results" / "raw" / "cfd" / "paraview_locate.txt"
    loc_txt.write_text(
        "\n".join(f"{k}={v}" for k, v in info.items()) + "\n",
        encoding="utf-8",
    )
    pvpython = info["pvpython"]
    paraview = info["paraview"]
    out = root / "figures" / "paraview"
    state = root / "visualization" / "phaseforge_3d.pvsm"
    if not args.gui_only:
        if not pvpython:
            print("pvpython not found after automatic discovery")
            return 2
        script = root / "scripts" / "paraview_phaseforge_3d.py"
        foam = root / "simulations/cfd/phaseforge_channel_3d/phaseforge_3d.foam"
        vtk = root / "simulations/cfd/phaseforge_channel_3d/VTK/phaseforge_channel_3d.vtm.series"
        rc = _run_pvpython(
            Path(pvpython),
            script,
            [
                "--foam",
                str(foam),
                "--vtk-series",
                str(vtk),
                "--out",
                str(out),
                "--state",
                str(state),
                "--tag",
                "moderate",
                "--animation",
            ],
        )
        if rc != 0:
            print("pvpython moderate failed", rc)
            return rc
        foam_h = root / "simulations/cfd/phaseforge_channel_3d_hpht/phaseforge_3d.foam"
        vtk_h = root / "simulations/cfd/phaseforge_channel_3d_hpht/VTK/phaseforge_channel_3d_hpht.vtm.series"
        state_h = root / "visualization" / "phaseforge_3d_hpht.pvsm"
        rc_h = _run_pvpython(
            Path(pvpython),
            script,
            [
                "--foam",
                str(foam_h),
                "--vtk-series",
                str(vtk_h),
                "--out",
                str(out),
                "--state",
                str(state_h),
                "--tag",
                "hpht",
            ],
        )
        print("hpht pvpython rc", rc_h)
    _stitch_mp4(out)
    of_fig = improve_openfoam_log_figure()
    gui_png = root / "figures/software_evidence/paraview_phaseforge_3d_gui.png"
    captured = False
    if paraview and not args.skip_gui:
        captured = capture_paraview_gui(Path(paraview), state, gui_png)
    if captured and of_fig is not None:
        software_composite(
            gui_png,
            of_fig,
            root / "figures/software_evidence/phaseforge_software_validation.png",
        )
    print("gui_captured", captured)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
