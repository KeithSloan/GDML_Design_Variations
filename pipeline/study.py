"""Load a study (studies/<name>/study.toml) and derive what each run needs.

Standard library only: imported both by the pipeline (any Python >= 3.11)
and by generate_gdml.py inside FreeCAD.

A study directory holds
    study.toml   what to build, which variants, physics lists, sources,
                 scoring mesh, reference values (see studies/README.md)
    build.py     build(gd, params): builds one variant with GDMLDesign
    metrics.py   run_metrics(), derived() and optional extra_plots()
    geometry_variants.csv, physics_variants.csv
                 the variations as tables, generated from study.toml
                 (tools/export_csv.py) - do not edit them by hand
"""
import fnmatch
import re
import tomllib
import zlib
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


@dataclass
class Variant:
    name: str
    params: dict
    note: str = ""


@dataclass
class Source:
    name: str
    particle: str
    energy_MeV: float
    events: int
    position_mm: tuple = (0.0, 0.0, 0.0)
    direction: tuple = (0.0, 0.0, 1.0)
    cone_half_angle_deg: float = 0.0   # >0: isotropic cone about +z
    disc_radius_mm: float = 0.0        # >0: parallel beam over a disc
    extra_gps: list = field(default_factory=list)
    note: str = ""


@dataclass
class Study:
    name: str
    dir: Path
    title: str
    description: str
    objective: str
    primary_metric: str
    better: str                 # "lower" or "higher"
    world_size_mm: tuple
    world_material: str
    materials: dict             # custom materials: name -> {density, formula|mixture}
    variants: list
    physics_lists: list
    sources: list
    mesh: dict                  # {} = no mesh
    mesh_physics: list          # physics lists that also write the mesh
    compare_metrics: list       # metrics compared between physics lists
    plot_metrics: list
    reference: dict
    checks: dict
    raw: dict

    def variant(self, name):
        for v in self.variants:
            if v.name == name:
                return v
        raise KeyError(name)

    def source(self, name):
        for s in self.sources:
            if s.name == name:
                return s
        raise KeyError(name)


def _check_name(kind, name):
    if not _NAME.match(name):
        raise ValueError(f"{kind} name '{name}': use letters, digits and _ "
                         "(starting with a letter)")


def _vec3(value, what):
    if len(value) != 3:
        raise ValueError(f"{what} needs 3 values")
    return tuple(float(v) for v in value)


def load(study):
    """study: a study directory, its study.toml, or a name in studies/."""
    path = Path(study)
    if not path.exists():
        path = REPO / "studies" / str(study)
    if path.is_dir():
        path = path / "study.toml"
    if not path.is_file():
        raise FileNotFoundError(f"no study.toml for '{study}'")
    with open(path, "rb") as f:
        raw = tomllib.load(f)

    s = raw["study"]
    _check_name("study", s["name"])
    defaults = raw.get("defaults", {})
    variants = []
    for v in raw["variants"]:
        v = dict(v)
        name = v.pop("name")
        _check_name("variant", name)
        note = v.pop("note", "")
        params = dict(defaults)
        params.update(v)
        variants.append(Variant(name, params, note))
    names = [v.name for v in variants]
    if len(set(names)) != len(names):
        raise ValueError("variant names must be unique")

    sources = []
    for src in raw["sources"]:
        _check_name("source", src["name"])
        sources.append(Source(
            name=src["name"],
            particle=src["particle"],
            energy_MeV=float(src["energy_MeV"]),
            events=int(src["events"]),
            position_mm=_vec3(src.get("position_mm", (0, 0, 0)), "position_mm"),
            direction=_vec3(src.get("direction", (0, 0, 1)), "direction"),
            cone_half_angle_deg=float(src.get("cone_half_angle_deg", 0.0)),
            disc_radius_mm=float(src.get("disc_radius_mm", 0.0)),
            extra_gps=list(src.get("extra_gps", [])),
            note=src.get("note", ""),
        ))

    physics = raw["physics"]
    lists = list(physics["lists"])
    mesh = dict(raw.get("mesh", {}))
    world = raw["world"]
    return Study(
        name=s["name"],
        dir=path.parent,
        title=s.get("title", s["name"]),
        description=s.get("description", ""),
        objective=s.get("objective", ""),
        primary_metric=s.get("primary_metric", ""),
        better=s.get("better", "lower"),
        world_size_mm=_vec3(world["size_mm"], "world size_mm"),
        world_material=world.get("material", "G4_Galactic"),
        materials=dict(raw.get("materials", {})),
        variants=variants,
        physics_lists=lists,
        sources=sources,
        mesh=mesh,
        mesh_physics=list(mesh.get("physics", lists[:1])) if mesh else [],
        compare_metrics=list(raw.get("analysis", {}).get("compare", [])),
        plot_metrics=list(raw.get("analysis", {}).get("plot", [])),
        reference=dict(raw.get("reference", {})),
        checks=dict(raw.get("checks", {})),
        raw=raw,
    )


def results_dir(study, root=None):
    return Path(root or REPO / "results") / study.name


def select(items, patterns):
    """Items (with .name) matching any of the comma-separated globs."""
    if not patterns:
        return list(items)
    pats = [p.strip() for p in patterns.split(",") if p.strip()]
    return [i for i in items if any(fnmatch.fnmatch(i.name, p) for p in pats)]


# ---------------------------------------------------------------------------
#   Runs
# ---------------------------------------------------------------------------
def run_key(variant, physics, source):
    return f"{variant}__{physics}__{source}"


def split_key(key):
    variant, physics, source = key.split("__")
    return variant, physics, source


def run_seed(key, base=0):
    """Reproducible seed per run (same key -> same random numbers)."""
    return (zlib.crc32(key.encode()) + int(base)) % 900_000_000 + 1


def gps_commands(src):
    x, y, z = src.position_mm
    cmds = [
        "/gps/verbose 0",
        f"/gps/particle {src.particle}",
        "/gps/ene/type Mono",
        f"/gps/ene/mono {src.energy_MeV:.9g} MeV",
    ]
    if src.disc_radius_mm > 0:
        cmds += [
            "/gps/pos/type Plane",
            "/gps/pos/shape Circle",
            f"/gps/pos/centre {x:g} {y:g} {z:g} mm",
            f"/gps/pos/radius {src.disc_radius_mm:g} mm",
            "/gps/direction {:g} {:g} {:g}".format(*src.direction),
        ]
    elif src.cone_half_angle_deg > 0:
        # GPS 'iso' emits along -(sin t cos p, sin t sin p, cos t): theta in
        # [180 - a, 180] deg gives a cone of half-angle a about +z.
        cmds += [
            "/gps/pos/type Point",
            f"/gps/pos/centre {x:g} {y:g} {z:g} mm",
            "/gps/ang/type iso",
            f"/gps/ang/mintheta {180.0 - src.cone_half_angle_deg:g} deg",
            "/gps/ang/maxtheta 180 deg",
        ]
    else:
        cmds += [
            "/gps/pos/type Point",
            f"/gps/pos/centre {x:g} {y:g} {z:g} mm",
            "/gps/direction {:g} {:g} {:g}".format(*src.direction),
        ]
    return cmds + list(src.extra_gps)


MESH_NAME = "mesh"
MESH_CSV = "mesh_edep.csv"
MATERIALS_CSV = "mesh_materials.csv"


def mesh_commands(mesh):
    hx, hy, hz = _vec3(mesh["half_size_mm"], "mesh half_size_mm")
    cx, cy, cz = _vec3(mesh.get("centre_mm", (0, 0, 0)), "mesh centre_mm")
    nx, ny, nz = (int(n) for n in mesh["bins"])
    return [
        f"/score/create/boxMesh {MESH_NAME}",
        f"/score/mesh/boxSize {hx:g} {hy:g} {hz:g} mm",
        f"/score/mesh/nBin {nx} {ny} {nz}",
        f"/score/mesh/translate/xyz {cx:g} {cy:g} {cz:g} mm",
        "/score/quantity/energyDeposit eDep MeV",
        "/score/close",
        f"/gdmlvar/voxelise {MESH_NAME} {MATERIALS_CSV}",
    ]


def macro(study, src, events, with_mesh):
    lines = [
        f"# {study.name}: source {src.name}, {events} events",
        "/control/verbose 0",
        "/run/verbose 0",
        "/event/verbose 0",
        "/tracking/verbose 0",
        "/run/initialize",
    ]
    if with_mesh and study.mesh:
        lines += mesh_commands(study.mesh)
    lines += gps_commands(src)
    lines += [
        f"/run/printProgress {max(1, events // 10)}",
        f"/run/beamOn {events}",
    ]
    if with_mesh and study.mesh:
        lines.append(f"/score/dumpQuantityToFile {MESH_NAME} eDep {MESH_CSV} csv")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
#   CSV documentation of the variations (generated from study.toml)
# ---------------------------------------------------------------------------
GEOMETRY_CSV = "geometry_variants.csv"
PHYSICS_CSV = "physics_variants.csv"

# Electromagnetic option suffixes accepted by G4PhysListFactory (Geant4 11.4)
EM_OPTIONS = {
    "_EM0": "standard option 0", "_EMV": "standard option 1",
    "_EMX": "standard option 2", "_EMY": "standard option 3",
    "_EMZ": "standard option 4", "_LIV": "Livermore", "_PEN": "Penelope",
    "__GS": "Goudsmit-Saunderson MSC", "__SS": "single scattering",
    "_WVI": "WentzelVI MSC", "__LE": "low-energy (LowEP)",
}


def split_physics_list(name):
    """'FTFP_BERT_EMZ' -> ('FTFP_BERT', '_EMZ'); no suffix -> (name, '')."""
    for suffix in sorted(EM_OPTIONS, key=len, reverse=True):
        if name.endswith(suffix) and len(name) > len(suffix):
            return name[:-len(suffix)], suffix
    return name, ""


def _cell(value):
    if isinstance(value, float):
        return f"{value:g}"
    if isinstance(value, (list, tuple)):
        return " ".join(_cell(v) for v in value)
    return str(value)


def geometry_rows(study):
    """One row per FreeCAD export: the variant and all its parameters."""
    keys = []
    for v in study.variants:
        for k in v.params:
            if k not in keys:
                keys.append(k)
    header = ["variant"] + keys + ["gdml", "note"]
    rows = [[v.name] + [_cell(v.params.get(k, "")) for k in keys]
            + [f"{v.name}.gdml", v.note] for v in study.variants]
    return header, rows


def _beam(src):
    if src.disc_radius_mm > 0:
        return f"disc r={src.disc_radius_mm:g} mm"
    if src.cone_half_angle_deg > 0:
        return f"point, cone {src.cone_half_angle_deg:g} deg about +z"
    return "pencil " + _cell(src.direction)


def physics_rows(study):
    """One row per Geant4 setting (physics list x source), each applied to
    every geometry variant without re-exporting."""
    header = ["physics_list", "hadronic", "em_physics", "source", "particle",
              "energy_MeV", "position_mm", "beam", "events", "mesh",
              "runs_per_setting"]
    rows = []
    for p in study.physics_lists:
        had, suffix = split_physics_list(p)
        em = EM_OPTIONS.get(suffix, "list default")
        for s in study.sources:
            rows.append([p, had, em, s.name, s.particle, _cell(s.energy_MeV),
                         _cell(s.position_mm), _beam(s), str(s.events),
                         "yes" if p in study.mesh_physics else "no",
                         str(len(study.variants))])
    return header, rows


def csv_texts(study):
    """{file name: CSV text} for the study's two variation tables."""
    import csv
    import io

    out = {}
    for name, (header, rows) in ((GEOMETRY_CSV, geometry_rows(study)),
                                 (PHYSICS_CSV, physics_rows(study))):
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
        out[name] = buf.getvalue()
    return out


def write_csvs(study, outdir=None):
    """Write the two tables next to study.toml (or into outdir); returns the
    files whose content changed."""
    outdir = Path(outdir or study.dir)
    changed = []
    for name, text in csv_texts(study).items():
        path = outdir / name
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
            changed.append(path)
    return changed


def runs(study, variants=None, physics=None, sources=None):
    """Every (variant, physics list, source) of the study, optionally
    restricted by comma-separated globs."""
    out = []
    for v in select(study.variants, variants):
        for p in study.physics_lists:
            if physics and not any(fnmatch.fnmatch(p, g.strip())
                                   for g in physics.split(",")):
                continue
            for s in select(study.sources, sources):
                out.append((v, p, s))
    return out
