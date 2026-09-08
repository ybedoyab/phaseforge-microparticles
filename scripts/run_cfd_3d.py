"""Solve true-3D PhaseForge interFoam cases in GeoChemFoam Docker (OpenFOAM v2212).

Does not rerun the 2D screening case. Hydrodynamics only.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from phaseforge.requirements import repo_root

IMAGE = "jcmaes/geochemfoam-5.2"
OF_BASHRC = "source /usr/lib/openfoam/openfoam2212/etc/bashrc"


def _docker_run(inner: str, *, cfd: Path, logs: Path, extra_env: list[str] | None = None) -> int:
    env = extra_env or []
    cmd = [
        "docker",
        "run",
        "--rm",
        "-u",
        "0",
        "-v",
        f"{cfd}:/data",
        "-v",
        f"{logs}:/logs",
        *env,
        IMAGE,
        "bash",
        "-lc",
        f"{OF_BASHRC}; {inner}",
    ]
    print(">>", inner[:180].replace("\n", " "))
    return subprocess.call(cmd)


def _solve_case(tag: str, case_rel: str, *, cfd: Path, logs: Path, parallel: bool = True) -> int:
    """blockMesh → checkMesh → setFields → interFoam → foamToVTK."""
    par = f"""
export OMPI_ALLOW_RUN_AS_ROOT=1
export OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
decomposePar > /logs/{tag}_decomposePar.log 2>&1
mpirun --allow-run-as-root -np 4 interFoam -parallel > /logs/{tag}_interFoam.log 2>&1
reconstructPar > /logs/{tag}_reconstructPar.log 2>&1
rm -rf processor*
"""
    serial = f"interFoam > /logs/{tag}_interFoam.log 2>&1\n"
    solve = par if parallel else serial
    inner = f"""
set -e
cd /data/{case_rel}
rm -rf constant/polyMesh processor* VTK [1-9]* 0.[0-9]*
blockMesh > /logs/{tag}_blockMesh.log 2>&1
checkMesh > /logs/{tag}_checkMesh.log 2>&1
if grep -q 'Failed' /logs/{tag}_checkMesh.log && ! grep -q 'Mesh OK' /logs/{tag}_checkMesh.log; then
  echo CHECKMESH_FAILED >> /logs/{tag}_metadata.txt
  cat /logs/{tag}_checkMesh.log | tail -40
  exit 41
fi
cp -f 0/alpha.water.org 0/alpha.water
setFields > /logs/{tag}_setFields.log 2>&1
{solve}
foamToVTK > /logs/{tag}_foamToVTK.log 2>&1 || true
echo TAG={tag} > /logs/{tag}_metadata.txt
echo OF=$WM_PROJECT_VERSION >> /logs/{tag}_metadata.txt
echo IMAGE={IMAGE} >> /logs/{tag}_metadata.txt
echo CASE={case_rel} >> /logs/{tag}_metadata.txt
ls -1 >> /logs/{tag}_metadata.txt
grep -E 'Time =|ExecutionTime|Courant|End' /logs/{tag}_interFoam.log | tail -100 > /logs/{tag}_residuals.txt || true
if grep -q '^End' /logs/{tag}_interFoam.log; then
  echo SOLVE_END=yes >> /logs/{tag}_metadata.txt
else
  echo SOLVE_END=no >> /logs/{tag}_metadata.txt
  tail -40 /logs/{tag}_interFoam.log
  exit 42
fi
"""
    return _docker_run(inner, cfd=cfd, logs=logs)


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--only", choices=("coarse", "moderate", "hpht", "all"), default="all")
    args = p.parse_args(argv)
    root = repo_root()
    cfd = root / "simulations" / "cfd"
    logs = root / "results" / "raw" / "cfd"
    logs.mkdir(parents=True, exist_ok=True)
    import importlib.util

    writer = repo_root() / "scripts" / "write_phaseforge_3d_case.py"
    spec = importlib.util.spec_from_file_location("write_phaseforge_3d_case", writer)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    mod.main()
    all_cases = [
        ("cfd3d_coarse", "phaseforge_channel_3d_coarse"),
        ("cfd3d_moderate", "phaseforge_channel_3d"),
        ("cfd3d_hpht", "phaseforge_channel_3d_hpht"),
    ]
    if args.only == "all":
        cases = all_cases
    else:
        cases = [c for c in all_cases if c[0].endswith(args.only)]
    rc_map: dict[str, int] = {}
    for tag, rel in cases:
        rc = _solve_case(tag, rel, cfd=cfd, logs=logs, parallel=True)
        if rc != 0:
            print(f"{tag} parallel failed rc={rc}; retrying serial")
            rc = _solve_case(tag, rel, cfd=cfd, logs=logs, parallel=False)
        rc_map[tag] = rc
        print(f"{tag} rc={rc}")
        if tag == "cfd3d_coarse" and rc != 0:
            print("coarse 3D solve failed; not claiming 3D results")
            return rc
    from phaseforge.cfd_3d_postprocess import main as post

    post()
    worst = max(rc_map.values()) if rc_map else 1
    return 0 if all(v == 0 for v in rc_map.values()) else worst


if __name__ == "__main__":
    sys.path.insert(0, str(repo_root()))
    raise SystemExit(main())
