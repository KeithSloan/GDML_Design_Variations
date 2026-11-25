# Design-variation studies with FreeCAD GDML and Geant4: a scripted pipeline with AI-assisted design and review

Keith Sloan — draft, November 2026

> **Status.** Section 6 reports the first full run of the three sample
> studies (round 1, 25 November 2026).  The full reviews, metric tables,
> plots and renders are in [docs/results/round1](results/round1/README.md).
> Round 2 (the variants proposed by the reviews) is pending.

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
built-in check against tabulated data, show the approach.  In the first
full run (102 Geant4 runs, about 11 minutes on a laptop) the checks
confirmed the FreeCAD → GDML → Geant4 chain, including custom materials.
They also exposed a systematic 1–3 % excess photon attenuation in the
standard electromagnetic option at 662 keV, and the review found that one
study's design could not answer half of its own objective.

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

Round 1 could not show LaBr₃'s main advantage, its energy resolution, so
round 2 applies resolution in the analysis.  Each event's deposited energy
is smeared with a Gaussian of FWHM f·√(E·E₀), where f is the crystal's
published FWHM at 662 keV (`[resolution]` in `study.toml`: NaI 7.0 %,
CsI 8.5 %, BGO 10 %, LYSO 7.5 %, LaBr₃ 3.0 %).  The smearing is seeded from
the run key, so it is reproducible.  Three metrics follow:
- resolved peak efficiency: full-energy events inside E₀ ± FWHM;
- peak purity: the fraction of events in that window that are full-energy
  events, the rest being Compton continuum smeared in;
- peak-to-Compton: peak height over the mean height of the 358–382 keV
  Compton plateau.

### 4.4 Hadron calorimeter (round 2)

The round-1 calorimeters were 0.8–2.5 interaction lengths deep, too shallow
to contain a 10 GeV pion shower, so their pion results could not answer the
e/π question.  The `hcal` study reuses the calorimeter's geometry and
metrics (its `build.py` and `metrics.py` load the calorimeter's by path) at
800 × 800 mm and 1500 mm deep.  The variants are:
- Fe 20 mm / scintillator 5 mm × 60 layers (about 7.5 λ);
- Fe 10/5 × 100 (about 6.6 λ);
- Pb 10/2.5 × 120 (about 7.0 λ), lead to scintillator 4:1 by thickness, the
  ratio associated with compensation.

The depths in λ use the interaction lengths Geant4 reported in round 1.
The sources are 10 GeV electrons and π⁺ (1000 events each).  The physics
lists are FTFP_BERT, QGSP_BIC and FTFP_BERT_HP; the last adds
high-precision neutron transport, which matters for the slow-neutron
signal in hydrogen-rich scintillator.  One metric is added to the
calorimeter's: the non-compensation |e/π − 1|.  The objective is the best
pion resolution with e/π close to 1.

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

Round 1 ran every study at full statistics on a MacBook Air (macOS 26.1,
arm64).  The GDML was generated with FreeCAD 1.1.4 and GDML workbench
2.2.16, and simulated with Geant4 11.4.3 from conda-forge.  All 102 runs
succeeded: 30 shield, 36 calorimeter and 36 detector.  They took about
11 minutes elapsed (35 process-minutes), with runs in parallel (by
default one per CPU core, less one).  The 22 GDML exports took 0.7–1.8 s
each.  No run reported a geometry
overlap.  Everything below is taken from the round-1 reviews and tables in
[docs/results/round1](results/round1/README.md).  Values are quoted for the
three physics lists in the order given in section 4.

### 6.1 Validation

- **Attenuation.**  Of the 48 uncollided-fraction checks (30 shield, 18
  detector), 46 pass.
  - The two failures, W 10 mm (−2.5 %, −3.4 σ) and CsI 38 mm (−2.9 %,
    −3.8 σ), are both FTFP_BERT.
  - FTFP_BERT is below the NIST value in all 15 shielded cases (−0.3 % to
    −2.9 %).  FTFP_BERT_EMZ and FTFP_BERT_LIV scatter on both sides of it.
  - So the same GDML files are right, and the difference is in the physics
    model.  Without polarisation, option 0's Compton process uses
    `G4KleinNishinaCompton`, an empirical cross-section parametrisation.
    The EMZ and LIV options use the Monash and Livermore models below
    20 MeV.
  - The results fit option 0 attenuating 662 keV photons about 1–2 % more
    than the NIST tables.
- **Custom materials.**  LYSO and LaBr₃, defined in FreeCAD with
  `addMaterial`, pass their attenuation checks under every list (within
  2.6 σ).  This tests formula-defined materials end to end.
- **Calorimeter.**  The electron e/mip lies within the expected range in
  all 18 runs (0.681–0.887), highest for iron and lowest for the thickest
  lead layers.
- **Spectra.**  The crystal spectra show the Compton edge near 0.48 MeV and
  the full-energy peak at 0.662 MeV.

### 6.2 Shield

The dose transmission ranking is the same under all three lists
([shield/REVIEW.md](results/round1/shield/REVIEW.md),
[plot](results/round1/shield/plots/dose_transmission__Cs137_pencil.png)).

| variant | ρt (g/cm²) | dose transmission |
|---|---|---|
| Pb 20 mm | 22.7 | 0.1355 ± 0.0050 / 0.1442 ± 0.0052 / 0.1527 ± 0.0054 |
| Fe 40 mm | 31.5 | 0.2390 ± 0.0066 / 0.2352 ± 0.0064 / 0.2326 ± 0.0064 |
| W 10 mm | 19.3 | 0.2469 ± 0.0070 / 0.2594 ± 0.0073 / 0.2443 ± 0.0069 |
| concrete 100 mm | 23.0 | 0.3927 ± 0.0088 / 0.3856 ± 0.0087 / 0.3850 ± 0.0087 |
| Pb 10 mm | 11.35 | 0.4062 ± 0.0096 / 0.4042 ± 0.0096 / 0.4009 ± 0.0095 |

- **Per mass:** lead and tungsten attenuate the dose about twice as well
  as iron or concrete (effective 0.067–0.088 vs 0.039–0.046 cm²/g).
- **Per thickness:** tungsten is best.
- **Build-up:** the low-Z shields show the larger build-up (2.3–2.4 at
  their thicker variants, against 1.2–1.8 for lead).
- **Physics lists:** no dose-transmission difference between lists
  exceeds 3 σ.  The largest is +12.7 % (2.3 σ) for Pb 20 mm.

### 6.3 Sampling calorimeter

**Electrons (1 GeV).**  The resolution ranking is the same under all three
lists ([calorimeter/REVIEW.md](results/round1/calorimeter/REVIEW.md)):
- Pb 1 mm / scintillator 2 mm × 120: 0.0633 ± 0.0010 / 0.05892 ± 0.00094 /
  0.05924 ± 0.00094.
- The 2 mm / 4 mm baseline: 0.0802 ± 0.0013 / 0.0811 ± 0.0013 /
  0.0766 ± 0.0012.
- 4 mm / 4 mm: 0.1176–0.1225.

Halving both layers improves σ/E by 21–27 % at the same depth.  For
compactness, the tungsten variant (324 mm, 24.5 X₀) contains 98 % of the
energy with a resolution close to the baseline.  Two physics-list effects
are significant:
- **EM option:** EMZ lowers the sampling fraction of the thin-layer
  variant by 2.0 % (11 σ).  This is a calibration effect at fine sampling.
- **Hadronic models:** QGSP_BIC raises the electron sampling fraction of
  the iron/scintillator variant by 1.2 % (4 σ).  The two lists share their
  EM physics, so this points to how photo-nuclear products are treated.
  The cause has not been verified.

**Pions (10 GeV).**  The variants are only 0.83–2.46 interaction lengths
deep, and contain 21–48 % of the pion energy.  The pion resolution
(0.48–1.03) and e/π (1.8–3.7) therefore measure leakage, and no
physics-list difference is significant with 500 pions.  The review
concluded that the pion half of the objective cannot be answered with this
design, and proposed a separate, contained hadron-calorimeter study.

### 6.4 Gamma-ray crystal detector

Absolute full-energy-peak efficiency for the Cs-137 point source, per
photon emitted into 4π, 10⁻³
([detector/REVIEW.md](results/round1/detector/REVIEW.md)).  The ranking is
the same under all three lists.

| variant | crystal mass (kg) | peak efficiency | peak-to-total |
|---|---|---|---|
| NaI 3 × 3 in | 1.274 | 11.100 ± 0.079 / 10.967 ± 0.078 / 11.087 ± 0.079 | 0.552–0.556 |
| BGO 1.5 × 1.5 in | 0.310 | 5.340 ± 0.057 / 5.103 ± 0.056 / 5.109 ± 0.056 | 0.764–0.782 |
| LYSO 1.5 × 1.5 in | 0.308 | 4.486 ± 0.053 / 4.442 ± 0.053 / 4.359 ± 0.052 | 0.689–0.699 |
| CsI 1.5 × 1.5 in | 0.196 | 2.375 ± 0.039 / 2.399 ± 0.039 / 2.449 ± 0.040 | 0.476–0.487 |
| LaBr₃ 1.5 × 1.5 in | 0.221 | 2.156 ± 0.037 / 2.046 ± 0.036 / 2.036 ± 0.036 | 0.399–0.411 |
| NaI 1.5 × 1.5 in | 0.159 | 1.668 ± 0.033 / 1.681 ± 0.033 / 1.690 ± 0.033 | 0.386–0.393 |

- **Size matters most:** the 3-inch NaI has 6.5–6.7 times the peak
  efficiency of the 1.5-inch one.
- **At equal size:** BGO is best (3.0–3.2 × NaI), then LYSO, CsI and
  LaBr₃.  BGO and LYSO are also best per kilogram.
- **Physics lists:** for the high-Z crystals FTFP_BERT gives 4–6 % higher
  peak efficiencies than EMZ and LIV (2–3 σ).  This is in the direction of
  its stronger attenuation.

### 6.5 What the pipeline added

Three outcomes of round 1 come from the pipeline's structure rather than
from any single run:
- **The attenuation offset** of the standard EM option was found because
  every study carries a reference check and every geometry runs under
  several lists.  A single-list study would have shown it as a 1–3 %
  shift in shielding performance, with nothing to compare it against.
- **The design flaw** in the calorimeter's pion half was found by the
  review, from the containment and longitudinal profiles, before any
  conclusion was drawn from the pion numbers.
- **Two pipeline faults** were caught by the first runs themselves:
  - a crash when writing summaries for runs with a scoring mesh;
  - near-zero deposits in vacuum drawn as if they were energy.
  Both were fixed before the full run.  The reproducible records (seeds,
  versions, logs) made each a short investigation.

## 7. Discussion and limitations

- **Deposited energy is not a detector signal.**  No light collection,
  quenching or electronics are simulated.  Calorimeter resolutions and e/π
  are therefore ideal values, best used to compare variants; Birks
  quenching in particular changes e/π in scintillator.  The detector
  study's energy resolution (from round 2) is a published FWHM applied in
  the analysis, not simulated.
- **Choice of EM option for photons.**  Round 1 shows the standard EM
  option (FTFP_BERT) attenuating 662 keV photons 1–3 % more than NIST in
  high-Z materials.  For absolute shielding or efficiency numbers at these
  energies, EMZ or LIV should be preferred.
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
