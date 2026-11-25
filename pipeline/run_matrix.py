#!/usr/bin/env python3
"""Run every variant x physics list x source of a study through gdmlvar.

    python3 pipeline/run_matrix.py shield -j 8
    python3 pipeline/run_matrix.py calorimeter --only 'Pb*' --physics QGSP_BIC
    python3 pipeline/run_matrix.py detector --events-scale 0.1   # quick look

Needs the GDML from generate_gdml.py (results/<study>/gdml/) and a built
g4app (g4app/build/gdmlvar, or --app).  Each run gets its own directory
results/<study>/runs/<variant>__<physics>__<source>/ with run.mac, g4.log,
events.csv.gz, summary.json and, for the mesh physics lists, mesh.vti.
Every finished run is appended to results/<study>/runs.jsonl; runs already
recorded as ok are skipped (resume), unless --force.

Standard library only, except the mesh conversion (numpy), which is skipped
with a note if numpy is missing.
"""
import argparse
import concurrent.futures as cf
import gzip
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import study as studylib  # noqa: E402

_lock = threading.Lock()


def _done(jsonl):
    ok = {}
    if jsonl.exists():
        for line in jsonl.read_text().splitlines():
            if line.strip():
                rec = json.loads(line)
                ok[rec["key"]] = rec["status"] == "ok"
    return {k for k, v in ok.items() if v}


def _record(jsonl, rec):
    with _lock:
        with open(jsonl, "a") as f:
            f.write(json.dumps(rec) + "\n")


def _g4_error(log_path):
    """The last fatal G4Exception in g4.log, as one line, or ''."""
    try:
        lines = log_path.read_text(errors="replace").splitlines()
    except OSError:
        return ""
    msg = ""
    for i, line in enumerate(lines):
        if line.startswith("*** G4Exception :"):
            code = line.split(":", 1)[1].strip()
            origin = lines[i + 1].split(":", 1)[1].strip() if i + 1 < len(lines) else ""
            text = lines[i + 2].strip() if i + 2 < len(lines) else ""
            fatal = any("Fatal" in x for x in lines[i + 3:i + 6])
            if fatal or not msg:
                msg = f"{code} in {origin}: {text}"
    return msg


def _gzip(path):
    with open(path, "rb") as src, gzip.open(str(path) + ".gz", "wb") as dst:
        shutil.copyfileobj(src, dst)
    path.unlink()


def run_one(st, variant, physics, src, args, gdml_dir, runs_dir, jsonl):
    key = studylib.run_key(variant.name, physics, src.name)
    rdir = runs_dir / key
    if rdir.exists():
        shutil.rmtree(rdir)
    rdir.mkdir(parents=True)
    events = max(1, int(round(src.events * args.events_scale)))
    with_mesh = physics in st.mesh_physics and not args.no_mesh
    (rdir / "run.mac").write_text(studylib.macro(st, src, events, with_mesh))
    seed = studylib.run_seed(key, args.seed)
    cmd = [str(args.app), "-g", str(gdml_dir / f"{variant.name}.gdml"),
           "-p", physics, "-m", "run.mac", "-s", str(seed), "-o", "."]
    if args.no_overlap_check:
        cmd.append("--no-overlap-check")

    rec = {"key": key, "variant": variant.name, "physics": physics,
           "source": src.name, "events_requested": events, "seed": seed,
           "mesh": with_mesh, "run_dir": str(rdir.relative_to(runs_dir.parent))}
    t0 = time.time()
    try:
        with open(rdir / "g4.log", "w") as log:
            proc = subprocess.run(cmd, cwd=rdir, stdout=log, stderr=subprocess.STDOUT,
                                  timeout=args.timeout)
        rec["rc"] = proc.returncode
    except subprocess.TimeoutExpired:
        rec["rc"] = None
        rec["status"] = "timeout"
    rec["seconds"] = round(time.time() - t0, 1)

    summary_path = rdir / "summary.json"
    if "status" not in rec:
        if rec["rc"] == 0 and summary_path.exists():
            summary = json.loads(summary_path.read_text())
            rec["events"] = summary["events"]
            exc = summary.get("exceptions", {})
            rec["overlaps"] = exc.get("GeomVol1002", 0)
            rec["warnings"] = sum(exc.values())
            rec["status"] = "ok" if summary["events"] == events else "incomplete"
        else:
            rec["status"] = "failed"
    if rec["status"] != "ok":
        err = _g4_error(rdir / "g4.log")
        if err:
            rec["error"] = err

    if rec["status"] == "ok":
        if (rdir / "events.csv").exists():
            _gzip(rdir / "events.csv")
        if with_mesh and (rdir / studylib.MESH_CSV).exists():
            try:
                from pipeline import to_vtk
                to_vtk.convert(rdir, events=rec["events"], keep_csv=args.keep_csv)
                rec["vti"] = "mesh.vti"
            except ImportError as exc:
                rec["vti_error"] = f"not converted ({exc})"
            except Exception as exc:  # keep the run; report the problem
                rec["vti_error"] = str(exc)
    _record(jsonl, rec)
    return rec


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("study", help="study name (studies/<name>) or directory")
    ap.add_argument("-j", "--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--app", type=Path,
                    default=studylib.REPO / "g4app" / "build" / "gdmlvar")
    ap.add_argument("--results", type=Path, default=None, help="results root")
    ap.add_argument("--only", help="variant globs, comma-separated")
    ap.add_argument("--physics", help="physics-list globs, comma-separated")
    ap.add_argument("--sources", help="source globs, comma-separated")
    ap.add_argument("--events-scale", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=0, help="offset added to every seed")
    ap.add_argument("--timeout", type=float, default=3600.0, help="seconds per run")
    ap.add_argument("--force", action="store_true", help="re-run finished runs")
    ap.add_argument("--no-mesh", action="store_true")
    ap.add_argument("--keep-csv", action="store_true", help="keep mesh CSV files")
    ap.add_argument("--no-overlap-check", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="list the runs only")
    args = ap.parse_args(argv)

    st = studylib.load(args.study)
    out = studylib.results_dir(st, args.results).resolve()  # runs use their own cwd
    gdml_dir, runs_dir, jsonl = out / "gdml", out / "runs", out / "runs.jsonl"
    todo = studylib.runs(st, args.only, args.physics, args.sources)
    done = set() if args.force else _done(jsonl)
    todo = [(v, p, s) for v, p, s in todo
            if studylib.run_key(v.name, p, s.name) not in done]
    print(f"{st.name}: {len(todo)} runs to do ({len(done)} already done)")
    if args.dry_run:
        for v, p, s in todo:
            print("  ", studylib.run_key(v.name, p, s.name))
        return 0
    if not todo:
        return 0

    missing = sorted({v.name for v, _, _ in todo
                      if not (gdml_dir / f"{v.name}.gdml").exists()})
    if missing:
        sys.exit(f"no GDML for {', '.join(missing)} in {gdml_dir}: "
                 "run pipeline/gen_gdml.sh first")
    if not args.app.exists():
        sys.exit(f"{args.app} not found: build g4app (see README)")
    args.app = args.app.resolve()
    runs_dir.mkdir(parents=True, exist_ok=True)

    failed = 0
    with cf.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(run_one, st, v, p, s, args, gdml_dir, runs_dir, jsonl)
                   for v, p, s in todo]
        for i, fut in enumerate(cf.as_completed(futures), 1):
            rec = fut.result()
            extra = ""
            if rec.get("overlaps"):
                extra += f"  OVERLAPS={rec['overlaps']}"
            if rec.get("vti_error"):
                extra += f"  vti: {rec['vti_error']}"
            if rec.get("error"):
                extra += f"\n      {rec['error']}"
            print(f"[{i}/{len(todo)}] {rec['key']}: {rec['status']} "
                  f"({rec['seconds']} s){extra}", flush=True)
            failed += rec["status"] != "ok"
    print(f"{st.name}: {len(todo) - failed} ok, {failed} not ok")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
