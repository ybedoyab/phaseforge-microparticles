"""Locate ParaView / pvpython on Windows (and POSIX) without requiring them at import."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def _exe_name(stem: str) -> str:
    return f"{stem}.exe" if os.name == "nt" else stem


def _version_from_binary(path: Path) -> str | None:
    try:
        proc = subprocess.run(
            [str(path), "--version"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    return None


def _candidate_roots() -> list[Path]:
    roots: list[Path] = []
    env = os.environ.get("PARAVIEW_HOME") or os.environ.get("ParaView_DIR")
    if env:
        roots.append(Path(env))
    home = Path.home()
    local = Path(os.environ.get("LOCALAPPDATA", str(home / "AppData" / "Local")))
    pf = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
    pf86 = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
    roots.extend(
        [
            Path(r"D:\ParaView"),
            Path(r"C:\ParaView"),
            pf,
            pf86,
            local / "Programs",
            home / "Downloads",
            home / "Escritorio",
            home / "Desktop",
        ]
    )
    return roots


def _search_binaries() -> tuple[Path | None, Path | None]:
    paraview = shutil.which(_exe_name("paraview"))
    pvpython = shutil.which(_exe_name("pvpython"))
    pv = Path(paraview) if paraview else None
    py = Path(pvpython) if pvpython else None
    extra: list[Path] = []
    for root in _candidate_roots():
        if not root.exists():
            continue
        extra.append(root)
        extra.extend(root.glob("ParaView*"))
        extra.extend(root.glob("paraview*"))
    seen: set[Path] = set()
    for base in extra:
        if base in seen or not base.exists():
            continue
        seen.add(base)
        bins = [base / "bin", base]
        if base.is_dir():
            bins.extend([p for p in base.glob("*/bin") if p.is_dir()][:20])
        for b in bins:
            cand_pv = b / _exe_name("paraview")
            cand_py = b / _exe_name("pvpython")
            if pv is None and cand_pv.is_file():
                pv = cand_pv
            if py is None and cand_py.is_file():
                py = cand_py
            if pv and py:
                return pv, py
        if pv and py:
            return pv, py
    # If only one was found via PATH, look beside it.
    if pv and py is None:
        sib = pv.parent / _exe_name("pvpython")
        if sib.is_file():
            py = sib
    if py and pv is None:
        sib = py.parent / _exe_name("paraview")
        if sib.is_file():
            pv = sib
    return pv, py


def locate_paraview() -> dict[str, str | None]:
    """Return paths and a version string. Missing tools are None, never invented."""
    pv, py = _search_binaries()
    version = None
    if py is not None:
        version = _version_from_binary(py)
    if version is None and pv is not None:
        version = _version_from_binary(pv)
    return {
        "paraview": str(pv) if pv else None,
        "pvpython": str(py) if py else None,
        "version": version,
    }


def is_real_paraview_state(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")[:4000]
    head = text.lstrip()
    if not head.startswith("<"):
        return False
    return "ServerManagerState" in text or "ParaView" in text
