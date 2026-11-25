# Review: Gamma shield slab (Cs-137, 662 keV)

Reviewed 25 Nov 2026 from `review_input.md` (full statistics: 30 runs,
100 000 photons each; GDML from FreeCAD 1.1.4 / GDML workbench 2.2.16;
Geant4 11.4.3).  Following docs/REVIEW_GUIDE.md.  Values are given as
FTFP_BERT / FTFP_BERT_EMZ / FTFP_BERT_LIV where all three are quoted.

## Summary

For the lowest dose behind the shield, 20 mm of lead is clearly best
(dose transmission 0.136–0.153).  Then come 40 mm of iron and 10 mm of
tungsten, which cannot be separated at this statistics (0.233–0.259).
Per unit mass, lead and tungsten are about twice as effective as iron or
concrete.  Tungsten is best per unit thickness.  The ranking is the same
under all three physics lists.  The one reference mismatch is an
electromagnetic-model effect of the standard EM option (FTFP_BERT), not a
geometry or material error.

## Validity

- **Runs:** 30 of 30 ok, no Geant4 warnings, no overlaps reported when
  reading the GDML.
- **Reference check, uncollided fraction vs NIST:** 29 of 30 pass.  The
  failure is `W_10mm__FTFP_BERT`: 0.1477 ± 0.0011 vs 0.15143 (−2.48 %,
  −3.4 σ).
- **The failure is model-dependent, not geometric:**
  - The same GDML agrees with NIST under EMZ and LIV (0.1531 ± 0.0011 for
    both, +1.1 %, +1.5 σ).
  - FTFP_BERT is below the reference in all nine shielded variants
    (−0.42 % to −2.48 %).  EMZ and LIV scatter on both sides of it.
  - Option 0's Compton process in Geant4 11.4.3 is `G4KleinNishinaCompton`,
    an empirical cross-section parametrisation whose final state neglects
    electron binding.  EMZ (Monash/LowEP model) and LIV (Livermore model)
    use evaluated data below 20 MeV.
  - The data fit option 0 attenuating 662 keV photons about 1–2 % more
    than the NIST tables.  This study cannot isolate the cause further.
- **Geometry in the renders:** as designed.  The slab starts at z = 0, the
  water phantom spans 150–160 mm, and there are no deposits outside
  material (e.g. `render/Concrete_100mm__FTFP_BERT__Cs137_pencil_xz.png`).

## Results

Dose transmission (dose in the phantom / dose without a shield), with
areal density ρt.  It is the same ranking under every list:

| variant | ρt (g/cm²) | dose transmission (FB / EMZ / LIV) | effective μ/ρ from dose (cm²/g, FB) |
|---|---|---|---|
| Pb_20mm | 22.7 | 0.1355 ± 0.0050 / 0.1442 ± 0.0052 / 0.1527 ± 0.0054 | 0.0880 ± 0.0016 |
| Fe_40mm | 31.5 | 0.2390 ± 0.0066 / 0.2352 ± 0.0064 / 0.2326 ± 0.0064 | 0.04544 ± 0.00087 |
| W_10mm | 19.3 | 0.2469 ± 0.0070 / 0.2594 ± 0.0073 / 0.2443 ± 0.0069 | 0.0725 ± 0.0015 |
| Concrete_100mm | 23.0 | 0.3927 ± 0.0088 / 0.3856 ± 0.0087 / 0.3850 ± 0.0087 | 0.04064 ± 0.00098 |
| Pb_10mm | 11.35 | 0.4062 ± 0.0096 / 0.4042 ± 0.0096 / 0.4009 ± 0.0095 | 0.0794 ± 0.0021 |
| Fe_20mm | 15.75 | 0.520 ± 0.011 / 0.513 ± 0.011 / 0.507 ± 0.011 | 0.0415 ± 0.0013 |
| W_5mm | 9.65 | 0.524 ± 0.011 / 0.520 ± 0.011 / 0.526 ± 0.011 | 0.0671 ± 0.0022 |
| Concrete_50mm | 11.5 | 0.640 ± 0.013 / 0.618 ± 0.012 / 0.629 ± 0.012 | 0.0389 ± 0.0017 |
| Pb_5mm | 5.675 | 0.655 ± 0.013 / 0.664 ± 0.013 / 0.656 ± 0.013 | 0.0744 ± 0.0035 |

Within the statistical errors these pairs are indistinguishable: Fe_40mm
and W_10mm; Concrete_100mm and Pb_10mm; Fe_20mm and W_5mm; Concrete_50mm
and Pb_5mm.

**Trade-offs (the objective):**
- **Per mass (areal density):** lead (0.074–0.088 cm²/g effective) and
  tungsten (0.067–0.073) attenuate about twice as well as iron
  (0.042–0.046) or concrete (0.039–0.042).
  - At about 20 g/cm², Pb_20mm (22.7 g/cm²) transmits 0.14–0.15.  W_10mm
    (19.3 g/cm²) transmits 0.24–0.26 and Concrete_100mm (23.0 g/cm²)
    0.385–0.393.
  - At 662 keV lead is slightly better than tungsten per gram, as its NIST
    μ/ρ (0.1102 vs 0.0978 cm²/g) predicts.
- **Per thickness:** tungsten is best.  10 mm of W does about as well as
  40 mm of Fe and better than 10 mm of Pb (0.25 vs 0.40).
- **Scattered dose:** the build-up factor (transmission / uncollided
  fraction) is lowest for the high-Z shields.
  - Pb: 1.23–1.82.
  - W: 1.34–1.69.
  - Fe and concrete: 1.51–1.67 at the thinner and 2.32–2.44 at the thicker
    variants.
  - So low-Z shields need noticeably more mass than narrow-beam
    attenuation alone suggests.

## Physics-list dependence

- **Dose transmission:** no variant differs between lists by more than
  3 σ.  The largest spread is Pb_20mm: 0.1355 (FB) to 0.1527 (LIV),
  +12.7 % at 2.3 σ.  It follows the lower uncollided fraction under FB
  (0.08078 vs 0.08406).
- **Uncollided fraction:** the three flagged differences (W_10mm EMZ and
  LIV +3.7 %, Concrete_50mm LIV +2.5 %) are the option-0 effect described
  under Validity.  EMZ and LIV agree with each other and with NIST.
- **Conclusion:** the ranking and the trade-offs above hold for all three
  lists.  For absolute transmission of thick high-Z shields at this
  energy, prefer EMZ or LIV, which reproduce the NIST attenuation.

## Recommendation

- **Thinnest shield:** tungsten.
- **Lightest shield for a given dose reduction:** lead.  Pb_20mm is the
  best variant tested.
- **Iron or concrete:** they need about twice the mass and more thickness
  for the same reduction, and give a larger scattered-dose fraction.
- **Physics list:** use FTFP_BERT_EMZ or FTFP_BERT_LIV for photon
  shielding at these energies.

## Proposed next variants

These are proposals for approval.  Each answers a question this round
left open.

```toml
[[variants]]   # equal-mass comparison with Pb_20mm (22.7 g/cm2)
name = "W_12mm"
material = "G4_W"
thickness_mm = 11.76
note = "same areal density as Pb_20mm: Pb vs W per mass, directly"

[[variants]]   # equal-mass comparison for the low-Z shields
name = "Fe_29mm"
material = "G4_Fe"
thickness_mm = 28.83
note = "22.7 g/cm2, as Pb_20mm"

[[variants]]   # where the Pb curve goes beyond the tested range
name = "Pb_40mm"
material = "G4_Pb"
thickness_mm = 40.0
note = "build-up and effective attenuation at larger thickness"
```

- **More events:** the Pb_20mm and W_10mm differences between lists
  (2–3 σ) would need about 4× the photons (400 000) to resolve at 5 σ.
  The dose errors (1.3–3.5 %) dominate the transmission errors.

## Limitations

- **Narrow beam:** a pencil beam on a 300 × 300 mm slab, with a 10 mm
  phantom 140 mm behind it.  Build-up factors depend on this geometry and
  are not broad-beam or point-source values.
- **Dose:** dose to the water phantom, deposited energy only, with no
  dose-equivalent weighting.
- **Material and energy:** one photon energy, and ideal materials (NIST
  compositions and densities; ordinary concrete).
