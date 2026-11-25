# Workflow: who does what

The pipeline has five stages.  **AI is involved in two of them: design and
review.**  Everything in between (building the GDML, running Geant4,
computing metrics, checking them, drawing plots) is done by ordinary
scripts, so the numbers are reproducible and come only from Geant4.  You
(the person running the study) approve the two hand-overs between them.

| # | Stage | Done by | Input | Output | You |
|---|---|---|---|---|---|
| 1 | **Design** | AI with you | an idea ("a gamma shield") | `studies/<name>/build.py`, `study.toml` (objective, source, physics lists, metrics), `metrics.py` | agree the design and the objective |
| 2 | **Variations** | AI proposes | the design and objective | `[[variants]]` entries in `study.toml`, each with a reason | **approve before any compute** |
| 3 | GDML generation | script: `pipeline/gen_gdml.sh` (FreeCAD + `generate_gdml.py`) | `build.py`, variants | `results/<name>/gdml/*.gdml` and `*.json` | - |
| 4 | Geant4 runs | script: `pipeline/run_matrix.py` (runs `gdmlvar`) | GDML, physics lists, sources | `results/<name>/runs/*/` | - |
| 4a | Analysis and checks | script: `pipeline/analyse.py`, `render.py` | run outputs | `metrics.csv`, `flags.json`, plots, renders, `review_input.md` | - |
| 5 | **Review** | AI | `review_input.md`, plots, renders | `results/<name>/REVIEW.md`: validity, results, physics-list dependence, recommendation, proposed next variants | **decide**: accept, or approve the next round (back to 2) |

`pipeline/run_all.sh` runs stages 3 to 4a in one go and resumes where it
stopped.

## Why the split

- **Scripts for the mechanical stages.** Building 20 GDML files or running
  100 Geant4 jobs needs no judgement.  Scripts do it faster and more
  cheaply, do it the same way every time, and record seeds and versions so
  any run can be repeated exactly.  An AI agent per run would add cost and
  variability, and nothing else.
- **AI for judgement.**  Turning an idea into a parametric design, choosing
  variations that answer the question, and reading results critically are
  the steps where an assistant helps.
- **Facts before judgement.**  Stage 4a checks everything that can be
  checked mechanically (failed runs, overlaps, reference values, physics
  lists that disagree) and writes it into the review packet, so the review
  starts from facts rather than having to find them.

## Rules the AI follows

- In **design**, geometry is built with the GDML workbench's scripting API
  (`freecad.gdml.GDMLDesign`), and tested in FreeCAD when it is available
  (e.g. through the FreeCAD MCP server).
- In **variations**, every variant has a reason.  The table is a proposal
  until you approve it.  The AI does not start runs on its own initiative.
- In **review**, every number quoted comes from `review_input.md`,
  `metrics.csv` or `flags.json`, with its statistical error; nothing comes
  from memory.  Validity problems (failed runs, overlaps, reference
  mismatches) are reported first, before any conclusion about the designs.
  The steps are in [REVIEW_GUIDE.md](REVIEW_GUIDE.md).
- The AI may start the scripts when you ask it to (it is then just running
  a command for you).  It never edits run outputs or substitutes numbers of
  its own.

## Running it

On the machine with FreeCAD and Geant4 (e.g. your Mac):

```bash
conda activate g4                  # Geant4 and its data sets
pipeline/run_all.sh shield         # stages 3-4a; resumes if interrupted
```

Then ask for the review, e.g. "review results/shield".  The AI reads
`results/shield/review_input.md` and the pictures and writes
`results/shield/REVIEW.md`.  Results stay on your machine; commit the
reviews you want to keep under `docs/results/`.

A scheduled task can run stage 3-4a unattended and ask for the review
afterwards.  The approval of new variants stays with you.
