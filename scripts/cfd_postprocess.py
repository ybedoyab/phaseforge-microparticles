"""Dimensionless diagnostics wrapper; field extraction lives in phaseforge.cfd_postprocess."""

from __future__ import annotations

from phaseforge.cfd_postprocess import intended_dimensionless, write_metrics_csv
from phaseforge.cfd_postprocess import main as _main


def diagnostics() -> dict[str, float]:
    d = intended_dimensionless(65.0)
    return {k: v for k, v in d.items() if isinstance(v, int | float)}


if __name__ == "__main__":
    write_metrics_csv()
    raise SystemExit(_main())
