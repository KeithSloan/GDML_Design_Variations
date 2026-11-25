# Contributing

Contributions are welcome: new studies, metrics, checks against reference
data, and improvements to the Geant4 application or the pipeline.

- Open an issue to discuss larger changes first.
- Work on a branch and open a pull request against `main`.
- New studies follow [studies/README.md](studies/README.md).  Give every
  metric an error estimate and, where one exists, a reference value.
- Before a pull request, run:

  ```bash
  python3 tests/test_builds.py
  python3 tests/test_pipeline.py
  ```

  For changes to `g4app/`, also build it against Geant4 11 and run one
  study with `EVENTS_SCALE=0.05 pipeline/run_all.sh <study>`.
- Do not commit `results/`.  To publish the results of a study, put its
  `REVIEW.md` and selected plots under `docs/results/<study>/`.
- The roles of AI and scripts are fixed in [docs/WORKFLOW.md](docs/WORKFLOW.md).
  AI-assisted contributions are welcome, within those roles.

By contributing you agree that your contribution is licensed under the
GPL-3.0-or-later, as in [LICENSE](LICENSE).
