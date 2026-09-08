"""True-3D VoF post-processing for PhaseForge channel cases.

Uses volumetric alpha.water on a structured hex mesh.
Sphericity is the 3D Wadell definition from volume and interface area.
Provenance: CFD_3D_MODEL_PREDICTION.
Does not invent fields if time directories are missing.
"""

from __future__ import annotations

import csv
import json
import math
import re
from collections import deque
from pathlib import Path

import numpy as np

from phaseforge.cfd_postprocess import parse_block_mesh, parse_internal_field
from phaseforge.provenance import Provenance
from phaseforge.requirements import repo_root

PROVENANCE = Provenance.CFD_3D_MODEL_PREDICTION


def d_eq_from_volume_m(volume_m3: float) -> float:
    """Volume-equivalent spherical diameter: (6V/π)^(1/3)."""
    if volume_m3 <= 0.0 or not math.isfinite(volume_m3):
        return float("nan")
    return (6.0 * volume_m3 / math.pi) ** (1.0 / 3.0)


def sphericity_wadell(volume_m3: float, area_m2: float) -> float:
    """Wadell sphericity π^(1/3) (6V)^(2/3) / A. 1 = sphere."""
    if volume_m3 <= 0.0 or area_m2 <= 0.0:
        return float("nan")
    return (math.pi ** (1.0 / 3.0)) * ((6.0 * volume_m3) ** (2.0 / 3.0)) / area_m2


def of_cell_xyz(
    nx: int, ny: int, nz: int, xmin: float, xmax: float, ymin: float, ymax: float, zmin: float, zmax: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    dx = (xmax - xmin) / nx
    dy = (ymax - ymin) / ny
    dz = (zmax - zmin) / nz
    xs = xmin + dx * (np.arange(nx) + 0.5)
    ys = ymin + dy * (np.arange(ny) + 0.5)
    zs = zmin + dz * (np.arange(nz) + 0.5)
    xx = np.empty(nx * ny * nz)
    yy = np.empty(nx * ny * nz)
    zz = np.empty(nx * ny * nz)
    k = 0
    for kk in range(nz):
        for j in range(ny):
            for i in range(nx):
                xx[k] = xs[i]
                yy[k] = ys[j]
                zz[k] = zs[kk]
                k += 1
    return xx, yy, zz


def reshape_alpha(alpha: np.ndarray, nx: int, ny: int, nz: int) -> np.ndarray:
    """OpenFOAM hex: i fastest, then j, then k → shape (nz, ny, nx)."""
    return alpha.reshape((nz, ny, nx))


def label_oil_3d(oil: np.ndarray) -> np.ndarray:
    """6-connected components on a binary (nz, ny, nx) mask."""
    nz, ny, nx = oil.shape
    labels = np.zeros(oil.shape, dtype=np.int32)
    lab = 0
    nbr = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                if not oil[k, j, i] or labels[k, j, i] != 0:
                    continue
                lab += 1
                q: deque[tuple[int, int, int]] = deque([(k, j, i)])
                labels[k, j, i] = lab
                while q:
                    ck, cj, ci = q.popleft()
                    for dk, dj, di in nbr:
                        nk, nj, ni = ck + dk, cj + dj, ci + di
                        if 0 <= nk < nz and 0 <= nj < ny and 0 <= ni < nx:
                            if oil[nk, nj, ni] and labels[nk, nj, ni] == 0:
                                labels[nk, nj, ni] = lab
                                q.append((nk, nj, ni))
    return labels


def interface_area_gradient(alpha_vol: np.ndarray, dx: float, dy: float, dz: float) -> float:
    """VoF interface area ≈ ∫ |∇α| dV over a padded field (water=1 outside)."""
    pad = np.pad(alpha_vol, 1, mode="constant", constant_values=1.0)
    gx, gy, gz = np.gradient(pad, dz, dy, dx)
    mag = np.sqrt(gx * gx + gy * gy + gz * gz)
    core = mag[1:-1, 1:-1, 1:-1]
    return float(np.sum(core) * dx * dy * dz)


def droplet_metrics_3d(
    alpha: np.ndarray,
    nx: int,
    ny: int,
    nz: int,
    bounds: tuple[tuple[float, float, float], tuple[float, float, float]],
    *,
    thresh: float = 0.5,
    min_volume_m3: float = 1e-15,
) -> list[dict]:
    mn, mx = bounds
    xmin, ymin, zmin = mn
    xmax, ymax, zmax = mx
    dx = (xmax - xmin) / nx
    dy = (ymax - ymin) / ny
    dz = (zmax - zmin) / nz
    vcell = dx * dy * dz
    a3 = reshape_alpha(alpha, nx, ny, nz)
    oil_frac = np.clip(1.0 - a3, 0.0, 1.0)
    oil = a3 < thresh
    labels = label_oil_3d(oil)
    xx, yy, zz = of_cell_xyz(nx, ny, nz, xmin, xmax, ymin, ymax, zmin, zmax)
    out: list[dict] = []
    nlab = int(labels.max())
    for lab in range(1, nlab + 1):
        mask3 = labels == lab
        vol = float(oil_frac[mask3].sum() * vcell)
        if vol < min_volume_m3:
            continue
        mask = mask3.ravel(order="C")
        # reshape_alpha uses C order (k,j,i) matching ravel of OF i-fastest? 
        # OF: index = i + j*nx + k*nx*ny. numpy reshape (nz,ny,nx) C-order ravel is
        # i fastest, then j, then k. Yes matches OF.
        cx = float(np.average(xx[mask], weights=oil_frac.ravel()[mask]))
        cy = float(np.average(yy[mask], weights=oil_frac.ravel()[mask]))
        cz = float(np.average(zz[mask], weights=oil_frac.ravel()[mask]))
        isolated = np.ones_like(a3)
        isolated[mask3] = a3[mask3]
        area = interface_area_gradient(isolated, dx, dy, dz)
        d_eq = d_eq_from_volume_m(vol)
        sph = sphericity_wadell(vol, area)
        pts = np.column_stack((xx[mask], yy[mask], zz[mask]))
        if pts.shape[0] >= 4:
            cov = np.cov(pts, rowvar=False)
            eig = np.sort(np.clip(np.linalg.eigvalsh(cov), 1e-30, None))
            deformation = float(1.0 - math.sqrt(eig[0] / eig[2]))
        else:
            deformation = float("nan")
        out.append(
            {
                "id": lab,
                "volume_m3": vol,
                "d_eq_m": d_eq,
                "d_eq_um": d_eq * 1e6,
                "centroid_x_m": cx,
                "centroid_y_m": cy,
                "centroid_z_m": cz,
                "surface_area_m2": area,
                "sphericity": sph,
                "deformation": deformation,
            }
        )
    out.sort(key=lambda r: r["centroid_x_m"])
    for i, r in enumerate(out, start=1):
        r["id"] = i
    return out


def min_separation_3d(drops: list[dict]) -> float:
    if len(drops) < 2:
        return float("nan")
    m = float("inf")
    for i, a in enumerate(drops):
        for b in drops[i + 1 :]:
            d = math.sqrt(
                (a["centroid_x_m"] - b["centroid_x_m"]) ** 2
                + (a["centroid_y_m"] - b["centroid_y_m"]) ** 2
                + (a["centroid_z_m"] - b["centroid_z_m"]) ** 2
            )
            m = min(m, d)
    return m


def case_time_dirs(case: Path) -> list[Path]:
    out = []
    if not case.exists():
        return out
    for p in case.iterdir():
        if p.is_dir() and re.fullmatch(r"[0-9]+(\.[0-9]+)?", p.name) and p.name != "0":
            if (p / "alpha.water").exists():
                out.append(p)
    return sorted(out, key=lambda p: float(p.name))


def extract_case_3d(case: Path, tag: str) -> list[dict]:
    mesh = case / "system" / "blockMeshDict"
    if not mesh.exists():
        return []
    nx, ny, nz, _conv, mn, mx = parse_block_mesh(mesh)
    if nz < 2:
        return []
    rows: list[dict] = []
    times = case_time_dirs(case)
    # include t=0 if alpha after setFields exists
    t0 = case / "0"
    if (t0 / "alpha.water").exists():
        times = [t0, *times]
    prev_n: int | None = None
    coalescence_events = 0
    ncell = nx * ny * nz
    xmin, ymin, zmin = mn
    xmax, ymax, zmax = mx
    for td in times:
        try:
            alpha = parse_internal_field(td / "alpha.water")
        except ValueError:
            continue
        if alpha.size != ncell:
            continue
        drops = droplet_metrics_3d(alpha, nx, ny, nz, (mn, mx))
        n = len(drops)
        if prev_n is not None and n < prev_n:
            coalescence_events += prev_n - n
        prev_n = n
        sep = min_separation_3d(drops)
        dp = float("nan")
        pr = td / "p_rgh"
        if pr.exists():
            try:
                p = parse_internal_field(pr)
                if p.size == ncell:
                    p3 = reshape_alpha(p, nx, ny, nz)
                    dp = float(p3[:, :, 0].mean() - p3[:, :, -1].mean())
            except ValueError:
                dp = float("nan")
        t = float(td.name)
        umag = float("nan")
        uf = td / "U"
        if uf.exists():
            try:
                U = parse_internal_field(uf)
                if U.ndim == 2 and U.shape[0] == ncell:
                    umag = float(np.mean(np.linalg.norm(U, axis=1)))
            except ValueError:
                umag = float("nan")
        base = {
            "case": tag,
            "time_s": t,
            "n_droplets": n,
            "n_cells": ncell,
            "nx": nx,
            "ny": ny,
            "nz": nz,
            "min_separation_m": sep if np.isfinite(sep) else None,
            "coalescence_events_cumulative": coalescence_events,
            "mean_U_m_s": umag,
            "pressure_drop_Pa": dp,
            "provenance": PROVENANCE.value,
        }
        if not drops:
            rows.append({**base, "droplet_id": None, "d_eq_um": None, "sphericity": None})
            continue
        for d in drops:
            rows.append(
                {
                    **base,
                    "droplet_id": d["id"],
                    "volume_m3": d["volume_m3"],
                    "d_eq_um": d["d_eq_um"],
                    "centroid_x_m": d["centroid_x_m"],
                    "centroid_y_m": d["centroid_y_m"],
                    "centroid_z_m": d["centroid_z_m"],
                    "surface_area_m2": d["surface_area_m2"],
                    "sphericity": d["sphericity"],
                    "deformation": d["deformation"],
                }
            )
    return rows


def parse_checkmesh(text: str) -> dict:
    def _grab(pat: str, default: float | None = None) -> float | None:
        m = re.search(pat, text)
        if not m:
            return default
        return float(m.group(1).rstrip("."))

    ok = bool(re.search(r"Mesh OK\.", text))
    failed = bool(re.search(r"Failed", text)) and not ok
    ncell = _grab(r"cells:\s+(\d+)")
    return {
        "mesh_ok": ok and not failed,
        "n_cells": int(ncell) if ncell is not None else None,
        "max_aspect_ratio": _grab(r"Max aspect ratio = ([0-9.eE+-]+)"),
        "max_nonorthogonality": _grab(r"Mesh non-orthogonality Max:\s+([0-9.eE+-]+)"),
        "max_skewness": _grab(r"Max skewness = ([0-9.eE+-]+)"),
        "min_volume": _grab(r"Min volume = ([0-9.eE+-]+)"),
        "max_volume": _grab(r"Max volume = ([0-9.eE+-]+)"),
        "failed": failed,
    }


def dimensionless_3d(*, rho: float, mu: float, U: float, L: float, d: float, sigma: float, mu_d: float) -> dict:
    Re = rho * U * L / mu
    We = rho * U**2 * d / max(sigma, 1e-12)
    Ca = mu * U / max(sigma, 1e-12)
    Oh = mu / math.sqrt(max(rho * sigma * d, 1e-30))
    return {
        "Re": Re,
        "We": We,
        "Ca": Ca,
        "Oh": Oh,
        "viscosity_ratio": mu_d / mu,
        "provenance": PROVENANCE.value,
        "notes": "Incompressible 3D hydrodynamics only; 10000 psi is not a CFD chemical-rate variable.",
    }


def write_metrics_csv(path: Path | None = None) -> Path:
    root = repo_root()
    path = path or (root / "results" / "tables" / "cfd_3d_metrics.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for tag, rel in (
        ("phaseforge_channel_3d", "simulations/cfd/phaseforge_channel_3d"),
        ("phaseforge_channel_3d_hpht", "simulations/cfd/phaseforge_channel_3d_hpht"),
        ("phaseforge_channel_3d_coarse", "simulations/cfd/phaseforge_channel_3d_coarse"),
    ):
        case = root / rel
        if case.exists():
            rows.extend(extract_case_3d(case, tag))
    if not rows:
        path.write_text(
            "case,time_s,n_droplets,notes,provenance\n"
            f"phaseforge_channel_3d,,,no solved 3D time directories; fields not fabricated,{PROVENANCE.value}\n",
            encoding="utf-8",
        )
        return path
    keys = [
        "case",
        "time_s",
        "n_droplets",
        "droplet_id",
        "d_eq_um",
        "sphericity",
        "deformation",
        "volume_m3",
        "centroid_x_m",
        "centroid_y_m",
        "centroid_z_m",
        "surface_area_m2",
        "min_separation_m",
        "coalescence_events_cumulative",
        "mean_U_m_s",
        "pressure_drop_Pa",
        "n_cells",
        "nx",
        "ny",
        "nz",
        "provenance",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return path


def mesh_sensitivity_summary(path: Path | None = None) -> dict:
    root = repo_root()
    nom = extract_case_3d(root / "simulations/cfd/phaseforge_channel_3d", "nominal")
    crs = extract_case_3d(root / "simulations/cfd/phaseforge_channel_3d_coarse", "coarse")
    def _last(rows: list[dict]) -> dict | None:
        if not rows:
            return None
        tmax = max(r["time_s"] for r in rows)
        sub = [r for r in rows if r["time_s"] == tmax and r.get("d_eq_um")]
        if not sub:
            return None
        return {
            "time_s": tmax,
            "n_droplets": sub[0]["n_droplets"],
            "d_eq_um_mean": float(np.mean([r["d_eq_um"] for r in sub])),
            "sphericity_mean": float(np.nanmean([r["sphericity"] for r in sub])),
            "pressure_drop_Pa": sub[0]["pressure_drop_Pa"],
            "centroid_x_mean_m": float(np.mean([r["centroid_x_m"] for r in sub])),
        }

    out = {
        "label": "mesh sensitivity",
        "not_mesh_independence": True,
        "nominal": _last(nom),
        "coarse": _last(crs),
        "provenance": PROVENANCE.value,
    }
    dest = path or (root / "results" / "tables" / "cfd_3d_mesh_sensitivity.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


def main() -> int:
    p = write_metrics_csv()
    print(f"wrote {p}")
    print(mesh_sensitivity_summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
