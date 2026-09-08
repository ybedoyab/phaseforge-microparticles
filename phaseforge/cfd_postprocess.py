"""Parse OpenFOAM 2D structured VoF output and couple droplet size to ChemGate delay.

Provenance of extracted numbers: CFD_MODEL_PREDICTION.
Does not invent fields if no time directories exist.
"""

from __future__ import annotations

import csv
import math
import re
from pathlib import Path

import numpy as np

from phaseforge.activation_diffusion import evaluate_sphere
from phaseforge.chemgate import ChemGateInputs, evaluate_chemgate
from phaseforge.provenance import Provenance
from phaseforge.requirements import repo_root

PROVENANCE = Provenance.CFD_MODEL_PREDICTION


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def parse_block_mesh(path: Path) -> tuple[int, int, int, float, tuple[float, float, float], tuple[float, float, float]]:
    text = _read_text(path)
    conv = float(re.search(r"convertToMeters\s+([0-9.eE+-]+)", text).group(1))
    verts = re.findall(r"\(\s*([0-9.eE+-]+)\s+([0-9.eE+-]+)\s+([0-9.eE+-]+)\s*\)", text.split("vertices")[1].split("blocks")[0])
    xs = [float(v[0]) * conv for v in verts]
    ys = [float(v[1]) * conv for v in verts]
    zs = [float(v[2]) * conv for v in verts]
    nx, ny, nz = [int(x) for x in re.search(r"hex\s*\([^)]+\)\s*\(\s*(\d+)\s+(\d+)\s+(\d+)\s*\)", text).groups()]
    return nx, ny, nz, conv, (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def parse_internal_field(path: Path) -> np.ndarray:
    text = _read_text(path)
    m = re.search(r"internalField\s+nonuniform\s+List<(scalar|vector)>\s*\n\s*(\d+)\s*\n\(", text)
    if not m:
        uni = re.search(r"internalField\s+uniform\s+(\([^)]+\)|[0-9.eE+-]+)", text)
        if not uni:
            raise ValueError(f"no internalField in {path}")
        tok = uni.group(1).strip()
        if tok.startswith("("):
            vals = [float(x) for x in tok.strip("()").split()]
            return np.array([vals])
        return np.array([float(tok)])
    kind = m.group(1)
    n = int(m.group(2))
    body = text[m.end() :]
    inner = body.split("\n)", 1)[0]
    if kind == "vector":
        vecs = re.findall(r"\(\s*([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s*\)", inner)
        arr = np.array(vecs, dtype=float)
        if arr.shape != (n, 3):
            raise ValueError(f"vector field length {arr.shape} vs n={n} in {path}")
        return arr
    nums = re.findall(r"[-+0-9.eE]+", inner)
    arr = np.array([float(x) for x in nums], dtype=float)
    if arr.size != n:
        raise ValueError(f"field length {arr.size} vs n={n} in {path}")
    return arr


def of_cell_xy(nx: int, ny: int, xmin: float, xmax: float, ymin: float, ymax: float) -> tuple[np.ndarray, np.ndarray]:
    dx = (xmax - xmin) / nx
    dy = (ymax - ymin) / ny
    xs = xmin + dx * (np.arange(nx) + 0.5)
    ys = ymin + dy * (np.arange(ny) + 0.5)
    xx = np.empty(nx * ny)
    yy = np.empty(nx * ny)
    k = 0
    for j in range(ny):
        for i in range(nx):
            xx[k] = xs[i]
            yy[k] = ys[j]
            k += 1
    return xx, yy


def _label_oil(alpha_water: np.ndarray, nx: int, ny: int, thresh: float = 0.5) -> np.ndarray:
    oil = (alpha_water.reshape(ny, nx) < thresh).astype(np.int32)
    labels = np.zeros_like(oil)
    lab = 0
    from collections import deque

    for j in range(ny):
        for i in range(nx):
            if oil[j, i] == 0 or labels[j, i] != 0:
                continue
            lab += 1
            q = deque([(j, i)])
            labels[j, i] = lab
            while q:
                cj, ci = q.popleft()
                for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nj, ni = cj + dj, ci + di
                    if 0 <= nj < ny and 0 <= ni < nx and oil[nj, ni] and labels[nj, ni] == 0:
                        labels[nj, ni] = lab
                        q.append((nj, ni))
    return labels


def droplet_metrics(alpha_water: np.ndarray, nx: int, ny: int, xmin: float, xmax: float, ymin: float, ymax: float) -> list[dict]:
    labels = _label_oil(alpha_water, nx, ny)
    dx = (xmax - xmin) / nx
    dy = (ymax - ymin) / ny
    area_cell = dx * dy
    xs, ys = of_cell_xy(nx, ny, xmin, xmax, ymin, ymax)
    out = []
    nlab = int(labels.max())
    for lab in range(1, nlab + 1):
        mask = labels.ravel() == lab
        area = float(mask.sum()) * area_cell
        if area <= 0:
            continue
        cx = float(np.average(xs[mask]))
        cy = float(np.average(ys[mask]))
        d_eq = 2.0 * math.sqrt(area / math.pi)
        # perimeter via 4-neighbor oil/water edges
        lab2 = labels
        peri = 0.0
        for j in range(ny):
            for i in range(nx):
                if lab2[j, i] != lab:
                    continue
                if i == 0 or lab2[j, i - 1] != lab:
                    peri += dy
                if i == nx - 1 or lab2[j, i + 1] != lab:
                    peri += dy
                if j == 0 or lab2[j - 1, i] != lab:
                    peri += dx
                if j == ny - 1 or lab2[j + 1, i] != lab:
                    peri += dx
        circ = (4.0 * math.pi * area / peri**2) if peri > 0 else 0.0
        deform = max(0.0, 1.0 - circ)
        out.append(
            {
                "id": lab,
                "centroid_x_m": cx,
                "centroid_y_m": cy,
                "area_m2": area,
                "d_eq_um": d_eq * 1e6,
                "circularity": circ,
                "deformation": deform,
            }
        )
    return out


def min_separation(drops: list[dict]) -> float:
    if len(drops) < 2:
        return float("inf")
    m = float("inf")
    for i, a in enumerate(drops):
        for b in drops[i + 1 :]:
            d = math.hypot(a["centroid_x_m"] - b["centroid_x_m"], a["centroid_y_m"] - b["centroid_y_m"])
            m = min(m, d)
    return m


def dimensionless_groups(*, rho: float, mu: float, U: float, L: float, d: float, sigma: float, mu_d: float) -> dict:
    Re = rho * U * L / mu
    We = rho * U**2 * d / max(sigma, 1e-12)
    Ca = mu * U / max(sigma, 1e-12)
    Oh = mu / math.sqrt(max(rho * sigma * d, 1e-30))
    lam = mu_d / mu
    # Hinze: dmax ~ C (sigma/rho)^0.6 epsilon^{-0.4}; channel epsilon ~ U^3/L
    eps = U**3 / max(L, 1e-12)
    d_hinze = 0.55 * (sigma / rho) ** 0.6 * eps ** (-0.4)
    return {
        "Re": Re,
        "We": We,
        "Ca": Ca,
        "Oh": Oh,
        "viscosity_ratio": lam,
        "d_hinze_um": d_hinze * 1e6,
        "d_cfd_um": d * 1e6,
        "provenance": PROVENANCE.value,
        "notes": "Incompressible hydrodynamics only; 10000 psi is not a CFD chemical-rate variable.",
    }


def case_time_dirs(case: Path) -> list[Path]:
    out = []
    for p in case.iterdir():
        if p.is_dir() and re.fullmatch(r"[0-9]+(\.[0-9]+)?", p.name) and p.name != "0":
            if (p / "alpha.water").exists():
                out.append(p)
    return sorted(out, key=lambda p: float(p.name))


def extract_case(case: Path, tag: str) -> list[dict]:
    mesh = case / "system" / "blockMeshDict"
    if not mesh.exists():
        return []
    nx, ny, nz, conv, mn, mx = parse_block_mesh(mesh)
    xmin, ymin, _ = mn
    xmax, ymax, _ = mx
    rows = []
    times = case_time_dirs(case)
    prev_n = None
    coalescence_events = 0
    for td in times:
        alpha = parse_internal_field(td / "alpha.water")
        if alpha.size != nx * ny:
            # latestTime might include extra cells; skip mismatched
            continue
        drops = droplet_metrics(alpha, nx, ny, xmin, xmax, ymin, ymax)
        n = len(drops)
        if prev_n is not None and n < prev_n:
            coalescence_events += prev_n - n
        prev_n = n
        sep = min_separation(drops)
        # pressure drop if p_rgh present
        dp = float("nan")
        pr = td / "p_rgh"
        if pr.exists():
            p = parse_internal_field(pr)
            if p.size == nx * ny:
                p2 = p.reshape(ny, nx)
                dp = float(p2[:, 0].mean() - p2[:, -1].mean())
        t = float(td.name)
        Umag = float("nan")
        uf = td / "U"
        if uf.exists():
            try:
                U = parse_internal_field(uf)
                if U.ndim == 2:
                    Umag = float(np.mean(np.linalg.norm(U, axis=1)))
            except ValueError:
                Umag = float("nan")
        for d in drops:
            cg = evaluate_chemgate(ChemGateInputs(diameter_um=d["d_eq_um"], temperature_C=150.0, D_mode="lee_ambient"))
            sph = evaluate_sphere(d["d_eq_um"], T_C=25.0, mode="lee_ambient")
            rows.append(
                {
                    "case": tag,
                    "time_s": t,
                    "n_droplets": n,
                    "droplet_id": d["id"],
                    "centroid_x_m": d["centroid_x_m"],
                    "centroid_y_m": d["centroid_y_m"],
                    "d_eq_um": d["d_eq_um"],
                    "circularity": d["circularity"],
                    "deformation": d["deformation"],
                    "min_separation_m": sep if np.isfinite(sep) else None,
                    "coalescence_events_cumulative": coalescence_events,
                    "mean_U_m_s": Umag,
                    "pressure_drop_Pa": dp,
                    "t_diff_min": sph.t_avg_50_s / 60.0,
                    "t_transform_min": cg.t_transform_min,
                    "chemgate_pathway": cg.pathway,
                    "provenance": PROVENANCE.value,
                }
            )
        if not drops:
            rows.append(
                {
                    "case": tag,
                    "time_s": t,
                    "n_droplets": 0,
                    "droplet_id": None,
                    "d_eq_um": None,
                    "coalescence_events_cumulative": coalescence_events,
                    "provenance": PROVENANCE.value,
                }
            )
    return rows


def plot_phase_snapshots(case: Path, figdir: Path, name: str = "26_cfd_phase_fraction_snapshots") -> None:
    import matplotlib.pyplot as plt

    mesh = case / "system" / "blockMeshDict"
    if not mesh.exists():
        return
    nx, ny, nz, conv, mn, mx = parse_block_mesh(mesh)
    times = case_time_dirs(case)
    if not times:
        return
    pick = times[:: max(1, len(times) // 3)][:4]
    fig, axes = plt.subplots(1, len(pick), figsize=(3.2 * len(pick), 3.2), squeeze=False)
    xmin, ymin, _ = mn
    xmax, ymax, _ = mx
    for ax, td in zip(axes[0], pick, strict=True):
        alpha = parse_internal_field(td / "alpha.water")
        if alpha.size != nx * ny:
            ax.set_title(f"t={td.name}s (size mismatch)")
            continue
        im = ax.imshow(
            alpha.reshape(ny, nx),
            origin="lower",
            extent=(xmin * 1e3, xmax * 1e3, ymin * 1e3, ymax * 1e3),
            vmin=0,
            vmax=1,
            cmap="RdYlBu",
            aspect="auto",
        )
        ax.set_title(f"t = {td.name} s")
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("y (mm)")
    fig.colorbar(im, ax=axes.ravel().tolist(), fraction=0.02, label="alpha.water")
    fig.suptitle("CFD phase fraction (1=aqueous). Data-derived, not decorative.")
    figdir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(figdir / f"{name}.png", dpi=300)
    fig.savefig(figdir / f"{name}.svg")
    plt.close(fig)


def write_metrics_csv(path: Path | None = None) -> Path:
    root = repo_root()
    path = path or (root / "results" / "tables" / "cfd_metrics.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for tag, rel in (
        ("phaseforge_channel", "simulations/cfd/phaseforge_channel"),
        ("phaseforge_channel_hpht", "simulations/cfd/phaseforge_channel_hpht"),
    ):
        case = root / rel
        if case.exists():
            rows.extend(extract_case(case, tag))
    if not rows:
        path.write_text(
            "case,time_s,n_droplets,notes,provenance\n"
            f"phaseforge_channel,,,no solved time directories; fields not fabricated,{PROVENANCE.value}\n",
            encoding="utf-8",
        )
        return path
    keys = sorted({k for r in rows for k in r})
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return path


def intended_dimensionless(temperature_C: float = 65.0) -> dict:
    if temperature_C < 100:
        rho, mu, mu_d, sigma = 983.0, 983.0 * 4.1e-7, 960.0 * 5.1e-7, 0.004
    else:
        rho, mu, mu_d, sigma = 917.0, 917.0 * 2.0e-7, 880.0 * 3.2e-7, 0.0032
    return dimensionless_groups(rho=rho, mu=mu, U=0.05, L=0.003, d=5.0e-4, sigma=sigma, mu_d=mu_d)


def main() -> int:
    p = write_metrics_csv()
    print(f"wrote {p}")
    print(intended_dimensionless(65.0))
    print(intended_dimensionless(150.0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
