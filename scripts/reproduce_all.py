"""Reproduce lightweight analytical results, figures, and evidence tables."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phaseforge.reporting import generate_all_figures  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Reproduce PhaseForge analytical POC")
    p.add_argument("--skip-figures", action="store_true")
    p.add_argument("--figures-only", action="store_true")
    p.add_argument("--report-only", action="store_true")
    p.add_argument("--skip-uq", action="store_true", help="Skip Monte Carlo / Sobol (faster smoke)")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logging.info("PhaseForge reproduce_all starting (seed=%s)", args.seed)
    summary = generate_all_figures(skip_uq=args.skip_uq or args.report_only)
    logging.info("Nominal overall: %s", summary["nominal"]["overall"])
    logging.info("HPHT 150 C overall (no extra latency): %s", summary["hpht"]["overall"])
    logging.info("Wrote figures, tables, and results/final_metrics.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
