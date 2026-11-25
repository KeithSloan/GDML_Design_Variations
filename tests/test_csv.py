#!/usr/bin/env python3
"""The variation tables (geometry_variants.csv, physics_variants.csv) are
up to date with study.toml, and the check notices when they are not.

    python3 tests/test_csv.py
"""
import csv
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from pipeline import study as studylib  # noqa: E402
from tools import export_csv  # noqa: E402


def main():
    assert export_csv.main(["--check"]) == 0, "CSV files out of date: run tools/export_csv.py"

    for name in export_csv.all_studies():
        st = studylib.load(name)
        geo = list(csv.reader(open(st.dir / studylib.GEOMETRY_CSV, encoding="utf-8")))
        phys = list(csv.reader(open(st.dir / studylib.PHYSICS_CSV, encoding="utf-8")))
        assert [r[0] for r in geo[1:]] == [v.name for v in st.variants], name
        assert len(phys) - 1 == len(st.physics_lists) * len(st.sources), name
        runs = sum(int(r[-1]) for r in phys[1:])
        assert runs == len(studylib.runs(st)), name
        print(f"OK {name}: {len(geo) - 1} geometry variants (FreeCAD exports) x "
              f"{len(phys) - 1} physics settings = {runs} Geant4 runs")

    # a changed study.toml makes the check fail until the CSVs are rewritten
    tmp = Path(tempfile.mkdtemp(prefix="gdv_csv_"))
    try:
        d = tmp / "shield"
        shutil.copytree(REPO / "studies" / "shield", d)
        toml = d / "study.toml"
        toml.write_text(toml.read_text().replace('name = "Pb_5mm"', 'name = "Pb_6mm"'))
        st = studylib.load(d)
        texts = studylib.csv_texts(st)
        assert (d / studylib.GEOMETRY_CSV).read_text() != texts[studylib.GEOMETRY_CSV]
        assert studylib.write_csvs(st) == [d / studylib.GEOMETRY_CSV]
        assert studylib.write_csvs(st) == []
        print("OK stale tables are detected and rewritten")
    finally:
        shutil.rmtree(tmp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
