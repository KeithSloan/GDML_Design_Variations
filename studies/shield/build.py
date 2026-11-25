"""Shield study geometry: a shield slab and a water phantom.

Called by pipeline/generate_gdml.py in FreeCAD, once per variant, in a new
GDML document whose world is already sized (study.toml [world]).

    build(gd, p)   gd = freecad.gdml.GDMLDesign, p = the variant's parameters
"""


def build(gd, p):
    width = float(p["width_mm"])
    t = float(p["thickness_mm"])
    if t > 0:
        # front face at z = 0
        gd.makeBox(width, width, t, material=p["material"], name="Shield",
                   position=(0, 0, t / 2), colour="grey")

    d = float(p["phantom_mm"])
    z = float(p["phantom_front_mm"]) + d / 2
    if t >= float(p["phantom_front_mm"]):
        raise ValueError(f"shield ({t} mm) would reach the phantom")
    phantom = gd.makeBox(width, width, d, material="G4_WATER", name="Phantom",
                         position=(0, 0, z), colour="blue")
    gd.setSensitive(phantom, "Phantom")
