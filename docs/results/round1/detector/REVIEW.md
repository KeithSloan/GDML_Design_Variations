# Review: Gamma-ray crystal detector (Cs-137, 662 keV)

Reviewed 25 Nov 2026 from `review_input.md` (full statistics: 36 runs;
100 000 photons per cone run, 50 000 per pencil run; GDML from FreeCAD
1.1.4 / GDML workbench 2.2.16; Geant4 11.4.3).  Following
docs/REVIEW_GUIDE.md.  Three-way values are FTFP_BERT / FTFP_BERT_EMZ /
FTFP_BERT_LIV.  Efficiencies are per photon emitted into 4π.

## Summary

- **Largest crystal:** the 3 × 3 inch NaI has by far the highest absolute
  full-energy-peak efficiency (1.10–1.11 × 10⁻²), 6.5–6.7 times the
  1.5-inch NaI reference.
- **Same 1.5 × 1.5 inch size:** BGO is best (5.1–5.3 × 10⁻³, 3.0–3.2 × NaI),
  then LYSO (2.6–2.7 ×), CsI (1.4 ×) and LaBr₃ (1.2–1.3 ×).  BGO also has
  the highest peak-to-total (0.76–0.78).
- **Robustness:** the ranking is the same under all three physics lists.
- **Validity:** the one reference mismatch is the same option-0 EM-model
  effect seen in the shield study, not a material or geometry error.  The
  two custom materials, LYSO and LaBr₃, defined in FreeCAD with
  `addMaterial`, pass their NIST attenuation checks.

## Validity

- **Runs:** 36 of 36 ok, no Geant4 warnings, no overlaps reported when
  reading the GDML.
- **Reference check, uncollided fraction through housing and crystal vs
  NIST:** 17 of 18 pass.  The failure is `CsI_1p5in__FTFP_BERT`: 0.2461 ±
  0.0019 vs 0.25336 (−2.88 %, −3.8 σ).
  - Under EMZ and LIV the same GDML agrees with NIST (0.2558 and 0.2556,
    +1.0 % and +0.9 %, both within 1.2 σ).
  - FTFP_BERT is below the reference for all six crystals (−0.34 % to
    −2.88 %).  This matches the shield study: option 0's Compton
    cross-section (`G4KleinNishinaCompton`, empirical, binding neglected in
    the final state) attenuates about 1–2 % more than the NIST tables.
- **Custom materials:** LYSO (Lu₉Y₁Si₅O₂₅, 7.1 g/cm³) and LaBr₃
  (5.08 g/cm³) pass under all three lists (−2.1 % to +1.4 %, within 2.6 σ).
  So the `addMaterial` → GDML → Geant4 chain is right for formula-defined
  materials.
- **Spectra** (`plots/spectra.png`): a Compton continuum ending at the
  Compton edge near 0.48 MeV, multiple-scatter events between the edge
  and the peak, and the full-energy peak at 0.662 MeV.  These are the
  expected features.
- **Renders:** the crystals and housings are as designed.  In
  `render/BGO_1p5in__FTFP_BERT__Cs137_cone_xz.png` the 1 mm side wall falls
  between the 2 mm cell centres, so the material panel shows no side wall.
  This is a sampling effect of the mesh, not missing geometry (the front
  and back walls show).  Deposits stay in material, concentrated in the
  front half of the dense crystals.

## Results

Cone source (point source 100 mm in front, 30° cone):

| variant | crystal mass (kg) | peak efficiency (10⁻³) | total efficiency (10⁻³) | peak-to-total |
|---|---|---|---|---|
| NaI_3in | 1.274 | 11.100 ± 0.079 / 10.967 ± 0.078 / 11.087 ± 0.079 | 19.958 / 19.883 / 20.006 (± 0.097) | 0.5562 / 0.5516 / 0.5542 (± 0.0029) |
| BGO_1p5in | 0.3097 | 5.340 ± 0.057 / 5.103 ± 0.056 / 5.109 ± 0.056 | 6.827 / 6.664 / 6.686 (± 0.064) | 0.7822 / 0.7658 / 0.7642 (± 0.0042) |
| LYSO_1p5in | 0.3084 | 4.486 ± 0.053 / 4.442 ± 0.053 / 4.359 ± 0.052 | 6.419 / 6.435 / 6.322 (± 0.062) | 0.6989 / 0.6903 / 0.6894 (± 0.0047) |
| CsI_1p5in | 0.1959 | 2.375 ± 0.039 / 2.399 ± 0.039 / 2.449 ± 0.040 | 4.993 / 4.982 / 5.027 (± 0.056) | 0.4758 / 0.4815 / 0.4872 (± 0.0058) |
| LaBr3_1p5in | 0.2207 | 2.156 ± 0.037 / 2.046 ± 0.036 / 2.036 ± 0.036 | 5.244 / 5.127 / 5.009 (± 0.057) | 0.4112 / 0.3992 / 0.4066 (± 0.0056) |
| NaI_1p5in | 0.1593 | 1.668 ± 0.033 / 1.681 ± 0.033 / 1.690 ± 0.033 | 4.305 / 4.274 / 4.381 (± 0.052) | 0.3874 / 0.3932 / 0.3858 (± 0.0061) |

Derived from the table (my arithmetic, ranges over the three lists):

| variant | peak efficiency per kg (10⁻³/kg) | peak efficiency / NaI_1p5in |
|---|---|---|
| BGO_1p5in | 16.5–17.2 | 3.02–3.20 |
| LYSO_1p5in | 14.1–14.6 | 2.58–2.69 |
| CsI_1p5in | 12.1–12.5 | 1.42–1.45 |
| NaI_1p5in | 10.5–10.6 | 1 |
| LaBr3_1p5in | 9.2–9.8 | 1.20–1.29 |
| NaI_3in | 8.6–8.7 | 6.52–6.65 |

**Trade-offs (the objective):**
- **Highest absolute peak efficiency:** the 3-inch NaI.  It is 8 times the
  crystal mass of the 1.5-inch NaI, and the least efficient per kilogram.
- **Best per unit size and per unit mass:** BGO.  Being densest and of
  highest Z, it has the best peak-to-total.  LYSO is close behind on all
  three.
- **LaBr₃:** at 662 keV and this size its stopping power gives only a
  modest gain over NaI.  Its real advantage, energy resolution, is not
  simulated here (see Limitations), so this study does not capture why it
  would be chosen.
- **CsI:** about 1.4 × NaI, with intermediate peak-to-total.

## Physics-list dependence

- **Ranking:** the same under all three lists.
- **Uncollided fraction:** the flagged CsI differences (EMZ and LIV +3.9 to
  +4.0 % vs FTFP_BERT, 3.5 σ) are the option-0 attenuation effect under
  Validity.
- **Efficiencies of high-Z crystals:** EMZ and LIV give lower values than
  FTFP_BERT.
  - BGO peak efficiency: 4.3–4.4 % lower (2.9 σ).
  - LaBr₃ peak efficiency: 5.1–5.6 % lower (2.1–2.3 σ).
  - BGO peak-to-total: 2.1–2.3 % lower, with LIV vs FTFP_BERT flagged at
    3.1 σ.
  - The direction fits option 0's stronger attenuation.  EMZ and LIV agree
    with each other.
- **Conclusion:** for absolute efficiencies at the few-per-cent level,
  prefer EMZ or LIV, which reproduce the NIST attenuation.  The
  comparison between crystals does not depend on the choice.

## Recommendation

- **Maximum counting efficiency at 662 keV within a fixed size:** BGO,
  with LYSO as the close alternative.
- **Maximum absolute efficiency:** the largest crystal; size matters more
  than material.
- **Absolute efficiency values:** quote EMZ or LIV results.
- **Choosing between crystals for spectroscopy:** first add detector
  resolution (see Limitations).  It would likely change the comparison
  between LaBr₃, NaI and BGO.

## Proposed next variants

These are proposals for approval.

```toml
[[variants]]   # size scan for the best material
name = "BGO_2in"
material = "G4_BGO"
radius_mm = 25.4
length_mm = 50.8
note = "does BGO's lead persist at a larger size?"

[[variants]]   # equal-mass comparison with NaI_3in
name = "BGO_eqmass_NaI3in"
material = "G4_BGO"
radius_mm = 30.5
length_mm = 61.1
note = "same mass as NaI_3in (1.27 kg at 7.13 g/cm3), length = diameter"

[[variants]]   # LYSO at the same size as BGO_2in
name = "LYSO_2in"
material = "LYSO"
radius_mm = 25.4
length_mm = 50.8
```

- **Proposed metrics change (design stage):** apply a per-material energy
  resolution (Gaussian σ(E) from published values) before counting the
  peak, so that the efficiency in a realistic peak window can be compared.
  This changes `metrics.py`, not the runs.

## Limitations

- **Deposited energy only:** no energy resolution, light yield or
  non-proportionality is applied.  The peak efficiencies are ideal values,
  and LaBr₃'s main advantage is absent.
- **Source:** one source distance (100 mm) and one energy.  The
  efficiencies scale with solid angle and would change for other
  distances and energies.
- **Housing:** a 1 mm aluminium housing with no reflector, optical window
  or photomultiplier mass.
