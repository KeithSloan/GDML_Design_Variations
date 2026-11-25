#!/usr/bin/env python3
"""Write each study's variations as two CSV tables, from its study.toml.

    geometry_variants.csv  one row per FreeCAD export (GDML file):
                           the variant and every build parameter
    physics_variants.csv   one row per Geant4 setting (physics list x
                           source), each run on every geometry variant

study.toml stays the source of truth; the CSV files are for reading
(GitHub, Numbers, Excel, LibreOffice) and must not be edited by hand.

    python3 tools/export_csv.py              # all studies
    python3 tools/export_csv.py shield
    python3 tools/export_csv.py --check      # exit 1 if any are out of date
"""
import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from pipeline import study as studylib  # noqa: E402


def all_studies():
    return sorted(p.parent.name for p in (REPO / "studies").glob("*/study.toml"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("studies", nargs="*", help="default: every study")
    ap.add_argument("--check", action="store_true",
                    help="only report CSV files that differ from study.toml")
    args = ap.parse_args(argv)

    stale = []
    for name in args.studies or all_studies():
        st = studylib.load(name)
        if args.check:
            for fname, text in studylib.csv_texts(st).items():
                path = st.dir / fname
                if not path.exists() or path.read_text(encoding="utf-8") != text:
                    stale.append(path)
        else:
            for path in studylib.write_csvs(st):
                print(f"wrote {path.relative_to(REPO)}")
    if args.check:
        for path in stale:
            print(f"out of date: {path.relative_to(REPO)} "
                  "(run python3 tools/export_csv.py)")
        return 1 if stale else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
