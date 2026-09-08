"""PhaseForge-ChemGate: chemically gated latent ROMP in organic droplets.

Two-stage deployment (architecture, not a measured 150 C recipe):

  Stage A — placement fluid: low-viscosity aqueous carrier + latent-catalyst
            DCPD-family droplets. Activator is NOT freely available.
  Stage B — activator chase: aqueous activator reaches placed droplets, then

    aqueous activator
      → liquid-liquid partition
      → diffusion into organic droplets
      → latent catalyst activation
      → surface-to-core ROMP
      → discrete particles.

Timing split (do not treat operational delay as material kinetics):

  t_trigger_arrival          operational Stage-B arrival
                             tag: ASSUMED_FOR_DEPLOYMENT_SCENARIO
  t_post_trigger_particle  = t_partition + t_diffusion + t_activation
                             + t_polymerization
  t_total_after_initial_pumping
                           = t_trigger_arrival + t_post_trigger_particle

Innocentive 25-75 min is interpreted two ways:
  A. from initial reactive-fluid pumping  = t_total_after_initial_pumping
  B. from activator contact               = t_post_trigger_particle

D899/Cu literature is an ANALOGUE, not a PhaseForge recipe and not our IP.

Lee 2024: D899 dormant through ~200 C frontal polymerization until Cu(I).
Lee 2025: aqueous Cu(I) → organic DCPD ink via interfacial diffusion; D≈6e-12 m2/s
          ambient; filaments <~400 um fully cured in ≥~20 min.
Suslick 2022: ambient gel times ~5 min (CuX) to 12 h (Cu(PPh3)3X).

None of that is an isothermal 25-75 min measurement at 150 C. Status cannot be PASS.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from phaseforge.activation_diffusion import (
    D_LEE2025_M2_S,
    DIAMETERS_UM,
    evaluate_sphere,
)
from phaseforge.provenance import Provenance, RequirementStatus
from phaseforge.requirements import classify_transform_time_s
from phaseforge.units import um_to_m

FAMILY_CHEMGATE = "PhaseForge-ChemGate"
FAMILY_CHEMGATE_ACID = "PhaseForge-ChemGate-Acid"

# Ambient analogue gel/activation windows (Suslick 2022 / Lee 2024). Not 150 C.
T_ACT_CUCL_S = 10.0 * 60.0  # "within minutes" simple CuX
T_ACT_SLOW_S = 12.0 * 3600.0  # coordinatively saturated Cu
T_POLY_AFTER_S = 15.0 * 60.0  # Lee color/film ~20 min includes diffusion; residual polymerisation analogue
T_PARTITION_S = 2.0 * 60.0  # ASSUMED interfacial transfer lag

TRIGGER_ARRIVAL_TAG = "ASSUMED_FOR_DEPLOYMENT_SCENARIO"
DEFAULT_TRIGGER_ARRIVAL_S = 30.0 * 60.0  # engineering scenario, not kinetics
WINDOW_LO_MIN = 25.0
WINDOW_HI_MIN = 75.0
TRIGGER_SEARCH_MAX_MIN = 60.0
# Engineering-level assumed spread of the Stage-B activator front (not measured).
FRONT_DISPERSION_SIGMA_MIN = (5.0, 10.0, 15.0)


@dataclass(frozen=True, slots=True)
class ChemGateInputs:
    diameter_um: float = 270.0
    temperature_C: float = 150.0
    t_trigger_arrival_s: float = DEFAULT_TRIGGER_ARRIVAL_S
    t_partition_s: float = T_PARTITION_S
    t_activation_s: float = T_ACT_CUCL_S
    t_polymerization_s: float = T_POLY_AFTER_S
    D_mode: str = "lee_ambient"
    empirical_D_factor: float = 1.0
    partition_K: float = 1.0
    activator_activity: float = 1.0  # scales t_activation as 1/activity


@dataclass(frozen=True, slots=True)
class ChemGateResult:
    family: str
    t_trigger_arrival_s: float
    t_trigger_arrival_tag: str
    t_partition_s: float
    t_diff_s: float
    t_activation_s: float
    t_polymerization_s: float
    t_post_trigger_particle_s: float
    t_total_after_initial_pumping_s: float
    t_transform_s: float  # interpretation A alias; not intrinsic latency
    t_transform_min: float
    t_post_trigger_particle_min: float
    t_from_pumping_min: float
    t_from_contact_min: float
    t_arr_min_allowable_min: float | None
    t_arr_max_allowable_min: float | None
    t_transport_leak_s: float
    Da_diff_act: float
    Da_diff_poly: float
    regime: str
    status: RequirementStatus
    pathway: str
    stage_a_activator_present: bool
    premature_during_transport: bool
    notes: str
    provenance: Provenance

    @property
    def t_delay_s(self) -> float:
        """Deprecated alias of operational t_trigger_arrival_s (not kinetics)."""
        return self.t_trigger_arrival_s

    def as_dict(self) -> dict:
        return {
            "family": self.family,
            "t_trigger_arrival_min": self.t_trigger_arrival_s / 60.0,
            "t_trigger_arrival_tag": self.t_trigger_arrival_tag,
            "t_partition_min": self.t_partition_s / 60.0,
            "t_diff_min": self.t_diff_s / 60.0 if np.isfinite(self.t_diff_s) else None,
            "t_activation_min": self.t_activation_s / 60.0,
            "t_polymerization_min": self.t_polymerization_s / 60.0,
            "t_post_trigger_particle_min": (
                self.t_post_trigger_particle_min
                if np.isfinite(self.t_post_trigger_particle_min)
                else None
            ),
            "t_total_after_initial_pumping_min": (
                self.t_from_pumping_min if np.isfinite(self.t_from_pumping_min) else None
            ),
            "t_from_pumping_min": self.t_from_pumping_min if np.isfinite(self.t_from_pumping_min) else None,
            "t_from_contact_min": self.t_from_contact_min if np.isfinite(self.t_from_contact_min) else None,
            "t_transform_min": self.t_transform_min if np.isfinite(self.t_transform_min) else None,
            "t_arr_min_allowable_min": self.t_arr_min_allowable_min,
            "t_arr_max_allowable_min": self.t_arr_max_allowable_min,
            "Da_diff_act": self.Da_diff_act,
            "Da_diff_poly": self.Da_diff_poly,
            "regime": self.regime,
            "status": self.status.value,
            "pathway": self.pathway,
            "stage_a_activator_present": self.stage_a_activator_present,
            "premature_during_transport": self.premature_during_transport,
            "notes": self.notes,
        }


def damkohler(t_diff_s: float, t_react_s: float) -> float:
    """Da = t_diff / t_react. >>1 diffusion-limited; <<1 reaction-limited."""
    if not np.isfinite(t_diff_s) or t_react_s <= 0.0:
        return float("nan")
    return t_diff_s / t_react_s


def _regime(da_act: float, da_poly: float) -> str:
    da = max(da_act, da_poly) if np.isfinite(da_act) else da_poly
    if not np.isfinite(da):
        return "unknown"
    if da >= 3.0:
        return "diffusion_limited"
    if da <= 0.3:
        return "activation_or_reaction_limited"
    return "mixed"


def allowable_trigger_arrival_min(
    t_post_trigger_particle_min: float,
    *,
    window_lo: float = WINDOW_LO_MIN,
    window_hi: float = WINDOW_HI_MIN,
    t_arr_search_lo: float = 0.0,
    t_arr_search_hi: float = TRIGGER_SEARCH_MAX_MIN,
) -> dict:
    """Arrival times such that window_lo <= t_arr + t_post <= window_hi.

    Search is restricted to t_arr in [t_arr_search_lo, t_arr_search_hi] minutes.
    Returns None bounds when no arrival in the search range lands in the window.
    """
    t_post = float(t_post_trigger_particle_min)
    if not np.isfinite(t_post):
        return {
            "t_post_trigger_particle_min": t_post,
            "t_trigger_arrival_min_allowable": None,
            "t_trigger_arrival_max_allowable": None,
            "feasible": False,
            "interpretation_B_in_window": False,
        }
    arr_lo = max(t_arr_search_lo, window_lo - t_post)
    arr_hi = min(t_arr_search_hi, window_hi - t_post)
    feasible = arr_lo <= arr_hi and t_post <= window_hi
    return {
        "t_post_trigger_particle_min": t_post,
        "t_trigger_arrival_min_allowable": arr_lo if feasible else None,
        "t_trigger_arrival_max_allowable": arr_hi if feasible else None,
        "feasible": bool(feasible),
        "interpretation_A": "time from initial reactive-fluid pumping",
        "interpretation_B": "time from activator contact",
        "interpretation_B_in_window": window_lo <= t_post <= window_hi,
        "requires_arbitrary_fixed_30_min": False,
    }


def front_dispersion_still_in_window(
    t_total_min: float,
    sigma_min: float,
    *,
    window_lo: float = WINDOW_LO_MIN,
    window_hi: float = WINDOW_HI_MIN,
) -> dict:
    """Whether t_total ± assumed activator-front sigma stays inside 25-75 min."""
    lo = t_total_min - sigma_min
    hi = t_total_min + sigma_min
    return {
        "sigma_min": sigma_min,
        "t_total_minus_sigma_min": lo,
        "t_total_plus_sigma_min": hi,
        "entire_band_in_window": window_lo <= lo and hi <= window_hi,
        "band_intersects_window": hi >= window_lo and lo <= window_hi,
        "provenance": "ASSUMED_FOR_SENSITIVITY",
    }


def evaluate_chemgate(inp: ChemGateInputs | None = None, *, family: str = FAMILY_CHEMGATE) -> ChemGateResult:
    inp = inp or ChemGateInputs()
    sph = evaluate_sphere(
        inp.diameter_um,
        T_C=inp.temperature_C,
        mode=inp.D_mode,
        empirical_factor=inp.empirical_D_factor,
        partition_K=inp.partition_K,
    )
    t_diff = sph.t_avg_50_s
    t_act = inp.t_activation_s / max(inp.activator_activity, 1e-6)
    t_poly = inp.t_polymerization_s
    t_post = inp.t_partition_s + t_diff + t_act + t_poly
    t_arr = inp.t_trigger_arrival_s
    t_tot = t_arr + t_post
    # If Stage A already contains available activator, cure starts at pumping (t_arr=0).
    stage_a_has_activator = t_arr <= 0.0
    leak = t_post
    premature = stage_a_has_activator and leak < WINDOW_LO_MIN * 60.0
    da_a = damkohler(t_diff, t_act)
    da_p = damkohler(t_diff, t_poly)
    window_status = classify_transform_time_s(t_tot, unknown=True)
    in_window_A = WINDOW_LO_MIN * 60.0 <= t_tot <= WINDOW_HI_MIN * 60.0
    if premature:
        pathway = "NEEDS_TWO_STAGE_DEPLOYMENT"
        status = RequirementStatus.UNKNOWN
    elif in_window_A and inp.D_mode == "lee_ambient":
        pathway = "PLAUSIBLE_CANDIDATE"
        status = RequirementStatus.UNKNOWN
    elif in_window_A:
        pathway = "PLAUSIBLE_WITH_EXTRAPOLATED_D"
        status = RequirementStatus.UNKNOWN
    else:
        pathway = "OUTSIDE_WINDOW_OR_UNCONSTRAINED"
        status = RequirementStatus.UNKNOWN
    env = allowable_trigger_arrival_min(t_post / 60.0)
    notes = (
        f"{family}: operational t_trigger_arrival={t_arr / 60.0:.3g} min "
        f"({TRIGGER_ARRIVAL_TAG}, not material kinetics). "
        f"Modelled t_post_trigger_particle={t_post / 60.0:.3g} min "
        f"= partition {inp.t_partition_s / 60.0:.3g} (ASSUMED) + diff {t_diff / 60.0:.3g} "
        f"(Lee ambient D analogue unless D_mode={inp.D_mode}) + act {t_act / 60.0:.3g} "
        f"(Suslick analogue) + poly {t_poly / 60.0:.3g} (analogue). "
        f"t_total_after_initial_pumping={t_tot / 60.0:.3g} min (interpretation A). "
        f"t_from_contact={t_post / 60.0:.3g} min (interpretation B). "
        "D899/Cu is analogue/prior art, not a PhaseForge invention. "
        f"pathway={pathway}. NEVER upgraded to PASS without 150 C isothermal data. "
        f"{sph.notes}"
    )
    _ = window_status
    return ChemGateResult(
        family=family,
        t_trigger_arrival_s=t_arr,
        t_trigger_arrival_tag=TRIGGER_ARRIVAL_TAG,
        t_partition_s=inp.t_partition_s,
        t_diff_s=t_diff,
        t_activation_s=t_act,
        t_polymerization_s=t_poly,
        t_post_trigger_particle_s=t_post,
        t_total_after_initial_pumping_s=t_tot,
        t_transform_s=t_tot,
        t_transform_min=t_tot / 60.0,
        t_post_trigger_particle_min=t_post / 60.0,
        t_from_pumping_min=t_tot / 60.0,
        t_from_contact_min=t_post / 60.0,
        t_arr_min_allowable_min=env["t_trigger_arrival_min_allowable"],
        t_arr_max_allowable_min=env["t_trigger_arrival_max_allowable"],
        t_transport_leak_s=leak,
        Da_diff_act=da_a,
        Da_diff_poly=da_p,
        regime=_regime(da_a, da_p),
        status=status,
        pathway=pathway,
        stage_a_activator_present=stage_a_has_activator,
        premature_during_transport=premature,
        notes=notes,
        provenance=Provenance.MODEL_PREDICTION,
    )


def feasibility_map(
    diameters_um: tuple[float, ...] = DIAMETERS_UM,
    activities: tuple[float, ...] = (0.2, 0.5, 1.0, 2.0, 5.0),
    *,
    T_C: float = 150.0,
    D_mode: str = "lee_ambient",
    t_trigger_arrival_s: float = DEFAULT_TRIGGER_ARRIVAL_S,
    quantity: str = "post_trigger",
) -> np.ndarray:
    """Time in minutes, shape (n_activity, n_diameter).

    quantity='post_trigger' is intrinsic after activator contact (no operational delay).
    quantity='total' adds t_trigger_arrival (interpretation A).
    """
    Z = np.empty((len(activities), len(diameters_um)), dtype=float)
    for i, a in enumerate(activities):
        for j, d in enumerate(diameters_um):
            r = evaluate_chemgate(
                ChemGateInputs(
                    diameter_um=d,
                    temperature_C=T_C,
                    D_mode=D_mode,
                    t_trigger_arrival_s=t_trigger_arrival_s,
                    activator_activity=a,
                )
            )
            Z[i, j] = (
                r.t_post_trigger_particle_min if quantity == "post_trigger" else r.t_from_pumping_min
            )
    return Z


def search_plausible_150C(*, n: int = 80, seed: int = 42) -> dict:
    """Engineering-level search over arrival 0-60 min. Does not invent a PASS."""
    rng = np.random.default_rng(seed)
    hits_ambient = 0
    hits_se = 0
    examples: list[dict] = []
    for _ in range(n):
        d = float(rng.choice(DIAMETERS_UM))
        arrival = float(rng.uniform(0.0, TRIGGER_SEARCH_MAX_MIN) * 60.0)
        act = float(rng.choice([0.3, 1.0, 3.0]))
        K = float(rng.choice([0.3, 1.0, 2.0]))
        for mode in ("lee_ambient", "stokes_einstein"):
            r = evaluate_chemgate(
                ChemGateInputs(
                    diameter_um=d,
                    temperature_C=150.0,
                    t_trigger_arrival_s=arrival,
                    activator_activity=act,
                    partition_K=K,
                    D_mode=mode,
                )
            )
            ok = WINDOW_LO_MIN <= r.t_from_pumping_min <= WINDOW_HI_MIN
            if mode == "lee_ambient" and ok:
                hits_ambient += 1
            if mode == "stokes_einstein" and ok:
                hits_se += 1
            if ok and len(examples) < 8:
                examples.append(
                    {
                        "mode": mode,
                        "d_um": d,
                        "t_trigger_arrival_min": arrival / 60.0,
                        "t_post_trigger_particle_min": r.t_post_trigger_particle_min,
                        "t_total_after_initial_pumping_min": r.t_from_pumping_min,
                        "pathway": r.pathway,
                        "regime": r.regime,
                    }
                )
    return {
        "n": n,
        "fraction_in_window_lee_ambient_D": hits_ambient / n,
        "fraction_in_window_stokes_einstein_D": hits_se / n,
        "examples": examples,
        "verdict": (
            "PLAUSIBLE_PATHWAY if Stage-B activator chase is sequenced after Stage-A "
            "placement; 150 C window is modelled not measured; status UNKNOWN not PASS. "
            "t_trigger_arrival is operational, not intrinsic kinetics."
        ),
    }


def trigger_timing_envelope_rows(
    diameters_um: tuple[float, ...] = DIAMETERS_UM,
    *,
    D_modes: tuple[str, ...] = ("lee_ambient", "stokes_einstein"),
    activities: tuple[float, ...] = (1.0,),
    t_arr_min_grid: np.ndarray | None = None,
    T_C: float = 150.0,
) -> list[dict]:
    """Design envelope over t_trigger_arrival = 0-60 min. Not a single 30 min pick."""
    if t_arr_min_grid is None:
        t_arr_min_grid = np.linspace(0.0, TRIGGER_SEARCH_MAX_MIN, 13)
    rows: list[dict] = []
    for mode in D_modes:
        for act in activities:
            for d in diameters_um:
                base = evaluate_chemgate(
                    ChemGateInputs(
                        diameter_um=d,
                        temperature_C=T_C,
                        D_mode=mode,
                        t_trigger_arrival_s=0.0,
                        activator_activity=act,
                    )
                )
                env = allowable_trigger_arrival_min(base.t_post_trigger_particle_min)
                for t_arr in t_arr_min_grid:
                    r = evaluate_chemgate(
                        ChemGateInputs(
                            diameter_um=d,
                            temperature_C=T_C,
                            D_mode=mode,
                            t_trigger_arrival_s=float(t_arr) * 60.0,
                            activator_activity=act,
                        )
                    )
                    disp = [
                        front_dispersion_still_in_window(r.t_from_pumping_min, sig)
                        for sig in FRONT_DISPERSION_SIGMA_MIN
                    ]
                    rows.append(
                        {
                            "diameter_um": d,
                            "D_mode": mode,
                            "diffusion_model": mode,
                            "activator_activity": act,
                            "temperature_C": T_C,
                            "t_partition_min": r.t_partition_s / 60.0,
                            "t_diffusion_min": r.t_diff_s / 60.0 if np.isfinite(r.t_diff_s) else None,
                            "t_activation_min": r.t_activation_s / 60.0,
                            "t_polymerization_min": r.t_polymerization_s / 60.0,
                            "t_post_trigger_particle_min": r.t_post_trigger_particle_min,
                            "t_trigger_arrival_min": t_arr,
                            "t_trigger_arrival_tag": TRIGGER_ARRIVAL_TAG,
                            "t_total_after_initial_pumping_min": r.t_from_pumping_min,
                            "in_challenge_window_from_pumping": (
                                WINDOW_LO_MIN <= r.t_from_pumping_min <= WINDOW_HI_MIN
                            ),
                            "in_window_from_contact": (
                                WINDOW_LO_MIN <= r.t_post_trigger_particle_min <= WINDOW_HI_MIN
                            ),
                            "t_arr_min_allowable_min": env["t_trigger_arrival_min_allowable"],
                            "t_arr_max_allowable_min": env["t_trigger_arrival_max_allowable"],
                            "envelope_feasible": env["feasible"],
                            "status": r.status.value,
                            "pathway": r.pathway,
                            "uncertainty": (
                                "Lee D is ambient; partition/activation/poly are analogue/"
                                "ASSUMED; trigger arrival is operational "
                                f"{TRIGGER_ARRIVAL_TAG}; front dispersion "
                                "ASSUMED_FOR_SENSITIVITY ±5/10/15 min."
                            ),
                            "dispersion_5min_entire_band_in_window": disp[0]["entire_band_in_window"],
                            "dispersion_10min_entire_band_in_window": disp[1]["entire_band_in_window"],
                            "dispersion_15min_entire_band_in_window": disp[2]["entire_band_in_window"],
                        }
                    )
    return rows


def envelope_summary(
    diameters_um: tuple[float, ...] = DIAMETERS_UM,
    *,
    D_mode: str = "lee_ambient",
    activator_activity: float = 1.0,
    T_C: float = 150.0,
) -> dict:
    """Per-diameter allowable Stage-B arrival windows at nominal activity."""
    per: list[dict] = []
    posts: list[float] = []
    for d in diameters_um:
        r = evaluate_chemgate(
            ChemGateInputs(
                diameter_um=d,
                temperature_C=T_C,
                D_mode=D_mode,
                t_trigger_arrival_s=0.0,
                activator_activity=activator_activity,
            )
        )
        env = allowable_trigger_arrival_min(r.t_post_trigger_particle_min)
        posts.append(r.t_post_trigger_particle_min)
        per.append(
            {
                "diameter_um": d,
                "t_post_trigger_particle_min": r.t_post_trigger_particle_min,
                "t_trigger_arrival_min_allowable": env["t_trigger_arrival_min_allowable"],
                "t_trigger_arrival_max_allowable": env["t_trigger_arrival_max_allowable"],
                "feasible": env["feasible"],
                "interpretation_B_in_window": env["interpretation_B_in_window"],
                "D_mode": D_mode,
            }
        )
    nom = evaluate_chemgate(
        ChemGateInputs(diameter_um=270.0, temperature_C=T_C, D_mode=D_mode, activator_activity=activator_activity)
    )
    feasible = [p for p in per if p["feasible"]]
    return {
        "D_mode": D_mode,
        "activator_activity": activator_activity,
        "post_trigger_cure_min_range": (
            [float(np.nanmin(posts)), float(np.nanmax(posts))] if posts else [None, None]
        ),
        "nominal_270um": {
            "t_post_trigger_particle_min": nom.t_post_trigger_particle_min,
            "t_trigger_arrival_min_scenario": nom.t_trigger_arrival_s / 60.0,
            "t_trigger_arrival_tag": TRIGGER_ARRIVAL_TAG,
            "t_total_after_initial_pumping_min": nom.t_from_pumping_min,
            "t_arr_min_allowable_min": nom.t_arr_min_allowable_min,
            "t_arr_max_allowable_min": nom.t_arr_max_allowable_min,
            "requires_arbitrary_fixed_30_min": False,
        },
        "allowable_arrival_across_feasible_diameters_min": {
            "min": (
                min(p["t_trigger_arrival_min_allowable"] for p in feasible) if feasible else None
            ),
            "max": (
                max(p["t_trigger_arrival_max_allowable"] for p in feasible) if feasible else None
            ),
        },
        "per_diameter": per,
        "requires_arbitrary_fixed_30_min": False,
        "status": "UNKNOWN",
    }


def t_shell_vs_coalescence(
    diameter_um: float,
    coalescence_time_s: float,
    D: float = D_LEE2025_M2_S,
) -> dict:
    """Hypothesis: surface gel vs collision time. Not a proven non-agglomeration claim."""
    R = um_to_m(diameter_um) / 2.0
    # Fo~0.01: thin surface layer (order 0.1 R).
    t_shell = 0.01 * R**2 / max(D, 1e-30)
    return {
        "diameter_um": diameter_um,
        "t_shell_s": t_shell,
        "t_coalescence_s": coalescence_time_s,
        "shell_faster": t_shell < coalescence_time_s,
        "notes": (
            "Hypothesis only: if t_shell < t_collision after activator contact, "
            "surface-first cure may reduce coalescence. Not experimental proof."
        ),
    }
