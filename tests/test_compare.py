#!/usr/bin/env python3
"""tools/compare_results.py tells identical, consistent and different
results apart, on small made-up metrics tables.

    python3 tests/test_compare.py
"""
import contextlib
import csv
import io
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from tools import compare_results  # noqa: E402

COLUMNS = ["key", "variant", "physics", "source", "events", "overlaps",
           "warnings", "wall_seconds", "mass_kg", "mass_kg_err",
           "efficiency", "efficiency_err"]


def table(root, rows):
    d = root / "toy"
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "metrics.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for key, mass, eff, err, events in rows:
            v, p, s = key.split("__")
            w.writerow(dict(key=key, variant=v, physics=p, source=s,
                            events=events, overlaps=0, warnings=0,
                            wall_seconds=1.0, mass_kg=mass, mass_kg_err="",
                            efficiency=eff, efficiency_err=err))


REF = [("A__L1__S", 1.5, 0.200, 0.002, 1000),
       ("B__L1__S", 2.5, 0.300, 0.003, 1000)]


def run(tmp, new_rows):
    shutil.rmtree(tmp / "new", ignore_errors=True)
    table(tmp / "new", new_rows)
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = compare_results.main(["toy", "--results", str(tmp / "new"),
                                   "--ref", str(tmp / "ref")])
    return rc, out.getvalue()


def main():
    tmp = Path(tempfile.mkdtemp(prefix="gdv_compare_"))
    try:
        table(tmp / "ref", REF)
        cases = [
            ("identical", REF, 0, "IDENTICAL"),
            ("within errors", [("A__L1__S", 1.5, 0.203, 0.002, 1000),
                               ("B__L1__S", 2.5, 0.296, 0.003, 1000)], 0, "CONSISTENT"),
            ("fewer events", [("A__L1__S", 1.5, 0.205, 0.006, 100),
                              ("B__L1__S", 2.5, 0.300, 0.009, 100)], 0, "different event count"),
            ("pull > 4", [("A__L1__S", 1.5, 0.215, 0.002, 1000),
                          ("B__L1__S", 2.5, 0.300, 0.003, 1000)], 1, "DIFFERENT"),
            ("mass differs", [("A__L1__S", 1.6, 0.200, 0.002, 1000),
                              ("B__L1__S", 2.5, 0.300, 0.003, 1000)], 1, "1 differ"),
            ("run missing", REF[:1], 1, "missing: B__L1__S"),
        ]
        for name, rows, want_rc, want_text in cases:
            rc, text = run(tmp, rows)
            assert rc == want_rc and want_text in text, f"{name}: rc={rc}\n{text}"
            print(f"OK {name}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("compare test passed")


if __name__ == "__main__":
    main()
