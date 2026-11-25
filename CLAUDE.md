# GDML Design Variations — guide for AI assistants

Orientation for AI coding and review assistants working in this repo.
Read [README.md](README.md) and [docs/WORKFLOW.md](docs/WORKFLOW.md) first.

## Your role

AI takes part in **design** and **review** only:

- **Design**: write or change `studies/<name>/build.py`, `study.toml` and
  `metrics.py`; propose variants.  Proposed variants need the user's
  approval before any run.
- **Review**: read `results/<name>/review_input.md`, plots and renders, and
  write `results/<name>/REVIEW.md` following
  [docs/REVIEW_GUIDE.md](docs/REVIEW_GUIDE.md).

GDML generation, Geant4 runs and analysis are scripts (`pipeline/`).  You
may run them when the user asks, as you would any command, but:

- never edit files under `results/` other than `REVIEW.md`;
- never put numbers in a review that did not come from the pipeline's
  outputs, and always give their errors;
- report validity problems (failed runs, overlaps, reference mismatches)
  before conclusions.

## Key facts

- Geometry is built with the GDML workbench's scripting API,
  `freecad.gdml.GDMLDesign` (`gd.apiSummary()` lists it).  Use it rather
  than creating FreeCAD objects by hand.  The `make*` functions live at the
  end of `GDMLObjects.py` in the workbench.
- GDML export needs the FreeCAD GUI, so `generate_gdml.py` runs inside
  FreeCAD: through `pipeline/gen_gdml.sh`, the FreeCAD Python console, or
  the FreeCAD MCP server's `execute_code`.
- Detectors are volumes marked with `gd.setSensitive(vol, NAME)`.  The
  marking is exported as a GDML `SensDet` auxiliary, and `gdmlvar` turns it
  into a sensitive detector named NAME.  Copy numbers (`placeCopy(...,
  copynumber=i)`) are recorded per hit.
- Two kinds of variation: geometry/material (one FreeCAD export each) and
  physics (physics list, source: applied by Geant4 to every export).  Both
  live in `study.toml`; `geometry_variants.csv` and `physics_variants.csv`
  are generated from it by `tools/export_csv.py`.  Never edit the CSVs.
- `pipeline/study.py` is standard library only: FreeCAD imports it.
- Units: mm, MeV, g/cm3 throughout, as in the file and key names.

## Checks before committing

```bash
python3 tools/export_csv.py          # after any change to a study.toml
python3 tests/test_builds.py
python3 tests/test_csv.py
python3 tests/test_pipeline.py
python3 -m py_compile pipeline/*.py studies/*/*.py tests/*.py tools/*.py
```

C++ (`g4app/`): build with CMake against Geant4 11 with GDML.

## Conventions

- Short, focused functions; the study-specific code lives in the study.
- New metrics need an error estimate, and a reference value wherever one
  exists.
- Work goes on a branch.  The user pushes.
