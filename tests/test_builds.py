#!/usr/bin/env python3
"""Geometry test for the studies' build.py, without FreeCAD.

Calls build(gd, params) for every variant with a mock of GDMLDesign that
records the boxes, tubes and copies, then checks, in world coordinates:
  * every volume lies inside its mother, and the world;
  * volumes sharing a mother do not overlap (axis-aligned boxes);
  * every source and the scoring mesh are inside the world;
  * the expected sensitive detectors exist.
The real check is Geant4's overlap test when it reads the GDML.

    python3 tests/test_builds.py
"""
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from pipeline import study as studylib  # noqa: E402

EXPECTED_SD = {"shield": {"Phantom"}, "calorimeter": {"Absorber", "Active"},
               "detector": {"Crystal", "Monitor"}}
EPS = 1e-6


class Vol:
    def __init__(self, name, half, pos, parent, material, copy=0):
        self.name, self.half, self.pos = name, tuple(half), tuple(pos)
        self.parent, self.material, self.copy = parent, material, copy
        self.sensdet = None

    def world_box(self):
        x, y, z = self.pos
        p = self.parent
        while p is not None:
            x, y, z = x + p.pos[0], y + p.pos[1], z + p.pos[2]
            p = p.parent
        return [(c - h, c + h) for c, h in zip((x, y, z), self.half)]


class MockGD:
    """The parts of freecad.gdml.GDMLDesign the sample builds use."""

    def __init__(self, world_size):
        self.world = Vol("World", [s / 2 for s in world_size], (0, 0, 0), None, "")
        self.vols = []

    def _add(self, name, half, material, parent, position, **_):
        v = Vol(name, half, position or (0, 0, 0), parent or self.world, material)
        self.vols.append(v)
        return v

    def makeBox(self, x, y, z, material=None, name=None, parent=None, position=None, **kw):
        return self._add(name, (x / 2, y / 2, z / 2), material, parent, position)

    def makeTube(self, rmin, rmax, z, material=None, name=None, parent=None,
                 position=None, **kw):
        return self._add(name, (rmax, rmax, z / 2), material, parent, position)

    def getVolume(self, obj):
        return obj

    def setSensitive(self, vol, name):
        vol.sensdet = name

    def placeCopy(self, vol, parent=None, name=None, position=None, copynumber=0, **kw):
        c = Vol(name, vol.half, position, parent or self.world, vol.material, copynumber)
        c.sensdet = vol.sensdet
        self.vols.append(c)
        return c


def inside(inner, outer):
    return all(o[0] - EPS <= i[0] and i[1] <= o[1] + EPS for i, o in zip(inner, outer))


def overlap(a, b):
    return all(min(x[1], y[1]) - max(x[0], y[0]) > EPS for x, y in zip(a, b))


def check_study(st):
    spec = importlib.util.spec_from_file_location("b", st.dir / "build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    world = [(-s / 2, s / 2) for s in st.world_size_mm]
    problems = []
    for v in st.variants:
        gd = MockGD(st.world_size_mm)
        mod.build(gd, dict(v.params))
        boxes = {id(x): x.world_box() for x in gd.vols}
        for x in gd.vols:
            mother = world if x.parent is gd.world else boxes[id(x.parent)]
            if not inside(boxes[id(x)], mother):
                problems.append(f"{v.name}: {x.name} outside its mother")
        by_parent = {}
        for x in gd.vols:
            by_parent.setdefault(id(x.parent), []).append(x)
        for sibs in by_parent.values():
            for i, a in enumerate(sibs):
                for b in sibs[i + 1:]:
                    if overlap(boxes[id(a)], boxes[id(b)]):
                        problems.append(f"{v.name}: {a.name} overlaps {b.name}")
        sds = {x.sensdet for x in gd.vols if x.sensdet}
        if sds != EXPECTED_SD[st.name]:
            problems.append(f"{v.name}: sensitive detectors {sds}")
        if st.name == "calorimeter":
            n = int(v.params["layers"])
            copies = sorted(x.copy for x in gd.vols if x.sensdet == "Active")
            if copies != list(range(n)):
                problems.append(f"{v.name}: active copy numbers {copies[:5]}...")
    for s in st.sources:
        if not all(lo < c < hi for c, (lo, hi) in zip(s.position_mm, world)):
            problems.append(f"source {s.name} outside the world")
    if st.mesh:
        mesh = [(c - h, c + h) for c, h in zip(st.mesh["centre_mm"], st.mesh["half_size_mm"])]
        if not inside(mesh, world):
            problems.append("mesh outside the world")
    return problems


def main():
    bad = 0
    for name in EXPECTED_SD:
        st = studylib.load(name)
        problems = check_study(st)
        bad += len(problems)
        print(f"{'OK  ' if not problems else 'FAIL'} {name}: {len(st.variants)} variants")
        for p in problems:
            print("     ", p)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
