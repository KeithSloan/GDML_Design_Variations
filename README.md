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
| [hcal](studies/hcal) (round 2) | contained hadron calorimeter, the calorimeter's layers at 800 × 800 × 1500 mm | absorber (Fe, Pb), sampling | 10 GeV e⁻ and π⁺ | FTFP_BERT, QGSP_BIC, FTFP_BERT_HP | pion energy resolution | e/mip of the sampling fraction |

LYSO and LaBr3 are defined in the study with `GDMLDesign.addMaterial`, so
the detector study also tests custom materials through GDML into Geant4.

## Requirements

- **FreeCAD 1.1** with the GDML workbench, including its `GDMLDesign`
  scripting API (Main branch, 2.2.16 or later).  Only needed to generate
  GDML.
- **One conda environment** with everything else, from
  [environment.yml](environment.yml) (conda-forge):
  - Geant4 11.4 with GDML and its data sets;
  - expat, CMake, make and a C++ compiler, to build `g4app`;
  - Python 3.11+ with numpy, matplotlib and vtk.

Geant4, the compiler and Python must all come from that one environment.
Two mix-ups break the pipeline on macOS:
- If the environment has no Python of its own, `python3` falls through to
  Homebrew's or the system's.
- If the environment has no expat headers, CMake takes the older expat in
  the macOS SDK, and `find_package(Geant4)` fails.

`pipeline/check_setup.sh` reports both, and `run_all.sh` runs it first.

## Setup

```bash
conda env create -f environment.yml        # new environment "gdml-variations"
conda activate gdml-variations
#   or, to add what is missing to an existing Geant4 environment:
#   conda env update -n g4 -f environment.yml && conda deactivate && conda activate g4
pipeline/check_setup.sh                    # every line ok (FreeCAD lines may warn)
cp pipeline/local.env.example pipeline/local.env   # then set FREECAD etc. for this machine
```

`pipeline/local.env` (not committed) holds machine-specific settings such
as which FreeCAD generates the GDML.  Otherwise the scripts use the newest
`/Applications/FreeCAD*.app`.  A variable set on the command line overrides
it.

`requirements.txt` lists the Python packages for pip users, but the conda
environment is the supported setup.

## Quick start

```bash
EVENTS_SCALE=0.05 pipeline/run_all.sh shield   # quick look: GDML, build, runs, analysis
pipeline/run_all.sh                            # all studies, full statistics
```

Close FreeCAD first: `run_all.sh` starts its own copy to generate the GDML.

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
| `environment.yml` | the conda environment (Geant4, build tools, Python packages) |
| `pipeline/check_setup.sh` | checks the environment and says what to fix |
| `tools/export_csv.py` | writes the variation tables from `study.toml` (`--check` to verify) |
| `tools/attenuation_refs.py` | regenerates the NIST reference coefficients |
| `docs/` | workflow, review guide, [paper](docs/PAPER.md) |

## Status

- **Round 1 complete** (25 Nov 2026): all three studies at full statistics.
  - 102/102 Geant4 runs on macOS (arm64), Geant4 11.4.3 from conda-forge.
  - GDML from FreeCAD 1.1.4 and GDML workbench 2.2.16.
  - Reviews, tables and plots are in
    [docs/results/round1](docs/results/round1/README.md), and the paper's
    results section covers them.
- **Round 2 complete** (25 Nov 2026): the variants proposed by the round-1
  reviews, 141/141 runs, 87/90 reference checks pass.  Reviews, tables and
  plots are in [docs/results/round2](docs/results/round2/README.md); the
  paper's section 6.6 summarises them.
  - Shield: at equal mass, lead gives 18–27 % less dose than tungsten and
    about half that of iron.
  - Calorimeter: 1 mm lead with 2 mm liquid argon gives the best electron
    resolution (σ/E 0.055–0.058 at 1 GeV).
  - Detector: at equal mass BGO gives 27–30 % more peak efficiency than
    NaI.  FTFP_BERT simulates no X-ray escape, so quote EMZ or LIV.
- **Round 2 design** (branch `round-2-design`), both proposed by the round-1
  reviews:
  - the detector study applies each crystal's published energy resolution
    in the analysis, giving resolved peak efficiency, peak purity and
    peak-to-Compton;
  - a new `hcal` study, deep enough (about 7 λ) to contain 10 GeV pions,
    with three approved variants, not yet run.
- **Round 3 proposals** are in the round-2 reviews, awaiting approval.
- **Tests:** the Python stages pass `tests/test_pipeline.py`, every variant
  passes `tests/test_builds.py`, and the variation tables pass
  `tests/test_csv.py`.  `pipeline/check_setup.sh` is tested against
  stand-in environments.

## Licence

GPL-3.0-or-later, see [LICENSE](LICENSE).  Results produced with Geant4
should cite the Geant4 papers (see the paper's references).
