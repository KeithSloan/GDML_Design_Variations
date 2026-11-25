"""Hadron calorimeter metrics: those of studies/calorimeter/metrics.py
(resolution, sampling fraction, containment, signal per GeV, e/mip,
shower maximum, last-layer fraction, depth in X0 and lambda; e_over_pi on
the pion rows), plus

  noncompensation   |e/pi - 1| on the pion rows: 0 for a compensating
                    calorimeter (signal, i.e. deposited energy, only - no
                    Birks quenching or readout is simulated)
"""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().parent.parent / "calorimeter" / "metrics.py"
_spec = importlib.util.spec_from_file_location("calorimeter_metrics", _path)
_calorimeter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_calorimeter)

run_metrics = _calorimeter.run_metrics
extra_plots = _calorimeter.extra_plots


def derived(rows, study):
    _calorimeter.derived(rows, study)
    for r in rows:
        if r.get("e_over_pi") is not None:
            r["noncompensation"] = abs(r["e_over_pi"] - 1.0)
            r["noncompensation_err"] = r.get("e_over_pi_err")
