#!/usr/bin/env python3
"""Plumbing test: every study through run_matrix -> to_vtk -> analyse ->
render, with tests/fake_gdmlvar.py standing in for Geant4 and dummy GDML
files standing in for FreeCAD.  Checks files and formats, not physics.

    python3 tests/test_pipeline.py          (needs numpy, matplotlib; vtk optional)
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from pipeline import analyse, render, run_matrix, to_vtk  # noqa: E402
from pipeline import study as studylib  # noqa: E402

FAKE = REPO / "tests" / "fake_gdmlvar.py"


def fake_gdml(st, root):
    gdir = studylib.results_dir(st, root) / "gdml"
    gdir.mkdir(parents=True)
    for v in st.variants:
        (gdir / f"{v.name}.gdml").write_text("<!-- dummy GDML for the plumbing test -->\n")
        (gdir / f"{v.name}.json").write_text(json.dumps(
            {"study": st.name, "variant": v.name, "params": v.params}))


def main():
    root = Path(tempfile.mkdtemp(prefix="gdv_test_"))
    try:
        for name in ("shield", "calorimeter", "detector"):
            st = studylib.load(name)
            fake_gdml(st, root)
            rc = run_matrix.main([name, "--app", str(FAKE), "--results", str(root),
                                  "--events-scale", "0.02", "-j", "2"])
            assert rc == 0, f"{name}: run_matrix failed"
            out = studylib.results_dir(st, root)
            # resume: nothing left at the same event count, everything at another
            jsonl = out / "runs.jsonl"
            assert run_matrix.pending(st, jsonl, 0.02)[0] == []
            assert len(run_matrix.pending(st, jsonl, 1.0)[0]) == len(studylib.runs(st))
            assert run_matrix.main([name, "--app", str(FAKE), "--results", str(root),
                                    "--events-scale", "0.02", "--dry-run"]) == 0
            recs = analyse.latest_records(out / "runs.jsonl")
            assert len(recs) == len(studylib.runs(st)), "missing runs"
            vti = [r for r in recs.values() if r.get("vti")]
            assert len(vti) == len(st.variants) * len(st.sources), "mesh runs"
            m = to_vtk.read_vti(out / vti[0]["run_dir"] / "mesh.vti")
            assert m["shape"] == tuple(st.mesh["bins"])
            rows, flags = analyse.analyse(name, root)
            assert rows and all(st.primary_metric in r or r["source"] != st.sources[0].name
                                for r in rows)
            assert (out / "review_input.md").exists() and (out / "metrics.csv").exists()
            assert any((out / "plots").glob("*.png"))
            args = [name, "--results", str(root)]
            try:
                import vtk  # noqa: F401
                args.append("--3d")
            except ImportError:
                pass
            render.main(args + ["--only", vti[0]["key"]])
            assert any((out / "render").glob("*_xz.png"))
            print(f"OK {name}: {len(rows)} rows, {len(flags)} flags")
        print("plumbing test passed")
        return 0
    finally:
        if "--keep" in sys.argv:
            print("kept", root)
        else:
            shutil.rmtree(root)


if __name__ == "__main__":
    sys.exit(main())
