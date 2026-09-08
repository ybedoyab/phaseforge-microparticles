#!/usr/bin/env bash
# Clone optional external codes into ./external (gitignored). Pin commits when known.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXT="$ROOT/external"
mkdir -p "$EXT"

clone_pin () {
  local url="$1"
  local dest="$2"
  local pin="${3:-}"
  if [ -d "$dest/.git" ]; then
    echo "exists: $dest"
    return
  fi
  git clone --depth 1 "$url" "$dest"
  if [ -n "$pin" ]; then
    git -C "$dest" fetch --depth 1 origin "$pin"
    git -C "$dest" checkout "$pin"
  fi
}

clone_pin "https://github.com/GeoChemFoam/GeoChemFoam.git" "$EXT/GeoChemFoam"
clone_pin "https://github.com/GeoChemFoam/GeoChemFoam-5.2.git" "$EXT/GeoChemFoam-5.2"
clone_pin "https://github.com/HugoMVale/polykin.git" "$EXT/polykin"
# Optional:
# clone_pin "https://github.com/GeoEnergyLab-EPFL/PyFrac.git" "$EXT/PyFrac"

echo "External clones completed under $EXT (not committed)."
echo "Licenses: inspect each repo COPYING/LICENSE before use."
