"""Detector study geometry: crystal in a housing, monitor disc behind.

The housing (aluminium tube, closed at both ends) has its front face at
z = 0; the crystal sits inside it, centred.  The monitor is a 1 mm vacuum
disc behind the housing, sensitive detector "Monitor", used only to count
uncollided pencil-beam photons.  Custom materials (LYSO, LaBr3) are added
to the document by generate_gdml.py before build() is called.

    build(gd, p)   gd = freecad.gdml.GDMLDesign, p = the variant's parameters
"""


def build(gd, p):
    r = float(p["radius_mm"])
    length = float(p["length_mm"])
    h = float(p["housing_mm"])
    hl = length + 2 * h

    housing = gd.makeTube(0, r + h, hl, material=p["housing_material"],
                          name="Housing", position=(0, 0, hl / 2),
                          colour="grey")
    crystal = gd.makeTube(0, r, length, material=p["material"],
                          name="Crystal", parent=gd.getVolume(housing),
                          colour="cyan")
    gd.setSensitive(crystal, "Crystal")

    gap = float(p["monitor_gap_mm"])
    monitor = gd.makeTube(0, 5.0, 1.0, material="G4_Galactic", name="Monitor",
                          position=(0, 0, hl + gap + 0.5), colour="red")
    gd.setSensitive(monitor, "Monitor")
