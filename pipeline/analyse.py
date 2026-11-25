#!/usr/bin/env python3
"""Turn a study's finished runs into metrics, checks, plots and the packet
the AI review reads.

    python3 pipeline/analyse.py shield

Writes to results/<study>/:
    metrics.csv, metrics.json   one row per run: every metric and its error
    flags.json                  what the review must look at, by severity
    plots/*.png                 each metric vs variant, one series per
                                physics list, references in black
    review_input.md             the review packet (see docs/REVIEW_GUIDE.md)

Checks made here, mechanically, so the review starts from facts:
    reference   metric vs analytic/tabulated value or allowed range
    physics     physics lists differing by > 3 sigma and > physics_rel_tol
    geometry    overlaps reported by Geant4 when it read the GDML
    runs        failed, incomplete or missing runs
Needs numpy and matplotlib.
"""
import argparse
import csv
import gzip
import importlib.util
import io
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import study as studylib  # noqa: E402

BASE_COLUMNS = ["key", "variant", "physics", "source", "events", "overlaps",
                "warnings", "wall_seconds"]


@dataclass
class RunContext:
    study: object
    variant: object
    physics: str
    source: object
    key: str
    run_dir: Path
    summary: dict
    events: dict
    record: dict


def load_metrics_module(st):
    spec = importlib.util.spec_from_file_location(f"metrics_{st.name}",
                                                  st.dir / "metrics.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_events(run_dir):
    path = run_dir / "events.csv.gz"
    opener = gzip.open if path.exists() else open
    if not path.exists():
        path = run_dir / "events.csv"
    with opener(path, "rt") as f:
        header = f.readline().strip().split(",")
        data = np.loadtxt(io.StringIO(f.read()), delimiter=",", ndmin=2)
    if data.size == 0:
        data = np.zeros((0, len(header)))
    return {name: data[:, i] for i, name in enumerate(header)}


def latest_records(jsonl):
    recs = {}
    if jsonl.exists():
        for line in jsonl.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                recs[r["key"]] = r
    return recs


def fmt(v, e=None):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "-"
    if e is None or e == 0 or not math.isfinite(e):
        return f"{v:.4g}"
    digits = max(0, 1 - int(math.floor(math.log10(abs(e))))) if e > 0 else 4
    if abs(v) >= 1e5 or (v != 0 and abs(v) < 1e-3):
        return f"{v:.3e} ± {e:.1e}"
    return f"{v:.{digits}f} ± {e:.{digits}f}"


def check_references(rows, refs, st):
    out = []
    for r in rows:
        for metric, ref in refs.get(r["key"], {}).items():
            v, e = r.get(metric), r.get(metric + "_err")
            if v is None:
                continue
            item = {"key": r["key"], "metric": metric, "value": v, "error": e}
            if isinstance(ref, (tuple, list)):
                lo, hi = ref
                item.update(range=[lo, hi], ok=bool(lo <= v <= hi))
            else:
                tol = float(st.checks.get(f"{metric}_rel_tol",
                                          st.checks.get("reference_rel_tol", 0.02)))
                rel = (v - ref) / ref if ref else float("inf")
                z = (v - ref) / e if e else float("inf")
                item.update(reference=ref, rel_diff=rel, sigma=z, rel_tol=tol,
                            ok=bool(abs(rel) <= tol or abs(z) <= 3))
            out.append(item)
    return out


def compare_physics(rows, st):
    tol = float(st.checks.get("physics_rel_tol", 0.01))
    base = st.physics_lists[0]
    by = {(r["variant"], r["source"], r["physics"]): r for r in rows}
    out = []
    for metric in st.compare_metrics:
        for r in rows:
            if r["physics"] == base or metric not in r:
                continue
            b = by.get((r["variant"], r["source"], base))
            if b is None or metric not in b:
                continue
            v, e = r[metric], r.get(metric + "_err") or 0.0
            v0, e0 = b[metric], b.get(metric + "_err") or 0.0
            diff = v - v0
            sig = math.sqrt(e * e + e0 * e0)
            z = diff / sig if sig else float("inf")
            rel = diff / abs(v0) if v0 else float("inf")
            out.append({"metric": metric, "variant": r["variant"], "source": r["source"],
                        "physics": r["physics"], "base": base, "value": v, "base_value": v0,
                        "rel_diff": rel, "sigma": z,
                        "significant": bool(abs(z) > 3 and abs(rel) > tol)})
    return out


def ranking(rows, st):
    m = st.primary_metric
    out = {}
    for p in st.physics_lists:
        for s in st.sources:
            sel = [r for r in rows if r["physics"] == p and r["source"] == s.name
                   and r.get(m) is not None]
            if sel:
                sel.sort(key=lambda r: r[m], reverse=(st.better == "higher"))
                out[f"{p} / {s.name}"] = [(r["variant"], r[m], r.get(m + "_err"))
                                          for r in sel]
    return out


def make_plots(rows, refs, st, plotdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plotdir.mkdir(parents=True, exist_ok=True)
    written = []
    variants = [v.name for v in st.variants]
    for metric in st.plot_metrics:
        for s in st.sources:
            sel = [r for r in rows if r["source"] == s.name and r.get(metric) is not None]
            if not sel:
                continue
            fig, ax = plt.subplots(figsize=(max(6.0, 0.8 * len(variants)), 4.2))
            width = 0.7 / max(1, len(st.physics_lists))
            for i, p in enumerate(st.physics_lists):
                xs, ys, es = [], [], []
                for r in sel:
                    if r["physics"] == p:
                        xs.append(variants.index(r["variant"]) + (i - (len(st.physics_lists) - 1) / 2) * width)
                        ys.append(r[metric])
                        es.append(r.get(metric + "_err") or 0.0)
                if xs:
                    ax.errorbar(xs, ys, yerr=es, fmt="o", ms=4, capsize=2, label=p)
            rx, ry = [], []
            for r in sel:
                ref = refs.get(r["key"], {}).get(metric)
                if isinstance(ref, (int, float)) and r["physics"] == st.physics_lists[0]:
                    rx.append(variants.index(r["variant"]))
                    ry.append(ref)
            if rx:
                ax.plot(rx, ry, "k_", ms=18, mew=2, label="reference")
            ax.set_xticks(range(len(variants)))
            ax.set_xticklabels(variants, rotation=35, ha="right", fontsize=8)
            ax.set_ylabel(metric)
            ax.set_title(f"{st.name}: {metric} ({s.name})")
            ax.grid(alpha=0.3)
            ax.legend(fontsize=8)
            fig.tight_layout()
            path = plotdir / f"{metric}__{s.name}.png"
            fig.savefig(path, dpi=130)
            plt.close(fig)
            written.append(path)
    return written, plt


def table(rows, st, metric, source):
    lines = ["| variant | " + " | ".join(st.physics_lists) + " |",
             "|---|" + "---|" * len(st.physics_lists)]
    by = {(r["variant"], r["physics"]): r for r in rows if r["source"] == source}
    any_value = False
    for v in st.variants:
        cells = []
        for p in st.physics_lists:
            r = by.get((v.name, p))
            if r is not None and r.get(metric) is not None:
                cells.append(fmt(r[metric], r.get(metric + "_err")))
                any_value = True
            else:
                cells.append("-")
        lines.append(f"| {v.name} | " + " | ".join(cells) + " |")
    return "\n".join(lines) if any_value else ""


def write_review_input(path, st, rows, recs, flags, ref_checks, phys, rank, plots,
                       metric_names):
    out = [f"# Review input: {st.title}", "",
           "Generated by pipeline/analyse.py. Review it as described in "
           "docs/REVIEW_GUIDE.md and write REVIEW.md next to this file.", "",
           "## Study", "", st.description.strip(), "",
           f"**Objective:** {' '.join(st.objective.split())}", "",
           f"**Primary metric:** `{st.primary_metric}` ({st.better} is better)", "",
           "## Variants", "", "| variant | parameters | note |", "|---|---|---|"]
    for v in st.variants:
        params = ", ".join(f"{k}={val}" for k, val in v.params.items())
        out.append(f"| {v.name} | {params} | {v.note} |")
    out += ["", "## Runs", ""]
    status = {}
    for r in recs.values():
        status[r["status"]] = status.get(r["status"], 0) + 1
    expected = len(studylib.runs(st))
    out.append(f"{expected} runs in the study matrix; recorded: "
               + (", ".join(f"{n} {s}" for s, n in sorted(status.items())) or "none"))
    out += ["", f"Physics lists: {', '.join(st.physics_lists)}; sources: "
            + "; ".join(f"{s.name} ({s.particle}, {s.energy_MeV:g} MeV, {s.events} events)"
                        for s in st.sources), ""]

    out += ["## Flags", ""]
    if not flags:
        out.append("None.")
    for f in flags:
        out.append(f"- **{f['severity']}** [{f['kind']}] {f['message']}")

    out += ["", "## Reference checks", ""]
    if ref_checks:
        out += ["| run | metric | value | reference | result |", "|---|---|---|---|---|"]
        for c in ref_checks:
            if "range" in c:
                ref = f"[{c['range'][0]:g}, {c['range'][1]:g}]"
            else:
                ref = f"{c['reference']:.5g} ({c['rel_diff']:+.2%}, {c['sigma']:+.1f} σ)"
            out.append(f"| {c['key']} | {c['metric']} | {fmt(c['value'], c['error'])} | "
                       f"{ref} | {'ok' if c['ok'] else '**MISMATCH**'} |")
    else:
        out.append("No reference values for this study.")

    out += ["", f"## Ranking by {st.primary_metric}", ""]
    for group, items in rank.items():
        out.append(f"- {group}: " + ", ".join(f"{v} ({fmt(x, e)})" for v, x, e in items))

    out += ["", "## Physics-list differences", "",
            f"Relative to {st.physics_lists[0]}; significant = more than 3 σ and more "
            f"than {float(st.checks.get('physics_rel_tol', 0.01)):.0%}.", ""]
    sig = [c for c in phys if c["significant"]]
    if sig:
        for c in sig:
            out.append(f"- {c['metric']}, {c['variant']}, {c['source']}: {c['physics']} "
                       f"{c['rel_diff']:+.1%} ({c['sigma']:+.1f} σ)")
    else:
        out.append("None significant.")

    out += ["", "## Metrics", ""]
    for s in st.sources:
        for m in metric_names:
            t = table(rows, st, m, s.name)
            if t:
                out += [f"### {m} — {s.name}", "", t, ""]

    out += ["## Plots", ""] + [f"- plots/{p.name}" for p in plots]
    renders = sorted((path.parent / "render").glob("*.png"))
    if renders:
        out += ["", "## Renders", ""] + [f"- render/{p.name}" for p in renders]
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def analyse(study, results=None):
    st = studylib.load(study)
    out = studylib.results_dir(st, results)
    recs = latest_records(out / "runs.jsonl")
    mod = load_metrics_module(st)

    rows, refs, contexts, flags = [], {}, [], []
    wanted = {studylib.run_key(v.name, p, s.name): (v, p, s)
              for v, p, s in studylib.runs(st)}
    for key, (v, p, s) in wanted.items():
        rec = recs.get(key)
        if rec is None:
            flags.append({"severity": "info", "kind": "runs", "message": f"{key}: not run"})
            continue
        if rec["status"] != "ok":
            why = f": {rec['error']}" if rec.get("error") else ""
            flags.append({"severity": "high", "kind": "runs",
                          "message": f"{key}: {rec['status']}{why} "
                                     f"(see {rec['run_dir']}/g4.log)"})
            continue
        run_dir = out / rec["run_dir"]
        summary = json.loads((run_dir / "summary.json").read_text())
        ctx = RunContext(st, v, p, s, key, run_dir, summary, read_events(run_dir), rec)
        metrics, ref = mod.run_metrics(ctx)
        row = {"key": key, "variant": v.name, "physics": p, "source": s.name,
               "events": summary["events"], "overlaps": rec.get("overlaps", 0),
               "warnings": rec.get("warnings", 0),
               "wall_seconds": round(summary.get("wall_seconds", 0.0), 1)}
        for name, (val, err) in metrics.items():
            row[name] = float(val)
            row[name + "_err"] = None if err is None else float(err)
        rows.append(row)
        refs[key] = ref
        contexts.append(ctx)
        if row["overlaps"]:
            flags.append({"severity": "high", "kind": "geometry",
                          "message": f"{key}: Geant4 found {row['overlaps']} overlap(s) "
                                     "reading the GDML (GeomVol1002 in g4.log)"})
        other = row["warnings"] - row["overlaps"]
        if other:
            flags.append({"severity": "info", "kind": "runs",
                          "message": f"{key}: {other} other Geant4 warning(s) (g4.log)"})
    mod.derived(rows, st)

    ref_checks = check_references(rows, refs, st)
    for c in ref_checks:
        if not c["ok"]:
            if "range" in c:
                msg = (f"{c['key']}: {c['metric']} = {c['value']:.4g} outside "
                       f"[{c['range'][0]:g}, {c['range'][1]:g}]")
            else:
                msg = (f"{c['key']}: {c['metric']} = {fmt(c['value'], c['error'])} vs "
                       f"reference {c['reference']:.5g} ({c['rel_diff']:+.2%}, "
                       f"{c['sigma']:+.1f} σ)")
            flags.append({"severity": "high", "kind": "reference", "message": msg})
    phys = compare_physics(rows, st)
    for c in phys:
        if c["significant"]:
            flags.append({"severity": "medium", "kind": "physics",
                          "message": f"{c['metric']} for {c['variant']} / {c['source']}: "
                                     f"{c['physics']} differs from {c['base']} by "
                                     f"{c['rel_diff']:+.1%} ({c['sigma']:+.1f} σ)"})
    rank = ranking(rows, st)

    metric_names = []
    for r in rows:
        for k in r:
            if k not in BASE_COLUMNS and not k.endswith("_err") and k not in metric_names:
                metric_names.append(k)
    columns = BASE_COLUMNS + [c for m in metric_names for c in (m, m + "_err")]
    with open(out / "metrics.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    (out / "metrics.json").write_text(json.dumps(
        {"study": st.name, "rows": rows, "references": refs}, indent=1) + "\n")
    order = {"high": 0, "medium": 1, "info": 2}
    flags.sort(key=lambda f: order[f["severity"]])
    (out / "flags.json").write_text(json.dumps(
        {"flags": flags, "reference_checks": ref_checks, "physics": phys}, indent=1) + "\n")

    plots = []
    if rows:
        plots, plt = make_plots(rows, refs, st, out / "plots")
        if hasattr(mod, "extra_plots"):
            plots += mod.extra_plots(contexts, st, out / "plots", plt)
    write_review_input(out / "review_input.md", st, rows, recs, flags, ref_checks,
                       phys, rank, plots, metric_names)
    high = sum(f["severity"] == "high" for f in flags)
    print(f"{st.name}: {len(rows)} runs analysed, {len(flags)} flags ({high} high) "
          f"-> {out / 'review_input.md'}")
    return rows, flags


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("study")
    ap.add_argument("--results", type=Path, default=None, help="results root")
    args = ap.parse_args(argv)
    analyse(args.study, args.results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
