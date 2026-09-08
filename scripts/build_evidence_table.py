"""Build / refresh the requirements traceability table without full UQ."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phaseforge.coupled import OperatingPoint, evaluate_point, from_yaml_point
from phaseforge.reporting import build_traceability, write_traceability_md
from phaseforge.requirements import load_baseline, repo_root


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    baseline = load_baseline()
    nom = evaluate_point(from_yaml_point(baseline["operating_point_nominal"], "nominal"))
    hpht = evaluate_point(
        OperatingPoint(
            temperature_C=150.0,
            phi=0.15,
            catalyst_relative=0.5,
            inhibitor_index=0.95,
            latency_extra=1.0,
            label="hpht_no_extra_latency",
        )
    )
    df = build_traceability(nom, hpht)
    root = repo_root()
    out = root / "results" / "tables" / "requirements_traceability.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    write_traceability_md(df, root / "docs")
    logging.info("Wrote %s (%d rows)", out, len(df))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
