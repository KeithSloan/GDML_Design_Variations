#!/usr/bin/env python3
"""Reference photon mass attenuation coefficients for the sample studies.

Prints mu/rho (cm2/g, total including coherent scattering) at a photon
energy for each material, ready to paste into a study.toml [reference]
table.  Element values come from the Elam, Ravel & Sieber tables shipped
with xraydb, which reproduce the NIST tables of Hubbell & Seltzer
(NISTIR 5632) at their energies and are valid up to 800 keV.  Compounds
use the mixture rule with the compositions Geant4 uses
(G4NistMaterialBuilder.cc, Geant4 11.4).

    pip install xraydb
    python3 tools/attenuation_refs.py            # 661.657 keV (Cs-137)
    python3 tools/attenuation_refs.py 0.6        # MeV
"""
import sys

import xraydb

# name -> ("atoms", {symbol: count}) or ("mass", {symbol: fraction})
MATERIALS = {
    "G4_Pb": ("atoms", {"Pb": 1}),
    "G4_Fe": ("atoms", {"Fe": 1}),
    "G4_W": ("atoms", {"W": 1}),
    "G4_Al": ("atoms", {"Al": 1}),
    "G4_WATER": ("atoms", {"H": 2, "O": 1}),
    "G4_CONCRETE": ("mass", {"H": 0.01, "C": 0.001, "O": 0.529107, "Na": 0.016,
                             "Mg": 0.002, "Al": 0.033872, "Si": 0.337021,
                             "K": 0.013, "Ca": 0.044, "Fe": 0.014}),
    "G4_SODIUM_IODIDE": ("atoms", {"Na": 1, "I": 1}),
    "G4_CESIUM_IODIDE": ("atoms", {"Cs": 1, "I": 1}),
    "G4_BGO": ("atoms", {"Bi": 4, "Ge": 3, "O": 12}),
    # custom materials defined in studies/detector/study.toml
    "LYSO": ("atoms", {"Lu": 9, "Y": 1, "Si": 5, "O": 25}),
    "LaBr3": ("atoms", {"La": 1, "Br": 3}),
}


def mass_fractions(kind, comp):
    if kind == "mass":
        total = sum(comp.values())
        return {el: w / total for el, w in comp.items()}
    masses = {el: n * xraydb.atomic_mass(el) for el, n in comp.items()}
    total = sum(masses.values())
    return {el: m / total for el, m in masses.items()}


def mu_rho(name, energy_eV):
    kind, comp = MATERIALS[name]
    return sum(w * xraydb.mu_elam(el, energy_eV, kind="total")
               for el, w in mass_fractions(kind, comp).items())


def main():
    energy_MeV = float(sys.argv[1]) if len(sys.argv) > 1 else 0.661657
    if energy_MeV > 0.8:
        sys.exit("the Elam tables are only valid up to 0.8 MeV")
    print(f"# mu/rho (cm2/g, with coherent) at {energy_MeV} MeV - "
          f"Elam tables (xraydb {xraydb.__version__}), mixture rule")
    for name in MATERIALS:
        print(f'"{name}" = {float(mu_rho(name, energy_MeV * 1e6)):.5g}')


if __name__ == "__main__":
    main()
