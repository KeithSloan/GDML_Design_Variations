"""Calorimeter study geometry: absorber/active layers in an envelope.

Layer i (0 .. layers-1) is an absorber followed by an active layer.  The
first absorber and active volumes are built once; the others are placed
copies with copy number i, so Geant4 reports the layer of every hit.
Both are sensitive detectors ("Absorber", "Active").

    build(gd, p)   gd = freecad.gdml.GDMLDesign, p = the variant's parameters
"""


def build(gd, p):
    width = float(p["width_mm"])
    a = float(p["absorber_mm"])
    s = float(p["active_mm"])
    n = int(p["layers"])
    if n < 1:
        raise ValueError("layers must be >= 1")
    pitch = a + s
    depth = n * pitch

    # vacuum envelope, front face at z = 0
    envelope = gd.makeBox(width, width, depth, material="G4_Galactic",
                          name="Calorimeter", position=(0, 0, depth / 2))
    env = gd.getVolume(envelope)
    z0 = -depth / 2  # front face in envelope coordinates

    absorber = gd.makeBox(width, width, a, material=p["absorber_material"],
                          name="Absorber", parent=env,
                          position=(0, 0, z0 + a / 2), colour="grey")
    active = gd.makeBox(width, width, s, material=p["active_material"],
                        name="Active", parent=env,
                        position=(0, 0, z0 + a + s / 2), colour="cyan")
    gd.setSensitive(absorber, "Absorber")
    gd.setSensitive(active, "Active")

    for i in range(1, n):
        dz = i * pitch
        gd.placeCopy(absorber, parent=env, name=f"Absorber_L{i}",
                     position=(0, 0, z0 + a / 2 + dz), copynumber=i)
        gd.placeCopy(active, parent=env, name=f"Active_L{i}",
                     position=(0, 0, z0 + a + s / 2 + dz), copynumber=i)
