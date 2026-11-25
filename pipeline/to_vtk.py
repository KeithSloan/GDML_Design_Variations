"""Convert a run's scoring mesh to a VTK image file (mesh.vti).

Inputs in the run directory (written by gdmlvar through run.mac):
    mesh_edep.csv             /score/dumpQuantityToFile: ix,iy,iz,sum,sum2,n
    mesh_materials.csv(.json) /gdmlvar/voxelise: ix,iy,iz,material_id
    run.mac                   mesh size, bins and position

mesh.vti has one cell per mesh bin, with cell arrays
    edep_MeV       energy deposited per primary particle
    dose_Gy        dose per primary (0 in vacuum)
    density_g_cm3  material density at the cell centre
    material_id    index into the "materials" field (name list)
It opens in ParaView or VTK (vtkXMLImageDataReader); read_vti() reads it
back without VTK.  Needs numpy.
"""
import json
import re
import struct
from pathlib import Path

import numpy as np

from pipeline import study as studylib

MEV_TO_J = 1.602176634e-13
_TYPES = {np.dtype("<f4"): "Float32", np.dtype("<f8"): "Float64",
          np.dtype("<i4"): "Int32", np.dtype("<u1"): "UInt8"}


def mesh_geometry(macro_text):
    """(half_size_mm, centre_mm, bins) from the /score/mesh commands."""
    def nums(cmd):
        m = re.search(rf"^{re.escape(cmd)}\s+(.+)$", macro_text, re.M)
        if not m:
            raise ValueError(f"{cmd} not in run.mac")
        return [float(x) for x in m.group(1).split()[:3]]
    half = nums("/score/mesh/boxSize")
    bins = [int(x) for x in nums("/score/mesh/nBin")]
    try:
        centre = nums("/score/mesh/translate/xyz")
    except ValueError:
        centre = [0.0, 0.0, 0.0]
    return half, centre, bins


def _grid(path, shape, column):
    data = np.loadtxt(path, delimiter=",", comments="#", ndmin=2)
    out = np.zeros(shape)
    if data.size:
        ix, iy, iz = (data[:, i].astype(int) for i in range(3))
        out[ix, iy, iz] = data[:, column]
    return out


def convert(run_dir, events, keep_csv=False):
    run_dir = Path(run_dir)
    half, centre, bins = mesh_geometry((run_dir / "run.mac").read_text())
    shape = tuple(bins)
    spacing = [2 * h / n for h, n in zip(half, bins)]
    origin = [c - h for c, h in zip(centre, half)]

    edep_csv = run_dir / studylib.MESH_CSV
    edep = _grid(edep_csv, shape, 3) / float(events)

    mat_csv = run_dir / studylib.MATERIALS_CSV
    arrays = {"edep_MeV": edep.astype("<f4")}
    names = []
    if mat_csv.exists():
        legend = json.loads(Path(str(mat_csv) + ".json").read_text())
        names = [m["name"] for m in legend]
        density_of = np.array([m["density_g_cm3"] for m in legend] + [0.0])
        mat = _grid(mat_csv, shape, 3).astype(int)
        mat[mat < 0] = len(legend)          # outside the world -> density 0
        density = density_of[mat]
        voxel_cm3 = spacing[0] * spacing[1] * spacing[2] * 1e-3
        mass_kg = density * voxel_cm3 * 1e-3
        dose = np.divide(edep * MEV_TO_J, mass_kg, out=np.zeros(shape),
                         where=density > 1e-3)  # leave vacuum at 0
        mat[mat == len(legend)] = 255
        arrays["dose_Gy"] = dose.astype("<f4")
        arrays["density_g_cm3"] = density.astype("<f4")
        arrays["material_id"] = mat.astype("<u1")

    write_vti(run_dir / "mesh.vti", origin, spacing, shape, arrays,
              fields={"materials": names, "events": events})
    if not keep_csv:
        edep_csv.unlink()
        for f in (mat_csv, Path(str(mat_csv) + ".json")):
            if f.exists():
                f.unlink()
    return run_dir / "mesh.vti"


def write_vti(path, origin, spacing, shape, arrays, fields=None):
    """Cell arrays shaped (nx, ny, nz) -> VTK XML ImageData, raw appended
    data (UInt64 sizes).  fields: extra metadata, stored as a JSON string
    in a FieldData array named 'metadata'."""
    nx, ny, nz = shape
    blocks, xml_arrays, offset = [], [], 0

    def add(name, flat, ncomp=1, where="cell"):
        nonlocal offset
        raw = np.ascontiguousarray(flat).tobytes()
        blocks.append(struct.pack("<Q", len(raw)) + raw)
        vtype = _TYPES[flat.dtype]
        xml_arrays.append((where, f'<DataArray type="{vtype}" Name="{name}" '
                                  f'NumberOfComponents="{ncomp}" format="appended" '
                                  f'offset="{offset}"/>'))
        offset += 8 + len(raw)

    for name, a in arrays.items():
        a = np.asarray(a)
        if a.shape != tuple(shape):
            raise ValueError(f"{name}: shape {a.shape} != {shape}")
        add(name, a.transpose(2, 1, 0).ravel())   # VTK order: x fastest
    if fields:
        meta = np.frombuffer(json.dumps(fields).encode(), dtype="<u1")
        add("metadata", meta, where="field")

    cell = "\n".join(x for w, x in xml_arrays if w == "cell")
    field = "\n".join(x for w, x in xml_arrays if w == "field")
    ox, oy, oz = origin
    sx, sy, sz = spacing
    header = (
        '<?xml version="1.0"?>\n'
        '<VTKFile type="ImageData" version="1.0" byte_order="LittleEndian" '
        'header_type="UInt64">\n'
        f'<ImageData WholeExtent="0 {nx} 0 {ny} 0 {nz}" '
        f'Origin="{ox:g} {oy:g} {oz:g}" Spacing="{sx:g} {sy:g} {sz:g}">\n'
        + (f"<FieldData>\n{field}\n</FieldData>\n" if field else "")
        + f'<Piece Extent="0 {nx} 0 {ny} 0 {nz}">\n'
        f'<CellData Scalars="edep_MeV">\n{cell}\n</CellData>\n'
        "</Piece>\n</ImageData>\n"
        '<AppendedData encoding="raw">\n_'
    )
    with open(path, "wb") as f:
        f.write(header.encode())
        for b in blocks:
            f.write(b)
        f.write(b"\n</AppendedData>\n</VTKFile>\n")


def read_vti(path):
    """Read a file written by write_vti (not general VTK files).
    Returns dict: origin, spacing, shape, arrays {name: (nx, ny, nz)}, fields."""
    data = Path(path).read_bytes()
    start = data.index(b'<AppendedData encoding="raw">')
    start = data.index(b"_", start) + 1
    head = data[:start].decode()
    ext = [int(v) for v in re.search(r'WholeExtent="([^"]+)"', head).group(1).split()]
    shape = (ext[1], ext[3], ext[5])
    origin = [float(v) for v in re.search(r'Origin="([^"]+)"', head).group(1).split()]
    spacing = [float(v) for v in re.search(r'Spacing="([^"]+)"', head).group(1).split()]
    inv = {v: k for k, v in _TYPES.items()}
    arrays, fields = {}, {}
    for m in re.finditer(r'<DataArray type="(\w+)" Name="(\w+)"[^>]*offset="(\d+)"', head):
        vtype, name, off = m.group(1), m.group(2), int(m.group(3))
        n = struct.unpack("<Q", data[start + off:start + off + 8])[0]
        flat = np.frombuffer(data[start + off + 8:start + off + 8 + n], dtype=inv[vtype])
        if name == "metadata":
            fields = json.loads(flat.tobytes().decode())
        else:
            arrays[name] = flat.reshape(shape[2], shape[1], shape[0]).transpose(2, 1, 0)
    return {"origin": origin, "spacing": spacing, "shape": shape,
            "arrays": arrays, "fields": fields}
