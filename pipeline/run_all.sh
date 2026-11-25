#!/usr/bin/env bash
# The scripted part of the pipeline, for one or more studies (default: all):
#   0. the variation tables (CSV) from study.toml
#   1. GDML for each variant, in FreeCAD      (skipped where it exists)
#   2. build the Geant4 app                   (skipped if up to date)
#   3. every variant x physics list x source  (resumes; finished runs skipped)
#   4. metrics, checks, plots, review packet
#   5. pictures of the scoring meshes
# No AI is involved: the review of results/<study>/review_input.md comes
# afterwards (docs/WORKFLOW.md).
#
#   conda activate g4                      # Geant4 + its data sets
#   pipeline/run_all.sh                    # all studies
#   pipeline/run_all.sh shield detector
#   JOBS=6 EVENTS_SCALE=0.1 pipeline/run_all.sh calorimeter   # quick look
#
# JOBS          parallel Geant4 processes (default: CPUs - 1)
# EVENTS_SCALE  multiply every source's event count (default 1)
# RENDER_3D=1   also 3D views (needs the vtk Python package)
# FREECAD       FreeCAD.app or executable for step 1 (see gen_gdml.sh)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"
PY="${PYTHON:-python3}"

if [ $# -eq 0 ]; then
  set -- $(ls studies/*/study.toml | xargs -n1 dirname | xargs -n1 basename)
fi
studies=("$@")

command -v geant4-config >/dev/null ||
  { echo "geant4-config not found: activate the Geant4 environment (conda activate g4)" >&2; exit 2; }
"$PY" -c "import numpy, matplotlib" 2>/dev/null ||
  { echo "$PY needs numpy and matplotlib: $PY -m pip install -r requirements.txt" >&2; exit 2; }

# 0. variation tables (geometry_variants.csv, physics_variants.csv) from study.toml
"$PY" tools/export_csv.py "${studies[@]}"

# 1. GDML
need=""
for s in "${studies[@]}"; do
  missing=$("$PY" - "$s" <<'EOF'
import sys
from pipeline import study
st = study.load(sys.argv[1])
d = study.results_dir(st) / "gdml"
print(sum(not (d / f"{v.name}.gdml").exists() for v in st.variants))
EOF
)
  if [ "$missing" -gt 0 ]; then need="$need $s"; fi
done
if [ -n "$need" ]; then
  echo "== GDML:$need"
  pipeline/gen_gdml.sh $need
fi

# 2. Geant4 app
app=g4app/build/gdmlvar
if [ ! -x "$app" ] || [ -n "$(find g4app -path g4app/build -prune -o -newer "$app" \( -name '*.cc' -o -name '*.hh' -o -name CMakeLists.txt \) -print -quit)" ]; then
  echo "== building $app"
  cmake -S g4app -B g4app/build -DCMAKE_BUILD_TYPE=Release >/dev/null
  cmake --build g4app/build -j "${JOBS:-4}"
fi

# 3-5
jobs=""; [ -n "${JOBS:-}" ] && jobs="-j $JOBS"
rc=0
for s in "${studies[@]}"; do
  echo "== runs: $s"
  "$PY" pipeline/run_matrix.py "$s" $jobs --events-scale "${EVENTS_SCALE:-1}" || rc=1
  echo "== analysis: $s"
  r3d=""; [ "${RENDER_3D:-0}" = "1" ] && r3d="--3d"
  "$PY" pipeline/render.py "$s" $r3d
  "$PY" pipeline/analyse.py "$s"
done
echo "Review packets: results/<study>/review_input.md (see docs/REVIEW_GUIDE.md)"
exit $rc
