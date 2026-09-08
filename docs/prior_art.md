# Prior art and differentiation (not legal advice)

This is a technical landscape map for a computational proof-of-concept. It is **not** a freedom-to-operate opinion and not legal advice.

## Landscape

| Class | What it is | Overlap with PhaseForge | Differentiation that might actually matter |
|---|---|---|---|
| Generic in-situ generated proppants (ISP) | Liquid injected, solids form downhole | Same job-to-be-done | PhaseForge specifies isolated droplet microreactors + ≤10 cP + 25–75 min delay + 70–600 μm as a **coupled** envelope |
| Temperature-triggered phase-change resins | Epoxy / vinyl / polyester PCL + NPCL | Strong analogue (Chen, Bai, Yang) | Those systems often have μ ~ 20–80 mPa s, above 10 cP |
| Styrene-based ISP | Polymerizing styrene droplets | Same dispersion idea | Different chemistry, VOC/toxicity, Tg/strength profile; not modelled as primary here |
| Epoxy systems | Chen 2022/2023 LSPCAP | Particle size by shear; spherical; crush data | Viscosity and chemistry differ; epoxy is the **comparison** candidate |
| DCPD/TriCPD downhole ROMP | US11377580B2 and Hu JPSE | **High overlap** on monomer family, latent phosphite, in-situ polymer, fracturing pillars | Patent emphasizes **pillars/plugs/lost circulation** and sequential polymerizable-composition + spacer stages more than a surfactant-stabilized **microparticle** size window |
| pDCPD suspension beads | Della Martina 2005 | Droplets as microreactors | Lab beads, not HPHT fracturing fluid; often porogen/extraction |
| Delayed ROMP catalysts | Kordes/Buchmeiser latent Mo/Ru | Latency toolkit | Not demonstrated as brine-dispersed 70–600 μm particles at 150 °C |
| PhaseForge-HT-Thermal Mo NHC | Kordes 2024; Elser 2018; Momin 2021 | No DCPD polymerization up to ~150 °C (Kordes); DSC onsets ~52–142 °C | Thermal trigger is >150 °C; 25–75 min at exactly 150 °C UNKNOWN |
| Chemically gated DCPD ROMP | Lee 2024/2025 D899 + aqueous Cu(I); Suslick 2022 | **Strongest high-T analogue**: latency independent of ~200 °C front; aqueous→organic diffusion activation | **Prior art / high IP risk** if copied. PhaseForge uses the **architecture**, not their recipe |
| Acid-latent Ru | Samec 2010; Monsaert 2010 | Chemical unmasking | No 150 °C evidence retrieved |

## US11377580B2 — flag, do not ignore

The patent (Schlumberger) covers methods of introducing a polymerizable polycyclic composition (including DCPD and DCPD/TriCPD) with a catalyst into a subterranean formation and polymerizing in situ to form high-Tg polymer, including fracturing treatments that generate **solid polymer pillars** with Tg at least 200 °F, emulsions/foams/slurries, and phosphite-modified latency.

**Strong overlap:** DCPD/TriCPD + ROMP + downhole + delayed gel + load-bearing polymer in fractures.

Table 3 analogue (patent experimental examples, **not** PhaseForge measurements): at a 50 °C reaction condition, no phosphite ≈ 88 MPa RT / 47 MPa at 98 °C; phosphite:M2 ≈ 1:1 ≈ 82 MPa RT / 50 MPa at 98 °C; at 80 °C one delayed formulation ≈ 73 MPa RT / 33 MPa at 98 °C (other formulations lower at high T). 70/30 DCPD/TriCPD is reported stronger than pure pDCPD at RT and 98 °C. 33 MPa is below 41 MPa (6000 psi).

**Plausible technical distinctions (still not a legal conclusion):**

- Explicit **microparticle** specification 70–600 μm with **minimal agglomeration**, versus pillar/cluster morphology controlled by pumping stages.
- **Aqueous continuous phase as the majority delivery fluid** with organic **microreactors**, aiming at μ_eff ≤ 10 cP, versus resin stages that may be closer to monomer viscosity control by solvents (benzoate ester mentioned in the patent).
- Coupled probabilistic compliance envelope (viscosity × delay × size × residual permeability) as an engineering object.

Combining two known ideas (ISP emulsions + DCPD ROMP) is **not** automatically novel. Any submission should treat US11377580B2 and related family members as the primary IP risk and should not claim exclusive invention of downhole DCPD ROMP.

## Chen / Bai / Yang analogue

These papers already demonstrate the **challenge morphology**: liquid–liquid dispersion → spherical particles → crush/conductivity. They are the reason PhaseForge can argue particle formation is physically plausible. They are also why “we thought of in-situ proppant” is not a differentiator.

PhaseForge’s computational case vs those analogues is:

- **Viscosity headroom** (DCPD ~1 cP vs epoxy PCL 33–80 mPa s).
- **Latency chemistry** that is ROMP-specific (phosphite / latent Mo), not tertiary-amine epoxy accelerants.
- **Honesty that 150 °C latency and Tg-limited strength are not closed.**

## Della Martina beads

Supports the microreactor picture: a stabilized DCPD droplet can polymerize as an individual particle. It does **not** demonstrate HPHT transport, 10,000 psi, or 6,000 psi crush of dense (non-macroporous) beads.

## Recommended language

Use: “computationally validated against published experimental analogues” and “TRL-3 candidate requiring targeted laboratory confirmation.”

Do **not** use: “we experimentally demonstrated PhaseForge,” “TRL 3 achieved,” or “patentably unique because we combined droplets with DCPD.”
