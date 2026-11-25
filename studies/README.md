# Studies

Each study is a directory with three files you write and two that are
generated.  The pipeline finds a study by its directory name (`shield` =
`studies/shield`).

| file | what it holds | used by |
|---|---|---|
| `study.toml` | description, objective, world, custom materials, default parameters, variants, physics lists, sources, scoring mesh, metrics to compare and plot, reference values, check tolerances | everything |
| `build.py` | `build(gd, params)`: builds one variant with `freecad.gdml.GDMLDesign` | `pipeline/generate_gdml.py` in FreeCAD |
| `metrics.py` | `run_metrics(ctx)`, `derived(rows, study)`, optional `extra_plots(...)` | `pipeline/analyse.py` |
| `geometry_variants.csv` | *generated*: one row per FreeCAD export, every build parameter | people (spreadsheet view) |
| `physics_variants.csv` | *generated*: one row per Geant4 setting (physics list × source) | people (spreadsheet view) |

Geometry and material variations need one FreeCAD export each.  Physics
variations (physics lists, sources) are applied by Geant4 to every export,
at run time.  `study.toml` defines both; `python3 tools/export_csv.py`
rewrites the two tables from it, and `pipeline/run_all.sh` does so too.
Never edit the CSV files by hand: `tests/test_csv.py` fails if they differ
from `study.toml`.

## study.toml

```toml
[study]
name = "shield"                 # = directory name; letters, digits, _
title = "..."
description = """..."""
objective = """..."""           # what the review must answer
primary_metric = "dose_transmission"
better = "lower"                # or "higher"

[world]
size_mm = [400.0, 400.0, 400.0] # full lengths, centred on the origin
material = "G4_Galactic"

[materials.LYSO]                # optional: added with GDMLDesign.addMaterial
density = "7.1 g/cm3"
formula = "Lu9Y1Si5O25"         # or mixture = "0.7 G4_Cu + 0.3 G4_Zn"

[defaults]                      # parameters every variant starts from
width_mm = 300.0

[[variants]]                    # one per design variation
name = "Pb_10mm"
material = "G4_Pb"
thickness_mm = 10.0
note = "optional, shown in the review"

[physics]
lists = ["FTFP_BERT", "FTFP_BERT_EMZ"]   # Geant4 reference lists (+ EM option)

[[sources]]                     # General Particle Source
name = "Cs137_pencil"
particle = "gamma"
energy_MeV = 0.661657
position_mm = [0.0, 0.0, -150.0]
direction = [0.0, 0.0, 1.0]     # pencil beam (default)
# cone_half_angle_deg = 30.0    # or: isotropic cone about +z
# disc_radius_mm = 10.0         # or: parallel beam over a disc
# extra_gps = ["/gps/..."]      # anything else
events = 100000

[mesh]                          # optional energy-deposit mesh -> mesh.vti
half_size_mm = [150.0, 150.0, 90.0]
centre_mm = [0.0, 0.0, 80.0]
bins = [60, 60, 90]
physics = ["FTFP_BERT"]         # lists that write it (default: the first)

[analysis]
compare = ["dose_transmission"] # compared between physics lists
plot = ["dose_transmission"]

[reference]                     # free-form, read by metrics.py
[checks]                        # tolerances: <metric>_rel_tol, physics_rel_tol, ...
```

The world, every source and the mesh must lie inside the world box
(`tests/test_builds.py` checks this).  Every run of the study is
variants x physics lists x sources.

## build.py

```python
def build(gd, p):
    """gd = freecad.gdml.GDMLDesign; p = this variant's parameters (dict).
    The document exists, its world is sized and custom materials added."""
    box = gd.makeBox(100, 100, p["thickness_mm"], material=p["material"],
                     name="Shield", position=(0, 0, p["thickness_mm"] / 2))
    gd.setSensitive(box, "Shield")     # a detector named "Shield"
```

- Every volume that should record energy needs `gd.setSensitive(vol, NAME)`.
  Volumes may share a name; copies made with `gd.placeCopy(...,
  copynumber=i)` keep it, and the copy number is recorded per hit.
- Raise an exception for parameters that make no sense; the variant is then
  reported as failed in `results/<study>/gdml/generation.json`.
- `gd.apiSummary()` in FreeCAD lists the whole API.

## metrics.py

```python
def run_metrics(ctx):
    """One run.  ctx has: study, variant (.name, .params), physics,
    source (.name, .particle, .energy_MeV, ...), key, run_dir,
    summary (summary.json as a dict), events ({column: numpy array}).
    events columns: <detector>_edep_MeV, <detector>_uncollided (0/1).
    Return (metrics, references):
      metrics    {name: (value, error or None)}
      references {name: expected value, or (low, high) allowed range}"""

def derived(rows, study):
    """All runs: add metrics that combine runs (e.g. relative to a
    reference variant).  rows are dicts with variant, physics, source and
    every metric as <name> and <name>_err."""

def extra_plots(contexts, study, outdir, plt):   # optional
    """Study-specific figures; return the list of files written."""
```

## Adding a study

1. Copy a sample study directory and rename it (and `[study] name`).
2. Write `build.py`; try it in FreeCAD:
   `from pipeline import generate_gdml; generate_gdml.generate("mystudy", only="First*")`.
3. Write `metrics.py`, with a reference value wherever one exists.
4. `python3 tools/export_csv.py mystudy` to write the variation tables.
5. `python3 tests/test_builds.py` (add the study's detectors to
   `EXPECTED_SD`), then `pipeline/run_all.sh mystudy` with
   `EVENTS_SCALE=0.05` for a quick first look.
