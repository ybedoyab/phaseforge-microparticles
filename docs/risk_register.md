# Risk register

Scores are qualitative (L/M/H). This is an engineering risk register, not a HSE procedure.

| ID | Risk | Probability | Impact | Detectability | Mitigation (concept) | Validation method | Residual |
|---|---|---|---|---|---|---|---|
| RK01 | Premature polymerization during pumping | H at 150 °C with published Ru/phosphite; **lower** if ChemGate activator is withheld | H (screen-out / tubing set) | M (rheology) | ChemGate delayed contact; do not put activator in transport brine; do not retune RuP to fake PASS | Isothermal t_gel of dispersed system with/without activator | H for RuP at 150 °C; M for ChemGate if gate holds |
| RK14 | IP overlap US11377580B2 | H | H (commercial) | H | Differentiate microparticle isolation vs pillars; get counsel | Landscape + counsel | H |
| RK16 | IP overlap D899/Cu (US12338310 and related) | H if recipe copied | H | H | Use architecture only; licensed/unencumbered pair | Counsel | H |
| RK17 | ChemGate premature cure if activator present during transport | H for 70 μm drops (t_diff minutes) | H | M | External delay / staged activator | Diffusion + jar tests | M–H |
| RK02 | Too-slow activation | M at low T / high inhibitor | M (particles never form) | H | Reduce inhibitor / raise catalyst activity | Same rheology map | M |
| RK03 | Bulk gel / continuous plug | M if coalescence during sticky window | H (challenge FAIL) | H (visual) | Keep φ moderate; stabilize interface; avoid gel while drops are in contact | Jar tests + slot flow | M |
| RK04 | Droplet coalescence | M at low σ, high φ, low shear after pumping | H (size >600 μm, adhesion) | M | IFT 3–5 mN/m analogue; sufficient stabilizer | Emulsion stability + size vs time | M |
| RK05 | Particle size outside 70–600 μm | M (Hinze/ε uncertain) | H | H | Tune shear and σ; Chen showed shear control | Mix-loop PSD | M |
| RK06 | High-T softening near Tg | H if Tg ~140–165 °C and T=150 °C | H (not load-bearing) | M | DCPD/TriCPD high-Tg (patent overlap); post-cure may not happen downhole | Crush at 150 °C | H |
| RK07 | Mechanical crushing | M at 41 MPa if derated | H | H | Safety factor; avoid claiming RT 78 MPa at 150 °C | Crush tests | M–H |
| RK08 | Insufficient residual permeability | M if settled dense pack + deformation | H | M | Limit φ; Chen noted conductivity loss from **deformation** not always breakage | Conductivity cell | M |
| RK09 | Catalyst poisoning by water/brine | H for many Mo systems; M for Ru | H (no cure or extra delay) | L downhole | Ru functional-group tolerance is a reason to consider Ru; still unproven in this emulsion | Cure in brine/surfactant matrix | H |
| RK10 | Pressure effects (10,000 psi) | U | M | L | Do not assume rate is pressure-independent | HPHT rheometer | U |
| RK11 | Reaction exotherm | L for 200 μm drops in water (model); H for bulk resin | M–H | M | Isolated droplets are the thermal mitigator | Droplet vs bulk DSC | M |
| RK12 | Surfactant compatibility | M | H | M | Screen nonionic packages (Chen NPCL analogue) | Compatibility matrix | M |
| RK13 | Cost / Ru catalyst | M | M | H | Low ppm loadings (patent 28 ppm mol example) | Techno-economic later | M |
| RK14 | IP overlap US11377580B2 | H | H (commercial) | H | Differentiate microparticle isolation vs pillars; get counsel | Landscape + counsel | H |
| RK15 | Arrhenius extrapolation error | H above 80 °C | H | L | Treat 150 °C as UNKNOWN | Measure, do not extrapolate | H |

## Dominant residual risks for the Innocentive question

1. **150 °C latency** (RK01 + RK15)
2. **150 °C mechanical strength vs Tg** (RK06)
3. **IP overlap** (RK14)
4. **Water/brine catalyst compatibility in droplets** (RK09)
