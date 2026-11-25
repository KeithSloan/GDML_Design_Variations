#!/usr/bin/env python3
"""Pictures of each run's scoring mesh (mesh.vti), for people and for the
AI review.

    python3 pipeline/render.py shield            # x-z slices (matplotlib)
    python3 pipeline/render.py shield --3d       # also 3D views (VTK)

Writes results/<study>/render/<run>_xz.png: material map and energy
deposited per primary (log scale) through the beam axis, with material
boundaries drawn on the deposit.  --3d adds <run>_3d.png: geometry surfaces
with iso-surfaces of the deposit, rendered off-screen with VTK.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import study as studylib  # noqa: E402
from pipeline import to_vtk  # noqa: E402


def slice_xz(vti, title, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm

    m = to_vtk.read_vti(vti)
    nx, ny, nz = m["shape"]
    ox, _, oz = m["origin"]
    sx, _, sz = m["spacing"]
    j = ny // 2
    extent = [oz, oz + nz * sz, ox, ox + nx * sx]   # z across, x up
    edep = m["arrays"]["edep_MeV"][:, j, :]
    names = m["fields"].get("materials", [])
    # Cells below the colour floor (6 decades under the maximum) are left
    # blank, not drawn in the lowest colour: vacuum (G4_Galactic) records
    # deposits of ~1e-12 of the maximum, which are numerical noise.  Cells
    # whose centre is vacuum but which straddle a wall do hold real energy
    # (partial volume), so they are not masked by material.

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    if "material_id" in m["arrays"]:
        mat = m["arrays"]["material_id"][:, j, :].astype(float)
        mat[mat == 255] = np.nan
        im = axes[0].imshow(mat, origin="lower", extent=extent, aspect="auto",
                            cmap="tab10", vmin=-0.5, vmax=9.5, interpolation="nearest")
        ids = sorted({int(v) for v in np.unique(mat[~np.isnan(mat)])})
        handles = [plt.Rectangle((0, 0), 1, 1, color=im.cmap(im.norm(i))) for i in ids]
        axes[0].legend(handles, [names[i] if i < len(names) else str(i) for i in ids],
                       fontsize=7, loc="upper right")
    axes[0].set_title("material (cell centres, as Geant4 sees it)")

    pos = edep[edep > 0]
    if pos.size:
        vmax = pos.max()
        norm = LogNorm(vmin=max(pos.min(), vmax * 1e-6), vmax=vmax)
        im = axes[1].imshow(np.where(edep >= norm.vmin, edep, np.nan), origin="lower",
                            extent=extent, aspect="auto", cmap="inferno", norm=norm,
                            interpolation="nearest")
        fig.colorbar(im, ax=axes[1], label="MeV per primary per cell")
    if "material_id" in m["arrays"]:
        zc = oz + (np.arange(nz) + 0.5) * sz
        xc = ox + (np.arange(nx) + 0.5) * sx
        axes[1].contour(zc, xc, np.nan_to_num(mat, nan=-1),
                        levels=np.arange(-0.5, 10.5, 1.0), colors="cyan",
                        linewidths=0.6)
    axes[1].set_title("energy deposited in material (log, 6 decades)")
    for ax in axes:
        ax.set_xlabel("z (mm)")
        ax.set_ylabel("x (mm)")
    fig.suptitle(f"{title} (slice y = {m['origin'][1] + (j + 0.5) * m['spacing'][1]:g} mm)")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def view_3d(vti, title, path, size=(1100, 800)):
    import vtk

    reader = vtk.vtkXMLImageDataReader()
    reader.SetFileName(str(vti))
    reader.Update()
    img = reader.GetOutput()
    rng = img.GetCellData().GetArray("edep_MeV").GetRange()

    ren = vtk.vtkRenderer()
    ren.SetBackground(1, 1, 1)

    if img.GetCellData().GetArray("density_g_cm3") is not None:
        thr = vtk.vtkThreshold()            # cells with matter, not vacuum
        thr.SetInputData(img)
        thr.SetInputArrayToProcess(0, 0, 0, vtk.vtkDataObject.FIELD_ASSOCIATION_CELLS,
                                   "density_g_cm3")
        thr.SetThresholdFunction(vtk.vtkThreshold.THRESHOLD_UPPER)
        thr.SetUpperThreshold(1e-3)
        surf = vtk.vtkDataSetSurfaceFilter()
        surf.SetInputConnection(thr.GetOutputPort())
        gm = vtk.vtkPolyDataMapper()
        gm.SetInputConnection(surf.GetOutputPort())
        gm.ScalarVisibilityOff()
        ga = vtk.vtkActor()
        ga.SetMapper(gm)
        ga.GetProperty().SetColor(0.6, 0.6, 0.65)
        ga.GetProperty().SetOpacity(0.15)
        ren.AddActor(ga)

    if rng[1] > 0:
        c2p = vtk.vtkCellDataToPointData()
        c2p.SetInputData(img)
        c2p.Update()
        c2p.GetOutput().GetPointData().SetActiveScalars("edep_MeV")
        iso = vtk.vtkContourFilter()
        iso.SetInputConnection(c2p.GetOutputPort())
        levels = rng[1] * np.array([1e-4, 1e-3, 1e-2, 1e-1])
        for i, lv in enumerate(levels):
            iso.SetValue(i, float(lv))
        lut = vtk.vtkLookupTable()
        lut.SetScaleToLog10()
        lut.SetTableRange(levels[0], levels[-1])
        lut.SetHueRange(0.66, 0.0)
        lut.Build()
        im = vtk.vtkPolyDataMapper()
        im.SetInputConnection(iso.GetOutputPort())
        im.SetLookupTable(lut)
        im.SetScalarRange(levels[0], levels[-1])
        ia = vtk.vtkActor()
        ia.SetMapper(im)
        ia.GetProperty().SetOpacity(0.35)
        ren.AddActor(ia)
        bar = vtk.vtkScalarBarActor()
        bar.SetLookupTable(lut)
        bar.SetTitle("MeV/primary")
        bar.GetTitleTextProperty().SetColor(0, 0, 0)
        bar.GetLabelTextProperty().SetColor(0, 0, 0)
        bar.SetNumberOfLabels(4)
        ren.AddViewProp(bar)

    outline = vtk.vtkOutlineFilter()
    outline.SetInputData(img)
    om = vtk.vtkPolyDataMapper()
    om.SetInputConnection(outline.GetOutputPort())
    oa = vtk.vtkActor()
    oa.SetMapper(om)
    oa.GetProperty().SetColor(0, 0, 0)
    ren.AddActor(oa)

    text = vtk.vtkTextActor()
    text.SetInput(title)
    text.GetTextProperty().SetColor(0, 0, 0)
    text.GetTextProperty().SetFontSize(18)
    text.SetPosition(10, 10)
    ren.AddViewProp(text)

    cam = ren.GetActiveCamera()
    cam.SetFocalPoint(0, 0, 0)
    cam.SetPosition(1, 0.8, -0.6)      # looking across the beam (+z)
    cam.SetViewUp(0, 1, 0)
    ren.ResetCamera()
    cam.Zoom(1.2)

    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.AddRenderer(ren)
    win.SetSize(*size)
    win.Render()
    grab = vtk.vtkWindowToImageFilter()
    grab.SetInput(win)
    grab.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(path))
    writer.SetInputConnection(grab.GetOutputPort())
    writer.Write()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("study")
    ap.add_argument("--results", type=Path, default=None)
    ap.add_argument("--3d", dest="three_d", action="store_true",
                    help="also render 3D views with VTK")
    ap.add_argument("--only", help="run-key globs, comma-separated")
    args = ap.parse_args(argv)

    st = studylib.load(args.study)
    out = studylib.results_dir(st, args.results)
    rdir = out / "render"
    rdir.mkdir(parents=True, exist_ok=True)
    recs = {}
    jsonl = out / "runs.jsonl"
    if jsonl.exists():
        for line in jsonl.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                recs[r["key"]] = r
    import fnmatch
    pats = [p for p in (args.only or "").split(",") if p]
    n = 0
    for key, r in sorted(recs.items()):
        if r["status"] != "ok" or not r.get("vti"):
            continue
        if pats and not any(fnmatch.fnmatch(key, p) for p in pats):
            continue
        vti = out / r["run_dir"] / "mesh.vti"
        if not vti.exists():
            continue
        title = f"{st.name}: {r['variant']} / {r['physics']} / {r['source']}"
        slice_xz(vti, title, rdir / f"{key}_xz.png")
        if args.three_d:
            view_3d(vti, title, rdir / f"{key}_3d.png")
        n += 1
    print(f"{st.name}: rendered {n} run(s) into {rdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
