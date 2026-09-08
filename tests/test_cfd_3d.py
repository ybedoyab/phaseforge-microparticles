"""True-3D CFD metric tests. Do not require a live Docker solve."""

from __future__ import annotations

import math

import numpy as np
from phaseforge.cfd_3d_postprocess import (
    d_eq_from_volume_m,
    droplet_metrics_3d,
    label_oil_3d,
    parse_checkmesh,
    sphericity_wadell,
)
from phaseforge.cfd_postprocess import parse_block_mesh


def test_volume_equivalent_diameter_sphere() -> None:
    r = 250e-6
    v = 4.0 / 3.0 * math.pi * r**3
    d = d_eq_from_volume_m(v)
    assert abs(d - 2 * r) < 1e-12


def test_sphericity_of_sphere_is_one() -> None:
    r = 250e-6
    v = 4.0 / 3.0 * math.pi * r**3
    a = 4.0 * math.pi * r**2
    assert abs(sphericity_wadell(v, a) - 1.0) < 1e-9


def test_sphericity_not_2d_circularity() -> None:
    # A pancake has low 3D sphericity even if the 2D outline is circular.
    v = 1e-12
    a = 1e-6
    s = sphericity_wadell(v, a)
    assert 0.0 < s < 0.2


def test_connected_components_and_centroids() -> None:
    nx, ny, nz = 20, 12, 10
    a = np.ones(nx * ny * nz)
    # Two oil blobs far apart on a 20x12x10 grid.
    a3 = a.reshape((nz, ny, nx))
    a3[3:6, 4:7, 2:5] = 0.0
    a3[3:6, 4:7, 14:17] = 0.0
    drops = droplet_metrics_3d(
        a3.ravel(),
        nx,
        ny,
        nz,
        ((0.0, 0.0, 0.0), (0.02, 0.003, 0.002)),
        min_volume_m3=1e-20,
    )
    assert len(drops) == 2
    assert drops[0]["centroid_x_m"] < drops[1]["centroid_x_m"]
    assert all(d["d_eq_um"] > 0 for d in drops)
    assert all(0.0 < d["sphericity"] <= 1.5 for d in drops)


def test_coalescence_event_count() -> None:
    oil = np.zeros((4, 4, 8), dtype=bool)
    oil[1:3, 1:3, 1:3] = True
    oil[1:3, 1:3, 5:7] = True
    labels = label_oil_3d(oil)
    assert int(labels.max()) == 2
    oil[:, :, 3:5] = True
    labels2 = label_oil_3d(oil)
    assert int(labels2.max()) == 1
    events = int(labels.max()) - int(labels2.max())
    assert events == 1


def test_checkmesh_parser() -> None:
    text = """
Checking geometry...
    Overall domain bounding box (0 0 0) (0.02 0.003 0.002)
    Mesh has 3 geometric (non-empty/wedge) directions (3D)
    Mesh has 3 solution (non-empty) directions (3D)
    Boundary openness (-1e-16 2e-16 0) OK.
    Max cell openness = 1.3e-16 OK.
    Max aspect ratio = 1.05 OK.
    Minimum face area = 3.9e-9. Maximum face area = 3.9e-9.  Face area magnitudes OK.
    Min volume = 2.44e-13. Max volume = 2.44e-13.  Total volume = 1.2e-7.  Cell volumes OK.
    Mesh non-orthogonality Max: 0 average: 0
    Max skewness = 1.2e-13 OK.
Mesh OK.
cells:          491520
"""
    d = parse_checkmesh(text)
    assert d["mesh_ok"] is True
    assert d["n_cells"] == 491520
    assert d["max_nonorthogonality"] == 0.0


def test_nominal_checkmesh_log_not_coarse() -> None:
    from phaseforge.requirements import repo_root

    path = repo_root() / "results/raw/cfd/cfd3d_nominal_checkMesh.log"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    d = parse_checkmesh(text)
    assert d["mesh_ok"] is True
    assert d["n_cells"] == 491520
    assert d["max_aspect_ratio"] == 1.0
    assert d["max_nonorthogonality"] == 0.0
    assert "phaseforge_channel_3d_coarse" not in text
    assert "Case   : /data/phaseforge_channel_3d" in text
    assert "Mesh has 3 geometric" in text
    assert "Mesh has 3 solution" in text
    assert "Mesh OK." in text


def test_3d_case_is_not_empty_patch() -> None:
    from phaseforge.requirements import repo_root

    root = repo_root()
    mesh = root / "simulations/cfd/phaseforge_channel_3d/system/blockMeshDict"
    fields = root / "simulations/cfd/phaseforge_channel_3d/system/setFieldsDict"
    if not mesh.exists():
        return
    text = mesh.read_text(encoding="utf-8")
    st = fields.read_text(encoding="utf-8")
    assert "type empty" not in text
    assert "sphereToCell" in st
    assert "cylinderToCell" not in st
    nx, ny, nz, conv, mn, mx = parse_block_mesh(mesh)
    assert nz >= 8
    assert nx * ny * nz >= 10000
    assert abs(mx[2] - mn[2]) >= 0.0015


def test_extract_3d_if_solved() -> None:
    from phaseforge.cfd_3d_postprocess import extract_case_3d
    from phaseforge.requirements import repo_root

    case = repo_root() / "simulations/cfd/phaseforge_channel_3d_coarse"
    if not (case / "0.08" / "alpha.water").exists():
        return
    rows = extract_case_3d(case, "coarse")
    assert rows
    assert rows[0]["provenance"] == "CFD_3D_MODEL_PREDICTION"
    assert rows[0]["nz"] >= 8
    assert any(r["n_droplets"] >= 3 for r in rows)
