"""Reviewer-facing rounding for challenge-stage model results.

Raw machine values may be stored in JSON. Documentation and figures should
not display unjustified precision (e.g. 273.0466868420546 um).
"""

from __future__ import annotations

import math


def round_cP(x: float) -> float:
    """Viscosity in cP to 0.01 (e.g. 0.50 cP)."""
    return float(round(x, 2))


def round_um(x: float) -> int:
    """Hinze-scale diameter to nearest 10 um (e.g. 270 um)."""
    return int(round(x / 10.0) * 10)


def round_sf(x: float) -> float:
    """Safety factor to 1 decimal (e.g. 1.4)."""
    return float(round(x, 1))


def round_prob(x: float) -> float:
    """Monte Carlo probability to 2 significant digits for n~400."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    return float(round(x, 2))


def round_krel(x: float) -> float:
    """Relative permeability heuristic to 2 decimals."""
    return float(round(x, 2))


def round_min(x: float) -> float:
    """Times in minutes: 2 significant figures if <100, else integer."""
    if not math.isfinite(x):
        return x
    if abs(x) < 10.0:
        return float(round(x, 1))
    if abs(x) < 100.0:
        return float(round(x, 0))
    return float(round(x, 0))


def sigfig(x: float, n: int = 2) -> float:
    if x == 0.0 or not math.isfinite(x):
        return x
    mag = math.floor(math.log10(abs(x)))
    return float(round(x, -mag + (n - 1)))
