#!/usr/bin/env python3
"""TEST DOUBLE for g4app's gdmlvar - not a simulation.

Takes the same arguments and writes the same files (events.csv,
summary.json, mesh_edep.csv, mesh_materials.csv[.json]) with made-up
numbers from toy formulas, so the pipeline (run_matrix -> to_vtk ->
analyse -> render) can be tested without Geant4 or FreeCAD.  It reads the
variant's parameters from the <variant>.json next to the GDML file and
knows the three sample studies only.  Nothing it writes is a result.
"""
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from pipeline import study as studylib  # noqa: E402

DENSITY = {"G4_Galactic": 1e-25, "G4_Pb": 11.35, "G4_W": 19.3, "G4_Fe": 7.874,
           "G4_CONCRETE": 2.3, "G4_WATER": 1.0, "G4_Al": 2.699,
           "G4_SODIUM_IODIDE": 3.667, "G4_CESIUM_IODIDE": 4.51, "G4_BGO": 7.13,
           "LYSO": 7.1, "LaBr3": 5.08, "G4_PLASTIC_SC_VINYLTOLUENE": 1.032,
           "G4_lAr": 1.396}
RADLEN = {"G4_Pb": 5.6, "G4_W": 3.5, "G4_Fe": 17.6,
          "G4_PLASTIC_SC_VINYLTOLUENE": 425.0, "G4_lAr": 140.0}
LAMBDA = {"G4_Pb": 182.0, "G4_W": 99.0, "G4_Fe": 168.0,
          "G4_PLASTIC_SC_VINYLTOLUENE": 700.0, "G4_lAr": 860.0}


def vol(name, mat, mass, placements=1, sd=""):
    return {"name": name, "material": mat, "density_g_cm3": DENSITY[mat],
            "radlen_mm": RADLEN.get(mat, 100.0),
            "nuclear_int_length_mm": LAMBDA.get(mat, 500.0),
            "mass_kg": mass, "placements": placements, "daughters": 0, "sensdet": sd}


def main():
    a = sys.argv[1:]
    opt = {a[i]: a[i + 1] for i in range(0, len(a) - 1, 2) if a[i].startswith("-")}
    gdml, physics, macro_file = Path(opt["-g"]), opt["-p"], opt["-m"]
    rng = np.random.default_rng(int(opt.get("-s", 1)))
    mac = Path(macro_file).read_text()
    n = int(re.search(r"^/run/beamOn (\d+)", mac, re.M).group(1))
    e0 = float(re.search(r"^/gps/ene/mono (\S+) MeV", mac, re.M).group(1))
    particle = re.search(r"^/gps/particle (\S+)", mac, re.M).group(1)
    cone = "/gps/ang/type iso" in mac
    meta = json.loads(gdml.with_suffix(".json").read_text())
    st = studylib.load(meta["study"])
    p = meta["params"]
    bias = {"FTFP_BERT": 1.0, "FTFP_BERT_EMZ": 1.003, "FTFP_BERT_LIV": 0.998,
            "QGSP_BIC": 0.97}.get(physics, 1.0)
    cols, dets, vols = {}, {}, [vol("World", st.world_material, 0.0)]

    if st.name == "shield":
        t = float(p["thickness_mm"])
        mu = st.reference["mu_rho_cm2_g"].get(p["material"], 0.08)
        u_prob = math.exp(-mu * DENSITY[p["material"]] * t / 10) if t > 0 else 1.0
        unc = rng.random(n) < u_prob
        hit = unc | (rng.random(n) < 0.3 * (1 - u_prob) * bias)
        edep = np.where(hit, rng.exponential(0.05, n), 0.0)
        cols = {"Phantom_edep_MeV": edep, "Phantom_uncollided": unc.astype(int)}
        mass = 0.3 * 0.3 * 0.01 * 1000
        dets["Phantom"] = (edep, unc, {0: edep}, mass, ["Phantom"])
        if t > 0:
            vols.append(vol("Shield", p["material"], DENSITY[p["material"]] * 0.09 * t))
        vols.append(vol("Phantom", "G4_WATER", mass, sd="Phantom"))
    elif st.name == "calorimeter":
        layers = int(p["layers"])
        tot = rng.normal(0.95 * e0 * bias, 0.03 * e0, n).clip(0)
        f = 0.1 * (1 + 0.1 * rng.normal(size=n)) * (0.7 if particle == "pi+" else 1.0)
        act, ab = tot * f, tot * (1 - f)
        prof = np.exp(-((np.arange(layers) - layers / 4) / (layers / 6)) ** 2)
        prof /= prof.sum()
        dets["Absorber"] = (ab, np.zeros(n, bool), {i: ab * w for i, w in enumerate(prof)},
                            1.0, ["Absorber"])
        dets["Active"] = (act, np.zeros(n, bool), {i: act * w for i, w in enumerate(prof)},
                          1.0, ["Active"])
        cols = {"Absorber_edep_MeV": ab, "Active_edep_MeV": act,
                "Absorber_uncollided": np.zeros(n, int), "Active_uncollided": np.zeros(n, int)}
        vols += [vol("Calorimeter", "G4_Galactic", 0.0),
                 vol("Absorber", p["absorber_material"], 1.0, layers, "Absorber"),
                 vol("Active", p["active_material"], 0.2, layers, "Active")]
    else:  # detector
        mu = st.reference["mu_rho_cm2_g"]
        x = (mu["G4_Al"] * DENSITY["G4_Al"] * 0.2
             + mu.get(p["material"], 0.08) * DENSITY[p["material"]] * float(p["length_mm"]) / 10)
        u_prob = math.exp(-x)
        size = float(p["radius_mm"]) / 19.05
        interacts = rng.random(n) < (0.4 * size if cone else 1 - u_prob)
        peak = interacts & (rng.random(n) < 0.45 * bias)
        edep = np.where(peak, e0, np.where(interacts, rng.uniform(0.01, 0.48, n), 0.0))
        mon = (~interacts) & (not cone)
        cols = {"Crystal_edep_MeV": edep, "Monitor_edep_MeV": np.zeros(n),
                "Crystal_uncollided": interacts.astype(int), "Monitor_uncollided": mon.astype(int)}
        dets["Crystal"] = (edep, interacts, {0: edep}, 0.2, ["Crystal"])
        dets["Monitor"] = (np.zeros(n), mon, {}, 0.0, ["Monitor"])
        vols += [vol("Housing", p["housing_material"], 0.05),
                 vol("Crystal", p["material"], 0.2, sd="Crystal"),
                 vol("Monitor", "G4_Galactic", 0.0, sd="Monitor")]

    names = list(cols)
    with open("events.csv", "w") as f:
        f.write("event," + ",".join(names) + "\n")
        for i in range(n):
            f.write(f"{i}," + ",".join(f"{cols[c][i]:.9g}" for c in names) + "\n")

    summary = {"app": "gdmlvar (FAKE test double)", "geant4_version": "none",
               "gdml": str(gdml), "physics_list": physics, "events": n,
               "wall_seconds": 0.01, "exceptions": {}, "detectors": {}, "volumes": vols}
    for name, (e, u, copies, mass, lvs) in dets.items():
        summary["detectors"][name] = {
            "volumes": lvs, "placements": 1, "mass_kg": mass,
            "sum_edep_MeV": float(e.sum()), "sum2_edep_MeV2": float((e * e).sum()),
            "events_with_edep": int((e > 0).sum()), "uncollided": int(u.sum()),
            "copies": {str(k): [float(v.sum()), float((v * v).sum())]
                       for k, v in copies.items()}}
    Path("summary.json").write_text(json.dumps(summary, indent=1))

    if "/score/create/boxMesh" in mac:
        from pipeline.to_vtk import mesh_geometry
        half, centre, bins = mesh_geometry(mac)
        nx, ny, nz = bins
        zc = centre[2] - half[2] + (np.arange(nz) + 0.5) * 2 * half[2] / nz
        xc = centre[0] - half[0] + (np.arange(nx) + 0.5) * 2 * half[0] / nx
        r2 = xc[:, None, None] ** 2 + xc[None, :, None] ** 2 if nx == ny else 0
        val = np.exp(-r2 / 200.0) * np.exp(-np.abs(zc[None, None, :] - zc.mean()) / 50.0)
        mat = (np.abs(zc - zc.mean()) < 15)[None, None, :] * np.ones((nx, ny, 1), int)
        with open(studylib.MESH_CSV, "w") as f, open(studylib.MATERIALS_CSV, "w") as g:
            f.write("# FAKE\n")
            g.write("# FAKE\n")
            for i in range(nx):
                for j in range(ny):
                    for k in range(nz):
                        f.write(f"{i},{j},{k},{val[i, j, k] * n:.6g},0,1\n")
                        g.write(f"{i},{j},{k},{mat[i, j, k]}\n")
        Path(studylib.MATERIALS_CSV + ".json").write_text(json.dumps(
            [{"id": 0, "name": st.world_material, "density_g_cm3": 1e-25},
             {"id": 1, "name": "G4_WATER", "density_g_cm3": 1.0}]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
