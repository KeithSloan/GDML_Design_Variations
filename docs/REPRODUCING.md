# Reproducing the published results with Claude

These prompts let anyone who clones this repository have Claude rebuild
the published results of the three sample studies, `shield`, `calorimeter`
and `detector`, and check them against the published tables.  The tables
are in [docs/results/round1](results/round1/README.md) and
[docs/results/round2](results/round2/README.md).

Claude only runs the repository's own scripts, as you could yourself;
every command is in the [README](../README.md).  The rules in
[CLAUDE.md](../CLAUDE.md) still hold:
- reproducing means no design changes, so no edits to `study.toml`,
  `build.py`, `metrics.py` or the pipeline;
- nothing under `results/` is written by hand except `REVIEW.md`;
- every number Claude reports comes from the scripts' outputs.

## What you need

- **Claude that can run commands in your clone.**  Claude Code started in
  the repository folder is simplest: it reads `CLAUDE.md` by itself.
  Claude in the desktop app with the folder connected also works.
- **conda** (Miniforge or Miniconda).  The prompts create the
  environment from [environment.yml](../environment.yml).
- **FreeCAD 1.1 with the GDML workbench**, Main branch 2.2.16 or later.
  The workbench's `GDMLDesign` scripting API is needed to generate the
  GDML.
  - On Linux without a display, `xvfb-run` is also needed.
  - Everything after GDML generation needs only the conda environment.
- **Time:** the 141 Geant4 runs take about 50 process-minutes, roughly
  15 minutes elapsed with runs in parallel on a recent laptop.  Most of it
  is the calorimeter.
- **Disk:** about 160 MB under `results/`, which is not committed.

## What to expect

- **Same platform:** on macOS arm64 with Geant4 11.4.3, the platform of
  the published runs, every run should be identical to the published one.
  Each run's random seed is fixed by its name.
- **Elsewhere:** other platforms or Geant4 versions give statistically
  consistent results.  Metrics agree within their errors, and the
  geometry-derived values agree exactly: crystal and shield masses, depths
  in mm, X₀ and λ, areal densities.
- **The check:** `tools/compare_results.py` decides this from the tables.
  It reports IDENTICAL, CONSISTENT or DIFFERENT for each study.

## The prompts

Use them in order, one at a time; each ends by reporting back to you.
Prompt 1 can be skipped if your setup already passes
`pipeline/check_setup.sh`.

### 1. Set up

```text
I want to reproduce the published results of the shield, calorimeter and
detector studies in this repository.  Read README.md, CLAUDE.md,
docs/WORKFLOW.md and docs/REPRODUCING.md first.

Set up this machine following the README's Requirements and Setup:
create (or update) the conda environment from environment.yml and use
it for everything; run pipeline/check_setup.sh; and if FreeCAD is not
found, ask me where it is and put FREECAD=... in pipeline/local.env
(copy pipeline/local.env.example).  On Linux without a display, also
set GDV_XVFB=1 there.

Do not install anything outside the conda environment and do not edit
any repository file except pipeline/local.env.  If check_setup.sh still
reports a problem you cannot fix that way, stop and tell me exactly
what it says.  Finish with the check_setup.sh output and the versions
of Geant4, Python, FreeCAD and the GDML workbench it found.
```

### 2. Quick look (about a tenth of the statistics)

```text
Make sure FreeCAD is not running (ask me to close it if it is).  Then,
with the conda environment active, run

    EVENTS_SCALE=0.1 pipeline/run_all.sh shield calorimeter detector

It generates the GDML in FreeCAD, builds the Geant4 application and
runs every variant with every physics list.  It can take several
minutes, so run it in the background and check on it rather than
letting a command time out.

When it finishes:
- report, per study, how many runs finished ok, and any failed run with
  the last error in its runs/<run>/g4.log;
- report any geometry overlaps or Geant4 warnings (results/<study>/runs.jsonl);
- run python3 tools/compare_results.py shield calorimeter detector and
  show its output.

At this statistics the runs differ from the published ones, so expect
"different event count" and CONSISTENT, not IDENTICAL.  The metrics
without errors (masses, depths, areal densities) must still all agree:
if any differ, stop and tell me, because the GDML or the materials are
not the published ones.  Do not change any file to make a check pass.
```

### 3. Full statistics

```text
With FreeCAD closed and the conda environment active, run the full
statistics:

    pipeline/run_all.sh shield calorimeter detector

Runs from the quick look are redone automatically because their event
count differs.  This takes about 50 process-minutes; run it in the
background and check on it every few minutes.

When it finishes, report as before (runs ok, failures, overlaps,
warnings), then run

    python3 tools/compare_results.py shield calorimeter detector
    python3 tools/compare_results.py --ref docs/results/round1 shield calorimeter detector

and show both outputs.  Summarise for each study whether the result is
IDENTICAL, CONSISTENT or DIFFERENT, and for anything DIFFERENT list the
runs and metrics the tool names.  Do not explain a difference away or
re-run anything to make it go away: report it.
```

### 4. Check the conclusions (optional, the review stage)

```text
For each of shield, calorimeter and detector, review
results/<study>/review_input.md following docs/REVIEW_GUIDE.md, looking
at results/<study>/plots/ and render/ as the guide says, and write
results/<study>/REVIEW.md.  Validity first; every number from the
pipeline's outputs with its error.

Then compare your conclusions with the published review,
docs/results/round2/<study>/REVIEW.md: list each published conclusion
and say whether these results support it, quoting the numbers from both.
Point out any published conclusion that does not reproduce.
```

### All in one

For an unattended run, prompts 1 to 3 can be given together:

```text
Reproduce the published results of the shield, calorimeter and detector
studies in this repository, following docs/REPRODUCING.md: set up (prompt
1), quick look (prompt 2), then full statistics (prompt 3), stopping
after any step whose checks fail.  Follow CLAUDE.md: no design or
pipeline changes, nothing under results/ written by hand.  End with the
output of tools/compare_results.py against round 2 and round 1 and a
one-line verdict per study.
```

## If something fails

```text
The last step failed.  Run pipeline/check_setup.sh and read the failing
run's results/<study>/runs/<run>/g4.log.  Tell me the cause and propose a
fix, but do not change repository files or anything under results/
until I agree.
```

The README's Requirements section lists the two setup mix-ups that most
often break the build on macOS (a Python or expat from outside the conda
environment).  `check_setup.sh` reports both.

## Without Claude

The same steps by hand:

```bash
conda env create -f environment.yml && conda activate gdml-variations
pipeline/check_setup.sh
cp pipeline/local.env.example pipeline/local.env     # set FREECAD if needed
EVENTS_SCALE=0.1 pipeline/run_all.sh shield calorimeter detector   # quick look
pipeline/run_all.sh shield calorimeter detector                    # full statistics
python3 tools/compare_results.py shield calorimeter detector
python3 tools/compare_results.py --ref docs/results/round1 shield calorimeter detector
```
