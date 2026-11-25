#!/usr/bin/env bash
# Build and export the GDML of every variant of one or more studies, by
# starting FreeCAD (with its GUI, which GDML export needs) on
# pipeline/generate_gdml.py.  FreeCAD quits when it has finished.
#
#   pipeline/gen_gdml.sh shield calorimeter detector
#   GDV_ONLY='Pb_*' GDV_FORCE=1 pipeline/gen_gdml.sh shield
#
# FREECAD   FreeCAD.app bundle or executable.  Default: the newest
#           /Applications/FreeCAD*.app (macOS) or 'freecad' on the PATH.
# GDV_XVFB=1  run under xvfb-run (Linux without a display).
#
# Close any running FreeCAD first: with FreeCAD's single-instance option the
# script would be handed to the running copy instead.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
. "$REPO/pipeline/_env.sh"
gdv_load_local_env "$REPO"
[ $# -ge 1 ] || { echo "usage: $0 STUDY [STUDY ...]" >&2; exit 2; }

fc="${FREECAD:-}"
if [ -z "$fc" ]; then
  if [ "$(uname)" = "Darwin" ]; then
    fc="$(ls -d /Applications/FreeCAD*.app 2>/dev/null | sort -V | tail -1 || true)"
  else
    fc="$(command -v freecad || command -v FreeCAD || true)"
  fi
fi
[ -n "$fc" ] || { echo "FreeCAD not found: set FREECAD" >&2; exit 2; }
if [ -d "$fc" ] && [ -d "$fc/Contents/MacOS" ]; then
  exe="$(defaults read "$fc/Contents/Info" CFBundleExecutable 2>/dev/null || echo FreeCAD)"
  fc="$fc/Contents/MacOS/$exe"
fi
[ -x "$fc" ] || { echo "not an executable: $fc" >&2; exit 2; }

if pgrep -f "$fc" >/dev/null 2>&1; then
  echo "FreeCAD ($fc) is already running - close it first" >&2
  exit 2
fi

studies="$(IFS=,; echo "$*")"
log="$REPO/results/gen_gdml.log"
mkdir -p "$REPO/results"
echo "FreeCAD: $fc"
echo "studies: $studies   (log: $log)"

run=("$fc" "$REPO/pipeline/generate_gdml.py")
[ "${GDV_XVFB:-0}" = "1" ] && run=(xvfb-run -a "${run[@]}")

start="$REPO/results/.gen_gdml_start"
touch "$start"
set +e
GDV_REPO="$REPO" GDV_STUDIES="$studies" GDV_AUTOQUIT=1 \
  GDV_ONLY="${GDV_ONLY:-}" GDV_FORCE="${GDV_FORCE:-0}" \
  "${run[@]}" >"$log" 2>&1
rc=$?
set -e

# Summarise from each study's generation.json: FreeCAD's own output can be
# cut short when it quits, so the log may lack the last lines.
for s in "$@"; do
  name="$(basename "$s")"
  gen="$REPO/results/$name/gdml/generation.json"
  if [ -f "$gen" ] && [ "$gen" -nt "$start" ]; then
    built=$(grep -c '"status": "ok"' "$gen" || true)
    kept=$(grep -c '"status": "kept"' "$gen" || true)
    failed=$(grep -c '"status": "failed"' "$gen" || true)
    echo "[generate_gdml] $name: $built built, $kept kept, $failed failed"
    [ "$failed" -eq 0 ] || rc=1
  else
    echo "[generate_gdml] $name: not generated - see $log" >&2
    rc=1
  fi
done
rm -f "$start"
[ $rc -eq 0 ] || echo "GDML generation incomplete - see $log and results/<study>/gdml/generation.json" >&2
exit $rc
