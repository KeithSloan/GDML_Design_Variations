"""Hadron calorimeter geometry: the sampling-calorimeter layout of
studies/calorimeter/build.py (absorber + active layers in a vacuum envelope,
copy number = layer, detectors "Absorber" and "Active"), reused as is.

    build(gd, p)   gd = freecad.gdml.GDMLDesign, p = the variant's parameters
"""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().parent.parent / "calorimeter" / "build.py"
_spec = importlib.util.spec_from_file_location("calorimeter_build", _path)
_calorimeter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_calorimeter)


def build(gd, p):
    _calorimeter.build(gd, p)
