# Review: Sampling calorimeter (1 GeV electrons, 10 GeV pions), round 2

Reviewed 25 Nov 2026 from `review_input.md`.
- **Runs:** 48, with 2000 electrons and 500 pions per run.  The 36 round-1
  runs were reused unchanged, and the 12 new ones are W0p7_Sc2_x120 and
  Pb1_LAr2_x120 under each list and source.
- **Versions:** GDML from FreeCAD 1.1.4 and GDML workbench 2.2.16, design
  commit 3fc0a90; Geant4 11.4.3.

Written following docs/REVIEW_GUIDE.md.  Where all three lists are quoted,
values are given as FTFP_BERT / QGSP_BIC / FTFP_BERT_EMZ.  The round-1
review is in [../../round1/calorimeter/REVIEW.md](../../round1/calorimeter/REVIEW.md).

## Summary

- **Fine sampling wins.**  The two new 120-layer variants join Pb1_Sc2_x120
  at the top of the electron-resolution ranking under all three lists.
  - Pb 1 mm / liquid argon 2 mm is best: σ/E = 0.055–0.058 at 1 GeV.
  - Pb 1 mm / scintillator 2 mm gives 0.059–0.063.
  - W 0.7 mm / scintillator 2 mm gives 0.061–0.068 in 10 % less depth
    (324 mm).
- **Halving the layers pays the same everywhere.**  It improves σ/E by
  20–27 % for lead/scintillator, lead/LAr and tungsten/scintillator alike.
- **Two questions remain open at this statistics:**
  - **LAr vs scintillator:** LAr is better by up to 9 %, but this is
    significant under EMZ only.
  - **The resolution flags between physics lists:** they are weakened by a
    few events in the tails of the signal distribution.
- **Pions:** as in round 1, these designs are too shallow for pions, which
  the new `hcal` study addresses.

## Validity

- **Runs:** 48 of 48 ok.  Every run has its requested number of events,
  with no Geant4 warnings and no overlaps reported when reading the GDML.
- **Reference check, electron e/mip:** 24 of 24 runs inside 0.55–1.0
  (0.681–0.887).  The new variants:
  - W0p7_Sc2_x120: 0.7969 ± 0.0012 / 0.7981 ± 0.0011 / 0.7815 ± 0.0010;
  - Pb1_LAr2_x120: 0.80567 ± 0.00095 / 0.8140 ± 0.0010 / 0.79912 ± 0.00093.
  As expected, finer sampling moves e/mip closer to 1.
- **Electron showers are contained longitudinally.**
  - The last layer holds (4.7–8.1) × 10⁻⁵ of the signal in the new
    variants.
  - The profiles in `plots/longitudinal_profile.png` fall to zero before
    the back.
  - Containment: W0p7_Sc2_x120 0.98101 ± 0.00037 / 0.98118 ± 0.00046 /
    0.98146 ± 0.00029; Pb1_LAr2_x120 0.97188 ± 0.00050 / 0.97187 ± 0.00040
    / 0.97130 ± 0.00036.
- **Pion showers are not contained**, as in round 1.
  - The new variants are 0.94–1.16 λ deep and hold 22–29 % of the pion
    energy.
  - Their profiles are flat to the back face.
  - Do not use the pion rows for conclusions.
- **Renders:** `render/W0p7_Sc2_x120__FTFP_BERT__e_1GeV_xz.png` shows
  material to 324 mm, then vacuum, as designed.
  - Its material panel shows about ten thick tungsten bands, not 120 thin
    layers.
  - The cause is that the mesh cells are coarser than the 2.7 mm layer
    pitch, so the cell centres alias the layering.  This is a sampling
    effect of the picture, not the geometry.
  - The same applies to the other 120-layer variants.
- **Tails in the electron signal:** the resolution is σ/mean of the
  active-layer signal, and its error assumes Gaussian fluctuations.  A few
  events far from the peak make both the value and its error unreliable.
  - In `runs/Pb1_Sc2_x120__FTFP_BERT__e_1GeV/events.csv.gz` two events have
    47 and 86 MeV of active signal.  The median is 185 MeV, and the lowest
    event under QGSP_BIC is 116 MeV.
  - Read the physics-list flags on resolution with this in mind (see
    below).

## Results — electrons (1 GeV), the electromagnetic objective

| variant | depth (mm / X₀) | resolution σ/E (FB / BIC / EMZ) | sampling fraction (FB) | containment (FB) |
|---|---|---|---|---|
| Pb1_LAr2_x120 | 360 / 23.1 | 0.05749 ± 0.00091 / 0.05829 ± 0.00093 / 0.05456 ± 0.00087 | 0.20128 ± 0.00024 | 0.97188 ± 0.00050 |
| Pb1_Sc2_x120 | 360 / 21.9 | 0.0633 ± 0.0010 / 0.05892 ± 0.00094 / 0.05924 ± 0.00094 | 0.19039 ± 0.00025 | 0.96966 ± 0.00062 |
| W0p7_Sc2_x120 | 324 / 24.5 | 0.0676 ± 0.0011 / 0.06242 ± 0.00099 / 0.06083 ± 0.00097 | 0.16494 ± 0.00025 | 0.98101 ± 0.00037 |
| Pb2_LAr4_x60 | 360 / 23.1 | 0.0762 ± 0.0012 / 0.0763 ± 0.0012 / 0.0752 ± 0.0012 | 0.18917 ± 0.00031 | 0.97136 ± 0.00042 |
| Pb2_Sc4_x60 | 360 / 21.9 | 0.0802 ± 0.0013 / 0.0811 ± 0.0013 / 0.0766 ± 0.0012 | 0.17475 ± 0.00031 | 0.97023 ± 0.00044 |
| W1p4_Sc4_x60 | 324 / 24.5 | 0.0843 ± 0.0013 / 0.0844 ± 0.0013 / 0.0817 ± 0.0013 | 0.15222 ± 0.00029 | 0.98167 ± 0.00025 |
| Fe6_Sc4_x60 | 600 / 21.0 | 0.0993 ± 0.0016 / 0.0972 ± 0.0016 / 0.0956 ± 0.0015 | 0.09232 ± 0.00020 | 0.97821 ± 0.00060 |
| Pb4_Sc4_x30 | 240 / 21.7 | 0.1209 ± 0.0019 / 0.1225 ± 0.0020 / 0.1176 ± 0.0019 | 0.09329 ± 0.00025 | 0.98038 ± 0.00028 |

The ranking is the same under all three lists.  The comparisons below are
my arithmetic on the table above.

**The round-2 questions:**

1. **Fine tungsten (W0p7_Sc2_x120): does it reach Pb1_Sc2 resolution in
   324 mm?**  Nearly, but not quite.
   - It is 6.9 / 5.9 / 2.7 % worse than Pb1_Sc2_x120 (+3.0 σ / +2.6 σ /
     +1.2 σ).
   - It is 36 mm shorter, 24.5 rather than 21.9 X₀ deep, and contains
     more of the shower (0.981 vs 0.970).
   - Against its coarse counterpart W1p4_Sc4_x60 it is 20–26 % better
     (10–13 σ).
2. **Fine liquid argon (Pb1_LAr2_x120): LAr or scintillator?**  LAr is the
   same or better, and its advantage is not yet established under every
   list.
   - It beats Pb1_Sc2_x120 by 9.1 % (−4.3 σ) under FTFP_BERT, 1.1 %
     (−0.5 σ) under QGSP_BIC and 7.9 % (−3.7 σ) under EMZ.
   - The FTFP_BERT scintillator value is inflated by the two low events
     noted under Validity.  So the clean comparisons are EMZ (LAr better
     at 3.7 σ) and QGSP_BIC (no difference).
   - LAr's sampling fraction is higher (0.201 vs 0.190).

**Sampling frequency:** halving both layer thicknesses improves σ/E
consistently.
- Pb2_Sc4 → Pb1_Sc2: 21–27 %.
- Pb2_LAr4 → Pb1_LAr2: 24–27 %.
- W1p4_Sc4 → W0p7_Sc2: 20–26 %.
- If σ/E scaled as the square root of the layer thickness, the gain would
  be 29 %.  The observed gains are somewhat smaller, as expected once
  other fluctuations (leakage, path-length) contribute.

**Trade-offs (the objective):**
- **Best resolution at 360 mm:** Pb1_LAr2_x120, best or tied best under
  all lists (0.055–0.058).  Pb1_Sc2_x120 is close (0.059–0.063).
- **Most compact for its resolution:** W0p7_Sc2_x120.  At 324 mm it is
  within 3–7 % of the best lead/scintillator design, and has the best
  electron containment (0.981).
- Unchanged from round 1: Pb4_Sc4_x30 is the shortest but worst, and
  Fe6_Sc4_x60 needs 600 mm.

## Results — pions (10 GeV)

The new variants contain 22–29 % of the pion energy, with e/π of
2.76–2.78 for W0p7_Sc2_x120 and 3.58–3.90 for Pb1_LAr2_x120.  As in round
1 these values measure leakage, not the calorimeter.  The contained design
is the `hcal` study (three variants approved, not yet run).

## Physics-list dependence

- **Electron resolution, EMZ vs FTFP_BERT:** EMZ gives a narrower
  resolution in all 8 variants, by 1.4–10.1 % (0.6–4.7 σ each).
  - Round 1 saw the same in 6 of 6, and the direction is now consistent
    across 8 designs.
  - The largest shift is W0p7_Sc2_x120 (−10.1 %, −4.7 σ, flagged).
- **Electron resolution, QGSP_BIC vs FTFP_BERT:**
  - The two lists share their EM physics, so for electrons they differ
    only in the hadronic models.  These cover photo- and electro-nuclear
    reactions and the neutrons they produce.
  - The two flagged cases (Pb1_Sc2_x120 −6.9 %, −3.2 σ; W0p7_Sc2_x120
    −7.7 %, −3.6 σ) are both 2 mm scintillator designs.
  - In Pb1_Sc2_x120 the FTFP_BERT width is driven by two low-tail events
    (see Validity).  Without them the three lists agree (checked by hand
    on the event file; not a pipeline metric).
  - In W0p7_Sc2_x120 FTFP_BERT has no such low events, and the difference
    is not explained here.
  - With Gaussian errors applied to a distribution that has tails, these
    flags are weak evidence.  A tail-insensitive width is proposed below.
- **Sampling fraction, EM option:** EMZ lowers the sampling fraction of
  thin active layers.  This is the round-1 effect, now seen in a second
  absorber.
  - 2 mm scintillator: −2.03 % (−11.4 σ) with lead, −1.94 % (−9.6 σ) with
    tungsten.
  - 2 mm LAr: −0.81 % (−4.9 σ; below the 1 % flag threshold).
  - 4 mm layers: −0.65 % to +0.26 %.
  - This is a calibration effect, not a ranking one.
- **Sampling fraction, QGSP_BIC vs FTFP_BERT:**
  - Two variants differ significantly:
    - Fe6_Sc4_x60 +1.24 % (+4.1 σ, round 1);
    - Pb1_LAr2_x120 +1.03 % (+6.0 σ) for electrons and +2.0 % (+3.3 σ)
      for pions.
  - The other six are within −0.14 % to +0.29 % (≤ 1.6 σ), including
    Pb2_LAr4_x60 at −0.01 %.
  - Round 1 suggested neutrons in hydrogen-rich scintillator as the cause.
    Liquid argon contains no hydrogen, so that cannot be the whole
    explanation.  The effect is real but not understood here.
- **Conclusion:** the electromagnetic ranking and the sampling-frequency
  rule hold under all lists.  Absolute energy scale and the small
  resolution differences depend on the list.

## Recommendation

- **Best electromagnetic resolution:** 1 mm lead with 2 mm active layers.
  Prefer liquid argon if the readout allows.  Its gain of up to 8–9 % is
  likely but not yet established under every list.
- **Depth-limited designs:** W0p7_Sc2_x120.  It gives near-best resolution
  in 324 mm with the best containment.
- **Calibration of thin-layer designs:** quote sampling fractions with the
  physics list.  They move by about 2 % between EM options for 2 mm
  scintillator, and by about 1 % between hadronic models in some designs.
- **Hadrons:** wait for `hcal`.

## Proposed next variants

These are proposals for approval.

```toml
[[variants]]   # compact and LAr together?
name = "W0p7_LAr2_x120"
absorber_material = "G4_W"
active_material = "G4_lAr"
absorber_mm = 0.7
active_mm = 2.0
layers = 120
note = "324 mm, as W0p7_Sc2_x120 with liquid argon"

[[variants]]   # does halving the layers keep paying?
name = "Pb0p5_Sc1_x240"
absorber_mm = 0.5
active_mm = 1.0
layers = 240
note = "360 mm; is the gain from halving still 20-27 %?"
```

- **More electrons:** 8000 per run (4×, now 2000).  This would halve the
  resolution errors and settle LAr vs scintillator (about 7 σ if the EMZ
  difference holds).  Electron runs take 18–141 s now, so up to about
  10 minutes each.
- **Proposed metric change (design stage):** add a tail-insensitive width
  next to σ/mean, e.g. half the 16–84 % range divided by the median, with
  a bootstrap error.  It changes `metrics.py`, not the runs, and would show
  whether the resolution flags between lists are tails or real.

## Limitations

As in round 1:
- **Deposited energy, not a detector signal:** no Birks quenching, LAr
  recombination, photostatistics or noise.  The LAr-vs-scintillator
  comparison is therefore about sampling alone.  Real light or charge
  yields would add terms that differ between the two.
- **Geometry:** 200 × 200 mm, too narrow for hadron showers.
- **Beam:** one energy per particle, a pencil beam at normal incidence.
