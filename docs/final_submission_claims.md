# Final submission claims

This file is the claim-control sheet for the Innocentive write-up.
No laboratory experiments were performed on the exact PhaseForge fluid in this repository.

## SAFE TO CLAIM

- This package is a **TRL-3-oriented analytical/computational proof-of-concept** with literature analogues, SI units, provenance tags, tests, and a requirements matrix.
- **Integrated PhaseForge is a TRL 2–3 candidate requiring targeted experimental confirmation.**
- DCPD monomer viscosity is **1.0 cP at 20 °C** (Madbouly 2025).
- Published Grubbs-II / DCPD gel times in the **40–60 °C** window, with **Ea ≈ 79.3 kJ/mol**, are experimental literature (Madbouly 2025).
- Phosphite can delay bulk DCPD ROMP at **50 °C** (Hu 2018: 5.98 min uninhibited vs 38.5 min with TPP). The same inhibited formulation gels in **about 2 min at 80 °C**.
- Chen 2023 (epoxy ISP analogue) formed spherical particles from a liquid–liquid mixture; size sorting improved with shear; crush behaviour was reported for that epoxy system.
- Della Martina 2005 polymerized DCPD droplets as **microreactors** into beads.
- Unreinforced pDCPD compressive strength **≈ 78 MPa at room temperature** (PMC12566568).
- Typical crosslinked pDCPD **Tg ≈ 140–165 °C** (Kovacic & Slugovc 2020).
- Elser 2018 and Momin 2021 report **tunable DSC onsets** for Mo imido alkylidene NHC / DCPD systems (approximately **65–140 °C** and **52–142 °C**).
- US11377580B2 Table 3 reports **patent experimental** compression yield strengths at RT and **98 °C** for delayed DCPD formulations (see analogue section below).
- For the **Ru/Grubbs + phosphite** Arrhenius branch used here: **moderate temperature is a feasible candidate window**; **150 °C kinetics FAIL** the 25–75 min hold (predicted solidification on the order of **2 min**, not 25–75 min). Mechanical status at 150 °C is **UNKNOWN**.
- Predicted emulsion viscosity at the YAML nominal point is **approximately 0.50–0.90 cP** depending on T and φ, below 10 cP.
- Hinze/Grace with an assumed dissipation structure predicts a characteristic cured size of **approximately 270 μm nominal**, with a **sensitivity range** (see `results/tables/diameter_sensitivity.csv`) rather than a 12-digit micrometre value.

## CLAIM WITH QUALIFICATION

Use the words **predicted**, **analogue**, **candidate**, or **approximately**:

- **Predicted** Taylor/Pal emulsion viscosity of a DCPD-in-brine analogue at φ ≈ 0.1–0.2 is below 10 cP.
- **Predicted** transformation time can be tuned into 25–75 min at **approximately 50–70 °C** by an engineering inhibitor index calibrated to Hu 2018 magnitude, not a molar recipe.
- **Predicted** particle diameter **approximately 270 μm** (robust range typically **about 100–500 μm** under the Hinze C / dissipation / IFT / shear sweeps). Do not quote 273.046 μm.
- **Analogue** liquid-to-particle ISP morphology: Chen / Bai / Yang epoxy or modified-resin systems, not PhaseForge.
- **Analogue** DCPD droplet polymerization: Della Martina beads; not HPHT fracturing.
- **Analogue** tunable ROMP latency: Hu phosphite; Kordes/Buchmeiser latent precatalysts.
- **Analogue** high-temperature latent catalyst **onset**: Elser 2018 / Momin 2021 DSC windows. These onsets are **not** 25–75 min isothermal latency at 150 °C.
- **Analogue** RT mechanical strength: 78 MPa pDCPD coupon; particle vs bulk discount is assumed.
- **Analogue** 98 °C strength: US11377580B2 Table 3 bulk yield **about 33–50 MPa** depending on formulation (some below 41 MPa / 6000 psi).
- **Analogue** residual flow/conductivity: Chen conductivity cells; PhaseForge `k_rel` is **relative to an assumed k_open = 1e-8 m²**, not measured fracture conductivity.
- Coalescence **risk score** is a comparative optimization metric (**ASSUMED_FOR_SENSITIVITY**). Heuristic low risk is **MARGINAL**, not a hard agglomeration PASS.
- Monte Carlo simultaneous-compliance probabilities (n = 400) should be quoted to **about 2 significant digits**.
- **PhaseForge-ChemGate** (primary high-T framing): chemically gated microreactor droplets. Lee 2024/2025 demonstrate high-T latency of D899 until Cu(I) and aqueous-to-organic activator diffusion. **Not our invention.** 25–75 min at 150 °C is modelled.
- Kordes 2024: hexacoordinated Mo NHC **does not polymerize DCPD up to ~150 °C**.
- Zhan 2024: sequential crosslinking can raise pDCPD-family Tg above 150 °C (**analogue**, not crush data).
- R03: a 70 °C candidate does **not** automatically satisfy operation up to approximately 150 °C. Upper-temperature capability of **exact PhaseForge = UNKNOWN**.

## DO NOT CLAIM

- Do not claim experimentally demonstrated by us
- Do not claim TRL 3 achieved
- Do not claim the full 150 C requirement is solved
- Do not claim proven non-agglomeration
- Do not claim measured PhaseForge fracture conductivity
- Do not claim patent novelty or freedom to operate
- Do not present k_rel as experimental or field conductivity
- Do not treat DSC T_onset as a 25-75 min isothermal hold at 150 C
- Do not treat an assumed 2000x latency multiplier as a published 150 C gel time
- Do not report GitHub Actions success unless Actions actually reports success
- Do not claim “PhaseForge works at 150 °C”
- Do not claim D899, Cu activation, or patented Mo complexes as our IP
- Do not treat Lee 2025 D as a 150 °C measurement
