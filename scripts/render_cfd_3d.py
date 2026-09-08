"""Professional 3D renders from solved OpenFOAM/VTK fields. Optional extra: cfd3d."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from phaseforge.requirements import repo_root

WIDTH = 2560
HEIGHT = 1440


def _try_import_pv():
    try:
        import pyvista as pv

        pv.OFF_SCREEN = True
        pv.global_theme.background = "white"
        pv.global_theme.font.color = "black"
        return pv
    except ImportError:
        return None


def _case_dir(tag: str) -> Path:
    root = repo_root()
    mapping = {
        "moderate": root / "simulations/cfd/phaseforge_channel_3d",
        "hpht": root / "simulations/cfd/phaseforge_channel_3d_hpht",
        "coarse": root / "simulations/cfd/phaseforge_channel_3d_coarse",
    }
    return mapping[tag]


def _vtk_files(case: Path) -> list[Path]:
    vtk = case / "VTK"
    if not vtk.exists():
        return []
    files = sorted(vtk.glob("*.vtm"))
    return [p for p in files if "boundary" not in p.name]


def _read_dataset(pv, path: Path):
    data = pv.read(str(path))
    if hasattr(data, "n_blocks"):
        # MultiBlock: prefer internal mesh
        for i in range(data.n_blocks):
            name = data.get_block_name(i) if hasattr(data, "get_block_name") else ""
            block = data[i]
            if block is None:
                continue
            if "internal" in str(name).lower() or "internal" in str(block):
                return block
        return data.combine()
    return data


def _interface(pv, mesh, value: float = 0.5):
    names = mesh.array_names
    key = "alpha.water" if "alpha.water" in names else None
    if key is None:
        for n in names:
            if "alpha" in n.lower():
                key = n
                break
    if key is None:
        return None
    try:
        mesh.set_active_scalars(key)
    except Exception:
        pass
    try:
        return mesh.contour([value], scalars=key)
    except Exception:
        return None


def _velocity_mag(mesh):
    if "U" in mesh.array_names:
        U = np.asarray(mesh["U"])
        if U.ndim == 2 and U.shape[1] == 3:
            mag = np.linalg.norm(U, axis=1)
            mag = np.clip(mag, 0.0, 0.5)
            mesh["Umag"] = mag
            return mag
    return None


def _camera(plotter, bounds) -> None:
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    cx = 0.5 * (xmin + xmax)
    cy = 0.5 * (ymin + ymax)
    cz = 0.5 * (zmin + zmax)
    dx = xmax - xmin
    plotter.camera_position = [
        (cx - 0.55 * dx, cy - 0.9 * dx, cz + 0.55 * dx),
        (cx, cy, cz),
        (0.1, 0.15, 0.98),
    ]
    plotter.camera.azimuth = 32
    plotter.camera.elevation = 22


def _save_meta(png: Path, **kwargs) -> None:
    payload = {
        "generated_utc": datetime.now(UTC).isoformat(),
        "openfoam": "v2212",
        "image": "jcmaes/geochemfoam-5.2",
        **kwargs,
        "file": str(png.name),
    }
    png.with_suffix(".json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _plotter(pv):
    pl = pv.Plotter(off_screen=True, window_size=(WIDTH, HEIGHT))
    pl.set_background("white")
    return pl


def render_case(tag: str = "moderate") -> list[Path]:
    pv = _try_import_pv()
    root = repo_root()
    out = root / "figures" / "cfd3d"
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    if pv is None:
        (out / "RENDER_SKIPPED.txt").write_text(
            "pyvista not installed. uv sync --extra cfd3d\n", encoding="utf-8"
        )
        return written
    case = _case_dir(tag)
    vtks = _vtk_files(case)
    if not vtks:
        (out / "NO_VTK.txt").write_text(f"No VTK in {case}\n", encoding="utf-8")
        return written

    def _one(path: Path):
        mesh = _read_dataset(pv, path)
        iso = _interface(pv, mesh)
        _velocity_mag(mesh)
        return mesh, iso

    first = vtks[0]
    last = vtks[-1]
    mesh0, iso0 = _one(first)
    mesh1, iso1 = _one(last)
    bounds = mesh0.bounds

    # 01 domain + initial droplets
    pl = _plotter(pv)
    outline = mesh0.outline()
    pl.add_mesh(outline, color="dimgray", line_width=1)
    if iso0 is not None and iso0.n_points:
        pl.add_mesh(iso0, color="#c45c26", opacity=0.95, smooth_shading=True)
    _camera(pl, bounds)
    pl.add_axes(line_width=2, labels_off=False)
    p = out / "01_3d_domain_initial.png"
    pl.show(screenshot=str(p))
    pl.close()
    _save_meta(p, case=tag, timestep=first.name, field="alpha.water isosurface 0.5")
    written.append(p)

    # 02 later transport
    pl = _plotter(pv)
    pl.add_mesh(mesh1.outline(), color="dimgray", line_width=1)
    if iso1 is not None and iso1.n_points:
        pl.add_mesh(iso1, color="#c45c26", opacity=0.95, smooth_shading=True)
    _camera(pl, bounds)
    pl.add_axes()
    p = out / "02_3d_droplet_transport.png"
    pl.show(screenshot=str(p))
    pl.close()
    _save_meta(p, case=tag, timestep=last.name, field="alpha.water isosurface 0.5")
    written.append(p)

    # 03 phase fraction surfaces + scalar bar
    pl = _plotter(pv)
    pl.add_mesh(mesh1.outline(), color="gainsboro", line_width=1, opacity=0.4)
    if iso1 is not None and iso1.n_points:
        pl.add_mesh(
            iso1,
            color="#1f4e79",
            opacity=0.92,
            smooth_shading=True,
            show_scalar_bar=False,
        )
        pl.add_text("alpha.water = 0.5 interface", font_size=10, color="black")
    _camera(pl, bounds)
    p = out / "03_3d_phase_fraction.png"
    pl.show(screenshot=str(p))
    pl.close()
    _save_meta(p, case=tag, timestep=last.name, field="alpha.water=0.5")
    written.append(p)

    # 04 velocity slice + droplets
    pl = _plotter(pv)
    try:
        sl = mesh1.slice(normal="z", origin=mesh1.center)
        if "Umag" in sl.array_names:
            pl.add_mesh(sl, scalars="Umag", cmap="viridis", show_scalar_bar=True, scalar_bar_args={"title": "|U| (m/s)"})
        else:
            pl.add_mesh(sl, color="lightgray")
    except Exception:
        pl.add_mesh(mesh1.outline(), color="gray")
    if iso1 is not None and iso1.n_points:
        pl.add_mesh(iso1, color="#c45c26", opacity=0.9, smooth_shading=True)
    _camera(pl, bounds)
    p = out / "04_3d_velocity_slice_and_droplets.png"
    pl.show(screenshot=str(p))
    pl.close()
    _save_meta(p, case=tag, timestep=last.name, field="U slice + interface")
    written.append(p)

    # 05 streamlines if topology is simple
    pl = _plotter(pv)
    streamed = False
    try:
        if "U" in mesh1.array_names:
            xmin, xmax, ymin, ymax, zmin, zmax = bounds
            seeds = pv.Plane(
                center=(xmin + 0.002, 0.5 * (ymin + ymax), 0.5 * (zmin + zmax)),
                direction=(1, 0, 0),
                i_size=0.8 * (ymax - ymin),
                j_size=0.8 * (zmax - zmin),
                i_resolution=6,
                j_resolution=4,
            )
            slines = mesh1.streamlines_from_source(seeds, vectors="U", max_time=0.4, integration_direction="forward")
            if slines.n_points > 10:
                _velocity_mag(slines) if "U" in slines.array_names else None
                scalars = "Umag" if "Umag" in slines.array_names else None
                pl.add_mesh(slines, scalars=scalars, cmap="plasma", line_width=1.5, show_scalar_bar=True)
                streamed = True
    except Exception:
        streamed = False
    if iso1 is not None and iso1.n_points:
        pl.add_mesh(iso1, color="#c45c26", opacity=0.88, smooth_shading=True)
    pl.add_mesh(mesh1.outline(), color="gainsboro", line_width=1)
    _camera(pl, bounds)
    p = out / "05_3d_velocity_streamlines.png"
    pl.show(screenshot=str(p))
    pl.close()
    _save_meta(p, case=tag, timestep=last.name, field="streamlines" if streamed else "streamlines unavailable")
    written.append(p)

    # 06 pressure
    pl = _plotter(pv)
    pfield = "p_rgh" if "p_rgh" in mesh1.array_names else ("p" if "p" in mesh1.array_names else None)
    try:
        sl = mesh1.slice(normal="y", origin=mesh1.center)
        if pfield:
            pl.add_mesh(sl, scalars=pfield, cmap="coolwarm", show_scalar_bar=True, scalar_bar_args={"title": "p (Pa)"})
        else:
            pl.add_mesh(sl, color="lightgray")
    except Exception:
        pl.add_mesh(mesh1.outline(), color="gray")
    if iso1 is not None and iso1.n_points:
        pl.add_mesh(iso1, color="#c45c26", opacity=0.9, smooth_shading=True)
    _camera(pl, bounds)
    p = out / "06_3d_pressure_field.png"
    pl.show(screenshot=str(p))
    pl.close()
    _save_meta(p, case=tag, timestep=last.name, field=pfield or "none")
    written.append(p)

    # 07 close-up
    pl = _plotter(pv)
    if iso1 is not None and iso1.n_points:
        pl.add_mesh(iso1, color="#c45c26", opacity=1.0, smooth_shading=True, show_edges=False)
        b = iso1.bounds
        pl.camera_position = "iso"
        pl.camera.zoom(1.6)
        pl.camera.azimuth = 35
        pl.camera.elevation = 18
        pl.reset_camera(bounds=b)
    p = out / "07_3d_droplet_closeup.png"
    pl.show(screenshot=str(p))
    pl.close()
    _save_meta(p, case=tag, timestep=last.name, field="interface close-up")
    written.append(p)

    # 08 final four droplets
    pl = _plotter(pv)
    pl.add_mesh(mesh1.outline(), color="dimgray", line_width=1, opacity=0.5)
    if iso1 is not None and iso1.n_points:
        pl.add_mesh(iso1, color="#b35c1e", opacity=0.95, smooth_shading=True)
    _camera(pl, bounds)
    pl.add_axes()
    p = out / "08_3d_four_droplets_final.png"
    pl.show(screenshot=str(p))
    pl.close()
    _save_meta(p, case=tag, timestep=last.name, field="final interfaces")
    written.append(p)

    # 10 mesh detail
    pl = _plotter(pv)
    try:
        cropped = mesh1.clip_box(mesh1.center + np.array([-0.002, -0.001, -0.001, 0.002, 0.001, 0.001]), invert=False)
        if cropped.n_cells == 0:
            cropped = mesh1
        pl.add_mesh(cropped, style="wireframe", color="#555555", opacity=0.35, line_width=0.4)
        if iso1 is not None:
            pl.add_mesh(iso1, color="#c45c26", opacity=0.85, smooth_shading=True)
    except Exception:
        pl.add_mesh(mesh1, style="wireframe", color="gray", opacity=0.2)
    p = out / "10_3d_mesh_detail.png"
    pl.show(screenshot=str(p))
    pl.close()
    _save_meta(p, case=tag, timestep=last.name, field="mesh wireframe")
    written.append(p)

    # time sequence
    picks = vtks
    if len(vtks) > 4:
        idx = np.linspace(0, len(vtks) - 1, 4).astype(int)
        picks = [vtks[i] for i in idx]
    for i, vp in enumerate(picks):
        mesh, iso = _one(vp)
        pl = _plotter(pv)
        pl.add_mesh(mesh.outline(), color="dimgray", line_width=1)
        if iso is not None and iso.n_points:
            pl.add_mesh(iso, color="#c45c26", opacity=0.95, smooth_shading=True)
        _camera(pl, bounds)
        p = out / f"3d_time_{i:03d}.png"
        pl.show(screenshot=str(p))
        pl.close()
        _save_meta(p, case=tag, timestep=vp.name, field="time sequence")
        written.append(p)

    # animation gif from time sequence
    try:
        import imageio.v2 as imageio

        frames = [imageio.imread(out / f"3d_time_{i:03d}.png") for i in range(len(picks)) if (out / f"3d_time_{i:03d}.png").exists()]
        if frames:
            imageio.mimsave(out / "phaseforge_3d_transport.gif", frames, duration=0.7)
            written.append(out / "phaseforge_3d_transport.gif")
            try:
                imageio.mimsave(out / "phaseforge_3d_transport.mp4", frames, fps=2)
                written.append(out / "phaseforge_3d_transport.mp4")
            except Exception:
                pass
    except Exception:
        pass

    # orbit of final state
    if iso1 is not None and iso1.n_points:
        try:
            import imageio.v2 as imageio

            orbit = []
            for ang in range(0, 360, 20):
                pl = _plotter(pv)
                pl.add_mesh(mesh1.outline(), color="gainsboro")
                pl.add_mesh(iso1, color="#c45c26", opacity=0.95, smooth_shading=True)
                _camera(pl, bounds)
                pl.camera.azimuth = 32 + ang
                tmp = out / f"_orbit_{ang:03d}.png"
                pl.show(screenshot=str(tmp))
                pl.close()
                orbit.append(imageio.imread(tmp))
                tmp.unlink(missing_ok=True)
            if orbit:
                imageio.mimsave(out / "phaseforge_3d_final_orbit.gif", orbit, duration=0.12)
                written.append(out / "phaseforge_3d_final_orbit.gif")
        except Exception:
            pass
    return written


def render_hpht_pair() -> Path | None:
    pv = _try_import_pv()
    if pv is None:
        return None
    root = repo_root()
    out = root / "figures" / "cfd3d"
    left = _vtk_files(_case_dir("moderate"))
    right = _vtk_files(_case_dir("hpht"))
    if not left or not right:
        return None
    m0, i0 = _read_dataset(pv, left[-1]), None
    m1 = _read_dataset(pv, right[-1])
    i0 = _interface(pv, m0)
    i1 = _interface(pv, m1)
    pl = pv.Plotter(off_screen=True, window_size=(WIDTH, HEIGHT), shape=(1, 2))
    pl.set_background("white")
    pl.subplot(0, 0)
    pl.add_mesh(m0.outline(), color="gray")
    if i0 is not None and i0.n_points:
        pl.add_mesh(i0, color="#c45c26", smooth_shading=True)
    pl.add_text("moderate-T analogue", font_size=10)
    _camera(pl, m0.bounds)
    pl.subplot(0, 1)
    pl.add_mesh(m1.outline(), color="gray")
    if i1 is not None and i1.n_points:
        pl.add_mesh(i1, color="#1f4e79", smooth_shading=True)
    pl.add_text("150 C property analogue", font_size=10)
    _camera(pl, m1.bounds)
    p = out / "09_3d_moderate_vs_hpht.png"
    pl.show(screenshot=str(p))
    pl.close()
    _save_meta(p, case="paired", field="interface")
    return p


def software_evidence_from_log() -> Path | None:
    import matplotlib.pyplot as plt

    root = repo_root()
    log = root / "results/raw/cfd/cfd3d_moderate_interFoam.log"
    if not log.exists():
        log = root / "results/raw/cfd/cfd3d_coarse_interFoam.log"
    if not log.exists():
        return None
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    tail = lines[-40:] if len(lines) > 40 else lines
    fig, ax = plt.subplots(figsize=(11, 6.2))
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    text = "OpenFOAM v2212 / GeoChemFoam image jcmaes/geochemfoam-5.2\n" + "\n".join(tail)
    ax.text(0.02, 0.98, text, va="top", ha="left", family="monospace", fontsize=7)
    dest = root / "figures/software_evidence"
    dest.mkdir(parents=True, exist_ok=True)
    p = dest / "openfoam_solver_end.png"
    fig.savefig(p, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return p


def chemgate_concept_schematic() -> Path:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

    root = repo_root()
    out = root / "figures" / "cfd3d"
    out.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(8.4, 6.2))
    ax = fig.add_subplot(111, projection="3d")
    u = np.linspace(0, 2 * np.pi, 40)
    v = np.linspace(0, np.pi, 20)
    r = 1.0
    x = r * np.outer(np.cos(u), np.sin(v))
    y = r * np.outer(np.sin(u), np.sin(v))
    z = r * np.outer(np.ones_like(u), np.cos(v))
    ax.plot_surface(x, y, z, color="#c45c26", alpha=0.55, linewidth=0)
    ax.plot_surface(1.15 * x, 1.15 * y, 1.15 * z, color="#9ecae1", alpha=0.12, linewidth=0)
    ax.quiver(2.2, 0, 0, -0.7, 0, 0, color="#1f4e79", arrow_length_ratio=0.2)
    ax.text(2.3, 0, 0.2, "aqueous activator", color="#1f4e79")
    ax.text(0, 0, 1.4, "organic droplet\nlatent catalyst", ha="center")
    ax.set_title("Concept schematic, not CFD chemistry")
    ax.set_axis_off()
    p = out / "chemgate_concept_schematic.png"
    fig.savefig(p, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return p


def submission_panel(metrics: dict | None = None) -> Path:
    import matplotlib.image as mpimg
    import matplotlib.pyplot as plt

    root = repo_root()
    out = root / "figures" / "cfd3d"
    names = [
        "01_3d_domain_initial.png",
        "02_3d_droplet_transport.png",
        "04_3d_velocity_slice_and_droplets.png",
        "08_3d_four_droplets_final.png",
    ]
    fig, axes = plt.subplots(2, 3, figsize=(14.5, 8.6))
    labels = ["A", "B", "C", "D"]
    for ax, name, lab in zip(axes.ravel()[:4], names, labels, strict=True):
        fp = out / name
        ax.axis("off")
        if fp.exists():
            ax.imshow(mpimg.imread(fp))
        ax.set_title(lab, loc="left", fontsize=11)
    box = axes[1, 2]
    box.axis("off")
    metrics = metrics or {}
    txt = (
        "E  3D CFD (hydrodynamics only)\n"
        f"solver: OpenFOAM v2212 / GeoChemFoam\n"
        f"mesh: {metrics.get('n_cells', '?')} hex cells\n"
        f"initial droplets: {metrics.get('n0', 4)}\n"
        f"d0 ~ 500 μm  t = {metrics.get('time_s', '?')} s\n"
        f"final droplets: {metrics.get('n_final', '?')}\n"
        f"coalescence events: {metrics.get('coalescence', '?')}\n"
        f"Re={metrics.get('Re', '?')}  We={metrics.get('We', '?')}  Ca={metrics.get('Ca', '?')}\n"
        "Not a chemistry or 10,000 psi proof."
    )
    box.text(0.02, 0.98, txt, va="top", family="monospace", fontsize=9)
    fig.suptitle("PhaseForge 3D hydrodynamic demonstration", fontsize=13)
    fig.tight_layout()
    p = out / "phaseforge_3d_submission_panel.png"
    fig.savefig(p, dpi=220, facecolor="white")
    plt.close(fig)
    return p


def main() -> int:
    written = render_case("moderate")
    if not written:
        written = render_case("coarse")
    render_hpht_pair()
    software_evidence_from_log()
    chemgate_concept_schematic()
    from phaseforge.cfd_3d_postprocess import dimensionless_3d, write_metrics_csv

    write_metrics_csv()
    dim = dimensionless_3d(
        rho=983.0, mu=983.0 * 4.1e-7, U=0.05, L=0.003, d=5e-4, sigma=0.004, mu_d=960.0 * 5.1e-7
    )
    submission_panel({"Re": f"{dim['Re']:.0f}", "We": f"{dim['We']:.3g}", "Ca": f"{dim['Ca']:.3g}"})
    print("renders", len(written))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
