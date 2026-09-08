"""Write the true-3D PhaseForge interFoam case (no empty frontAndBack)."""

from __future__ import annotations

from pathlib import Path

from phaseforge.requirements import repo_root

HEADER = r"""/*--------------------------------*- C++ -*----------------------------------*\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  2212                                  |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       %s;
    object      %s;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //
"""

# Domain mm. Isotropic Δ ≈ 62.5 μm → 8 cells across 500 μm droplet.
NOMINAL = {"nx": 320, "ny": 48, "nz": 32, "Lx": 20.0, "Ly": 3.0, "Lz": 2.0}
COARSE = {"nx": 160, "ny": 24, "nz": 16, "Lx": 20.0, "Ly": 3.0, "Lz": 2.0}

# Metres. Four non-overlapping 500 μm spheres at distinct Y and Z.
SPHERES = (
    ((0.0025, 0.00115, 0.00065), 0.00025),
    ((0.0050, 0.00185, 0.00140), 0.00025),
    ((0.0075, 0.00110, 0.00100), 0.00025),
    ((0.0100, 0.00175, 0.00070), 0.00025),
)


def _hdr(cls: str, obj: str) -> str:
    return HEADER % (cls, obj)


def block_mesh(spec: dict) -> str:
    return _hdr("dictionary", "blockMeshDict") + f"""
convertToMeters 0.001;

vertices
(
    (0 0 0)
    ({spec["Lx"]} 0 0)
    ({spec["Lx"]} {spec["Ly"]} 0)
    (0 {spec["Ly"]} 0)
    (0 0 {spec["Lz"]})
    ({spec["Lx"]} 0 {spec["Lz"]})
    ({spec["Lx"]} {spec["Ly"]} {spec["Lz"]})
    (0 {spec["Ly"]} {spec["Lz"]})
);

blocks
(
    hex (0 1 2 3 4 5 6 7) ({spec["nx"]} {spec["ny"]} {spec["nz"]}) simpleGrading (1 1 1)
);

edges
(
);

boundary
(
    inlet
    {{
        type patch;
        faces ((0 4 7 3));
    }}
    outlet
    {{
        type patch;
        faces ((1 2 6 5));
    }}
    walls
    {{
        type wall;
        faces
        (
            (0 1 5 4)
            (3 7 6 2)
            (0 3 2 1)
            (4 5 6 7)
        );
    }}
);

mergePatchPairs
(
);

// True 3D duct: four long faces are walls (noSlip). No empty patch.
// ************************************************************************* //
"""


def set_fields() -> str:
    regions = []
    for origin, radius in SPHERES:
        ox, oy, oz = origin
        regions.append(
            f"""    sphereToCell
    {{
        origin ({ox} {oy} {oz});
        radius {radius};
        fieldValues ( volScalarFieldValue alpha.water 0 );
    }}"""
        )
    return _hdr("dictionary", "setFieldsDict") + f"""
defaultFieldValues
(
    volScalarFieldValue alpha.water 1
);

regions
(
{chr(10).join(regions)}
);

// Four volumetric spheres, diameter 500 um. Coordinates in metres.
// ************************************************************************* //
"""


def control_dict(end_time: float = 0.08) -> str:
    return _hdr("dictionary", "controlDict") + f"""
application     interFoam;
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         {end_time};
deltaT          2e-5;
writeControl    adjustableRunTime;
writeInterval   0.02;
purgeWrite      0;
writeFormat     ascii;
writePrecision  6;
writeCompression off;
timeFormat      general;
timePrecision   6;
runTimeModifiable yes;
adjustTimeStep  yes;
maxCo           0.4;
maxAlphaCo      0.4;
maxDeltaT       0.002;

// ************************************************************************* //
"""


def fv_schemes() -> str:
    return _hdr("dictionary", "fvSchemes") + """
ddtSchemes
{
    default         Euler;
}

gradSchemes
{
    default         Gauss linear;
}

divSchemes
{
    default             none;
    div(rhoPhi,U)       Gauss linearUpwind grad(U);
    div(phi,alpha)      Gauss vanLeer;
    div(phirb,alpha)    Gauss linear;
    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
}

laplacianSchemes
{
    default         Gauss linear corrected;
}

interpolationSchemes
{
    default         linear;
}

snGradSchemes
{
    default         corrected;
}

// ************************************************************************* //
"""


def fv_solution() -> str:
    return _hdr("dictionary", "fvSolution") + """
solvers
{
    "alpha.water.*"
    {
        nAlphaCorr      2;
        nAlphaSubCycles 1;
        cAlpha          1;
        MULESCorr       yes;
        nLimiterIter    3;
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-8;
        relTol          0;
    }

    pcorr
    {
        solver          PCG;
        preconditioner  DIC;
        tolerance       1e-7;
        relTol          0;
    }

    pcorrFinal
    {
        $pcorr;
        relTol          0;
    }

    p_rgh
    {
        solver          PCG;
        preconditioner  DIC;
        tolerance       1e-7;
        relTol          0.05;
    }

    p_rghFinal
    {
        $p_rgh;
        relTol          0;
    }

    U
    {
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-6;
        relTol          0;
    }
}

PIMPLE
{
    momentumPredictor   no;
    nOuterCorrectors    1;
    nCorrectors         3;
    nNonOrthogonalCorrectors 1;
    pRefCell            0;
    pRefValue           0;
}

relaxationFactors
{
    equations
    {
        ".*" 1;
    }
}

// ************************************************************************* //
"""


def decompose() -> str:
    return _hdr("dictionary", "decomposeParDict") + """
numberOfSubdomains 4;
method          simple;

simpleCoeffs
{
    n               (4 1 1);
    delta           0.001;
}

distributed     no;
roots           ( );

// ************************************************************************* //
"""


def transport(kind: str) -> str:
    if kind == "hpht":
        comment = (
            "// HPHT thermal-property analogue (~150 C liquid). Incompressible VoF.\n"
            "// 10,000 psi is NOT modelled as a chemical rate.\n"
        )
        water = ("2.0e-07", "917")
        oil = ("3.2e-07", "880")
        sigma = "0.0032"
    else:
        comment = (
            "// Moderate-temperature analogue (~60-70 C). Hydrodynamics only.\n"
            "// Absolute hydrostatic pressure is NOT a chemical-rate variable here.\n"
        )
        water = ("4.1e-07", "983")
        oil = ("5.1e-07", "960")
        sigma = "0.004"
    return _hdr("dictionary", "transportProperties") + f"""
{comment}
phases (water oil);

water
{{
    transportModel  Newtonian;
    nu              [0 2 -1 0 0 0 0] {water[0]};
    rho             [1 -3 0 0 0 0 0] {water[1]};
}}

oil
{{
    transportModel  Newtonian;
    nu              [0 2 -1 0 0 0 0] {oil[0]};
    rho             [1 -3 0 0 0 0 0] {oil[1]};
}}

sigma           [1 0 -2 0 0 0 0] {sigma};

// ************************************************************************* //
"""


def g_file() -> str:
    return _hdr("uniformDimensionedVectorField", "g") + """
dimensions      [0 1 -2 0 0 0 0];
value           (0 0 0);

// ************************************************************************* //
"""


def turbulence() -> str:
    return _hdr("dictionary", "turbulenceProperties") + """
simulationType  laminar;

// ************************************************************************* //
"""


def field_u() -> str:
    return _hdr("volVectorField", "U") + """
dimensions      [0 1 -1 0 0 0 0];

internalField   uniform (0.05 0 0);

boundaryField
{
    inlet
    {
        type            fixedValue;
        value           uniform (0.05 0 0);
    }
    outlet
    {
        type            zeroGradient;
    }
    walls
    {
        type            noSlip;
    }
}

// ************************************************************************* //
"""


def field_alpha() -> str:
    return _hdr("volScalarField", "alpha.water") + """
dimensions      [0 0 0 0 0 0 0];

internalField   uniform 1;

boundaryField
{
    inlet
    {
        type            fixedValue;
        value           uniform 1;
    }
    outlet
    {
        type            zeroGradient;
    }
    walls
    {
        type            zeroGradient;
    }
}

// ************************************************************************* //
"""


def field_prgh() -> str:
    return _hdr("volScalarField", "p_rgh") + """
dimensions      [1 -1 -2 0 0 0 0];

internalField   uniform 0;

boundaryField
{
    inlet
    {
        type            fixedFluxPressure;
        value           uniform 0;
    }
    outlet
    {
        type            totalPressure;
        p0              uniform 0;
        value           uniform 0;
    }
    walls
    {
        type            fixedFluxPressure;
        value           uniform 0;
    }
}

// ************************************************************************* //
"""


def allrun() -> str:
    return """#!/bin/sh
cd "${0%/*}" || exit
. "${WM_PROJECT_DIR:?}/bin/tools/RunFunctions"
runApplication blockMesh
runApplication checkMesh
runApplication setFields
runApplication decomposePar
mpirun --allow-run-as-root -np 4 interFoam -parallel
runApplication reconstructPar
runApplication foamToVTK
"""


def write_case(case: Path, *, spec: dict, props: str = "moderate") -> None:
    (case / "system").mkdir(parents=True, exist_ok=True)
    (case / "constant").mkdir(parents=True, exist_ok=True)
    (case / "0").mkdir(parents=True, exist_ok=True)
    (case / "system" / "blockMeshDict").write_text(block_mesh(spec), encoding="utf-8")
    (case / "system" / "blockMeshDict.coarse").write_text(block_mesh(COARSE), encoding="utf-8")
    (case / "system" / "blockMeshDict.nominal").write_text(block_mesh(NOMINAL), encoding="utf-8")
    (case / "system" / "setFieldsDict").write_text(set_fields(), encoding="utf-8")
    (case / "system" / "controlDict").write_text(control_dict(), encoding="utf-8")
    (case / "system" / "fvSchemes").write_text(fv_schemes(), encoding="utf-8")
    (case / "system" / "fvSolution").write_text(fv_solution(), encoding="utf-8")
    (case / "system" / "decomposeParDict").write_text(decompose(), encoding="utf-8")
    (case / "constant" / "g").write_text(g_file(), encoding="utf-8")
    (case / "constant" / "turbulenceProperties").write_text(turbulence(), encoding="utf-8")
    (case / "constant" / "transportProperties.moderate").write_text(transport("moderate"), encoding="utf-8")
    (case / "constant" / "transportProperties.hpht").write_text(transport("hpht"), encoding="utf-8")
    (case / "constant" / "transportProperties").write_text(transport(props), encoding="utf-8")
    (case / "0" / "U").write_text(field_u(), encoding="utf-8")
    alpha = field_alpha()
    (case / "0" / "alpha.water").write_text(alpha, encoding="utf-8")
    (case / "0" / "alpha.water.org").write_text(alpha, encoding="utf-8")
    (case / "0" / "p_rgh").write_text(field_prgh(), encoding="utf-8")
    (case / "Allrun").write_text(allrun(), encoding="utf-8")
    (case / "phaseforge_3d.foam").write_text("", encoding="utf-8")
    ncell = spec["nx"] * spec["ny"] * spec["nz"]
    dx = spec["Lx"] / spec["nx"]
    (case / "README.md").write_text(
        "\n".join(
            [
                "# PhaseForge 3D channel — hydrodynamic demonstration",
                "",
                "True 3D `interFoam` case (OpenFOAM v2212 / GeoChemFoam). "
                "Not an extrusion of the 2D screening case.",
                "",
                f"- Domain: {spec['Lx']:g} × {spec['Ly']:g} × {spec['Lz']:g} mm",
                f"- Mesh: {spec['nx']} × {spec['ny']} × {spec['nz']} hex cells ({ncell} cells)",
                f"- Cell size: {dx * 1000:.1f} μm (isotropic in the nominal dict)",
                f"- Cells across 500 μm droplet: {0.5 / dx:.1f}",
                "- Boundaries: inlet/outlet patches; four long faces are **walls** (noSlip). "
                "No `empty` patch.",
                "- IC: four `sphereToCell` organic droplets, d = 500 μm, distinct Y and Z.",
                "- Hydrodynamics only. No ChemGate chemistry. 10,000 psi is not a chemical-rate variable.",
                "",
                "The 2D case `simulations/cfd/phaseforge_channel` remains **2D screening / baseline CFD**.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    root = repo_root()
    base = root / "simulations" / "cfd"
    write_case(base / "phaseforge_channel_3d", spec=NOMINAL, props="moderate")
    write_case(base / "phaseforge_channel_3d_coarse", spec=COARSE, props="moderate")
    write_case(base / "phaseforge_channel_3d_hpht", spec=NOMINAL, props="hpht")
    print("wrote 3D cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
