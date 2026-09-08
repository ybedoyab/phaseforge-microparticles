"""Load and evaluate Innocentive challenge requirements."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from phaseforge.provenance import RequirementStatus
from phaseforge.units import (
    CP_10_PA_S,
    PSI_4500_MPA,
    PSI_6000_MPA,
    PSI_10000_MPA,
    Pa_s_to_cP,
    m_to_um,
    psi_to_MPa,
)


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for p in [here, *here.parents]:
        if (p / "pyproject.toml").exists():
            return p
    return Path.cwd()


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def load_challenge_requirements(path: Path | None = None) -> dict[str, Any]:
    if path is None:
        path = repo_root() / "config" / "challenge_requirements.yaml"
    return load_yaml(path)


def load_baseline(path: Path | None = None) -> dict[str, Any]:
    if path is None:
        path = repo_root() / "config" / "baseline.yaml"
    return load_yaml(path)


def load_parameter_ranges(path: Path | None = None) -> dict[str, Any]:
    if path is None:
        path = repo_root() / "config" / "parameter_ranges.yaml"
    return load_yaml(path)


@dataclass(frozen=True, slots=True)
class ThresholdResult:
    requirement_id: str
    status: RequirementStatus
    predicted: float | None
    unit: str
    notes: str = ""


def classify_viscosity(mu_Pa_s: float, *, marginal_factor: float = 1.2) -> RequirementStatus:
    if mu_Pa_s <= CP_10_PA_S:
        return RequirementStatus.PASS
    if mu_Pa_s <= CP_10_PA_S * marginal_factor:
        return RequirementStatus.MARGINAL
    return RequirementStatus.FAIL


def classify_transform_time_s(
    t_s: float | None,
    t_min: float = 25.0 * 60.0,
    t_max: float = 75.0 * 60.0,
    *,
    unknown: bool = False,
) -> RequirementStatus:
    if unknown or t_s is None:
        return RequirementStatus.UNKNOWN
    if t_min <= t_s <= t_max:
        return RequirementStatus.PASS
    # within 10 min of the window is marginal
    if (t_min - 600.0) <= t_s <= (t_max + 600.0):
        return RequirementStatus.MARGINAL
    return RequirementStatus.FAIL


def classify_diameter_m(d_m: float) -> RequirementStatus:
    d_um = m_to_um(d_m)
    if 70.0 <= d_um <= 600.0:
        return RequirementStatus.PASS
    if 50.0 <= d_um <= 800.0:
        return RequirementStatus.MARGINAL
    return RequirementStatus.FAIL


def classify_mechanical_sf(sf: float | None, *, unknown: bool = False) -> RequirementStatus:
    if unknown or sf is None:
        return RequirementStatus.UNKNOWN
    if sf >= 1.25:
        return RequirementStatus.PASS
    if sf >= 1.0:
        return RequirementStatus.MARGINAL
    return RequirementStatus.FAIL


def classify_boolean(ok: bool | None, *, unknown_if_none: bool = True) -> RequirementStatus:
    if ok is None and unknown_if_none:
        return RequirementStatus.UNKNOWN
    return RequirementStatus.PASS if ok else RequirementStatus.FAIL


def worst_status(statuses: list[RequirementStatus]) -> RequirementStatus:
    """UNKNOWN never becomes PASS. FAIL dominates, then UNKNOWN, then MARGINAL."""
    if RequirementStatus.FAIL in statuses:
        return RequirementStatus.FAIL
    if RequirementStatus.UNKNOWN in statuses:
        return RequirementStatus.UNKNOWN
    if RequirementStatus.MARGINAL in statuses:
        return RequirementStatus.MARGINAL
    return RequirementStatus.PASS


def challenge_stress_mpa() -> dict[str, float]:
    return {
        "transport_pressure_max_MPa": PSI_10000_MPA,
        "post_transform_pressure_MPa": PSI_6000_MPA,
        "closure_min_MPa": PSI_4500_MPA,
        "closure_max_MPa": PSI_6000_MPA,
        "viscosity_max_cP": Pa_s_to_cP(CP_10_PA_S),
        "closure_min_psi": 4500.0,
        "closure_max_psi": 6000.0,
        "transport_pressure_psi": 10000.0,
        "psi_to_MPa_4500": psi_to_MPa(4500.0),
        "psi_to_MPa_6000": psi_to_MPa(6000.0),
    }
