#!/usr/bin/env bash
# Check that this machine has what the pipeline needs, and say what to fix.
#
#   pipeline/check_setup.sh          # report everything
#   pipeline/check_setup.sh -q       # problems only (used by run_all.sh)
#
# Exit status 1 if anything required is missing.  FreeCAD is only needed to
# generate GDML, so problems with it are warnings.
#
# Python: $PYTHON if set, else the active conda environment's python3, else
# python3 on the PATH - the same choice as run_all.sh.
set -u

quiet=0
[ "${1:-}" = "-q" ] && quiet=1
fail=0

ok()   { [ $quiet = 1 ] || printf '  ok    %s\n' "$*"; }
warn() { printf '  WARN  %s\n' "$*"; }
bad()  { printf '  FAIL  %s\n' "$*"; fail=1; }
fix()  { printf '        -> %s\n' "$*"; }

ENVFIX="conda env create -f environment.yml (or: conda env update -n <your env> -f environment.yml)"

# --- Python ----------------------------------------------------------------
[ $quiet = 1 ] || echo "Python"
py="${PYTHON:-}"
if [ -z "$py" ]; then
  if [ -n "${CONDA_PREFIX:-}" ] && [ -x "$CONDA_PREFIX/bin/python3" ]; then
    py="$CONDA_PREFIX/bin/python3"
  else
    py="$(command -v python3 || true)"
  fi
fi
if [ -z "$py" ] || ! "$py" -c "" 2>/dev/null; then
  bad "no working python3"
  fix "$ENVFIX"
else
  pyv="$("$py" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null)"
  if "$py" -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; then
    ok "python $pyv: $py"
  else
    bad "python $pyv at $py: 3.11 or later is needed"
    fix "$ENVFIX"
  fi
  if [ -n "${CONDA_PREFIX:-}" ] && [ -z "${PYTHON:-}" ]; then
    case "$py" in
      "$CONDA_PREFIX"/*) ;;
      *) warn "python3 is $py, not from the active conda environment ($CONDA_PREFIX)"
         fix "conda install -c conda-forge python numpy matplotlib vtk  (in that environment)" ;;
    esac
  fi
  for mod in numpy matplotlib; do
    if out="$("$py" -c "import $mod; print($mod.__version__)" 2>&1)"; then
      ok "$mod $out"
    else
      bad "$mod: cannot import with $py"
      printf '        %s\n' "$(printf '%s\n' "$out" | tail -1)"
      fix "conda install -c conda-forge numpy matplotlib vtk"
    fi
  done
  if out="$("$py" -c 'import vtk; print(vtk.vtkVersion.GetVTKVersion())' 2>/dev/null)"; then
    ok "vtk $out"
  else
    warn "vtk not importable: 3D renders (RENDER_3D=1) unavailable"
  fi
fi

# --- Geant4 ----------------------------------------------------------------
[ $quiet = 1 ] || echo "Geant4"
if ! command -v geant4-config >/dev/null 2>&1; then
  bad "geant4-config not found: Geant4 environment not active"
  fix "conda activate gdml-variations   (or your Geant4 environment)"
else
  g4v="$(geant4-config --version)"
  case "$g4v" in
    11.[4-9]*|11.[1-9][0-9]*|1[2-9].*) ok "Geant4 $g4v: $(command -v geant4-config)" ;;
    *) warn "Geant4 $g4v: gdmlvar has been checked against 11.4" ;;
  esac
  if [ "$(geant4-config --has-feature gdml)" = "yes" ]; then
    ok "GDML support"
  else
    bad "this Geant4 was built without GDML"
    fix "conda install -c conda-forge geant4"
  fi
  # Geant4's CMake config needs the expat it was built with; without the
  # environment's headers CMake falls back to the macOS SDK's older copy.
  if [ -n "${CONDA_PREFIX:-}" ]; then
    case "$(command -v geant4-config)" in
      "$CONDA_PREFIX"/*)
        if [ -f "$CONDA_PREFIX/include/expat.h" ]; then
          ok "expat headers in $CONDA_PREFIX"
        else
          bad "expat headers missing from $CONDA_PREFIX (needed to build g4app)"
          fix "conda install -c conda-forge expat"
        fi ;;
    esac
  fi
  # needed by FTFP_BERT, QGSP_BIC and their EM options; others are optional
  required=" G4ENSDFSTATEDATA G4LEDATA G4LEVELGAMMADATA G4PARTICLEXSDATA "
  missing_req="" missing_opt=""
  while read -r name var path; do
    [ -n "${var:-}" ] || continue
    dir="${!var:-$path}"
    if [ -d "$dir" ]; then
      :
    elif [ "${required#* $var }" != "$required" ]; then
      missing_req="$missing_req $name"
    else
      missing_opt="$missing_opt $name"
    fi
  done <<EOF
$(geant4-config --datasets)
EOF
  if [ -n "$missing_req" ]; then
    bad "Geant4 data sets missing:$missing_req"
    fix "conda install -c conda-forge geant4   (installs the geant4-data-* packages)"
  else
    ok "Geant4 data sets needed by the sample physics lists"
  fi
  [ -z "$missing_opt" ] || warn "optional Geant4 data sets missing:$missing_opt"
fi

# --- build tools -------------------------------------------------------------
[ $quiet = 1 ] || echo "Build tools (for g4app)"
if command -v cmake >/dev/null 2>&1; then
  cv="$(cmake --version | head -1 | awk '{print $3}')"
  case "$cv" in
    3.1[6-9]*|3.[2-9][0-9]*|[4-9].*) ok "cmake $cv" ;;
    *) bad "cmake $cv: 3.16 or later is needed"; fix "conda install -c conda-forge cmake" ;;
  esac
else
  bad "cmake not found"
  fix "conda install -c conda-forge cmake make cxx-compiler"
fi
cxx="${CXX:-}"
[ -n "$cxx" ] || cxx="$(command -v c++ || command -v clang++ || command -v g++ || true)"
if [ -n "$cxx" ] && command -v "$cxx" >/dev/null 2>&1; then
  ok "C++ compiler: $cxx"
else
  bad "no C++ compiler"
  fix "conda install -c conda-forge cxx-compiler"
fi

# --- FreeCAD (GDML generation only) -----------------------------------------
[ $quiet = 1 ] || echo "FreeCAD (for generating GDML)"
fc="${FREECAD:-}"
if [ -z "$fc" ]; then
  if [ "$(uname)" = "Darwin" ]; then
    fc="$(ls -d /Applications/FreeCAD*.app 2>/dev/null | sort -V | tail -1 || true)"
  else
    fc="$(command -v freecad || command -v FreeCAD || true)"
  fi
fi
if [ -n "$fc" ] && [ -e "$fc" ]; then
  ok "FreeCAD: $fc"
else
  warn "FreeCAD not found: set FREECAD to the FreeCAD.app or executable"
fi
gdml=""
for d in "$HOME/Library/Application Support/FreeCAD" "$HOME/.local/share/FreeCAD" "$HOME/.FreeCAD"; do
  [ -d "$d" ] || continue
  gdml="$(find -L "$d" -maxdepth 7 -path '*freecad/gdml/GDMLDesign.py' 2>/dev/null | head -1)"
  [ -n "$gdml" ] && break
done
if [ -n "$gdml" ]; then
  ok "GDML workbench with GDMLDesign: $(dirname "$(dirname "$(dirname "$gdml")")")"
else
  warn "GDML workbench with the GDMLDesign API not found in FreeCAD's Mod folders"
  fix "install the GDML workbench (Main branch, 2.2.16 or later)"
fi

if [ $fail = 1 ]; then
  echo "Setup incomplete: fix the FAIL lines above (see README, Requirements)."
  exit 1
fi
[ $quiet = 1 ] || echo "Setup OK."
exit 0
