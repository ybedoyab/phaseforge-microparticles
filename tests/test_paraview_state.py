"""ParaView state / locator tests. Do not require pvpython in CI."""

from __future__ import annotations

from phaseforge.paraview_locate import is_real_paraview_state, locate_paraview
from phaseforge.requirements import repo_root


def test_locate_paraview_returns_keys() -> None:
    info = locate_paraview()
    assert set(info) == {"paraview", "pvpython", "version"}
    for v in info.values():
        assert v is None or isinstance(v, str)


def test_markdown_notes_are_not_paraview_state() -> None:
    from pathlib import Path

    fake = Path("not-a-state.md")
    assert is_real_paraview_state(fake) is False


def test_committed_pvsm_is_xml_when_generated() -> None:
    root = repo_root()
    path = root / "visualization" / "phaseforge_3d.pvsm"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    if text.lstrip().startswith("#"):
        # Placeholder notes from an earlier pass; real XML is required after ParaView postprocess.
        return
    assert is_real_paraview_state(path)
    hpht = root / "visualization" / "phaseforge_3d_hpht.pvsm"
    if hpht.exists() and not hpht.read_text(encoding="utf-8", errors="replace").lstrip().startswith("#"):
        assert is_real_paraview_state(hpht)
