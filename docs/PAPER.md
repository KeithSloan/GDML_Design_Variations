# Design-variation studies with FreeCAD GDML and Geant4: a scripted pipeline with AI-assisted design and review

Keith Sloan — draft, November 2026

> **Status.** Sections 1–5 and 7–8 describe the pipeline and the three
> sample studies as implemented in this repository.  Section 6 (Results) is
> waiting for the first full run; it says which tables and figures will go
> there and where they come from.  No results are quoted before then.

## Abstract

We describe an open-source pipeline for comparing design variations of a
geometry (a shield, a calorimeter, a detector) with Geant4, under several
physics lists.  A design is a short parametric Python script written
against the scripting API of the FreeCAD GDML workbench.  A table of
variants is expanded into one GDML file per variant.  A single Geant4
application runs every variant with every physics list and particle source,
taking its detectors from `SensDet` auxiliary tags in the GDML.  The
outputs are reduced to metrics with statistical errors, which are checked
automatically against reference values and against each other across
physics lists.  Energy-deposit maps are written as VTK image data.  An AI
assistant takes part at two points only: turning an idea into a parametric
design with proposed variations, and reviewing the checked results against
the study's stated objective.  Generation, simulation and analysis are
deterministic scripts, so every number in a review can be traced to a
Geant4 run with a recorded seed.  Three sample studies, each with a
built-in check against tabulated data, show the approach.

## 1. Introduction

Choosing between designs with Monte Carlo simulation usually means
building each variant by hand, running it, extracting numbers and
comparing them.  It is easy to compare variants whose differences are
statistical noise, to rely on one physics list without knowing whether the
conclusion depends on it, or to miss a geometry error that makes one
variant wrong.

The FreeCAD GDML workbench [6] already lets a geometry be built in a CAD
environment and exported to GDML [4], the geometry format Geant4 [1–3]
reads directly.  Its scripting API, `GDMLDesign`, builds geometry from
Python, which makes a design *parametric*: one function, many variants.
This work adds what is needed around it to study variations
systematically: a study format, a generic Geant4 application, a run matrix,
automatic checks and a review step.

A second aim is to use an AI assistant where it helps and nowhere else.
Design and interpretation call for judgement.  Running a hundred
simulations does not, and an assistant in that loop would add cost and
variability.  The pipeline is built around that split (section 2).

## 2. The pipeline

| # | Stage | Done by | Output |
|---|---|---|---|
| 1 | Design | AI assistant with the user | `build.py`, `study.toml`, `metrics.py` |
| 2 | Variations | AI proposes, user approves | `[[variants]]` in `study.toml` |
| 3 | GDML generation | script, in FreeCAD | one GDML file per variant |
| 4 | Geant4 runs, analysis, checks | scripts | metrics, flags, plots, VTK maps, review packet |
| 5 | Review | AI assistant; the user decides | `REVIEW.md`; proposed next variants |

Stages 3–4 are run by one command (`pipeline/run_all.sh`), which resumes
after an interruption.  The user approves the two hand-overs: the variant
table before any compute (2 → 3), and the review's proposals before the
next round (5 → 2).  Because the analysis stage makes every check that can
be made mechanically, the review starts from established facts, and its
rules require every quoted number to come from the pipeline's outputs with
its error (`docs/REVIEW_GUIDE.md`).

## 3. Implementation

### 3.1 Designs as scripts

A study is a directory with `study.toml` (description, objective, world,
custom materials, default parameters, variants, physics lists, sources,
scoring mesh, reference values), `build.py` and `metrics.py`.
`build(gd, params)` builds one variant through `GDMLDesign`: `makeBox`,
`makeTube`, booleans, `placeCopy` for repeated volumes with copy numbers,
`addMaterial` for materials outside Geant4's NIST list, and `setSensitive`
to mark detector volumes.

Variations are of two kinds.  Geometry and material variations each need
their own GDML export.  Physics variations (the physics list and the
particle source) are applied by Geant4 at run time to every export.  A
study of n geometry variants and m physics settings therefore needs n
exports and n × m runs.  Both kinds are defined in `study.toml`, the
source of truth, and written out as two CSV tables,
`geometry_variants.csv` and `physics_variants.csv`, for reading as
spreadsheets.  A test fails if the tables differ from the TOML.

### 3.2 GDML generation

`pipeline/generate_gdml.py` runs inside FreeCAD.  For each variant it
creates a document, sizes the world, adds the custom materials, calls
`build`, and exports GDML.  It also writes a JSON record of the
parameters, the design tree and the FreeCAD and workbench versions.  GDML
export currently needs the FreeCAD GUI, so generation is serial in one
FreeCAD process.  For the sample studies this takes seconds per variant.

### 3.3 The Geant4 application

`gdmlvar` (`g4app/`, C++17, Geant4 11) reads the GDML with
`G4GDMLParser`, with overlap checking on.  It attaches a sensitive
detector to every logical volume carrying a `SensDet` auxiliary.  Volumes
with the same detector name share one detector; energy is recorded per
copy number.  The physics list is any Geant4 reference list, chosen by name
through `G4PhysListFactory`, including the electromagnetic option suffixes
(`_EMZ`, `_LIV`, …).  The source is the General Particle Source,
configured by a generated macro.  For each event the application records
the energy deposited in each detector, and whether the primary entered the
detector *uncollided* (same energy and direction as generated).  The
uncollided flag is what makes the attenuation checks of section 5
possible.

Outputs are `events.csv` and `summary.json`.  The summary holds sums, sums
of squares and per-copy sums for each detector, and for each volume its
material, density, radiation and interaction lengths, mass and number of
placements.  It also counts Geant4 warnings by code, so overlaps
(`GeomVol1002`) are visible to the analysis.  A command-based scoring mesh
records energy deposit on a 3D grid.  A custom command,
`/gdmlvar/voxelise`, records the material at each cell centre as Geant4
sees it, so deposits can be drawn on the geometry Geant4 actually used.

### 3.4 Run matrix

`pipeline/run_matrix.py` runs variants × physics lists × sources as
parallel processes.  Each run gets its own directory and a seed derived
from its name, so a run can be repeated exactly.  Finished runs are
recorded in `runs.jsonl` and skipped on re-running.

### 3.5 Analysis and checks

`pipeline/analyse.py` calls each study's `run_metrics` and `derived`
functions and then makes four kinds of check:

- **reference**: a metric against an analytic or tabulated value, or an
  allowed range; flagged when it differs by more than 3σ *and* more than a
  set tolerance (2 % for attenuation);
- **physics**: each list against the first, flagged when they differ by
  more than 3σ and more than 1 %;
- **geometry**: any overlap reported by Geant4;
- **runs**: failed, incomplete or missing runs.

It writes `metrics.csv`, `flags.json`, plots of every compared metric with
one series per physics list, and the review packet `review_input.md`.

### 3.6 VTK output

Each mesh run is converted to VTK XML image data (`mesh.vti`).  Its cell
arrays hold energy per primary, dose, density and material.  The files
open in ParaView or any VTK program.  `pipeline/render.py` draws slices
through the beam axis (matplotlib) and, optionally, 3D views with
geometry surfaces and deposit iso-surfaces (VTK, off-screen).

### 3.7 Review

The reviewer reads the packet, plots and renders.  It reports validity
first (failed runs, overlaps, reference mismatches), then treats
differences within about 3σ as no difference.  It separates conclusions
that hold for every physics list from model-dependent ones, answers the
study's objective with its trade-offs, and proposes a small number of next
variants, each with a reason, for the user to approve.

## 4. Sample studies

### 4.1 Gamma shield

A 662 keV (Cs-137) pencil beam crosses a 300 × 300 mm shield slab.  A
10 mm water phantom 150 mm downstream records the dose.  The world is
vacuum.  There are ten variants: no shield (the reference for the
transmission); lead 5/10/20 mm; tungsten 5/10 mm; iron 20/40 mm; ordinary
concrete 50/100 mm.  The physics lists are FTFP_BERT, FTFP_BERT_EMZ and
FTFP_BERT_LIV, which differ in their electromagnetic models; each run has
10⁵ photons.

Metrics:
- dose per photon in the phantom;
- dose transmission relative to no shield;
- uncollided fraction;
- build-up factor (transmission / uncollided fraction);
- effective mass attenuation, −ln T / (ρt).

The objective is the lowest dose, and the lowest dose per areal density.

### 4.2 Sampling calorimeter

There are 200 × 200 mm absorber/active layers, every layer a sensitive
detector with its layer index as copy number.  The six variants are:
- Pb 2 mm / scintillator 4 mm × 60 layers;
- Pb 4/4 × 30;
- Pb 1/2 × 120;
- W 1.4/4 × 60;
- Fe 6/4 × 60;
- Pb 2 / liquid argon 4 × 60.

All have roughly equal depth in radiation lengths.  The sources are 1 GeV
electrons (2000 events) and 10 GeV π⁺ (500 events).  The physics lists are
FTFP_BERT, QGSP_BIC (a different hadronic cascade model) and
FTFP_BERT_EMZ.

Metrics:
- energy resolution σ/E of the active-layer signal, and its stochastic
  term;
- sampling fraction;
- containment;
- e/mip;
- e/π signal ratio;
- longitudinal profile;
- depth in X₀ and λ, from Geant4's material properties.

The objective is the best electromagnetic resolution for a compact depth,
and an e/π close to 1.

### 4.3 Gamma-ray crystal detector

A cylindrical crystal sits in a 1 mm aluminium housing.  A Cs-137 point
source 100 mm in front emits into a 30° cone about the axis.  The six
variants are:
- NaI 1.5″ × 1.5″ (the reference) and 3″ × 3″;
- CsI, BGO, LYSO and LaBr₃, all 1.5″ × 1.5″.

LYSO and LaBr₃ are defined with `addMaterial`, so the study also tests
custom materials end to end.  A second source, an axial pencil beam, is
counted by a vacuum monitor disc behind the detector.  The physics lists
are as in 4.1.

Metrics, all from deposited energy with no detector resolution:
- absolute total efficiency;
- absolute full-energy-peak efficiency;
- peak-to-total ratio;
- crystal mass.

The objective is the highest peak efficiency.

## 5. Validation built into the studies

Each sample study has a check that does not depend on the design question:

- **Shield and detector, attenuation.**  For a pencil beam the fraction of
  photons arriving uncollided must be exp(−Σ μ/ρ · ρ · x) along the path.
  The mass attenuation coefficients μ/ρ (including coherent scattering) at
  661.657 keV come from the Elam, Ravel and Sieber tables [8]. These
  reproduce the NIST values of Hubbell and Seltzer [7] at the tabulated
  energies.  Compounds use the mixture rule with Geant4's own compositions
  (`tools/attenuation_refs.py`).  A mismatch beyond 2 % and 3σ points to
  a wrong thickness, density, composition or position in the exported
  geometry, or to a problem in the physics.  It tests, in one number, the
  whole chain from the FreeCAD design through GDML to Geant4.
- **Calorimeter, sampling fraction.**  The electron sampling fraction
  divided by the MIP sampling fraction, computed from PDG minimum dE/dx
  values [9], must lie in a plausible range (0.55–1.0).  This is a coarse
  check of the layer structure and materials, not a precision test [10].
- **All studies, geometry.**  Geant4's overlap check runs when it reads
  each GDML file; any overlap is a high-severity flag.
- **All studies, physics lists.**  Agreement between lists is a check on
  model dependence, not on correctness: the analysis reports where
  conclusions depend on the choice.

In addition, `tests/test_builds.py` checks every variant's geometry
(containment, sibling overlaps, detectors present, source and mesh inside
the world) without FreeCAD.  `tests/test_pipeline.py` runs every script
against a stand-in for Geant4.

## 6. Results

*Pending the first full run.*  For each study this section will contain:

- the run summary: runs, events, any failures or overlaps;
- the reference checks (pass/fail per run, largest deviation);
- the primary metric for every variant and physics list, with errors, and
  the ranking it gives;
- the physics-list differences that are significant, and whether they
  change the ranking;
- one slice render per variant;
- the review's recommendation and proposed next variants.

These come directly from `results/<study>/review_input.md`, `metrics.csv`
and `REVIEW.md`, and will be copied under `docs/results/`.

## 7. Discussion and limitations

- **Deposited energy is not a detector signal.**  No energy resolution,
  light collection, quenching or electronics are simulated.  Peak
  efficiencies and resolutions are therefore ideal values, best used to
  compare variants.
- **Physics-list spread is not an uncertainty.**  Agreement between
  reference lists shows robustness to model choice, but the lists share
  components and data and need not bracket reality.
- **Reference data range.**  The attenuation references use tables valid
  up to 800 keV; studies at higher energy need another source.  The PDG
  dE/dx values in the calorimeter study were taken from the PDG tables and
  have not been cross-checked within this work.
- **GDML generation is serial**, because the workbench's exporter needs the
  FreeCAD GUI.  Making export work headless would let generation run in
  parallel and in CI.  The obstacle is mainly the exporter finding the
  world volume through the GUI selection.
- **Simulation runs one thread per process**, with the parallelism across
  runs.  This suits matrices of many short runs.  Long runs would benefit
  from Geant4's multi-threaded run manager.
- **Out of scope for the samples**: neutron shielding (high-precision
  neutron data), optical photons and magnetic fields.  Each needs an
  addition to `gdmlvar`.

## 8. Reproducibility

The software environment is one conda-forge environment
(`environment.yml`: Geant4 with its data sets, build tools, Python
packages), checked by `pipeline/check_setup.sh`.  Every run records its
seed, macro, GDML file, physics list, Geant4 version and warnings.  Every GDML file records its parameters, design tree
and the FreeCAD, workbench and repository versions.  Re-running a study
with the same inputs reproduces the same numbers.  The code is available
under the GPL-3.0-or-later.

## Acknowledgements

The pipeline and this draft were developed with the help of an AI
assistant (Claude, Anthropic), in the roles described in section 2.

## References

1. S. Agostinelli et al., "Geant4 — a simulation toolkit", Nucl. Instrum.
   Meth. A 506 (2003) 250–303.
2. J. Allison et al., "Geant4 developments and applications", IEEE Trans.
   Nucl. Sci. 53 (2006) 270–278.
3. J. Allison et al., "Recent developments in Geant4", Nucl. Instrum.
   Meth. A 835 (2016) 186–225.
4. R. Chytracek, J. McCormick, W. Pokorski, G. Santin, "Geometry
   Description Markup Language for physics simulation and analysis
   applications", IEEE Trans. Nucl. Sci. 53 (2006) 2892–2896.
5. FreeCAD, https://www.freecad.org
6. K. Sloan et al., FreeCAD GDML workbench,
   https://github.com/KeithSloan/GDML
7. J. H. Hubbell, S. M. Seltzer, "Tables of X-ray mass attenuation
   coefficients and mass energy-absorption coefficients", NISTIR 5632
   (1995), https://www.nist.gov/pml/x-ray-mass-attenuation-coefficients
8. W. T. Elam, B. D. Ravel, J. R. Sieber, "A new atomic database for X-ray
   spectroscopic calculations", Radiat. Phys. Chem. 63 (2002) 121–128;
   via xraydb, https://xraypy.github.io/XrayDB/
9. Particle Data Group, Atomic and Nuclear Properties of Materials,
   https://pdg.lbl.gov/AtomicNuclearProperties/
10. R. Wigmans, *Calorimetry: Energy Measurement in Particle Physics*,
    2nd ed., Oxford University Press (2017).
11. W. Schroeder, K. Martin, B. Lorensen, *The Visualization Toolkit*,
    4th ed., Kitware (2006).
