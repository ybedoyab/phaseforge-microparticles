# Requirements traceability matrix

Machine-generated from `scripts/reproduce_all.py`. Status is computational
and analogue-based. This project did **not** physically perform experiments.

| ID | Model/evidence | Predicted | Status | Confidence | Remaining validation |
|---|---|---|---|---|---|
| R01_liquid_delivery | baseline concept + viscosity | liquid emulsion, no solids injected - | **PASS** | high (by design; analogue Chen 2023) | Confirm no premature solids at mix temperature. |
| R02_viscosity | Taylor/Pal emulsion viscosity | approximately 0.64 (nominal 60 C) cP | **PASS** | medium-high at 20-80 C; DCPD 1 cP is published | Measure emulsion viscosity of the actual stabilizer package. |
| R03_transport_temperature | upper-T capability of exact PhaseForge | moderate-T branch shows mechanism feasibility; PhaseForge-HT is the proposed 150 C pathway; DSC onset is not isothermal 25-75 min degC | **UNKNOWN** | low at 150 C for exact PhaseForge; published Mo DSC onsets 52-142 C are not a hold-time proof | Isothermal latency of the exact brine-dispersed fluid at 150 C. |
| R04_transport_pressure | literature liquids + coupled notes | 10000 psi = 68.95 MPa; liquids remain liquid psi | **UNKNOWN** | low (pressure effect on ROMP not retrieved as a quantitative rate law) | HPHT rheology and cure under 10,000 psi. |
| R05_post_transform_pressure | mechanics (temperature-qualified) | 6000 psi = 41.4 MPa; moderate-T PASS; 150 C UNKNOWN psi | **UNKNOWN** | medium at 60 C; UNKNOWN at 150 C | Particle crush at temperature and 6000 psi. |
| R06_controlled_activation | latent ROMP kinetics | temperature + inhibitor index - | **PASS** | medium (published latency analogues) | Programmed delay in brine-dispersed droplets. |
| R07_transformation_window | Arrhenius t_solid (Ru/phosphite) | approximately 78.0 min nominal; HPHT approximately 1.6 min FAIL min | **MARGINAL** | medium in 40-80 C; FAIL at 150 C for published Ru/phosphite | Droplet-scale conversion in water at target T. |
| R08_discrete_particles | phi isolation + Della Martina analogue | phi=0.85 continuous; discrete if phi<0.55 - | **PASS** | medium (analogue beads; not PhaseForge experiments) | Morphology after cure in brine. |
| R09_particle_size | Hinze/Grace with dissipation sensitivity | approximately 270 um nominal (robust range in diameter_sensitivity.csv) um | **PASS** | medium (order-of-magnitude; assumed dissipation structure) | Measure d32 vs shear for the actual IFT. |
| R10_sphericity | interfacial energy + analogue | near-spherical expected if IFT-stabilized - | **MARGINAL** | medium analogue, not measured here | Image analysis of cured particles. |
| R11_minimal_adhesion | coalescence_risk_score heuristic (ASSUMED_FOR_SENSITIVITY) | score approximately 0.27; heuristic cannot independently PASS risk 0-1 | **MARGINAL** | low (no PhaseForge adhesion test) | Cure in contact; sticky-window mapping. |
| R12_load_bearing | mechanics SF at moderate T (PASS candidate) | SF approximately 1.4 at nominal T - | **PASS** | medium at T≪Tg; UNKNOWN near Tg | Single-particle crush vs T. |
| R13_compressive_integrity | temperature-qualified SF vs 4500-6000 psi | moderate T: PASS candidate (SF approximately 1.4); 98 C analogue bulk 33-50 MPa → MARGINAL; 150 C: UNKNOWN dimensionless | **UNKNOWN** | low at 150 C; analogue only at 98 C | 6000 psi crush at 150 C on actual particles. |
| R14_remain_distributed | liquid-liquid placement analogue | liquids can enter branches (Chen analogue) - | **MARGINAL** | low-medium | Flow-loop placement and post-cure distribution. |
| R15_open_pathways | A geometric connectivity; B analytical k; C unvalidated conductivity | A connected=True; porosity approximately 0.85; C=UNVALIDATED_UNDER_CLOSURE - | **MARGINAL** | MARGINAL until CFD/experiment; FAIL if disconnected | Conductivity cell after in-situ formation under closure. |
| R16_flow_through_around | k_rel vs assumed k_open (not measured conductivity) | k_rel approximately 0.74 relative to assumed k_open=1e-8 m2 relative | **MARGINAL** | low (assumption tagged) | Measured conductivity vs closure. |
| R17_no_bulk_gel | isolated droplet hypothesis | PASS only if droplets remain isolated until solid - | **MARGINAL** | low-medium | Visual bulk-gel vs bead formation tests. |
