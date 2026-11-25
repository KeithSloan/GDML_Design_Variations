"""Build every variant of a study in FreeCAD and export it to GDML.

Runs inside FreeCAD (GDML workbench installed), because GDML export needs
the FreeCAD GUI.  For each variant it creates a new GDML document, sizes the
world, adds the study's custom materials, calls the study's build(gd,
params), exports results/<study>/gdml/<variant>.gdml and writes
<variant>.json (parameters, design tree, versions).  Existing outputs are
kept unless force=True.

From FreeCAD's Python console, a macro, or the FreeCAD MCP server:

    import sys; sys.path.insert(0, "/path/to/GDML_Design_Variations")
    from pipeline import generate_gdml
    generate_gdml.generate("shield")              # or a study directory
    generate_gdml.generate("detector", only="NaI*", force=True)

Unattended (pipeline/gen_gdml.sh): FreeCAD is started with this file as its
argument and these environment variables; it quits when done.
    GDV_STUDIES   comma-separated study names or directories
    GDV_ONLY      optional variant globs, GDV_FORCE=1 to rebuild
    GDV_AUTOQUIT=1
"""
import importlib.util
import json
import os
import platform
import subprocess
import sys
import time
import traceback
from pathlib import Path

try:
    _HERE = Path(__file__).resolve().parent
except NameError:  # exec'd without a file name
    _HERE = Path(os.environ.get("GDV_REPO", ".")).resolve() / "pipeline"
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from pipeline import study as studylib  # noqa: E402


def _load_build(study):
    spec = importlib.util.spec_from_file_location(f"build_{study.name}",
                                                  study.dir / "build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build


def _git_commit(path):
    try:
        return subprocess.run(["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return ""


def _versions():
    import FreeCAD
    import freecad.gdml as gdmlpkg

    gdml_dir = Path(gdmlpkg.__file__).resolve().parents[2]
    version = ""
    pkg = gdml_dir / "package.xml"
    if pkg.exists():
        text = pkg.read_text(encoding="utf-8", errors="replace")
        start = text.find("<version>")
        if start >= 0:
            version = text[start + 9:text.find("</version>", start)].strip()
    return {
        "freecad": ".".join(FreeCAD.Version()[:3]),
        "gdml_workbench": version,
        "gdml_workbench_commit": _git_commit(gdml_dir),
        "design_variations_commit": _git_commit(studylib.REPO),
        "platform": platform.platform(),
    }


def generate(study, out=None, only=None, force=False, close=True):
    """Build and export the study's variants; returns a list of result dicts."""
    import FreeCAD
    from freecad.gdml import GDMLDesign as gd

    st = studylib.load(study)
    out = Path(out) if out else studylib.results_dir(st) / "gdml"
    out.mkdir(parents=True, exist_ok=True)
    build = _load_build(st)
    versions = _versions()
    results = []

    for v in studylib.select(st.variants, only):
        gdml = out / f"{v.name}.gdml"
        meta = out / f"{v.name}.json"
        if gdml.exists() and meta.exists() and not force:
            results.append({"variant": v.name, "status": "kept"})
            continue
        t0 = time.time()
        doc = None
        try:
            doc = gd.newDocument(f"{st.name}_{v.name}", worldSize=st.world_size_mm,
                                 worldMaterial=st.world_material)
            for name, m in st.materials.items():
                gd.addMaterial(name, m["density"], formula=m.get("formula"),
                               mixture=m.get("mixture"), doc=doc)
            build(gd, dict(v.params))
            doc.recompute()
            tree = gd.designTree(doc)
            gd.exportGDML(str(gdml), doc=doc)
            meta.write_text(json.dumps({
                "study": st.name,
                "variant": v.name,
                "note": v.note,
                "params": v.params,
                "materials": st.materials,
                "design_tree": tree,
                "versions": versions,
                "seconds": round(time.time() - t0, 2),
            }, indent=2) + "\n", encoding="utf-8")
            results.append({"variant": v.name, "status": "ok",
                            "seconds": round(time.time() - t0, 2)})
        except Exception as exc:
            results.append({"variant": v.name, "status": "failed", "error": str(exc),
                            "traceback": traceback.format_exc()})
            for f in (gdml, meta):
                if f.exists() and f.stat().st_mtime >= t0:
                    f.unlink()
        finally:
            if doc is not None and close:
                FreeCAD.closeDocument(doc.Name)

    (out / "generation.json").write_text(json.dumps({
        "study": st.name, "versions": versions, "results": results,
    }, indent=2) + "\n", encoding="utf-8")
    failed = [r["variant"] for r in results if r["status"] == "failed"]
    print(f"[generate_gdml] {st.name}: {len(results)} variants, "
          f"{len(failed)} failed{': ' + ', '.join(failed) if failed else ''}")
    return results


def _unattended():
    """Run from pipeline/gen_gdml.sh, then quit FreeCAD."""
    code = 0
    try:
        for s in [x for x in os.environ.get("GDV_STUDIES", "").split(",") if x]:
            res = generate(s, only=os.environ.get("GDV_ONLY") or None,
                           force=os.environ.get("GDV_FORCE") == "1")
            if any(r["status"] == "failed" for r in res):
                code = 1
    except Exception:
        traceback.print_exc()
        code = 2
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)


if os.environ.get("GDV_AUTOQUIT") == "1":
    try:
        from PySide import QtCore  # FreeCAD's Qt binding
        QtCore.QTimer.singleShot(2000, _unattended)  # after the GUI is up
    except ImportError:
        _unattended()
