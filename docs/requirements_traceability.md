# Requirements traceability matrix

Machine-generated from `scripts/reproduce_all.py`. Status is computational
and analogue-based. This project did **not** physically perform experiments.

| ID | Model/evidence | Predicted | Status | Confidence | Remaining validation |
|---|---|---|---|---|---|
| R01_liquid_delivery | baseline concept + viscosity | liquid emulsion, no solids injected - | **PASS** | high (by design; analogue Chen 2023) | Confirm no premature solids at mix temperature. |
| R02_viscosity | Taylor/Pal emulsion viscosity | 0.64 (nominal 60 C) cP | **PASS** | medium-high at 20-80 C; DCPD 1 cP is published | Measure emulsion viscosity of the actual stabilizer package. |
| R03_transport_temperature | kinetics + mechanics at T | models evaluated to 150 C degC | **UNKNOWN** | low at 150 C | Isothermal latency and strength at 150 C. |
| R04_transport_pressure | literature liquids + coupled notes | 10000 psi = 68.95 MPa; liquids remain liquid psi | **UNKNOWN** | low (pressure effect on ROMP not retrieved as a quantitative rate law) | HPHT rheology and cure under 10,000 psi. |
| R05_post_transform_pressure | mechanics | 6000 psi = 41.369 MPa psi | **PASS** | medium at 60 C; low at 150 C | Particle crush at temperature and 6000 psi. |
| R06_controlled_activation | latent ROMP kinetics | temperature + inhibitor index - | **PASS** | medium (published latency analogues) | Programmed delay in brine-dispersed droplets. |
| R07_transformation_window | Arrhenius t_solid | 78.4 min nominal; HPHT 1.6 min min | **MARGINAL** | medium in 40-80 C; low/UNKNOWN at 150 C | Droplet-scale conversion in water at target T. |
| R08_discrete_particles | phi isolation + Della Martina analogue | phi=0.85 continuous; discrete if phi<0.55 - | **PASS** | medium (analogue beads; not PhaseForge experiments) | Morphology after cure in brine. |
| R09_particle_size | Hinze/Grace | 273 um | **PASS** | medium (order-of-magnitude; correlation uncertainty) | Measure d32 vs shear for the actual IFT. |
| R10_sphericity | interfacial energy + analogue | near-spherical expected if IFT-stabilized - | **MARGINAL** | medium analogue, not measured here | Image analysis of cured particles. |
| R11_minimal_adhesion | coalescence risk score | 0.27 risk 0-1 | **PASS** | low | Cure in contact; sticky-window mapping. |
| R12_load_bearing | mechanics SF | SF=1.41 at nominal T - | **PASS** | medium at T<<Tg; UNKNOWN near Tg | Single-particle crush vs T. |
| R13_compressive_integrity | SF_mech vs 4500-6000 psi | SF=1.41 (nom); HPHT SF=0.33 dimensionless | **PASS** | low at 150 C | 6000 psi crush at 150 C. |
| R14_remain_distributed | liquid-liquid placement analogue | liquids can enter branches (Chen analogue) - | **MARGINAL** | low-medium | Flow-loop placement and post-cure distribution. |
| R15_open_pathways | permeability / packing | porosity=0.85 - | **PASS** | medium if discrete; FAIL if bulk gel | Conductivity cell after in-situ formation. |
| R16_flow_through_around | k_rel | 0.739 relative | **PASS** | medium | Measured conductivity vs closure. |
| R17_no_bulk_gel | isolated droplet hypothesis | PASS only if droplets remain isolated until solid - | **MARGINAL** | low-medium | Visual bulk-gel vs bead formation tests. |
