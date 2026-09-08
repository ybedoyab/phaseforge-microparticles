# Scientific basis

This document separates (1) experimentally demonstrated by **prior literature**, (2) calculated here, (3) predicted here, and (4) unresolved.

No PhaseForge laboratory campaign was performed in this repository.

## 1. Mechanism (proposed)

A low-viscosity aqueous continuous phase carries DCPD-rich or DCPD/TriCPD-rich droplets. Droplets are the intended microreactors: ROMP and crosslinking stay inside each drop. After a thermally programmed delay, drops solidify into discrete pDCPD-family microparticles that prop a gap while leaving continuous-phase pathways.

This is a **proposed** integration of known pieces, not a photographed experiment.

## 2. Enabling chemistry demonstrated by others

| Piece | What was shown | Source | Access in this project |
|---|---|---|---|
| Liquid → discrete solid particles from an emulsified resin | Epoxy PCL + surfactant water; shear controls size; crush 3.56–8.42%; conductivity vs sand/ceramsite at 10–30 MPa | Chen et al., ACS Omega 2023 | Full OA text |
| ISP viscosity / 80 °C / ~20 min | ~30 mPa s, 80 °C, 20 min | Chen et al., Energies 2022 | OA |
| DCPD monomer viscosity 1.0 cP at 20 °C | Enables ≤10 cP emulsions at moderate φ | Madbouly et al., ACS Omega 2025 | OA |
| Arrhenius gel times, Ea = 79.3 ± 1.0 kJ/mol | t_gel 19.7 min at 55 °C, 0.04 wt% G2; 70→10 min at 50 °C for 0.04→0.12 wt% | Madbouly 2025 | OA |
| Phosphite latency | t_gel 5.98 → 38.5 min at 50 °C; ~2 min at 80 °C | Hu et al., JPSE 2019 | HTML snippet |
| Downhole DCPD/TriCPD ROMP, high Tg claims, TtP | TtP ~1 h at 30 °C, ~10 min at 50 °C; pillars Tg ≥ 200 °F | US11377580B2 | Patent text |
| Latent ROMP precatalysts | ~1 h RT latency with PPh3; Mo NHC T_onset 65–140 °C (DSC) | Kordes 2024; Elser 2018 | Abstract/snippet |
| pDCPD beads as droplet microreactors | Suspension polymerization; droplets as microreactors | Della Martina et al. 2005 | Abstract |
| pDCPD Tg typically 140–165 °C | Review | Kovacic & Slugovc 2020 | HTML |
| Unreinforced pDCPD compressive 78 MPa at ~23 °C | Coupon compression | PMC12566568 | OA |
| DCPD-modified resin 95 MPa; IFT 3.2–4.5 mN/m | Phase-change fluid | Yang 2026 | Abstract |
| Phenolic epoxy vinyl ISP, 4–30 min, sphericity ≥ 0.9 | Bai 2025 | Abstract |

Liang et al. 2025 (DOI 10.1016/j.geoen.2025.213998) is **cited as a bibliographic record only**. Full text was not retrieved; no numbers from that paper are used.

## 3. Calculated / predicted in this repository

- SI conversions (4500 psi = 31.03 MPa; 6000 psi = 41.37 MPa).
- Emulsion μ_eff(T, φ) via Taylor/Pal.
- t_gel(T, catalyst, inhibitor) by Arrhenius; t_solid = 1.8 t_gel.
- Hinze/Grace characteristic diameters.
- Lumped droplet energy balance.
- SF_mech(T) with Tg-based derating.
- Pack porosity / relative permeability.
- Coupled PASS/MARGINAL/FAIL/UNKNOWN envelope and UQ.

## 4. Unresolved (require laboratory validation)

- Isothermal gel/solidification time of a **water-dispersed** latent DCPD droplet at 90–150 °C.
- Catalyst poisoning by brine, oxygen, sulfur, or surfactant.
- Particle compressive strength at 150 °C and 6,000 psi.
- Sticky-cure agglomeration.
- Pressure (10,000 psi) effects on latency.
- Exact IFT of a field-compatible stabilizer package.

## 5. Why DCPD-rich droplets vs epoxy ISP as the primary candidate

Chen-type epoxy mixtures are the strongest **particle-formation analogue**, but published viscosities (30–80 mPa s) sit **above** the 10 cP challenge threshold unless heavily diluted. DCPD at 1 cP is the viscosity reason to prefer PhaseForge computationally. That preference is **not** experimental proof that PhaseForge particles match Chen crush performance at 69 MPa.

## 6. The 150 °C problem (central)

Madbouly’s Ea and 55 °C anchor imply uninhibited t_gel on the order of **seconds** at 150 °C. Hu’s inhibited system is already ~2 min at 80 °C. Therefore a 25–75 min window at 150 °C is **not** supported by published Ru/phosphite isothermal data. Highly latent Mo NHC catalysts have DSC onsets up to 140 °C; that is **not** the same as a 50 min isothermal hold at 150 °C. The HPHT point is FAIL or UNKNOWN, not PASS.
