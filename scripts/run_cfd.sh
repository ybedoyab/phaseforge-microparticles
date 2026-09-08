#!/usr/bin/env bash
# GeoChemFoam Docker workflow. Heavy CFD is not part of default CI.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOGDIR="$ROOT/results/raw/cfd"
mkdir -p "$LOGDIR"
CHECK_ONLY=0
if [ "${1:-}" = "--check" ]; then
  CHECK_ONLY=1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not available. Recorded as CFD limitation." | tee "$LOGDIR/docker_unavailable.txt"
  exit 0
fi

IMAGE="${GEOCHEMFOAM_IMAGE:-jcmaes/geochemfoam-5.2}"
echo "Checking image $IMAGE" | tee "$LOGDIR/cfd_check.log"
if [ "$CHECK_ONLY" -eq 1 ]; then
  docker images "$IMAGE" | tee -a "$LOGDIR/cfd_check.log" || true
  docker pull "$IMAGE" 2>&1 | tee -a "$LOGDIR/cfd_check.log" || {
    echo "pull failed" | tee -a "$LOGDIR/cfd_check.log"
    exit 0
  }
  docker run --rm "$IMAGE" bash -lc 'echo OF=$WM_PROJECT_VERSION; echo GCF=$GCFOAM_DIR; ls $GCFOAM_TUTORIALS | head' 2>&1 | tee -a "$LOGDIR/cfd_check.log" || true
  exit 0
fi

# Full tutorial attempt (2D channel / micromodel if present in the image)
docker pull "$IMAGE" 2>&1 | tee "$LOGDIR/docker_pull.log" || exit 0
docker run --rm -v "$ROOT/simulations/cfd:/data" "$IMAGE" bash -lc '
  set -e
  echo "OpenFOAM=${WM_PROJECT_VERSION:-unknown}"
  echo "GCFOAM_TUTORIALS=${GCFOAM_TUTORIALS:-unset}"
  if [ -n "${GCFOAM_TUTORIALS:-}" ]; then
    ls "$GCFOAM_TUTORIALS" | head -50
  fi
' 2>&1 | tee "$LOGDIR/tutorial_probe.log" || true
