# 150 °C decision tree

Computational / analogue statuses. **UNKNOWN is better than a fabricated PASS.** Ru/phosphite was **not** retuned to force a high-T window.

## Ru/phosphite (`PhaseForge-RuP`)

- Transport viscosity: PASS candidate (DCPD ~1 cP; emulsion modelled ≤10 cP)
- Latency at 150 °C: **FAIL** (Arrhenius t_solid ≈ 1.6 min using Madbouly Ea; Hu already ~2 min at 80 °C)
- Activation at 150 °C: too fast to be a hold
- Mechanical: **UNKNOWN** (150 °C near conventional pDCPD Tg)
- Overall: **FAIL**

## Mo thermal (`PhaseForge-HT-Thermal`)

- Transport stability: **SUPPORTED analogue** — Kordes 2024 hexacoordinated Mo(VI) imido alkylidene NHC **does not polymerize DCPD up to ~150 °C** (long pot life)
- Activation exactly at 150 °C into 25–75 min: **UNKNOWN** (thermal activation reported **above** 150 °C; full conversion on heating to ~175 °C / 150 mol-ppm)
- Mechanical: UNKNOWN (no 150 °C particle crush)
- Overall: **UNKNOWN**

## ChemGate D899/Cu analogue (`PhaseForge-ChemGate`) — primary high-T branch

- Thermal latency: **SUPPORTED by high-T prior art** (Lee 2024: D899 dormant through frontal polymerization ~200 °C until Cu(I); thermal treatment alone does not activate)
- Aqueous-to-organic activation: **SUPPORTED by Lee 2025** (Cu(I) in aqueous/activating bath diffuses into organic DCPD-family ink; surface-to-core cure; D ≈ 6×10⁻⁸ cm²/s from 20–30 min film growth; filaments <~400 μm fully cured in ≥~20 min)
- 25–75 min at 150 °C: **MODELLED / UNKNOWN**. This is **not** an intrinsic ~60 min chemical delay. Interpretation B (from activator contact) is a modelled **approximately 27–35 min** post-trigger sequence (≈29 min at 270 μm, Lee ambient D). Interpretation A (from initial pumping) adds operational `t_trigger_arrival` (`ASSUMED_FOR_DEPLOYMENT_SCENARIO`). Searching arrival over **0–60 min** gives a feasible Stage-B window of **approximately 0–46 min** at 270 μm so that total remains in 25–75 min. A default 30 min placement scenario is optional, not required. Stokes–Einstein 150 °C scaling makes diffusion **faster**. Shell-impeded D can add delay. **Not an experiment.**
- Mechanical: UNKNOWN crush at 150 °C. Narrative: 150 °C is near Tg of conventional pDCPD but **below Tg of several demonstrated high-Tg pDCPD-family networks** (Zhan 2024 sequential crosslinking Tg ~191–216 °C; TCPD copolymers — viscosity of high-TCPD liquids **UNKNOWN**)
- Overall: **UNKNOWN / PLAUSIBLE_CANDIDATE** (never PASS without 150 °C isothermal data)

Safe wording:

> PhaseForge-ChemGate removes the intrinsic high-temperature kinetic conflict of the Ru/phosphite branch by using a chemically gated latent catalyst in a two-stage deployment: Stage A places latent-catalyst droplets without available activator; Stage B is an aqueous activator chase. High-temperature catalyst latency and aqueous-to-organic chemical activation have been demonstrated independently in closely related DCPD systems. In the nominal deployment scenario, approximately 30 min of controlled Stage-B trigger arrival (`ASSUMED_FOR_DEPLOYMENT_SCENARIO`, not material kinetics) is followed by a modelled approximately 29 min post-trigger partition/diffusion/activation/cure sequence at 270 μm (Lee ambient D analogue). The 25–75 min window from initial pumping is a design envelope over Stage-B arrival (approximately 0–46 min at 270 μm), not a single intrinsic delay. Exact 150 °C transformation remains a model prediction requiring laboratory validation.

Do **not** write “PhaseForge works at 150 °C.”

## ChemGate acid (`PhaseForge-ChemGate-Acid`)

- Samec/Keitz/Grubbs 2010: 18e picolinate Ru inactive until HCl; used to mix DCPD before initiation
- Monsaert 2010: Schiff-base Ru latent in DCPD for ≥12 months; HCl activation
- 150 °C isothermal window: **not retrieved**
- Overall: **UNKNOWN** (exploratory secondary route)

## Strongest architecture for submission framing

**PhaseForge: chemically gated microreactor droplets**, with Ru/phosphite retained as the **lower-temperature reference / negative control at 150 °C**.

This is a **system-level** proposal. Exact catalyst/activator identities are subject to IP review (`docs/high_temperature_ip_review.md`). D899/Cu must not be submitted as our invention.
