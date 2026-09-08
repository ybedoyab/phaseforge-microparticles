"""CFD metrics parser tests. Do not require a live Docker solve."""

from phaseforge.cfd_postprocess import (
    PROVENANCE,
    dimensionless_groups,
    intended_dimensionless,
    parse_block_mesh,
)
from phaseforge.requirements import repo_root


def test_dimensionless_positive() -> None:
    d = intended_dimensionless(65.0)
    assert d["Re"] > 0
    assert d["We"] > 0
    assert d["Ca"] > 0
    assert d["Oh"] > 0
    assert d["provenance"] == PROVENANCE.value


def test_hinze_finite() -> None:
    g = dimensionless_groups(rho=1000.0, mu=1e-3, U=0.05, L=0.003, d=5e-4, sigma=0.004, mu_d=1e-3)
    assert g["d_hinze_um"] > 0


def test_parse_phaseforge_blockmesh() -> None:
    p = repo_root() / "simulations" / "cfd" / "phaseforge_channel" / "system" / "blockMeshDict"
    nx, ny, nz, conv, mn, mx = parse_block_mesh(p)
    assert nx == 200 and ny == 40 and nz == 1
    assert abs(conv - 0.001) < 1e-12
    assert mx[0] > mn[0]


def test_parser_on_solved_fields_if_present() -> None:
    case = repo_root() / "simulations" / "cfd" / "phaseforge_channel"
    from phaseforge.cfd_postprocess import case_time_dirs, extract_case

    times = case_time_dirs(case)
    if not times:
        return
    rows = extract_case(case, "phaseforge_channel")
    assert rows
    assert rows[0]["provenance"] == PROVENANCE.value
