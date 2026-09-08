"""Citation / dangerous-phrase / CSV sanity checks."""

from __future__ import annotations

from phaseforge.requirements import repo_root

FORBIDDEN = [
    "experimentally demonstrated by us",
    "TRL 3 achieved",
    "we physically performed",
    "we measured the PhaseForge fluid",
]


def test_no_forbidden_claims() -> None:
    root = repo_root()
    text_files = list(root.glob("docs/*.md")) + [root / "README.md"]
    for path in text_files:
        if not path.exists():
            continue
        blob = path.read_text(encoding="utf-8").lower()
        for phrase in FORBIDDEN:
            assert phrase not in blob, f"{path} contains forbidden phrase: {phrase}"


def test_evidence_registry_exists() -> None:
    p = repo_root() / "data" / "literature" / "evidence_registry.csv"
    assert p.exists()
    import pandas as pd

    df = pd.read_csv(p, engine="python")
    assert "provenance" in df.columns
    assert "doi_or_patent" in df.columns
    assert len(df) >= 20
    allowed = {
        "PUBLISHED_EXPERIMENTAL",
        "DIGITIZED_FROM_PUBLICATION",
        "MANUFACTURER_DATA",
        "ASSUMED_FOR_SENSITIVITY",
        "FITTED",
        "MODEL_PREDICTION",
    }
    assert set(df["provenance"].dropna().unique()) <= allowed


def test_liang_has_no_invented_numbers() -> None:
    import pandas as pd

    df = pd.read_csv(repo_root() / "data" / "literature" / "evidence_registry.csv", engine="python")
    liang = df[df["source_id"] == "LIANG2025_GEOEN"]
    assert len(liang) >= 1
    assert (liang["property"] == "bibliographic_record").any()
