#!/usr/bin/env bash
# The scripted part of the pipeline, for one or more studies (default: all):
#   0. check the setup; the variation tables (CSV) from study.toml
#   1. GDML for each variant, in FreeCAD      (skipped where it exists)
#   2. build the Geant4 app                   (skipped if up to date)
#   3. every variant x physics list x source  (resumes; finished runs skipped)
#   4. metrics, checks, plots, review packet
#   5. pictures of the scoring meshes
# No AI is involved: the review of results/<study>/review_input.md comes
# afterwards (docs/WORKFLOW.md).
#
#   conda activate gdml-variations         # see environment.yml
#   pipeline/run_all.sh                    # all studies
#   pipeline/run_all.sh shield detector
#   JOBS=6 EVENTS_SCALE=0.1 pipeline/run_all.sh calorimeter   # quick look
#
# JOBS          parallel Geant4 processes (default: CPUs - 1)
# EVENTS_SCALE  multiply every source's event count (default 1)
# RENDER_3D=1   also 3D views (needs the vtk Python package)
# FREECAD       FreeCAD.app or executable for step 1 (see gen_gdml.sh)
# PYTHON        Python to use (default: the active conda environment's)
# Any of these can be set once in pipeline/local.env (see local.env.example).
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"
. "$REPO/pipeline/_env.sh"
gdv_load_local_env "$REPO"

# Same choice as check_setup.sh: never a Homebrew/system python3 when a
# conda environment is active and has its own.
if [ -z "${PYTHON:-}" ]; then
  if [ -n "${CONDA_PREFIX:-}" ] && [ -x "$CONDA_PREFIX/bin/python3" ]; then
    PYTHON="$CONDA_PREFIX/bin/python3"
  else
    PYTHON="$(command -v python3 || echo python3)"
  fi
fi
export PYTHON
PY="$PYTHON"

if [ $# -eq 0 ]; then
  set -- $(ls studies/*/study.toml | xargs -n1 dirname | xargs -n1 basename)
fi
studies=("$@")

# 0. setup and variation tables
pipeline/check_setup.sh -q || exit 2
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

# 2. Geant4 app.  Configure from scratch each time it is rebuilt, so a
# dependency found in the wrong place earlier is not kept in the cache.
app=g4app/build/gdmlvar
if [ ! -x "$app" ] || [ -n "$(find g4app -path g4app/build -prune -o -newer "$app" \( -name '*.cc' -o -name '*.hh' -o -name CMakeLists.txt \) -print -quit)" ]; then
  echo "== building $app"
  fresh=""
  cmake --help 2>/dev/null | grep -q -- "--fresh" && fresh="--fresh"
  log="$(mktemp)"
  if ! cmake $fresh -S g4app -B g4app/build -DCMAKE_BUILD_TYPE=Release >"$log" 2>&1; then
    cat "$log" >&2
    echo "CMake could not configure g4app: run pipeline/check_setup.sh and fix what it reports." >&2
    exit 2
  fi
  rm -f "$log"
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
