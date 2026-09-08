#!/usr/bin/env bash
# GeoChemFoam / OpenFOAM CFD workflow.
# Hydrodynamics only. Do NOT solve unverified ROMP chemistry in CFD.
# Default CI does not run this script.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOGDIR="$ROOT/results/raw/cfd"
CASEDIR="$ROOT/simulations/cfd/phaseforge_channel"
mkdir -p "$LOGDIR"
MODE="${1:---check}"

record_status() {
  local status="$1"
  local detail="$2"
  printf '%s\n' "$detail" | tee "$LOGDIR/cfd_status.txt"
  printf '{"status":"%s","detail":%s}\n' "$status" "$(python -c "import json,sys; print(json.dumps(sys.argv[1]))" "$detail")" > "$LOGDIR/cfd_status.json" 2>/dev/null || \
    printf '{"status":"%s"}\n' "$status" > "$LOGDIR/cfd_status.json"
}

if ! command -v docker >/dev/null 2>&1; then
  record_status "docker_cli_missing" "Docker CLI not available. Recorded as CFD limitation."
  echo "Docker not available. Recorded as CFD limitation." | tee "$LOGDIR/docker_unavailable.txt"
  exit 0
fi

if ! docker info >/dev/null 2>&1; then
  MSG="Docker CLI is present but the engine is not reachable (Desktop Linux engine pipe/socket missing)."
  record_status "docker_engine_down" "$MSG"
  echo "$MSG" | tee "$LOGDIR/docker_unavailable.txt"
  docker info 2>&1 | tee -a "$LOGDIR/docker_unavailable.txt" || true
  exit 0
fi

IMAGE="${GEOCHEMFOAM_IMAGE:-jcmaes/geochemfoam-5.2}"
OF_IMAGE="${OPENFOAM_IMAGE:-opencfd/openfoam-default:2412}"

echo "Checking image $IMAGE" | tee "$LOGDIR/cfd_check.log"
docker images "$IMAGE" | tee -a "$LOGDIR/cfd_check.log" || true
docker pull "$IMAGE" 2>&1 | tee -a "$LOGDIR/cfd_check.log" || {
  echo "GeoChemFoam pull failed" | tee -a "$LOGDIR/cfd_check.log"
}

# Probe: versions + tutorial listing (not sufficient as a solve).
docker run --rm "$IMAGE" bash -lc '
  set +e
  echo OF=${WM_PROJECT_VERSION:-unknown}
  echo GCF=${GCFOAM_DIR:-unset}
  echo TUTORIALS=${GCFOAM_TUTORIALS:-unset}
  if [ -n "${GCFOAM_TUTORIALS:-}" ] && [ -d "${GCFOAM_TUTORIALS}" ]; then
    echo "=== GeoChemFoam tutorial directories ==="
    ls "$GCFOAM_TUTORIALS"
    echo "=== two-phase / VoF / interFoam candidates ==="
    find "$GCFOAM_TUTORIALS" -maxdepth 4 -type d \( -iname "*inter*" -o -iname "*vof*" -o -iname "*twoPhase*" -o -iname "*multiphase*" -o -iname "*droplet*" \) 2>/dev/null | head -80
  fi
  if [ -n "${FOAM_TUTORIALS:-}" ] && [ -d "${FOAM_TUTORIALS}" ]; then
    echo "=== OpenFOAM tutorial interFoam ==="
    ls "$FOAM_TUTORIALS/multiphase/interFoam" 2>/dev/null | head
  fi
' 2>&1 | tee -a "$LOGDIR/cfd_check.log" || true

if [ "$MODE" = "--check" ]; then
  record_status "image_probed" "Image probe completed. A listing of tutorials is not a solved case."
  exit 0
fi

run_solver_in_image() {
  local image="$1"
  local inner="$2"
  docker run --rm -v "$ROOT/simulations/cfd:/data" -v "$LOGDIR:/logs" "$image" bash -lc "$inner"
}

# Goal 1: run one official two-phase tutorial if present.
TUTORIAL_SCRIPT='
set -e
source /opt/openfoam*/etc/bashrc 2>/dev/null || source $WM_PROJECT_DIR/etc/bashrc 2>/dev/null || true
echo OF=${WM_PROJECT_VERSION:-unknown}
CAND=""
if [ -n "${GCFOAM_TUTORIALS:-}" ]; then
  CAND=$(find "$GCFOAM_TUTORIALS" -maxdepth 5 -type f -name "Allrun" \( -path "*inter*" -o -path "*VoF*" -o -path "*vof*" -o -path "*twoPhase*" -o -path "*multiphase*" \) 2>/dev/null | head -1)
fi
if [ -z "$CAND" ] && [ -n "${FOAM_TUTORIALS:-}" ]; then
  for p in \
    "$FOAM_TUTORIALS/multiphase/interFoam/laminar/damBreak/damBreak" \
    "$FOAM_TUTORIALS/multiphase/interFoam/RAS/damBreak/damBreak" \
    "$FOAM_TUTORIALS/multiphase/interFoam/laminar/capillaryRise"; do
    if [ -d "$p" ]; then CAND="$p"; break; fi
  done
fi
if [ -z "$CAND" ]; then
  echo "NO_OFFICIAL_TWOPHASE_TUTORIAL_FOUND"
  exit 21
fi
echo "TUTORIAL=$CAND"
WORKDIR=/tmp/of_tutorial
rm -rf "$WORKDIR"
cp -a "$CAND" "$WORKDIR"
cd "$WORKDIR"
if [ -f Allrun ]; then
  chmod +x Allrun || true
  timeout 180 ./Allrun 2>&1 | tee /logs/official_tutorial_solve.log || true
else
  blockMesh 2>&1 | tee /logs/official_blockMesh.log
  timeout 180 interFoam 2>&1 | tee /logs/official_tutorial_solve.log || timeout 180 foamRun 2>&1 | tee /logs/official_tutorial_solve.log || true
fi
echo "=== time directories ===" | tee -a /logs/official_tutorial_metadata.txt
ls -1 | tee -a /logs/official_tutorial_metadata.txt
echo "TUTORIAL_SRC=$CAND" > /logs/official_tutorial_metadata.txt
pwd >> /logs/official_tutorial_metadata.txt
ls -la >> /logs/official_tutorial_metadata.txt
if ls -d [0-9]* >/dev/null 2>&1; then
  echo "FIELDS_PRESENT=yes" | tee -a /logs/official_tutorial_metadata.txt
else
  echo "FIELDS_PRESENT=no" | tee -a /logs/official_tutorial_metadata.txt
fi
'

set +e
run_solver_in_image "$IMAGE" "$TUTORIAL_SCRIPT"
GCF_RC=$?
set -e

if [ "$GCF_RC" -ne 0 ]; then
  echo "GeoChemFoam tutorial solve failed (rc=$GCF_RC). Trying OpenFOAM image $OF_IMAGE" | tee -a "$LOGDIR/cfd_check.log"
  docker pull "$OF_IMAGE" 2>&1 | tee -a "$LOGDIR/cfd_check.log" || true
  set +e
  run_solver_in_image "$OF_IMAGE" "$TUTORIAL_SCRIPT"
  OF_RC=$?
  set -e
fi

# Goal 2: custom 2D PhaseForge transport case (interFoam hydrodynamics only).
PHASEFORGE_SCRIPT='
set -e
source /opt/openfoam*/etc/bashrc 2>/dev/null || source $WM_PROJECT_DIR/etc/bashrc 2>/dev/null || true
cd /data/phaseforge_channel
if [ ! -f system/controlDict ]; then
  echo "CASE_FILES_MISSING"
  exit 22
fi
blockMesh 2>&1 | tee /logs/phaseforge_blockMesh.log
set +e
timeout 240 interFoam 2>&1 | tee /logs/phaseforge_interFoam.log
RC=$?
set -e
echo "interFoam_rc=$RC" | tee /logs/phaseforge_case_metadata.txt
ls -1 | tee -a /logs/phaseforge_case_metadata.txt
if [ -f /logs/phaseforge_interFoam.log ]; then
  grep -E "Time =|Solving for|Courant|ExecutionTime" /logs/phaseforge_interFoam.log | tail -80 | tee /logs/phaseforge_residuals.txt || true
fi
'

set +e
run_solver_in_image "$IMAGE" "$PHASEFORGE_SCRIPT"
PF_RC=$?
if [ "$PF_RC" -ne 0 ]; then
  run_solver_in_image "${OF_IMAGE}" "$PHASEFORGE_SCRIPT"
  PF_RC=$?
fi
set -e

if [ -f "$LOGDIR/phaseforge_interFoam.log" ] && grep -q "End" "$LOGDIR/phaseforge_interFoam.log"; then
  record_status "phaseforge_case_solved" "Custom 2D interFoam case reached End."
elif [ -f "$LOGDIR/official_tutorial_solve.log" ] && grep -q "End" "$LOGDIR/official_tutorial_solve.log"; then
  record_status "official_tutorial_solved" "Official tutorial reached End. Custom case incomplete."
else
  record_status "solve_not_completed" "Docker engine reached; a full two-phase solve did not complete. See logs. Do not fabricate fields."
fi
exit 0
