# Contributing

Contributions are welcome: new studies, metrics, checks against reference
data, and improvements to the Geant4 application or the pipeline.

- Open an issue to discuss larger changes first.
- Work on a branch and open a pull request against `main`.
- Set up with [environment.yml](environment.yml) and check with
  `pipeline/check_setup.sh`.  A new dependency goes into `environment.yml`,
  `requirements.txt` (if Python) and `check_setup.sh` together.
- New studies follow [studies/README.md](studies/README.md).  Give every
  metric an error estimate and, where one exists, a reference value.
- Before a pull request, run:

  ```bash
  python3 tools/export_csv.py      # regenerate the variation tables
  python3 tests/test_builds.py
  python3 tests/test_csv.py
  python3 tests/test_pipeline.py
  python3 tests/test_compare.py
  ```

  For changes to `g4app/`, also build it against Geant4 11 and run one
  study with `EVENTS_SCALE=0.05 pipeline/run_all.sh <study>`.
- Do not commit `results/`.  To publish the results of a study, put its
  `REVIEW.md`, `review_input.md`, `metrics.csv`, `flags.json` and
  selected plots under `docs/results/<round>/<study>/` (see `round1`).
- The roles of AI and scripts are fixed in [docs/WORKFLOW.md](docs/WORKFLOW.md).
  AI-assisted contributions are welcome, within those roles.

By contributing you agree that your contribution is licensed under the
GPL-3.0-or-later, as in [LICENSE](LICENSE).
