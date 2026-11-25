# GDML Design Variations

A pipeline for testing **design variations** of a detector, shield or
other geometry with **Geant4**, under several **physics lists**.  Designs
are parametric scripts for the [FreeCAD GDML
workbench](https://github.com/KeithSloan/GDML).  Each variant is exported
to GDML and run through one Geant4 application for every physics list and
particle source.  The results are reduced to metrics with statistical
errors, checked against reference values, written as VTK files and plots,
and gathered into a packet for review.

```
 design (build.py) ──► FreeCAD + GDML workbench ──► variant.gdml ─┐
 variants (study.toml)                                            │
                     physics lists × sources × variants ──► gdmlvar (Geant4)
                                                                  │
            metrics + checks + plots + mesh.vti ◄─────────────────┘
                              │
                     review_input.md ──► review ──► next variants
```

## Who does what

**AI is involved only in design and review.**  The stages in between are
plain scripts, so every number comes from Geant4 and every run can be
repeated exactly.

| Stage | Done by |
|---|---|
| 1. Design: parametric `build.py`, objective, metrics | AI with you |
| 2. Variations: the `[[variants]]` table | AI proposes, **you approve** |
| 3. GDML for every variant | script (FreeCAD) |
| 4. Geant4 runs, metrics, checks, plots | scripts |
| 5. Review: validity, results, recommendation, next variants | AI, **you decide** |

Details: [docs/WORKFLOW.md](docs/WORKFLOW.md); review steps:
[docs/REVIEW_GUIDE.md](docs/REVIEW_GUIDE.md).

## Two kinds of variation

| Kind | Examples | Handled by | Table |
|---|---|---|---|
| **Geometry and material** | thickness, number of layers, crystal size, absorber material | one FreeCAD export per variant: n variants = n GDML files | `studies/<name>/geometry_variants.csv` |
| **Physics** | physics list (hadronic model, EM option), particle source | Geant4 at run time, on every GDML file, without re-exporting | `studies/<name>/physics_variants.csv` |

A study runs every geometry variant under every physics setting.  Both
kinds are defined in the study's `study.toml`, which is the source of
truth.  The two CSV tables are generated from it (`tools/export_csv.py`) so
the variations can be read as spreadsheets, on GitHub or in Numbers, Excel
or LibreOffice.  Do not edit the CSV files by hand.

## Sample studies

| Study | Design | Varied | Source | Physics lists | Primary metric | Check against |
|---|---|---|---|---|---|---|
| [shield](studies/shield) | slab shield, water phantom behind | material (Pb, W, Fe, concrete), thickness | Cs-137 662 keV pencil beam | FTFP_BERT, _EMZ, _LIV | dose transmission | uncollided fraction vs NIST attenuation |
| [calorimeter](studies/calorimeter) | sampling calorimeter, absorber/active layers | absorber (Pb, W, Fe), active (scintillator, LAr), thicknesses, layers | 1 GeV e⁻, 10 GeV π⁺ | FTFP_BERT, QGSP_BIC, FTFP_BERT_EMZ | EM energy resolution | e/mip of the sampling fraction |
| [detector](studies/detector) | crystal in Al housing | crystal (NaI, CsI, BGO, LYSO, LaBr3), size | Cs-137 point source (cone), pencil | FTFP_BERT, _EMZ, _LIV | full-energy-peak efficiency | crystal attenuation vs NIST |

LYSO and LaBr3 are defined in the study with `GDMLDesign.addMaterial`, so
the detector study also tests custom materials through GDML into Geant4.

## Requirements

- FreeCAD 1.1 with the GDML workbench, including its `GDMLDesign` scripting
  API (Main branch, 2.2.16 or later)
- Geant4 11 built with GDML (e.g. conda-forge `geant4`), its data sets,
  CMake and a C++17 compiler
- Python 3.11+ with numpy and matplotlib; vtk for 3D renders
  (`python3 -m pip install -r requirements.txt`)

## Quick start

```bash
conda activate g4                          # Geant4 environment
python3 -m pip install -r requirements.txt
pipeline/run_all.sh shield                 # GDML, build, runs, analysis
EVENTS_SCALE=0.05 pipeline/run_all.sh      # all studies, quick look
```

Then ask for the review of `results/shield/review_input.md` (stage 5).

The steps can also be run one at a time:

```bash
pipeline/gen_gdml.sh shield                # FreeCAD: results/shield/gdml/
cmake -S g4app -B g4app/build -DCMAKE_BUILD_TYPE=Release && cmake --build g4app/build
python3 pipeline/run_matrix.py shield -j 8 # Geant4: results/shield/runs/
python3 pipeline/render.py shield --3d     # results/shield/render/
python3 pipeline/analyse.py shield         # metrics, flags, plots, review_input.md
```

From inside FreeCAD (Python console, macro or the FreeCAD MCP server), the
GDML step is:

```python
import sys; sys.path.insert(0, "/path/to/GDML_Design_Variations")
from pipeline import generate_gdml
generate_gdml.generate("shield")
```

## What a run produces

`results/<study>/` (not committed):

| Path | Contents |
|---|---|
| `gdml/<variant>.gdml`, `.json` | geometry; parameters, design tree, FreeCAD/GDML versions |
| `runs/<variant>__<physics>__<source>/` | `run.mac`, `g4.log`, `events.csv.gz` (energy per detector per event), `summary.json` (sums, masses, Geant4 warnings), `mesh.vti` |
| `runs.jsonl` | one line per finished run: status, seed, overlaps, time |
| `metrics.csv`, `flags.json` | metrics with errors; everything the review must look at |
| `plots/`, `render/` | metric plots; slices and 3D views of the energy deposit |
| `review_input.md` | the review packet |
| `REVIEW.md` | the review |

`mesh.vti` holds energy per primary, dose, density and material per cell,
and opens in ParaView or any VTK program.

## Repository

| Path | |
|---|---|
| `studies/` | the studies (`study.toml`, `build.py`, `metrics.py`, the two variation tables); format in [studies/README.md](studies/README.md) |
| `g4app/` | `gdmlvar`: GDML geometry, `SensDet` volumes as detectors, any reference physics list by name, GPS source, scoring mesh |
| `pipeline/` | the scripted stages |
| `tests/` | `test_builds.py` (geometry of every variant, no FreeCAD needed), `test_pipeline.py` (all scripts against a stand-in for Geant4), `test_csv.py` (variation tables up to date) |
| `tools/export_csv.py` | writes the variation tables from `study.toml` (`--check` to verify) |
| `tools/attenuation_refs.py` | regenerates the NIST reference coefficients |
| `docs/` | workflow, review guide, [paper](docs/PAPER.md) |

## Status

- `gdmlvar` compiles against the Geant4 11.4.3 headers.  It has not yet
  been built and run against a full Geant4 install.
- The Python stages pass `tests/test_pipeline.py`, every variant passes
  `tests/test_builds.py`, and the variation tables pass `tests/test_csv.py`.
- The first end-to-end run, with FreeCAD and Geant4 on one machine, is the
  next step.  The paper's results section is waiting for it.

## Licence

GPL-3.0-or-later, see [LICENSE](LICENSE).  Results produced with Geant4
should cite the Geant4 papers (see the paper's references).
