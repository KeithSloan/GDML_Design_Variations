#!/usr/bin/env python3
"""Compare a study's results with a published round (docs/results/roundN).

Rows are matched by run key (variant__physics__source).  For each metric in
both tables:
  - with a statistical error: the pull (new - ref) / sqrt(err_new^2 +
    err_ref^2).  Pulls should look like a standard normal: about 5 % beyond
    2, 0.3 % beyond 3.  Metrics of one run share its events, so treat these
    fractions as a guide.
  - without one (masses, depths, areal densities, FWHM): must agree to a
    relative 1e-6.  They come from the geometry and the material tables,
    not from the random numbers, so a difference means different GDML or
    a different Geant4.
Runs with the same seed, Geant4 version and platform are expected to be
identical; elsewhere they should be statistically consistent.

    python3 tools/compare_results.py shield calorimeter detector
    python3 tools/compare_results.py --ref docs/results/round1 shield
    python3 tools/compare_results.py --results /other/results detector

Exit status 1 if a reference run is missing, an error-free metric differs
or any |pull| > 4; 0 otherwise.
"""
import argparse
import csv
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
NOT_METRICS = {"key", "variant", "physics", "source", "events", "overlaps",
               "warnings", "wall_seconds"}
EXACT_REL_TOL = 1e-6
FAIL_PULL = 4.0


def read_rows(path):
    with open(path, newline="") as f:
        return {r["key"]: r for r in csv.DictReader(f)}


def number(text):
    if text is None or text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def metric_names(columns):
    return [c for c in columns
            if c not in NOT_METRICS and not c.endswith("_err")]


def compare_metric(new, ref, name):
    """('pull', value) | ('exact', ok) | None when not comparable."""
    a, b = number(new.get(name)), number(ref.get(name))
    if a is None or b is None:
        return None
    ea, eb = number(new.get(name + "_err")), number(ref.get(name + "_err"))
    if ea is not None and eb is not None and (ea > 0 or eb > 0):
        return "pull", (a - b) / math.hypot(ea, eb)
    scale = max(abs(a), abs(b), 1e-300)
    return "exact", abs(a - b) <= EXACT_REL_TOL * scale


def compare_study(study, results, ref_root):
    new_path = results / study / "metrics.csv"
    ref_path = ref_root / study / "metrics.csv"
    for p in (new_path, ref_path):
        if not p.exists():
            print(f"{study}: {p} not found")
            return False
    new, ref = read_rows(new_path), read_rows(ref_path)
    common = sorted(set(new) & set(ref))
    missing = sorted(set(ref) - set(new))
    extra = sorted(set(new) - set(ref))
    names = [m for m in metric_names(next(iter(ref.values())).keys())
             if m in next(iter(new.values()))] if common else []

    pulls, exact_bad, n_exact, identical_runs = [], [], 0, 0
    fewer_events = 0
    for key in common:
        same = True
        if number(new[key]["events"]) != number(ref[key]["events"]):
            fewer_events += 1
        for m in names:
            res = compare_metric(new[key], ref[key], m)
            if res is None:
                continue
            kind, val = res
            if new[key].get(m) != ref[key].get(m):
                same = False
            if kind == "pull":
                pulls.append((abs(val), val, key, m))
            else:
                n_exact += 1
                if not val:
                    exact_bad.append((key, m, new[key][m], ref[key][m]))
        identical_runs += same

    print(f"{study} vs {ref_path.parent.relative_to(REPO) if ref_path.is_relative_to(REPO) else ref_path.parent}:")
    print(f"  runs: {len(common)} matched, {len(missing)} missing, {len(extra)} not in the reference")
    for key in missing[:10]:
        print(f"    missing: {key}")
    if fewer_events:
        print(f"  {fewer_events} runs have a different event count from the reference"
              " (EVENTS_SCALE?): pulls still apply, with larger errors")
    print(f"  identical runs (every metric the same): {identical_runs} of {len(common)}")
    print(f"  metrics without errors: {n_exact} compared, {len(exact_bad)} differ")
    for key, m, a, b in exact_bad[:10]:
        print(f"    {key} {m}: {a} vs {b}")
    n = len(pulls)
    if n:
        over2 = sum(p[0] > 2 for p in pulls)
        over3 = sum(p[0] > 3 for p in pulls)
        print(f"  pulls: {n} compared; |pull| > 2: {over2} ({100 * over2 / n:.1f} %, ~5 % expected);"
              f" > 3: {over3} ({100 * over3 / n:.1f} %, ~0.3 % expected)")
        for a, v, key, m in sorted(pulls, reverse=True)[:5]:
            if a > 2:
                print(f"    {v:+.1f}  {key} {m}")
    bad = bool(missing or exact_bad or any(p[0] > FAIL_PULL for p in pulls))
    if identical_runs == len(common) and common and not missing:
        verdict = "IDENTICAL"
    else:
        verdict = "DIFFERENT - see above" if bad else "CONSISTENT"
    print(f"  result: {verdict}")
    return not bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("studies", nargs="+")
    ap.add_argument("--results", type=Path, default=REPO / "results",
                    help="results root (default: results/)")
    ap.add_argument("--ref", type=Path, default=REPO / "docs" / "results" / "round2",
                    help="published round (default: docs/results/round2)")
    args = ap.parse_args(argv)
    ok = True
    for s in args.studies:
        ok &= compare_study(s, args.results.resolve(), args.ref.resolve())
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
