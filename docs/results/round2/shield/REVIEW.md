# Review: Gamma shield slab (Cs-137, 662 keV), round 2

Reviewed 25 Nov 2026 from `review_input.md`.
- **Runs:** 39, at full statistics of 100 000 photons each.  The 30 round-1
  runs were reused unchanged, and the 9 new ones are W_12mm, Fe_29mm and
  Pb_40mm under each list.
- **Versions:** GDML from FreeCAD 1.1.4 and GDML workbench 2.2.16, design
  commit 3fc0a90; Geant4 11.4.3.

Written following docs/REVIEW_GUIDE.md.  Where all three lists are quoted,
values are given as FTFP_BERT / FTFP_BERT_EMZ / FTFP_BERT_LIV.  The round-1
review is in [../../round1/shield/REVIEW.md](../../round1/shield/REVIEW.md).

## Summary

At equal mass (22.7 g/cm², 20.4 kg of slab), lead is the best shield at
662 keV:
- **Pb 20 mm:** transmission 0.136–0.153.
- **W 11.76 mm:** 0.186–0.191.
- **Fe 28.8 mm:** 0.355–0.381, about twice the lead value.
- **Concrete 100 mm** (23.0 g/cm²) is about the same as iron.

The three round-2 variants settle the equal-mass question that round 1 left
open, and the ranking is the same under all three physics lists.

Doubling lead to 40 mm cuts the transmission to 0.0165–0.0170.  It also
raises the build-up factor from 1.7–1.8 to 2.4–2.5, so the scattered
fraction of the dose grows with thickness.

Validity is as in round 1:
- one reference mismatch, the same option-0 EM-model effect;
- the new variants all pass their reference checks.

## Validity

- **Runs:** 39 of 39 ok.  Every run has its requested number of photons,
  with no Geant4 warnings and no overlaps reported when reading the GDML.
- **Reference check, uncollided fraction vs NIST:** 38 of 39 pass.
  - The failure is the round-1 run `W_10mm__FTFP_BERT`: 0.1477 ± 0.0011 vs
    0.15143 (−2.48 %, −3.4 σ).
  - Under EMZ and LIV the same GDML agrees with NIST (0.1531 ± 0.0011,
    +1.1 %, +1.5 σ).
- **The new variants pass under all three lists:**

  | variant | reference | FTFP_BERT | EMZ | LIV |
  |---|---|---|---|---|
  | W_12mm | 0.10862 | 0.10798 ± 0.00098 (−0.6 %, −0.7 σ) | 0.10827 ± 0.00098 (−0.3 %, −0.4 σ) | 0.10941 ± 0.00099 (+0.7 %, +0.8 σ) |
  | Fe_29mm | 0.18869 | 0.1882 ± 0.0012 (−0.3 %, −0.4 σ) | 0.1910 ± 0.0012 (+1.2 %, +1.8 σ) | 0.1889 ± 0.0012 (+0.1 %, +0.2 σ) |
  | Pb_40mm | 0.0067294 | 0.00667 ± 0.00026 (−0.9 %, −0.2 σ) | 0.00693 ± 0.00026 (+3.0 %, +0.8 σ) | 0.00688 ± 0.00026 (+2.2 %, +0.6 σ) |

- **The option-0 pattern holds:**
  - FTFP_BERT is below the NIST reference in all 12 shielded variants
    (−0.28 % to −2.48 %).  EMZ and LIV scatter on both sides.
  - The detector study shows the same for all 9 crystals.  Across both
    studies FTFP_BERT is low in 21 of 21 cases, too one-sided to be chance.
  - Most individual deviations are within 1–2 σ, so this round confirms the
    direction of the effect, not a size for each material.
- **Geometry in the renders:** as designed.
  - The new slabs have the right thicknesses: 0–40 mm of lead in
    `render/Pb_40mm__FTFP_BERT__Cs137_pencil_xz.png`, and likewise for
    `W_12mm` and `Fe_29mm`.
  - The phantom spans 150–160 mm.
  - There are no deposits outside material.

## Results

Dose transmission and the quantities behind it:

| variant | ρt (g/cm²) | dose transmission (FB / EMZ / LIV) | build-up factor (FB / EMZ / LIV) | effective μ/ρ from dose (cm²/g, FB / EMZ / LIV) |
|---|---|---|---|---|
| Pb_40mm | 45.4 | 0.0170 ± 0.0017 / 0.0167 ± 0.0016 / 0.0165 ± 0.0016 | 2.54 ± 0.27 / 2.42 ± 0.25 / 2.40 ± 0.25 | 0.0898 ± 0.0022 / 0.0901 ± 0.0021 / 0.0904 ± 0.0021 |
| Pb_20mm | 22.7 | 0.1355 ± 0.0050 / 0.1442 ± 0.0052 / 0.1527 ± 0.0054 | 1.678 ± 0.064 / 1.767 ± 0.066 / 1.816 ± 0.067 | 0.0880 ± 0.0016 / 0.0853 ± 0.0016 / 0.0828 ± 0.0015 |
| W_12mm | 22.7 | 0.1861 ± 0.0060 / 0.1908 ± 0.0060 / 0.1874 ± 0.0060 | 1.724 ± 0.057 / 1.763 ± 0.058 / 1.713 ± 0.057 | 0.0741 ± 0.0014 / 0.0730 ± 0.0014 / 0.0738 ± 0.0014 |
| Fe_40mm | 31.5 | 0.2390 ± 0.0066 / 0.2352 ± 0.0064 / 0.2326 ± 0.0064 | 2.437 ± 0.071 / 2.382 ± 0.069 / 2.336 ± 0.068 | 0.04544 ± 0.00087 / 0.04596 ± 0.00086 / 0.04631 ± 0.00088 |
| W_10mm | 19.3 | 0.2469 ± 0.0070 / 0.2594 ± 0.0073 / 0.2443 ± 0.0069 | 1.672 ± 0.049 / 1.694 ± 0.049 / 1.595 ± 0.047 | 0.0725 ± 0.0015 / 0.0699 ± 0.0015 / 0.0730 ± 0.0015 |
| Fe_29mm | 22.7 | 0.3714 ± 0.0088 / 0.3809 ± 0.0089 / 0.3553 ± 0.0085 | 1.974 ± 0.048 / 1.995 ± 0.048 / 1.881 ± 0.047 | 0.0436 ± 0.0010 / 0.0425 ± 0.0010 / 0.0456 ± 0.0011 |
| Concrete_100mm | 23.0 | 0.3927 ± 0.0088 / 0.3856 ± 0.0087 / 0.3850 ± 0.0087 | 2.373 ± 0.056 / 2.323 ± 0.055 / 2.323 ± 0.055 | 0.04064 ± 0.00098 / 0.04143 ± 0.00098 / 0.04150 ± 0.00098 |

The round-1 variants not shown (Pb_5mm, Pb_10mm, W_5mm, Fe_20mm,
Concrete_50mm) are unchanged; see the round-1 review.

**Equal mass, 22.7 g/cm² (the round-2 question):** at the same areal density
the dose ranking is lead, then tungsten, then iron and concrete.  The
differences below are my arithmetic on the table above.
- **Pb_20mm vs W_12mm:**
  - Lead transmits 0.0506 ± 0.0078 / 0.0467 ± 0.0079 / 0.0347 ± 0.0080
    less (−6.5 σ / −5.9 σ / −4.3 σ).
  - In relative terms that is 18–27 % less dose for the same mass.
  - The narrow-beam numbers agree: W_12mm lets through 30–34 % more
    uncollided photons than Pb_20mm.  This is what the NIST coefficients
    predict (μ/ρ 0.1102 for Pb vs 0.0978 cm²/g for W).
  - Tungsten is 41 % thinner (11.76 vs 20 mm).
- **W_12mm vs Fe_29mm:** tungsten transmits about half as much: 0.501 /
  0.501 / 0.527 of the iron value (16–18 σ).
- **Fe_29mm vs Concrete_100mm:** not distinguishable.  Iron is lower by
  −1.7 σ / −0.4 σ / −2.4 σ, so the two are equal at this statistics.
- **Effective μ/ρ from dose:**
  - lead 0.083–0.088 cm²/g;
  - tungsten 0.073–0.074;
  - iron 0.042–0.046;
  - concrete 0.041–0.042.
  Within each list, lead and tungsten are 1.6–2.2 times as effective per
  gram as iron and concrete, consistent with round 1's "about twice".

**Thicker lead (Pb_40mm):**
- **Transmission:** 0.0165–0.0170, 11–13 % of the Pb_20mm value.
- **Build-up:** rises from 1.68–1.82 to 2.40–2.54, an increase of
  2.2–3.1 σ.
- **Effective μ/ρ from dose:** rises from 0.083–0.088 to 0.090.  It tends
  towards the narrow-beam value from below as the slab thickens, because
  the build-up factor grows more slowly than the attenuation.
- **Statistics:** Pb_40mm's dose has a 10 % statistical error, against
  3.4 % for Pb_20mm.  Only 0.67–0.69 % of the photons cross 40 mm of lead
  uncollided.

**Per thickness**, tungsten remains best.  W_12mm (11.76 mm) does better
than Fe_40mm and Concrete_100mm, which are 3.4 and 8.5 times thicker.

## Physics-list dependence

- **Dose transmission:** for the new variants no pair of lists differs by
  more than 2.1 σ.  The largest spread is Fe_29mm, 0.3553 (LIV) to 0.3809
  (EMZ).  Pb_20mm keeps its round-1 spread of 0.1355 (FB) to 0.1527 (LIV),
  at 2.3 σ.
- **Uncollided fraction:** the only differences flagged significant are the
  round-1 ones (W_10mm, Concrete_50mm).  None of the new variants is
  flagged.
- **Conclusion:** the ranking, the equal-mass comparison and the Pb_40mm
  trend hold under all three lists.  For absolute transmission at this
  energy, the round-1 advice stands: prefer EMZ or LIV.

## Recommendation

- **Lightest shield for a given dose at 662 keV:** lead.  At equal mass it
  gives 18–27 % less dose than tungsten and about half the dose of iron or
  concrete.
- **Thinnest shield:** tungsten.  For the same mass it is 41 % thinner than
  lead, at the cost of a higher dose.
- **Iron and concrete** are equivalent per unit mass at this energy, and
  both need about twice the mass of lead.
- **Thick shields:** account for build-up when sizing them.  The
  narrow-beam attenuation underestimates the dose behind 40 mm of lead by
  a factor of 2.4–2.5 in this geometry.

## Proposed next variants

The equal-mass question is answered, so no further geometry variants are
needed for this objective.  These proposals extend the study and need
approval:

- **A second photon energy** (a physics variation, no new geometry), e.g. a
  1.3325 MeV pencil beam (the higher Co-60 line).  It would test whether
  lead's per-mass advantage over iron shrinks where Compton scattering
  dominates.
  - This needs a design change first: the study's reference μ/ρ values
    are for 662 keV only.  `[reference]` would need one table per source,
    and `tools/attenuation_refs.py` an energy argument.
- **More photons for Pb_40mm**, if its dose matters.  At 400 000 photons
  per run (4×), its 10 % dose error would halve.  The shield source applies
  to every variant, so this means 4× the run time.  The runs are cheap,
  2–20 s each.

## Limitations

As in round 1:
- **Geometry:** a pencil beam on a 300 × 300 mm slab, with a 10 mm water
  phantom whose front face is at z = 150 mm (50–150 mm behind the slab).  The build-up factors belong to this
  geometry, not to broad-beam or point-source conditions.
- **Dose:** deposited dose only, with no dose-equivalent weighting.
- **Energy and materials:** one photon energy, and ideal NIST materials.
- **Statistics:** Pb_40mm's dose is the least certain value in the table
  (± 10 %).
