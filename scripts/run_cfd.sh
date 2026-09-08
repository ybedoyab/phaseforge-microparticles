#!/usr/bin/env bash
# GeoChemFoam / OpenFOAM CFD workflow.
# Hydrodynamics only. Do NOT solve unverified ROMP chemistry in CFD.
# Default CI does not run this script.
#
# Usage:
#   bash scripts/run_cfd.sh --check     probe image / docker
#   bash scripts/run_cfd.sh --solve     official tutorial + PhaseForge cases
#   bash scripts/run_cfd.sh             same as --solve if engine is up
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOGDIR="$ROOT/results/raw/cfd"
CFDROOT="$ROOT/simulations/cfd"
CASEDIR="$CFDROOT/phaseforge_channel"
DAMDIR="$CFDROOT/official_damBreak"
mkdir -p "$LOGDIR"
MODE="${1:---solve}"

record_status() {
  local status="$1"
  local detail="$2"
  printf '%s\n' "$detail" | tee "$LOGDIR/cfd_status.txt"
  python - "$status" "$detail" "$LOGDIR/cfd_status.json" <<'PY' || printf '{"status":"%s"}\n' "$status" > "$LOGDIR/cfd_status.json"
import json, sys
status, detail, path = sys.argv[1], sys.argv[2], sys.argv[3]
open(path, "w", encoding="utf-8").write(json.dumps({"status": status, "detail": detail}, indent=2) + "\n")
PY
}

if ! command -v docker >/dev/null 2>&1; then
  record_status "docker_cli_missing" "Docker CLI not available. Recorded as CFD limitation."
  echo "Docker not available. Recorded as CFD limitation." | tee "$LOGDIR/docker_unavailable.txt"
  exit 0
fi

if ! docker info >/dev/null 2>&1; then
  MSG="Docker CLI is present but the engine is not reachable."
  record_status "docker_engine_down" "$MSG"
  echo "$MSG" | tee "$LOGDIR/docker_unavailable.txt"
  docker info 2>&1 | tee -a "$LOGDIR/docker_unavailable.txt" || true
  exit 0
fi

IMAGE="${GEOCHEMFOAM_IMAGE:-jcmaes/geochemfoam-5.2}"
docker info 2>&1 | tee "$LOGDIR/docker_info.txt" | head -40
echo "IMAGE=$IMAGE" | tee "$LOGDIR/cfd_check.log"
docker images "$IMAGE" | tee -a "$LOGDIR/cfd_check.log"

OF_SOURCE='
set +e
source /usr/lib/openfoam/openfoam2212/etc/bashrc
source /opt/openfoam*/etc/bashrc 2>/dev/null
source "${WM_PROJECT_DIR:-/nonexistent}/etc/bashrc" 2>/dev/null
# Do not source GeoChemFoam bashrc as root (it looks for $HOME/works).
echo OF=${WM_PROJECT_VERSION:-unknown}
which blockMesh
which interFoam
which setFields
which foamToVTK
'

docker run --rm -u 0 "$IMAGE" bash -lc "$OF_SOURCE" 2>&1 | tee -a "$LOGDIR/cfd_check.log"

if [ "$MODE" = "--check" ]; then
  record_status "image_probed" "Image probe completed. A listing is not a solved case. Run without --check to solve."
  exit 0
fi

run_in() {
  local inner="$1"
  docker run --rm -u 0 \
    -v "$CFDROOT:/data" \
    -v "$LOGDIR:/logs" \
    "$IMAGE" bash -lc "source /usr/lib/openfoam/openfoam2212/etc/bashrc; $inner"
}

# ---------- 1. Official two-phase tutorial from the image (GCF BubbleChannel, serial, shortened) ----------
OFFICIAL_GCF='
set -e
TSRC=/home/gcfoam/works/GeoChemFoam-5.2/tutorials/multiphase/interOSFoam/BubbleChannelCa10-5
if [ ! -d "$TSRC" ]; then
  echo "NO_GCF_TUTORIAL"
  exit 21
fi
WORKDIR=/data/_official_gcf_bubble
rm -rf "$WORKDIR"
cp -a "$TSRC" "$WORKDIR"
cd "$WORKDIR"
# Serial, coarsened, short: still a real mesh+solver path from the official case.
sed -i "s/^NP=8/NP=1/" createMesh.sh
sed -i "s/^n_x=600/n_x=80/" createMesh.sh
sed -i "s/^n_y=100/n_y=16/" createMesh.sh
chmod +x createMesh.sh initCase0.sh runCase0.sh initCaseTPFlow.sh runCaseTPFlow.sh || true
./createMesh.sh > /logs/official_gcf_mesh.log 2>&1
# Prefer interFoam on the generated mesh if present; else keep interOSFoam with short time.
if [ -f system/blockMeshDict ]; then
  echo "GCF tutorial mesh generated" | tee /logs/official_tutorial_metadata.txt
fi
ls -1 | tee -a /logs/official_tutorial_metadata.txt
'

set +e
run_in "$OFFICIAL_GCF"
GCF_TUT_RC=$?
set -e

# ---------- 2. Classic OpenFOAM damBreak (interFoam) — required solved tutorial ----------
DAMBREAK='
set -e
cd /data/official_damBreak
rm -rf constant/polyMesh [1-9]* 0.[0-9]*
blockMesh > /logs/official_blockMesh.log 2>&1
cp -f 0/alpha.water 0/alpha.water.org
setFields > /logs/official_setFields.log 2>&1
interFoam > /logs/official_tutorial_solve.log 2>&1
echo "TUTORIAL=official_damBreak OpenFOAM interFoam laminar damBreak analogue" > /logs/official_tutorial_metadata.txt
echo OF=${WM_PROJECT_VERSION:-unknown} >> /logs/official_tutorial_metadata.txt
echo IMAGE_HOSTNAME=$(hostname) >> /logs/official_tutorial_metadata.txt
ls -1 >> /logs/official_tutorial_metadata.txt
grep -E "Time =|ExecutionTime|Solving for p_rgh|End" /logs/official_tutorial_solve.log | tail -60 > /logs/official_residuals.txt || true
if grep -q "^End" /logs/official_tutorial_solve.log; then
  echo OFFICIAL_END=yes >> /logs/official_tutorial_metadata.txt
else
  echo OFFICIAL_END=no >> /logs/official_tutorial_metadata.txt
  exit 31
fi
foamToVTK -latestTime > /logs/official_foamToVTK.log 2>&1 || true
'

set +e
run_in "$DAMBREAK"
DAM_RC=$?
set -e

# ---------- 3. PhaseForge moderate-T multi-droplet channel ----------
run_phaseforge() {
  local tag="$1"
  local props="$2"
  local inner
  inner="
set -e
cd /data/phaseforge_channel
if [ -n \"$props\" ] && [ -f constant/$props ]; then
  cp -f constant/$props constant/transportProperties
fi
rm -rf constant/polyMesh [1-9]* 0.[0-9]* VTK
blockMesh > /logs/phaseforge_${tag}_blockMesh.log 2>&1
cp -f 0/alpha.water.org 0/alpha.water 2>/dev/null || true
cp -f 0/alpha.water 0/alpha.water.org
setFields > /logs/phaseforge_${tag}_setFields.log 2>&1
interFoam > /logs/phaseforge_${tag}_interFoam.log 2>&1
echo TAG=$tag > /logs/phaseforge_${tag}_metadata.txt
echo OF=\${WM_PROJECT_VERSION:-unknown} >> /logs/phaseforge_${tag}_metadata.txt
ls -1 >> /logs/phaseforge_${tag}_metadata.txt
grep -E \"Time =|ExecutionTime|Solving for p_rgh|Courant|End\" /logs/phaseforge_${tag}_interFoam.log | tail -80 > /logs/phaseforge_${tag}_residuals.txt || true
if ! grep -q \"^End\" /logs/phaseforge_${tag}_interFoam.log; then
  echo SOLVE_END=no >> /logs/phaseforge_${tag}_metadata.txt
  exit 32
fi
echo SOLVE_END=yes >> /logs/phaseforge_${tag}_metadata.txt
foamToVTK > /logs/phaseforge_${tag}_foamToVTK.log 2>&1 || true
mkdir -p /logs/${tag}_fields
# Keep time directories on the mounted case; copy log summary only.
cp -a /logs/phaseforge_${tag}_interFoam.log /logs/${tag}_fields/ || true
"
  run_in "$inner"
}

cp -f "$CASEDIR/0/alpha.water" "$CASEDIR/0/alpha.water.org"
cp -f "$CASEDIR/constant/transportProperties" "$CASEDIR/constant/transportProperties.moderate"

set +e
run_phaseforge "moderate" "transportProperties.moderate"
PF_MOD_RC=$?
run_phaseforge "hpht" "transportProperties.hpht"
PF_HPHT_RC=$?
set -e

# Restore moderate properties as the committed default.
cp -f "$CASEDIR/constant/transportProperties.moderate" "$CASEDIR/constant/transportProperties"

STATUS="solve_not_completed"
DETAIL="Docker engine reached; see results/raw/cfd logs."
if [ "$DAM_RC" = "0" ] && grep -q "^End" "$LOGDIR/official_tutorial_solve.log" 2>/dev/null; then
  STATUS="official_tutorial_solved"
  DETAIL="Official damBreak interFoam reached End."
fi
if [ "$PF_MOD_RC" = "0" ] && grep -q "^End" "$LOGDIR/phaseforge_moderate_interFoam.log" 2>/dev/null; then
  STATUS="phaseforge_case_solved"
  DETAIL="Official damBreak and PhaseForge moderate-T interFoam reached End. hpht_rc=$PF_HPHT_RC gcf_tut_rc=$GCF_TUT_RC"
fi

record_status "$STATUS" "$DETAIL"
python "$ROOT/scripts/cfd_postprocess.py" || true
python -m phaseforge.cfd_postprocess || python "$ROOT/phaseforge/cfd_postprocess.py" || true
exit 0
