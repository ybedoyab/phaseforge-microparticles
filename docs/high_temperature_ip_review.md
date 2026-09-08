# High-temperature IP review (not legal advice)

This is a **technical landscape map** for challenge submission hygiene. It is **not** a freedom-to-operate opinion, not legal advice, and not a novelty opinion.

The challenge agreement prohibits submitting third-party-controlled technology as though it is ours. **D899, Cu(I) transmetalation activation, patented Mo NHC complexes, and any proprietary latent metathesis package are not PhaseForge inventions.**

## Classification

| Technology | Role in this repo | Classification | Notes |
|---|---|---|---|
| D899 bis-NHC Ru | ChemGate **analogue** | published prior art; **high IP risk** if copied as the recipe | Lee 2024/2025; Suslick 2022 FROMP dual-component. Commercial Umicore D899 |
| Cu(I) activation of latent Ru (NHC transmetalation) | Mechanism analogue | **patent/patent-family found**; **high IP risk** | US12338310 B2 (Apeiron, 2025): Cu/Ru complexes with organic ligands activating latent Ru ROMP; gel times seconds–hours. US11820839 and related latent-metathesis families also exist |
| Aqueous activator diffusion into DCPD-family organic phase | Physical architecture analogue | published prior art (Lee 2025 EMB3D activating bath) | Usable as **experimental validation of the architecture**, not as a copied ink/bath formulation |
| Hexacoordinated Mo NHC latent DCPD (Kordes/Buchmeiser) | HT-Thermal analogue | published + likely **patent/patent-family** on Mo NHC metathesis | Transport stability to 150 °C is literature; not our catalyst |
| Acid-triggered latent Ru (picolinate / Schiff base) | ChemGate-Acid analogue | published prior art (Samec 2010; Monsaert 2010); patent status **unknown** here | Do not claim as ours |
| Downhole DCPD/TriCPD ROMP | Overlap with RuP/HT | **patent found** US11377580B2 (Schlumberger) | Pillars/plugs/high-Tg polymer in fractures. Primary downhole ROMP IP risk |
| DCPD/TCPD physical properties | High-Tg analogue | patent/manufacturer/prior art (US4703098, US4751337) **not** peer-reviewed experiments | Tag PATENT for physical-property support |
| Isolated droplet microreactors + delayed **chemical** activator in brine + 70–600 μm + ≤10 cP | Proposed **system-level** differentiation | **possible system-level differentiation**; FTO **unknown** | Combining published pieces is not automatically novel or free to operate |
| Exact PhaseForge formulation | Not specified as a molar recipe | **patent status unknown** | Engineering-level parameters only in this repo |

## Search notes (2026-09-08)

Queries covered: D899 / bis-NHC Ru latent ROMP; Cu(I)-activated D899; aqueous activator diffusion into DCPD; high-temperature latent metathesis; chemically triggered downhole polymerization; microparticle/proppant applications. Sources: publisher pages, NSF PAR, OSTI, Google Patents / USPTO gazette snippets. SEO blogs were not used.

**US12338310** (granted 2025-06-24, Apeiron Synthesis): method of activating olefin-metathesis Ru precatalysts with Cu complexes having organic ligands (and certain Ru complexes). Explicitly aimed at ROMP gel/cure control from seconds to hours. **Exact D899/Cu is strongly patent-touched.**

## Deployable-implementation rule

If the exact D899/Cu mechanism is strongly patent-controlled, use it in this package **only as experimental validation of the broader physical architecture**. A deployable implementation would require an **unencumbered or licensed** latent-catalyst / activator pair. This repository does **not** select that pair.

## Submission language

Allowed: “chemically gated latent metathesis in isolated droplets; aqueous activator after placement; diffusion-programmed delay.”

Not allowed: “our D899/Cu system,” “we invented Cu transmetalation activation,” “we own the Mo NHC precatalyst.”
